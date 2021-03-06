"""empty message

Revision ID: af37dc82768d
Revises: 8217afe681c9
Create Date: 2020-10-07 12:47:40.350090

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af37dc82768d'
down_revision = '8217afe681c9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('upload_errors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('datetime', sa.DATETIME(), nullable=True),
    sa.Column('model', sa.String(length=64), nullable=True),
    sa.Column('details', sa.TEXT(), nullable=True),
    sa.Column('error', sa.TEXT(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.alter_column('catalog', 'mrp',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('catalog', 'mrp',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.drop_table('upload_errors')
    # ### end Alembic commands ###
