from fastapi import FastAPI

from .database import Base, engine
from . import models
from .routers import halls, seats, sessions

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cinema Seet Managment")

app.include_router(halls.router)
app.include_router(seats.router)
app.include_router(sessions.router)

@app.get("/")
def root():
    return{"status": "ok"}
