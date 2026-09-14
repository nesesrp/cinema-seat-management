from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/halls/{hall_id}/seats", tags=["seats"])


def _get_hall_or_404(hall_id: int, db: Session) -> models.Hall:
    hall = db.get(models.Hall, hall_id)
    if hall is None:
        raise HTTPException(status_code=404, detail="Hall not found")
    return hall


@router.post("/", response_model=schemas.SeatRead)
def create_seat(hall_id: int, seat: schemas.SeatCreate, db: Session = Depends(get_db)):
    _get_hall_or_404(hall_id, db)

    db_seat = models.Seat(hall_id=hall_id, row=seat.row, number=seat.number)
    db.add(db_seat)
    db.commit()
    db.refresh(db_seat)
    return db_seat


@router.get("/", response_model=list[schemas.SeatRead])
def list_seats(hall_id: int, db: Session = Depends(get_db)):
    _get_hall_or_404(hall_id, db)

    return db.query(models.Seat).filter(models.Seat.hall_id == hall_id).all()
