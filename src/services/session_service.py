from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models

# Sessions have no duration field, so every session is assumed to occupy its
# hall for this long; two sessions in one hall may not start closer than this.
SESSION_SLOT = timedelta(hours=3)


def is_in_past(start_time: datetime) -> bool:
    # Naive datetimes are compared against the server's local time.
    return start_time < datetime.now(start_time.tzinfo)


def find_conflicting_session(
    db: Session, hall_id: int, start_time: datetime, exclude_session_id: int | None = None
) -> models.Session | None:
    query = db.query(models.Session).filter(
        models.Session.hall_id == hall_id,
        models.Session.start_time > start_time - SESSION_SLOT,
        models.Session.start_time < start_time + SESSION_SLOT,
    )
    if exclude_session_id is not None:
        query = query.filter(models.Session.id != exclude_session_id)
    return query.first()
