from app import db
from app.models.category import Category
from app.models.category_request import CategoryRequest
from app.models.professional import Professional


def get_explorable_categories():
    categories = Category.query.filter_by(estado="ACTIVO").order_by(Category.nombre).all()
    known_names = {category.nombre.casefold() for category in categories}
    rubros = [
        {
            "nombre": category.nombre,
            "descripcion": category.descripcion,
            "industria": "Servicios tecnicos",
            "source": "category",
        }
        for category in categories
    ]

    published_services = (
        db.session.query(Professional.servicio)
        .filter(Professional.servicio.isnot(None))
        .filter(Professional.servicio != "")
        .distinct()
        .order_by(Professional.servicio)
        .all()
    )

    for service_row in published_services:
        service_name = service_row[0].strip()
        normalized_name = service_name.casefold()

        if not service_name or normalized_name in known_names:
            continue

        known_names.add(normalized_name)
        rubros.append(
            {
                "nombre": service_name,
                "descripcion": None,
                "industria": "Servicios tecnicos",
                "source": "professional",
            }
        )

    return sorted(rubros, key=lambda rubro: rubro["nombre"].casefold())


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
