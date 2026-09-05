"""Add the PRO entitlement source discriminator.

The downgrade is structurally reversible but intentionally drops source_type.
TRANSACTIONAL/SUBSCRIPTION classifications are therefore lost and return as
NULL after a later re-upgrade. Back up the data and require explicit approval
before downgrading any database where that classification must be preserved.

Revision ID: 20260904_01
Revises: 20260726_07
Create Date: 2026-09-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260904_01"
down_revision: Union[str, Sequence[str], None] = "20260726_07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SOURCE_CHECK = "ck_subscriptions_source_type_valid"


def upgrade() -> None:
    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.add_column(sa.Column("source_type", sa.String(length=50), nullable=True))
        batch_op.create_check_constraint(
            SOURCE_CHECK,
            "source_type IS NULL OR source_type IN ('TRANSACTIONAL', 'SUBSCRIPTION')",
        )


def downgrade() -> None:
    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.drop_constraint(SOURCE_CHECK, type_="check")
        batch_op.drop_column("source_type")
