"""added quantity in order

Revision ID: e67e8b65c842
Revises: d7ef812070b5
Create Date: 2020-08-23 20:53:23.495172

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e67e8b65c842'
down_revision = 'd7ef812070b5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders_received', sa.Column('quantity', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orders_received', 'quantity')
    # ### end Alembic commands ###