from fastapi import FastAPI

from .database import Base, engine
from . import models
from .routers import halls

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cinema Seet Managment")

app.include_router(halls.router)

@app.get("/")
def root():
    return{"status": "ok"}
