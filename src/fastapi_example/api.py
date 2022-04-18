import csv
import logging
import typing
from io import StringIO

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from fastapi_example.models.movie_titles import MovieTitlesModel, MovieTitlesORM, engine

logger = logging.getLogger(__name__)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def docs():
    return RedirectResponse("/docs", status_code=308)


def save_batch(sqla_objs: typing.List[MovieTitlesORM]):
    session = Session(bind=engine)
    session.bulk_save_objects(
        sqla_objs
    )
    session.commit()


def table_has_items() -> bool:
    session = Session(bind=engine)
    return bool(session.query(MovieTitlesORM.id).count())


@app.post("/v1/movies/populate")
async def populate():
    if table_has_items():
        return

    dataset_url = "https://storage.googleapis.com/chmoder-site.appspot.com/disney_plus_titles.csv"
    field_names = ["show_id", "type", "title", "director", "cast", "country", "date_added", "release_year", "rating", "duration", "listed_in", "description"]
    response = requests.get(dataset_url)
    f = StringIO(response.content.decode())
    reader = csv.DictReader(f, field_names)
    num_header_rows = 1

    sqla_movie_titles = []
    for row_id, item in enumerate(reader):
        # skip header rows
        if row_id + 1 <= num_header_rows:
            continue

        pyd_movie_title = MovieTitlesModel(**item)
        sqla_movie_title = MovieTitlesORM(**pyd_movie_title.dict())
        sqla_movie_titles.append(sqla_movie_title)

        if len(sqla_movie_titles) >= 100:
            save_batch(sqla_movie_titles)
            sqla_movie_titles = []

    if len(sqla_movie_titles):
        save_batch(sqla_movie_titles)


@app.get("/v1/movies/search")
async def search(title: typing.Optional[str] = None, director: typing.Optional[str] = None):
    stmt = select(MovieTitlesORM)
    searchable_field_names = ["title", "director"]
    searchable_field_values = [title, director]

    if not any(searchable_field_values):
        raise HTTPException(
            status_code=400,
            detail=f"please include one or more query parameters of: {searchable_field_names}"
        )

    if title:
        stmt = stmt.where(MovieTitlesORM.title.ilike(f"%{title}%"))
    if director:
        stmt = stmt.where(MovieTitlesORM.director.ilike(f"%{director}%"))

    session = Session(bind=engine)
    r = session.execute(stmt)

    res = []
    for i in r.scalars():
        i.date_added = str(i.date_added)
        mtm = MovieTitlesModel.from_orm(i)
        res.append(mtm)

    if not len(res):
        raise HTTPException(status_code=404, detail="No movies found")

    return res


@app.get("/v1/movies/{id}")
async def get_movie_by_id(_id: int):
    stmt = select(MovieTitlesORM)
    stmt = stmt.where(MovieTitlesORM.id == _id)
    session = Session(bind=engine)
    result = session.execute(stmt).scalar()
    if result:
        return result
    else:
        raise HTTPException(status_code=404, detail="Movie not found")
