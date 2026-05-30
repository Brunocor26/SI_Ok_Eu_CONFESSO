"""rename username to user_id, add email

Revision ID: 025c0bf1ea59
Revises: 543cc333c559
Create Date: 2026-05-30 15:35:49.593177

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '025c0bf1ea59'
down_revision = '543cc333c559'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('email', sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint('uq_users_user_id', ['user_id'])
        batch_op.create_unique_constraint('uq_users_email', ['email'])
        batch_op.drop_column('username')


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('username', sa.VARCHAR(length=50), nullable=False))
        batch_op.drop_constraint('uq_users_email', type_='unique')
        batch_op.drop_constraint('uq_users_user_id', type_='unique')
        batch_op.drop_column('email')
        batch_op.drop_column('user_id')
