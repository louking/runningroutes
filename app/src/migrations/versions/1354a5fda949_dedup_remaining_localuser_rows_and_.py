"""dedup remaining exact-duplicate localuser rows and enforce uniqueness (louking/runningroutes#182)

Revision ID: 1354a5fda949
Revises: c5920aeabfbb
Create Date: 2026-08-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1354a5fda949'
down_revision = 'c5920aeabfbb'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


# c5920aeabfbb left any (user_id, interest_id) group alone if more than one row in it was
# active, since it couldn't tell which active row was "correct". #182 root-caused those
# leftover groups: docker-compose.yml hardcodes "--workers=4" with no env var indirection, so
# every boot starts 4 gunicorn workers that each independently call
# create_app() -> update_local_tables(). ManageLocalTables.update() (loutilities/user/model.py)
# had no locking, so concurrently booting workers could each find no existing localuser row
# for a newly-synced (user_id, interest_id) and insert their own -- one duplicate row per
# worker, racing before any could see the others' insert. This is louking/runningroutes#180
# (18 affected users on production) and the same race also produced #181 (StaleDataError at
# worker boot). update() now takes a lockfile (see models.py:update_local_tables(),
# loutilities>=3.13.1) that serializes those workers, so this specific race can't recur -- but
# the rows it already created are still sitting in the table.
#
# c5920aeabfbb's own comment guessed, based on inspection against a production-backup
# snapshot, that all leftover groups would turn out content-identical (differing only in
# version_id, never in copied fields) once actually collapsed. Running this migration against
# the dev database (loaded from a similar production-style snapshot) falsified that guess for
# 2 of the then-17 users (4 groups: user_id 164 and 175, both interests) -- their master User
# row's `name` was edited (a trailing space trimmed for one, "User" corrected to "Test User"
# for the other) *after* the duplicate rows were created, and ManageLocalTables's dict-based
# tracking (see loutilities/user/model.py:_updateuser_byinterest -- `alllocal[user_id,
# interest_id] = localuser` overwrites on each row seen, so whichever row a plain query
# happens to return last for that key is the only one still receiving future syncs) kept
# re-syncing only one row per group, leaving the others stuck with the pre-edit content. In
# both users' groups, the row with the highest `version_id` (2, vs. 1 for its groupmates) is
# also the row with the highest `id` and holds the corrected data -- confirming it's the row
# ManageLocalTables has been (and will keep) updating, and the rest are permanently orphaned.
#
# Given that, requiring exact content match before collapsing a group is stricter than
# necessary: version_id is direct evidence of which row is still live, regardless of whether
# an intervening edit has made the rest of the group diverge in content. This migration ranks
# each group by version_id DESC, active DESC, id DESC and keeps only rn=1, unconditionally --
# every (user_id, interest_id) group of more than one row is a duplicate-insert race artifact
# by construction (routes.localuser has no other table's FK pointing at it, confirmed by
# inspection), so there's no case where collapsing to the most-recently-synced row is wrong.
#
# Then adds a UNIQUE constraint on (user_id, interest_id) so this class of duplicate can't be
# created again by any future bug -- defense in depth alongside the update() locking fix. MySQL
# does not enforce uniqueness among NULLs, so rows with NULL user_id or interest_id are
# unaffected.
_DEDUP_LOCALUSER_SQL = """
WITH ranked AS (
    SELECT id,
           ROW_NUMBER() OVER (
               PARTITION BY user_id, interest_id
               ORDER BY version_id DESC, active DESC, id DESC
           ) AS rn,
           COUNT(*) OVER (PARTITION BY user_id, interest_id) AS grp_count
    FROM localuser
    WHERE user_id IS NOT NULL AND interest_id IS NOT NULL
)
DELETE FROM localuser WHERE id IN (
    SELECT id FROM (
        SELECT id FROM ranked
        WHERE grp_count > 1 AND rn > 1
    ) AS to_delete
)
"""


def upgrade_():
    op.get_bind().execute(sa.text(_DEDUP_LOCALUSER_SQL))
    op.create_unique_constraint('uq_localuser_user_interest', 'localuser', ['user_id', 'interest_id'])


def downgrade_():
    op.drop_constraint('uq_localuser_user_interest', 'localuser', type_='unique')
    # data cleanup only -- deleted duplicate rows can't be reconstructed
