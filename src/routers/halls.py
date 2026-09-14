from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/halls", tags=["halls"])


@router.post("/", response_model=schemas.HallRead)
def create_hall(hall: schemas.HallCreate, db: Session = Depends(get_db)):
    db_hall = models.Hall(name=hall.name)
    db.add(db_hall)
    db.commit()
    db.refresh(db_hall)
    return db_hall


@router.get("/", response_model=list[schemas.HallRead])
def list_halls(db: Session = Depends(get_db)):
    return db.query(models.Hall).all()
