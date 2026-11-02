"""Read adapters; domain services remain authoritative for account/ownership rules."""
from datetime import date
from sqlalchemy.orm import joinedload
from app.models.work_record import WorkRecord, WorkFollowup
from app.services import work_record_service as domain
from app.services.assistant_contracts import bounded_text
from app.services.assistant_links import canonical_url


def link(record_id):
    return canonical_url("work_records.detail", record_id=record_id)


def summary(row):
    return {"id": row.id, "title": bounded_text(row.title, 160),
            "work_date": row.work_date.isoformat(), "followup_enabled": row.followup.enabled,
            "url": link(row.id)}


def list_records(actor, args):
    result = domain.list_records(actor, {"q": args.get("q", ""),
        "page": str(args.get("page", 1)),
        "follow": "" if args.get("follow", "all") == "all" else args["follow"]})
    return {"items": [summary(row) for row in result["rows"]],
            "page": result["page"], "has_next": result["has_next"]}


def get_record(actor, args):
    row = domain.own_record(actor, args["record_id"])
    result = summary(row)
    notes = bounded_text(row.notes, 10000, 12000)
    f = row.followup
    result.update(notes=notes, notes_truncated=notes != row.notes,
                  followup={"enabled": f.enabled, "reason": bounded_text(f.reason, 300),
                            "tentative_date": f.tentative_date.isoformat() if f.tentative_date else None})
    return result


def list_followups(actor, args):
    # Existing list_records filters work_date, not tentative_date. Keep that API intact.
    domain.authorize(actor)
    query = WorkRecord.query.join(WorkFollowup).options(joinedload(WorkRecord.followup)).filter(
        WorkRecord.owner_user_id == actor, WorkFollowup.enabled.is_(True))
    if "from" in args:
        query = query.filter(WorkFollowup.tentative_date >= date.fromisoformat(args["from"]))
    if "to" in args:
        query = query.filter(WorkFollowup.tentative_date <= date.fromisoformat(args["to"]))
    page = args.get("page", 1)
    rows = query.order_by(WorkFollowup.tentative_date, WorkRecord.id).offset((page - 1) * 10).limit(11).all()
    return {"items": [{"record_id": row.id, "title": bounded_text(row.title, 160),
                       "reason": bounded_text(row.followup.reason, 300, 600),
                       "tentative_date": row.followup.tentative_date.isoformat(), "url": link(row.id)}
                      for row in rows[:10]], "page": page, "has_next": len(rows) > 10}
