from sqlalchemy.orm import Session

from .. import models


def get_seat_statuses(db: Session, session_id: int) -> list[dict] | None:
    """Return every seat in the session's hall tagged as occupied/available.

    Returns None if the session does not exist, so the caller can 404.
    """
    session = db.get(models.Session, session_id)
    if session is None:
        return None

    reserved_seat_ids = {
        seat_id
        for (seat_id,) in db.query(models.Reservation.seat_id).filter(
            models.Reservation.session_id == session_id
        )
    }

    seats = db.query(models.Seat).filter(models.Seat.hall_id == session.hall_id).all()

    return [
        {
            "id": seat.id,
            "row": seat.row,
            "number": seat.number,
            "status": "occupied" if seat.id in reserved_seat_ids else "available",
        }
        for seat in seats
    ]


def is_seat_reserved(db: Session, session_id: int, seat_id: int) -> bool:
    return (
        db.query(models.Reservation)
        .filter(
            models.Reservation.session_id == session_id,
            models.Reservation.seat_id == seat_id,
        )
        .first()
        is not None
    )
