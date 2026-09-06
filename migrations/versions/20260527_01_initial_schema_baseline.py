"""initial_schema_baseline

Revision ID: 20260527_01
Revises:
Create Date: 2026-05-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260527_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=50), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False),
        sa.Column("motivo_estado", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_table(
        "category_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre_rubro", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("email_notificacion", sa.String(length=120), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "professionals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("servicio", sa.String(length=120), nullable=False),
        sa.Column("zona", sa.String(length=120), nullable=False),
        sa.Column("telefono", sa.String(length=50), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("especialidad", sa.String(length=120), nullable=True),
        sa.Column("anios_experiencia", sa.Integer(), nullable=True),
        sa.Column("tipo_credencial", sa.String(length=120), nullable=True),
        sa.Column("numero_credencial", sa.String(length=120), nullable=True),
        sa.Column("certificaciones_text", sa.Text(), nullable=True),
        sa.Column("portfolio_urls", sa.Text(), nullable=True),
        sa.Column("estado_perfil", sa.String(length=50), nullable=False),
        sa.Column("perfil_completo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "budget_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("categoria", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("zona", sa.String(length=120), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "contract_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("professional_user_id", sa.Integer(), nullable=True),
        sa.Column("servicio", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("precio_acordado", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.Column("fecha_inicio", sa.DateTime(), nullable=True),
        sa.Column("fecha_fin", sa.DateTime(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["cliente_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["professional_id"], ["professionals.id"]),
        sa.ForeignKeyConstraint(["professional_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "emergency_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("categoria", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("zona", sa.String(length=120), nullable=False),
        sa.Column("prioridad", sa.String(length=50), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "proposal_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("categoria", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("presupuesto_estimado", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("fecha_limite", sa.DateTime(), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "reputation_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tipo_evento", sa.String(length=80), nullable=False),
        sa.Column("puntos", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["professional_id"], ["professionals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan", sa.String(length=50), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "terms_acceptances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tipo_termino", sa.String(length=120), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "verification_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tipo_usuario", sa.String(length=50), nullable=False),
        sa.Column("documento_identidad", sa.String(length=255), nullable=True),
        sa.Column("certificado_oficio", sa.String(length=255), nullable=True),
        sa.Column("titulo_profesional", sa.String(length=255), nullable=True),
        sa.Column("material_probatorio", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewer_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "abuse_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("reported_user_id", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["reported_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("abuse_reports")
    op.drop_table("verification_requests")
    op.drop_table("terms_acceptances")
    op.drop_table("subscriptions")
    op.drop_table("reviews")
    op.drop_table("reputation_events")
    op.drop_table("proposal_requests")
    op.drop_table("emergency_requests")
    op.drop_table("contract_requests")
    op.drop_table("budget_requests")
    op.drop_table("audit_logs")
    op.drop_table("professionals")
    op.drop_table("category_requests")
    op.drop_table("categories")
    op.drop_table("users")
