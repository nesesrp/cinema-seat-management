from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Hall(Base):
    __tablename__ = "halls"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    seats = relationship("Seat", back_populates="hall")
    sessions = relationship("Session", back_populates="hall")


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    row = Column(Integer, nullable=False)
    number = Column(Integer, nullable=False)

    hall = relationship("Hall", back_populates="seats")
    reservations = relationship("Reservation", back_populates="seat")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    movie_name = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)

    hall = relationship("Hall", back_populates="sessions")
    reservations = relationship("Reservation", back_populates="session")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)

    session = relationship("Session", back_populates="reservations")
    seat = relationship("Seat", back_populates="reservations")
