"""Add BtoB features tables

Revision ID: 002_add_btob_features_tables
Revises: 001_initial_migration
Create Date: 2025-01-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002_add_btob_features_tables'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create employees table
    op.create_table('employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('employee_code', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employees_id'), 'employees', ['id'], unique=False)
    op.create_index(op.f('ix_employees_user_id'), 'employees', ['user_id'], unique=True)
    op.create_index(op.f('ix_employees_employee_code'), 'employees', ['employee_code'], unique=True)

    # Create reduction_records table (CO2削減記録)
    op.create_table('reduction_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('energy_type', sa.Enum('electricity', 'gas', name='energy_type_enum'), nullable=False),
        sa.Column('usage', sa.Float(), nullable=False, comment='実際の使用量'),
        sa.Column('baseline', sa.Float(), nullable=False, comment='ベースライン使用量'),
        sa.Column('reduced_co2_kg', sa.Float(), nullable=False, comment='削減されたCO2量(kg)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reduction_records_id'), 'reduction_records', ['id'], unique=False)
    op.create_index(op.f('ix_reduction_records_user_id'), 'reduction_records', ['user_id'], unique=False)
    op.create_index(op.f('ix_reduction_records_date'), 'reduction_records', ['date'], unique=False)

    # Create point_rules table (ポイント付与ルール)
    op.create_table('point_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('rule_type', sa.Enum('per_kg', 'rank_bonus', name='rule_type_enum'), nullable=False),
        sa.Column('value', sa.Float(), nullable=False, comment='per_kg: CO2 1kg当たりのポイント, rank_bonus: 順位ボーナスポイント'),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_point_rules_id'), 'point_rules', ['id'], unique=False)

    # Create points_ledger table (ポイント履歴)
    op.create_table('points_ledger',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False, comment='ポイント増減（正=付与、負=消費）'),
        sa.Column('reason', sa.String(length=200), nullable=False, comment='付与・消費理由'),
        sa.Column('reference_id', sa.Integer(), nullable=True, comment='関連する削減記録や交換記録のID'),
        sa.Column('balance_after', sa.Integer(), nullable=False, comment='処理後のポイント残高'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_points_ledger_id'), 'points_ledger', ['id'], unique=False)
    op.create_index(op.f('ix_points_ledger_user_id'), 'points_ledger', ['user_id'], unique=False)

    # Create rewards table (景品)
    op.create_table('rewards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('stock', sa.Integer(), nullable=False, default=0),
        sa.Column('points_required', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rewards_id'), 'rewards', ['id'], unique=False)
    op.create_index(op.f('ix_rewards_category'), 'rewards', ['category'], unique=False)

    # Create redemptions table (景品交換履歴)
    op.create_table('redemptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reward_id', sa.Integer(), nullable=False),
        sa.Column('points_spent', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('申請中', '承認', '却下', '発送済', name='redemption_status_enum'), nullable=False, default='申請中'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reward_id'], ['rewards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_redemptions_id'), 'redemptions', ['id'], unique=False)
    op.create_index(op.f('ix_redemptions_user_id'), 'redemptions', ['user_id'], unique=False)

    # Create report_jobs table (レポート生成ジョブ)
    op.create_table('report_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('range_start', sa.Date(), nullable=False),
        sa.Column('range_end', sa.Date(), nullable=False),
        sa.Column('granularity', sa.Enum('monthly', 'quarterly', 'yearly', name='granularity_enum'), nullable=False),
        sa.Column('status', sa.Enum('queued', 'done', 'failed', name='job_status_enum'), nullable=False, default='queued'),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_jobs_id'), 'report_jobs', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_report_jobs_id'), table_name='report_jobs')
    op.drop_table('report_jobs')
    
    op.drop_index(op.f('ix_redemptions_user_id'), table_name='redemptions')
    op.drop_index(op.f('ix_redemptions_id'), table_name='redemptions')
    op.drop_table('redemptions')
    
    op.drop_index(op.f('ix_rewards_category'), table_name='rewards')
    op.drop_index(op.f('ix_rewards_id'), table_name='rewards')
    op.drop_table('rewards')
    
    op.drop_index(op.f('ix_points_ledger_user_id'), table_name='points_ledger')
    op.drop_index(op.f('ix_points_ledger_id'), table_name='points_ledger')
    op.drop_table('points_ledger')
    
    op.drop_index(op.f('ix_point_rules_id'), table_name='point_rules')
    op.drop_table('point_rules')
    
    op.drop_index(op.f('ix_reduction_records_date'), table_name='reduction_records')
    op.drop_index(op.f('ix_reduction_records_user_id'), table_name='reduction_records')
    op.drop_index(op.f('ix_reduction_records_id'), table_name='reduction_records')
    op.drop_table('reduction_records')
    
    op.drop_index(op.f('ix_employees_employee_code'), table_name='employees')
    op.drop_index(op.f('ix_employees_user_id'), table_name='employees')
    op.drop_index(op.f('ix_employees_id'), table_name='employees')
    op.drop_table('employees')