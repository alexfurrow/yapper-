"""Replace entry_id with user_and_entry_id as primary key

Revision ID: replace_entry_id_with_user_and_entry_id
Revises: add_title_date_column
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'replace_entry_id_with_user_and_entry_id'
down_revision = 'add_title_date_column'
branch_labels = None
depends_on = None

def upgrade():
    # Step 1: Add the new user_and_entry_id column (nullable initially)
    op.add_column('entries', sa.Column('user_and_entry_id', sa.String(), nullable=True))
    
    # Step 2: Populate user_and_entry_id with concatenated values
    # Format: user_id + '_' + user_entry_id
    op.execute("""
        UPDATE entries 
        SET user_and_entry_id = user_id || '_' || user_entry_id::text
        WHERE user_id IS NOT NULL AND user_entry_id IS NOT NULL
    """)
    
    # Step 3: Make user_and_entry_id NOT NULL (now that it's populated)
    op.alter_column('entries', 'user_and_entry_id', nullable=False)
    
    # Step 4: Drop the old primary key constraint on entry_id
    op.drop_constraint('entries_pkey', 'entries', type_='primary')
    
    # Step 5: Create new primary key on user_and_entry_id
    op.create_primary_key('entries_pkey', 'entries', ['user_and_entry_id'])
    
    # Step 6: Drop the old entry_id column
    op.drop_column('entries', 'entry_id')

def downgrade():
    # Step 1: Add back entry_id column
    op.add_column('entries', sa.Column('entry_id', sa.Integer(), nullable=True))
    
    # Step 2: Populate entry_id with a sequence (this will lose original IDs)
    op.execute("""
        UPDATE entries 
        SET entry_id = row_number() OVER (ORDER BY created_at)
    """)
    
    # Step 3: Make entry_id NOT NULL
    op.alter_column('entries', 'entry_id', nullable=False)
    
    # Step 4: Drop the new primary key
    op.drop_constraint('entries_pkey', 'entries', type_='primary')
    
    # Step 5: Create primary key on entry_id
    op.create_primary_key('entries_pkey', 'entries', ['entry_id'])
    
    # Step 6: Drop user_and_entry_id column
    op.drop_column('entries', 'user_and_entry_id')

