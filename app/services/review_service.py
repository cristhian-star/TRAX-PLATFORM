from app import db
from app.models.review import Review


def create_review(cliente_id, professional_id, rating, comentario=None):
    review = Review(
        cliente_id=cliente_id,
        professional_id=professional_id,
        rating=rating,
        comentario=comentario
    )

    db.session.add(review)
    db.session.commit()

    return review


def get_professional_reviews(professional_id):
    return (
        Review.query
        .filter_by(professional_id=professional_id, estado="VISIBLE")
        .order_by(Review.created_at.desc())
        .all()
    )


def get_professional_average_rating(professional_id):
    average = (
        db.session.query(db.func.avg(Review.rating))
        .filter_by(professional_id=professional_id, estado="VISIBLE")
        .scalar()
    )

    if average is None:
        return None

    return round(float(average), 2)


def update_review_status(review_id, estado):
    if estado not in Review.ESTADOS:
        raise ValueError("Estado de review invalido")

    review = Review.query.get(review_id)

    if review is None:
        return None

    review.estado = estado
    db.session.commit()

    return review
