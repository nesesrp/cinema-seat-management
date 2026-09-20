from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HallBase(BaseModel):
    name: str


class HallCreate(HallBase):
    pass


class HallUpdate(HallBase):
    pass


class HallRead(HallBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class SeatBase(BaseModel):
    row: int
    number: int


class SeatCreate(SeatBase):
    pass


class SeatUpdate(SeatBase):
    pass


class SeatBulkCreate(BaseModel):
    rows: int = Field(ge=1, le=50)
    seats_per_row: int = Field(ge=1, le=50)


class SeatRead(SeatBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hall_id: int


class SessionBase(BaseModel):
    movie_name: str
    start_time: datetime


class SessionCreate(SessionBase):
    hall_id: int


class SessionUpdate(SessionBase):
    pass


class SessionRead(SessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hall_id: int


class ReservationCreate(BaseModel):
    session_id: int
    seat_id: int


class ReservationRead(ReservationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class SeatStatusRead(BaseModel):
    id: int
    row: int
    number: int
    status: str