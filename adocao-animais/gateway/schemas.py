
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class AnimalCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    species: Literal["cachorro", "gato"]
    breed: str = Field(min_length=1, max_length=100)
    age_years: int = Field(le=100)
    description: str = Field(min_length=1, max_length=2000)


class AnimalUpdate(AnimalCreate):
    available: bool


class AdoptionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    animal_id: str = Field(min_length=36, max_length=36)
    adopter_name: str = Field(min_length=2, max_length=120)
    adopter_email: EmailStr


class AdoptionStatusUpdate(BaseModel):
    status: Literal["pendente", "aprovada", "rejeitada"]
