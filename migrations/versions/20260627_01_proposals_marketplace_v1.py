"""Create proposals marketplace v1.

Revision ID: 20260627_01
Revises: 20260626_01
Create Date: 2026-06-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20260627_01"
down_revision = "20260626_01"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    proposal_columns = {
        column["name"]
        for column in inspector.get_columns("proposal_requests")
    }

    def add_proposal_column(column):
        if column.name not in proposal_columns:
            op.add_column("proposal_requests", column)

    add_proposal_column(sa.Column("owner_user_id", sa.Integer(), nullable=True))
    add_proposal_column(sa.Column("industria", sa.String(length=120), nullable=True))
    add_proposal_column(sa.Column("rubro", sa.String(length=120), nullable=True))
    add_proposal_column(sa.Column("especialidad", sa.String(length=120), nullable=True))
    add_proposal_column(sa.Column("titulo", sa.String(length=160), nullable=True))
    add_proposal_column(sa.Column("ubicacion", sa.String(length=120), nullable=True))
    add_proposal_column(sa.Column("modalidad", sa.String(length=80), nullable=True))
    add_proposal_column(sa.Column("cantidad_profesionales", sa.Integer(), nullable=False, server_default="1"))
    add_proposal_column(sa.Column("fecha_inicio_estimada", sa.Date(), nullable=True))
    add_proposal_column(sa.Column("fecha_limite_postulacion", sa.Date(), nullable=True))
    add_proposal_column(sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))

    op.execute(
        """
        UPDATE proposal_requests
        SET owner_user_id = cliente_id,
            titulo = COALESCE(titulo, 'Propuesta de ' || categoria),
            industria = COALESCE(industria, 'Servicios tecnicos'),
            rubro = COALESCE(rubro, categoria),
            modalidad = COALESCE(modalidad, 'A coordinar'),
            estado = CASE
                WHEN estado IN ('ABIERTA', 'RECIBIENDO_PROPUESTAS') THEN 'PUBLICADA'
                ELSE estado
            END
        """
    )

    if not inspector.has_table("proposal_applications"):
        op.create_table(
            "proposal_applications",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("proposal_id", sa.Integer(), nullable=False),
            sa.Column("professional_id", sa.Integer(), nullable=False),
            sa.Column("professional_user_id", sa.Integer(), nullable=False),
            sa.Column("mensaje", sa.Text(), nullable=False),
            sa.Column("experiencia_relevante", sa.Text(), nullable=True),
            sa.Column("disponibilidad", sa.String(length=160), nullable=True),
            sa.Column("pretension_economica", sa.Numeric(precision=12, scale=2), nullable=True),
            sa.Column("estado", sa.String(length=50), nullable=False, server_default="POSTULADA"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["professional_id"], ["professionals.id"]),
            sa.ForeignKeyConstraint(["professional_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["proposal_id"], ["proposal_requests.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("proposal_id", "professional_id", name="uq_proposal_application_professional"),
        )


def downgrade():
    op.drop_table("proposal_applications")
    op.drop_column("proposal_requests", "created_at")
    op.drop_column("proposal_requests", "fecha_limite_postulacion")
    op.drop_column("proposal_requests", "fecha_inicio_estimada")
    op.drop_column("proposal_requests", "cantidad_profesionales")
    op.drop_column("proposal_requests", "modalidad")
    op.drop_column("proposal_requests", "ubicacion")
    op.drop_column("proposal_requests", "titulo")
    op.drop_column("proposal_requests", "especialidad")
    op.drop_column("proposal_requests", "rubro")
    op.drop_column("proposal_requests", "industria")
    op.drop_column("proposal_requests", "owner_user_id")
