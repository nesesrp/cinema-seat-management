from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/halls", tags=["halls"])


def _get_hall_or_404(hall_id: int, db: Session) -> models.Hall:
    hall = db.get(models.Hall, hall_id)
    if hall is None:
        raise HTTPException(status_code=404, detail="Hall not found")
    return hall


@router.post("/", response_model=schemas.HallRead)
def create_hall(hall: schemas.HallCreate, db: Session = Depends(get_db)):
    db_hall = models.Hall(name=hall.name)
    db.add(db_hall)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Hall name already exists")
    db.refresh(db_hall)
    return db_hall


@router.get("/", response_model=list[schemas.HallRead])
def list_halls(db: Session = Depends(get_db)):
    return db.query(models.Hall).all()


@router.get("/{hall_id}", response_model=schemas.HallRead)
def get_hall(hall_id: int, db: Session = Depends(get_db)):
    return _get_hall_or_404(hall_id, db)


@router.put("/{hall_id}", response_model=schemas.HallRead)
def update_hall(hall_id: int, hall: schemas.HallUpdate, db: Session = Depends(get_db)):
    db_hall = _get_hall_or_404(hall_id, db)

    db_hall.name = hall.name
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Hall name already exists")
    db.refresh(db_hall)
    return db_hall


@router.delete("/{hall_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hall(hall_id: int, db: Session = Depends(get_db)):
    hall = _get_hall_or_404(hall_id, db)

    has_seats = db.query(models.Seat).filter(models.Seat.hall_id == hall_id).first()
    has_sessions = db.query(models.Session).filter(models.Session.hall_id == hall_id).first()
    if has_seats or has_sessions:
        raise HTTPException(status_code=409, detail="Hall still has seats or sessions")

    db.delete(hall)
    db.commit()
