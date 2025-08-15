"""Initial migration

Revision ID: 001_initial_migration
Revises: 
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_superuser', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create devices table
    op.create_table('devices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('device_type', sa.String(length=100), nullable=False),
    sa.Column('model', sa.String(length=255), nullable=True),
    sa.Column('serial_number', sa.String(length=255), nullable=True),
    sa.Column('capacity', sa.Float(), nullable=True),
    sa.Column('efficiency', sa.Float(), nullable=True),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('installation_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_maintenance', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_devices_id'), 'devices', ['id'], unique=False)
    op.create_index(op.f('ix_devices_serial_number'), 'devices', ['serial_number'], unique=True)

    # Create energy_records table
    op.create_table('energy_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('energy_produced', sa.Float(), nullable=True),
    sa.Column('energy_consumed', sa.Float(), nullable=True),
    sa.Column('energy_stored', sa.Float(), nullable=True),
    sa.Column('grid_import', sa.Float(), nullable=True),
    sa.Column('grid_export', sa.Float(), nullable=True),
    sa.Column('voltage', sa.Float(), nullable=True),
    sa.Column('current', sa.Float(), nullable=True),
    sa.Column('power', sa.Float(), nullable=True),
    sa.Column('temperature', sa.Float(), nullable=True),
    sa.Column('efficiency', sa.Float(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('device_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_energy_records_id'), 'energy_records', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_energy_records_id'), table_name='energy_records')
    op.drop_table('energy_records')
    op.drop_index(op.f('ix_devices_serial_number'), table_name='devices')
    op.drop_index(op.f('ix_devices_id'), table_name='devices')
    op.drop_table('devices')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')