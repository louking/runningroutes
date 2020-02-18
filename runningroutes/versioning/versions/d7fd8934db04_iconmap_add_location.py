"""iconmap: add location

Revision ID: d7fd8934db04
Revises: 3928a3dca4be
Create Date: 2020-02-15 15:04:44.207540

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import runningroutes

# revision identifiers, used by Alembic.
revision = 'd7fd8934db04'
down_revision = '3928a3dca4be'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('icon', 'isAddrShown',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    op.alter_column('icon', 'isShownInTable',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    op.alter_column('icon', 'isShownOnMap',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    op.add_column('iconmap', sa.Column('location_id', sa.Integer(), nullable=True))
    op.alter_column('iconmap', 'page_description',
               existing_type=mysql.VARCHAR(length=512),
               type_=sa.String(length=2048),
               existing_nullable=True)
    op.create_foreign_key(None, 'iconmap', 'location', ['location_id'], ['id'])
    op.alter_column('interest', 'public',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    op.alter_column('location', 'geoloc_required',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    op.alter_column('route', 'active',
               existing_type=mysql.TINYINT(display_width=1),
               type_=runningroutes.models.LiberalBoolean(),
               existing_nullable=True)
    op.alter_column('user', 'active',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'active',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('route', 'active',
               existing_type=runningroutes.models.LiberalBoolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('location', 'geoloc_required',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('interest', 'public',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.drop_constraint(None, 'iconmap', type_='foreignkey')
    op.alter_column('iconmap', 'page_description',
               existing_type=sa.String(length=2048),
               type_=mysql.VARCHAR(length=512),
               existing_nullable=True)
    op.drop_column('iconmap', 'location_id')
    op.alter_column('icon', 'isShownOnMap',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('icon', 'isShownInTable',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('icon', 'isAddrShown',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    # ### end Alembic commands ###
