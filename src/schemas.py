from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HallBase(BaseModel):
    name: str


class HallCreate(HallBase):
    pass


class HallRead(HallBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class SeatBase(BaseModel):
    row: int
    number: int


class SeatCreate(SeatBase):
    pass


class SeatRead(SeatBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hall_id: int


class SessionBase(BaseModel):
    movie_name: str
    start_time: datetime


class SessionCreate(SessionBase):
    hall_id: int


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