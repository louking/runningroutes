"""dedup localuser rows from active-filter bug (loutilities#103)

Revision ID: c5920aeabfbb
Revises: 859a4f2134a0
Create Date: 2026-08-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c5920aeabfbb'
down_revision = '859a4f2134a0'
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


# ManageLocalTables._updateuser_byinterest() (loutilities/user/model.py) used to seed
# its "which rows already exist" lookup from active=True rows only. Once a localuser
# row's active flag went False, the next update_local_tables() call couldn't find it,
# so it inserted a duplicate row instead of updating the existing one -- one new
# duplicate per call, forever, for every inactive user. Fixed in loutilities#103
# (loutilities==3.13.0). This migration cleans up the rows that bug already created.
#
# No other table has a ForeignKey to routes.localuser.id, so there's no FK-preference
# tier here -- just:
#   - prefer the active row
#   - else keep the lowest id (oldest row)
#
# A group is left untouched (no deletes at all) if more than one row in it is active --
# a genuine ambiguity this automated pass can't safely resolve; review those manually.
# Confirmed against a production-backup snapshot loaded into dev (2026-08-17): 44
# duplicate (user_id, interest_id) groups, 3,006 total rows. 10 groups fit the
# active-flag bug exactly (all rows inactive, cleaned automatically). The other 34
# groups (17 distinct users, both interests) are a *different* bug, much more prevalent
# here than in contracts (louking/contracts#578): 4 exact-duplicate *active* rows per
# group. 15 of the 17 users have all 4 rows fully identical (same version_id, no
# distinguishing signal at all); only 2 have one row synced more recently than the
# other 3. Left alone here deliberately; see louking/runningroutes#180 for the
# followup issue.
_DEDUP_LOCALUSER_SQL = """
WITH ranked AS (
    SELECT id,
           ROW_NUMBER() OVER (
               PARTITION BY user_id, interest_id
               ORDER BY active DESC, id ASC
           ) AS rn,
           COUNT(*) OVER (PARTITION BY user_id, interest_id) AS grp_count,
           SUM(active) OVER (PARTITION BY user_id, interest_id) AS grp_active_count
    FROM localuser
    WHERE user_id IS NOT NULL AND interest_id IS NOT NULL
)
DELETE FROM localuser WHERE id IN (
    SELECT id FROM (
        SELECT id FROM ranked
        WHERE grp_count > 1 AND rn > 1 AND grp_active_count <= 1
    ) AS to_delete
)
"""


def upgrade_():
    op.get_bind().execute(sa.text(_DEDUP_LOCALUSER_SQL))


def downgrade_():
    # data cleanup only -- deleted duplicate rows can't be reconstructed
    pass
