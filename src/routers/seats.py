from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/halls/{hall_id}/seats", tags=["seats"])


def _get_hall_or_404(hall_id: int, db: Session) -> models.Hall:
    hall = db.get(models.Hall, hall_id)
    if hall is None:
        raise HTTPException(status_code=404, detail="Hall not found")
    return hall


def _get_seat_or_404(hall_id: int, seat_id: int, db: Session) -> models.Seat:
    _get_hall_or_404(hall_id, db)
    seat = db.get(models.Seat, seat_id)
    if seat is None or seat.hall_id != hall_id:
        raise HTTPException(status_code=404, detail="Seat not found")
    return seat


def _raise_if_position_taken(
    db: Session, hall_id: int, row: int, number: int, exclude_seat_id: int | None = None
) -> None:
    query = db.query(models.Seat).filter(
        models.Seat.hall_id == hall_id,
        models.Seat.row == row,
        models.Seat.number == number,
    )
    if exclude_seat_id is not None:
        query = query.filter(models.Seat.id != exclude_seat_id)
    if query.first():
        raise HTTPException(status_code=409, detail="A seat with this row and number already exists")


@router.post("/", response_model=schemas.SeatRead)
def create_seat(hall_id: int, seat: schemas.SeatCreate, db: Session = Depends(get_db)):
    _get_hall_or_404(hall_id, db)
    _raise_if_position_taken(db, hall_id, seat.row, seat.number)

    db_seat = models.Seat(hall_id=hall_id, row=seat.row, number=seat.number)
    db.add(db_seat)
    db.commit()
    db.refresh(db_seat)
    return db_seat


@router.post("/bulk", response_model=list[schemas.SeatRead])
def create_seats_bulk(
    hall_id: int, bulk: schemas.SeatBulkCreate, db: Session = Depends(get_db)
):
    _get_hall_or_404(hall_id, db)

    existing = set(
        db.query(models.Seat.row, models.Seat.number)
        .filter(models.Seat.hall_id == hall_id)
        .all()
    )
    new_seats = [
        models.Seat(hall_id=hall_id, row=row, number=number)
        for row in range(1, bulk.rows + 1)
        for number in range(1, bulk.seats_per_row + 1)
    ]
    if any((seat.row, seat.number) in existing for seat in new_seats):
        raise HTTPException(status_code=409, detail="Some of these seats already exist in the hall")

    db.add_all(new_seats)
    db.flush()
    seat_ids = [seat.id for seat in new_seats]
    db.commit()
    return (
        db.query(models.Seat)
        .filter(models.Seat.id.in_(seat_ids))
        .order_by(models.Seat.id)
        .all()
    )


@router.get("/", response_model=list[schemas.SeatRead])
def list_seats(hall_id: int, db: Session = Depends(get_db)):
    _get_hall_or_404(hall_id, db)

    return db.query(models.Seat).filter(models.Seat.hall_id == hall_id).all()


@router.put("/{seat_id}", response_model=schemas.SeatRead)
def update_seat(
    hall_id: int, seat_id: int, seat: schemas.SeatUpdate, db: Session = Depends(get_db)
):
    db_seat = _get_seat_or_404(hall_id, seat_id, db)

    _raise_if_position_taken(db, hall_id, seat.row, seat.number, exclude_seat_id=seat_id)

    db_seat.row = seat.row
    db_seat.number = seat.number
    db.commit()
    db.refresh(db_seat)
    return db_seat


@router.delete("/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seat(hall_id: int, seat_id: int, db: Session = Depends(get_db)):
    seat = _get_seat_or_404(hall_id, seat_id, db)

    has_reservations = (
        db.query(models.Reservation).filter(models.Reservation.seat_id == seat_id).first()
    )
    if has_reservations:
        raise HTTPException(status_code=409, detail="Seat still has reservations")

    db.delete(seat)
    db.commit()
