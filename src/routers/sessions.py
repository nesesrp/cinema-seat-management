from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import seat_service, session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_session_or_404(session_id: int, db: Session) -> models.Session:
    session = db.get(models.Session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _validate_start_time(
    db: Session, hall_id: int, start_time: datetime, exclude_session_id: int | None = None
) -> None:
    if session_service.is_in_past(start_time):
        raise HTTPException(status_code=400, detail="Session cannot start in the past")
    if session_service.find_conflicting_session(db, hall_id, start_time, exclude_session_id):
        raise HTTPException(status_code=409, detail="Another session in this hall is too close to this time")


@router.post("/", response_model=schemas.SessionRead)
def create_session(session: schemas.SessionCreate, db: Session = Depends(get_db)):
    hall = db.get(models.Hall, session.hall_id)
    if hall is None:
        raise HTTPException(status_code=404, detail="Hall not found")

    _validate_start_time(db, session.hall_id, session.start_time)

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
def list_sessions(
    hall_id: int | None = None,
    date: date | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Session)
    if hall_id is not None:
        query = query.filter(models.Session.hall_id == hall_id)
    if date is not None:
        day_start = datetime.combine(date, time.min)
        query = query.filter(
            models.Session.start_time >= day_start,
            models.Session.start_time < day_start + timedelta(days=1),
        )
    return query.all()


@router.get("/{session_id}", response_model=schemas.SessionRead)
def get_session(session_id: int, db: Session = Depends(get_db)):
    return _get_session_or_404(session_id, db)


@router.put("/{session_id}", response_model=schemas.SessionRead)
def update_session(
    session_id: int, session: schemas.SessionUpdate, db: Session = Depends(get_db)
):
    db_session = _get_session_or_404(session_id, db)

    # Only re-validate when the time actually moves, so past sessions stay editable.
    if session.start_time != db_session.start_time:
        _validate_start_time(db, db_session.hall_id, session.start_time, session_id)

    db_session.movie_name = session.movie_name
    db_session.start_time = session.start_time
    db.commit()
    db.refresh(db_session)
    return db_session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = _get_session_or_404(session_id, db)

    has_reservations = (
        db.query(models.Reservation)
        .filter(models.Reservation.session_id == session_id)
        .first()
    )
    if has_reservations:
        raise HTTPException(status_code=409, detail="Session still has reservations")

    db.delete(session)
    db.commit()


@router.get("/{session_id}/seats", response_model=list[schemas.SeatStatusRead])
def get_session_seats(session_id: int, db: Session = Depends(get_db)):
    statuses = seat_service.get_seat_statuses(db, session_id)
    if statuses is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return statuses
