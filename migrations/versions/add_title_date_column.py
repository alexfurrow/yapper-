"""Add title_date column to entries table

Revision ID: add_title_date_column
Revises: add_user_entry_id
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_title_date_column'
down_revision = 'add_user_entry_id'
branch_labels = None
depends_on = None

def upgrade():
    # Add title_date column as text (nullable, since existing entries won't have it)
    op.add_column('entries', sa.Column('title_date', sa.Text(), nullable=True))

def downgrade():
    # Remove title_date column
    op.drop_column('entries', 'title_date')

