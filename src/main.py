from fastapi import FastAPI

from .database import Base, engine
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cinema Seet Managment")

@app.get("/")
def root():
    return{"status": "ok"}
