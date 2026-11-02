"""Common visit/diagnosis tariff; coverage remains canonical on professionals."""
from alembic import op
import sqlalchemy as sa

revision = '20261028_01'
down_revision = '20261026_01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('emergency_configurations',
        sa.Column('professional_id', sa.Integer(), sa.ForeignKey('professionals.id', ondelete='RESTRICT'), primary_key=True),
        sa.Column('mode', sa.String(10), nullable=False),
        sa.Column('package_amount', sa.Numeric(12, 2)),
        sa.Column('visit_amount', sa.Numeric(12, 2)),
        sa.Column('diagnosis_amount', sa.Numeric(12, 2)),
        sa.Column('discount_repair', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.String(2000), nullable=False),
        sa.Column('repair_materials_separate', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.CheckConstraint("mode IN ('PACKAGE','SEPARATE')", name='ck_emergency_config_mode'),
        sa.CheckConstraint("(mode = 'PACKAGE' AND visit_amount IS NULL AND diagnosis_amount IS NULL) OR (mode = 'SEPARATE' AND package_amount IS NULL)", name='ck_emergency_config_applicable'),
        sa.CheckConstraint('version >= 1', name='ck_emergency_config_version'),
        sa.CheckConstraint('repair_materials_separate', name='ck_emergency_config_separate'),
        *(sa.CheckConstraint(f'{name} IS NULL OR ({name} >= 0 AND {name} <= 9999999999.99)', name=f'ck_emergency_config_{name}') for name in ('package_amount','visit_amount','diagnosis_amount')))


def downgrade():
    op.drop_table('emergency_configurations')
