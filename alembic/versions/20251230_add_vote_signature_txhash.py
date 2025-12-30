"""add signature, tx_hash, wallet_address to votes

Revision ID: 20251230_add_vote_signature_txhash
Revises: 20251229_add_election_admins_and_columns
Create Date: 2025-12-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251230_add_vote_signature_txhash'
down_revision = '20251229_add_election_admins_and_columns'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('votes', sa.Column('signature', sa.String(), nullable=True))
    op.add_column('votes', sa.Column('tx_hash', sa.String(), nullable=True))
    op.add_column('votes', sa.Column('wallet_address', sa.String(), nullable=True))


def downgrade():
    op.drop_column('votes', 'wallet_address')
    op.drop_column('votes', 'tx_hash')
    op.drop_column('votes', 'signature')
