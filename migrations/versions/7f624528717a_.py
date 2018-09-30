"""empty message

Revision ID: 7f624528717a
Revises: 16bf3770079e
Create Date: 2018-09-28 23:51:47.514231

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f624528717a'
down_revision = '16bf3770079e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('join_date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'join_date')
    # ### end Alembic commands ###
