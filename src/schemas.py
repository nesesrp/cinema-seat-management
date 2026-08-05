from pydantic import BaseModel, ConfigDict


class HallBase(BaseModel):
    name: str


class HallCreate(HallBase):
    pass


class HallRead(HallBase):
    model_config = ConfigDict(from_attributes=True)

    id: int