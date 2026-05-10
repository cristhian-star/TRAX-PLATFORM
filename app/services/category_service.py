from app import db
from app.models.category import Category
from app.models.category_request import CategoryRequest


def request_category(nombre_rubro, descripcion, email_notificacion):
    category_request = CategoryRequest(
        nombre_rubro=nombre_rubro,
        descripcion=descripcion,
        email_notificacion=email_notificacion
    )

    db.session.add(category_request)
    db.session.commit()

    count = CategoryRequest.query.filter(
        CategoryRequest.nombre_rubro.ilike(nombre_rubro)
    ).count()

    if count >= 10:
        CategoryRequest.query.filter(
            CategoryRequest.nombre_rubro.ilike(nombre_rubro)
        ).update({"estado": "NOTIFICAR_ADMIN"})

        db.session.commit()

    return count


def get_category_requests_summary():
    results = (
        db.session.query(
            CategoryRequest.nombre_rubro,
            db.func.count(CategoryRequest.id).label("total"),
            db.func.max(CategoryRequest.estado).label("estado")
        )
        .group_by(CategoryRequest.nombre_rubro)
        .order_by(db.func.count(CategoryRequest.id).desc())
        .all()
    )

    return results


def approve_category(nombre_rubro):
    existing = Category.query.filter(
        Category.nombre.ilike(nombre_rubro)
    ).first()

    if not existing:
        category = Category(
            nombre=nombre_rubro,
            descripcion="Rubro aprobado por solicitudes de usuarios",
            estado="ACTIVO"
        )
        db.session.add(category)

    CategoryRequest.query.filter(
        CategoryRequest.nombre_rubro.ilike(nombre_rubro)
    ).update({"estado": "APROBADO"})

    db.session.commit()