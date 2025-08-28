"""Add user security fields

Revision ID: add_user_security_fields
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_user_security_fields'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to users table
    op.add_column('users', sa.Column('email', sa.String(120), nullable=True))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('email_verification_token', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('password_reset_token', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('account_locked_until', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    
    # Create unique index on email
    op.create_unique_constraint('uq_users_email', 'users', ['email'])
    
    # Create unique index on email_verification_token
    op.create_unique_constraint('uq_users_email_verification_token', 'users', ['email_verification_token'])
    
    # Create unique index on password_reset_token
    op.create_unique_constraint('uq_users_password_reset_token', 'users', ['password_reset_token'])

def downgrade():
    # Remove unique constraints
    op.drop_constraint('uq_users_password_reset_token', 'users', type_='unique')
    op.drop_constraint('uq_users_email_verification_token', 'users', type_='unique')
    op.drop_constraint('uq_users_email', 'users', type_='unique')
    
    # Remove columns
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'account_locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'password_reset_expires')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'email')
