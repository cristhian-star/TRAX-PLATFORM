from app import db


class EmergencyConfiguration(db.Model):
    __tablename__ = 'emergency_configurations'
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id', ondelete='RESTRICT'), primary_key=True)
    mode = db.Column(db.String(10), nullable=False)
    package_amount = db.Column(db.Numeric(12, 2))
    visit_amount = db.Column(db.Numeric(12, 2))
    diagnosis_amount = db.Column(db.Numeric(12, 2))
    discount_repair = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.String(2000), nullable=False, default='')
    repair_materials_separate = db.Column(db.Boolean, nullable=False, default=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    __table_args__ = (
        db.CheckConstraint("mode IN ('PACKAGE','SEPARATE')", name='ck_emergency_config_mode'),
        db.CheckConstraint("(mode = 'PACKAGE' AND visit_amount IS NULL AND diagnosis_amount IS NULL) OR (mode = 'SEPARATE' AND package_amount IS NULL)", name='ck_emergency_config_applicable'),
        db.CheckConstraint('version >= 1', name='ck_emergency_config_version'),
        db.CheckConstraint('repair_materials_separate', name='ck_emergency_config_separate'),
        *(db.CheckConstraint(f'{name} IS NULL OR ({name} >= 0 AND {name} <= 9999999999.99)', name=f'ck_emergency_config_{name}') for name in ('package_amount','visit_amount','diagnosis_amount')),
    )
