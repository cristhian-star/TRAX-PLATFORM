from app import db
from app.models.abuse_report import AbuseReport


def create_abuse_report(reporter_id, reported_user_id, motivo, descripcion=None):
    abuse_report = AbuseReport(
        reporter_id=reporter_id,
        reported_user_id=reported_user_id,
        motivo=motivo,
        descripcion=descripcion
    )

    db.session.add(abuse_report)
    db.session.commit()

    return abuse_report


def get_open_reports():
    return (
        AbuseReport.query
        .filter(AbuseReport.estado.in_(("ABIERTO", "EN_REVISION")))
        .order_by(AbuseReport.created_at.asc())
        .all()
    )


def update_report_status(abuse_report_id, estado, reviewed_by=None):
    if estado not in AbuseReport.ESTADOS:
        raise ValueError("Estado de reporte invalido")

    abuse_report = AbuseReport.query.get(abuse_report_id)

    if abuse_report is None:
        return None

    abuse_report.estado = estado
    abuse_report.reviewed_by = reviewed_by
    db.session.commit()

    return abuse_report
