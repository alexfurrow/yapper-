"""Add user_entry_id column

Revision ID: add_user_entry_id
Revises: add_user_security_fields
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_user_entry_id'
down_revision = 'add_user_security_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Add user_entry_id column
    op.add_column('entries', sa.Column('user_entry_id', sa.Integer(), nullable=True))
    
    # Create index for better performance
    op.create_index('idx_entries_user_entry_id', 'entries', ['user_id', 'user_entry_id'])

def downgrade():
    # Remove index
    op.drop_index('idx_entries_user_entry_id', 'entries')
    
    # Remove column
    op.drop_column('entries', 'user_entry_id')
