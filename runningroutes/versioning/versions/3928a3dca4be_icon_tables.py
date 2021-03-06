"""icon tables

Revision ID: 3928a3dca4be
Revises: 
Create Date: 2020-02-09 13:11:43.570637

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import runningroutes

# revision identifiers, used by Alembic.
revision = '3928a3dca4be'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('location',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('version_id', sa.Integer(), nullable=False),
    sa.Column('location', sa.String(length=256), nullable=True),
    sa.Column('geoloc_required', sa.Boolean(), nullable=True),
    sa.Column('cached', sa.DateTime(), nullable=True),
    sa.Column('lat', sa.Float(), nullable=True),
    sa.Column('lng', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('icon',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('version_id', sa.Integer(), nullable=False),
    sa.Column('interest_id', sa.Integer(), nullable=True),
    sa.Column('icon', sa.String(length=32), nullable=True),
    sa.Column('legend_text', sa.String(length=64), nullable=True),
    sa.Column('svg_file_id', sa.String(length=50), nullable=True),
    sa.Column('color', sa.String(length=32), nullable=True),
    sa.Column('isShownOnMap', sa.Boolean(), nullable=True),
    sa.Column('isShownInTable', sa.Boolean(), nullable=True),
    sa.Column('isAddrShown', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['interest_id'], ['interest.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('iconmap',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('version_id', sa.Integer(), nullable=False),
    sa.Column('interest_id', sa.Integer(), nullable=True),
    sa.Column('page_title', sa.String(length=32), nullable=True),
    sa.Column('page_description', sa.String(length=512), nullable=True),
    sa.ForeignKeyConstraint(['interest_id'], ['interest.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('iconsubtype',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('version_id', sa.Integer(), nullable=False),
    sa.Column('interest_id', sa.Integer(), nullable=True),
    sa.Column('iconsubtype', sa.String(length=32), nullable=True),
    sa.ForeignKeyConstraint(['interest_id'], ['interest.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('iconlocation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('version_id', sa.Integer(), nullable=False),
    sa.Column('interest_id', sa.Integer(), nullable=True),
    sa.Column('locname', sa.String(length=64), nullable=True),
    sa.Column('icon_id', sa.Integer(), nullable=True),
    sa.Column('iconsubtype_id', sa.Integer(), nullable=True),
    sa.Column('location_id', sa.Integer(), nullable=True),
    sa.Column('location_popup_text', sa.String(length=256), nullable=True),
    sa.Column('contact_name', sa.String(length=256), nullable=True),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('phone', sa.String(length=16), nullable=True),
    sa.Column('addl_text', sa.String(length=64), nullable=True),
    sa.ForeignKeyConstraint(['icon_id'], ['icon.id'], ),
    sa.ForeignKeyConstraint(['iconsubtype_id'], ['iconsubtype.id'], ),
    sa.ForeignKeyConstraint(['interest_id'], ['interest.id'], ),
    sa.ForeignKeyConstraint(['location_id'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.alter_column('interest', 'public',
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
    op.alter_column('interest', 'public',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.drop_table('iconlocation')
    op.drop_table('iconsubtype')
    op.drop_table('iconmap')
    op.drop_table('icon')
    op.drop_table('location')
    # ### end Alembic commands ###
