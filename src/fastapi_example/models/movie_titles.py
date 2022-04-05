import datetime
import typing

from dateparser import parse
from sqlalchemy import Column, Integer, String, create_engine, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, constr, validator

Base = declarative_base()
engine = create_engine("sqlite:///:memory:", echo=True)


class MovieTitlesORM(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True, nullable=False)
    show_id = Column(String(8), index=True, nullable=False, unique=True)
    type = Column(String(8), index=True)
    title = Column(String(128), index=True)
    director = Column(String(128), index=True)
    cast = Column(Text)
    country = Column(String(256), index=True)
    date_added = Column(Date, nullable=True)
    release_year = Column(Integer, index=True)
    rating = Column(String(8), index=True)
    duration = Column(String(16), index=True)
    listed_in = Column(String(64), index=True)
    description = Column(Text)


class MovieTitlesModel(BaseModel):
    id: int = None
    show_id: constr(max_length=8)
    type: constr(max_length=8)
    title: constr(max_length=128)
    director: constr(max_length=128)
    cast: str
    country: constr(max_length=256)
    date_added: typing.Optional[typing.Union[datetime.date, str]]
    release_year: int
    rating: constr(max_length=8)
    duration: constr(max_length=16)
    listed_in: constr(max_length=64)
    description: str

    @validator('date_added', pre=True)
    def _parse_date(cls, v: any) -> typing.Union[datetime.date, any]:
        try:
            return parse(v)
        except ValueError:
            return v

    class Config:
        orm_mode = True


Base.metadata.create_all(engine)
