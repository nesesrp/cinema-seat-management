from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import seat_service

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("/", response_model=schemas.ReservationRead)
def create_reservation(reservation: schemas.ReservationCreate, db: Session = Depends(get_db)):
    session = db.get(models.Session, reservation.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    seat = db.get(models.Seat, reservation.seat_id)
    if seat is None:
        raise HTTPException(status_code=404, detail="Seat not found")

    if seat.hall_id != session.hall_id:
        raise HTTPException(status_code=400, detail="Seat does not belong to the session's hall")

    if seat_service.is_seat_reserved(db, reservation.session_id, reservation.seat_id):
        raise HTTPException(status_code=409, detail="Seat already reserved for this session")

    db_reservation = models.Reservation(
        session_id=reservation.session_id, seat_id=reservation.seat_id
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    return db_reservation


@router.get("/", response_model=list[schemas.ReservationRead])
def list_reservations(
    session_id: int | None = None,
    seat_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Reservation)
    if session_id is not None:
        query = query.filter(models.Reservation.session_id == session_id)
    if seat_id is not None:
        query = query.filter(models.Reservation.seat_id == seat_id)
    return query.all()


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.get(models.Reservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    db.delete(reservation)
    db.commit()
