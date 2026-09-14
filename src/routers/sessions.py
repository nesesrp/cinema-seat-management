from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import seat_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=schemas.SessionRead)
def create_session(session: schemas.SessionCreate, db: Session = Depends(get_db)):
    hall = db.get(models.Hall, session.hall_id)
    if hall is None:
        raise HTTPException(status_code=404, detail="Hall not found")

    db_session = models.Session(
        hall_id=session.hall_id,
        movie_name=session.movie_name,
        start_time=session.start_time,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@router.get("/", response_model=list[schemas.SessionRead])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(models.Session).all()


@router.get("/{session_id}/seats", response_model=list[schemas.SeatStatusRead])
def get_session_seats(session_id: int, db: Session = Depends(get_db)):
    statuses = seat_service.get_seat_statuses(db, session_id)
    if statuses is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return statuses
