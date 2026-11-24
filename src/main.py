import asyncio
from datetime import datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum
import shutil
from typing import Annotated, Any, Literal, overload
from fastapi.responses import JSONResponse, RedirectResponse
from typing_extensions import sentinel
from uuid import UUID

from fastapi import Body, Cookie, FastAPI, Form, Path, Query, Response, UploadFile
from pydantic import AfterValidator, BaseModel, BeforeValidator, EmailStr, Field
import uvicorn

app = FastAPI()


@app.get("/")
async def say_hello():
  return {"message": "hello world"}

@app.get("/items/{item_id}/{quantity}")
async def get_items(item_id: str, quantity: int | None = None) -> dict[str, Any]:
  return {
    "item_id": item_id,
    "quantity": quantity
  }

@app.get("/items")
@app.get("/items/{quantity:int}")
async def get_quantity(quantity: Annotated[int, Path(ge=50)]) -> dict[str, int]:

  return {
    "quantity": quantity
  }

class Color(StrEnum):
  RED = 'red'
  GREEN = 'green'

@app.get("/pick_color/{color}")
async def pick_color(color) -> str:
  match color:
    case Color.RED:
      return "I love red"
    case Color.GREEN:
      return "I hate green"
    case _:
      raise ValueError(f"unknown color: {color}")


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}


@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}

class Student(BaseModel):
  name: str
  age: int
  grade: str

@app.post("/create_student")
async def create_student(student: Student) -> Student:
  return student


@app.get("/files/{file_path:path}")
async def get_file_path(file_path: str) -> dict[str, str]:
  return {
    "file_path": file_path
  }

@app.get("/queries", tags=["readonly", "public"])
async def queries(q: Annotated[list[str], 
                                Query(
                                  title="Query string", 
                                  min_length=3, 
                                  examples='abc',
                                  alias="item-query")]):
  return {
    "queries": q
  }


def check_book_id(book_id: str) -> str:
  if not book_id.startswith("isbn"):
    raise ValueError("book id must start with isbn")
  return book_id

@app.get("/books/{book_id}")
async def get_book(book_id: Annotated[str, AfterValidator(check_book_id)]):
  return {
    "book_id": book_id
  }

@app.get("/books")
async def get_book_by_query(book_id: Annotated[str, Query(alias="id"), AfterValidator(check_book_id)]):
  return {
    "book_id_query": book_id
  }

class FilterParam(BaseModel):
  limit: Annotated[int, Field(ge=10, le=20)] = 10
  offset: Annotated[int, Field(ge=0)]
  order_by: Literal["created_at", "updated_at"] = "created_at"

  # model_config = {
  #       "json_schema_extra": {
  #           "examples": [
  #               {
  #                   "name": "Foo",
  #                   "description": "A very nice Item 11",
  #                   "price": 35.4,
  #                   "tax": 3.2,
  #               },
  #               {
  #                   "name": "Foo",
  #                   "description": "A very nice Item 22",
  #                   "price": 35.4,
  #                   "tax": 3.2,
  #               }
  #           ]
  #       }
  #   }

@app.get("/filter-items")
async def filter_items(filter_param: Annotated[FilterParam, Query(
  openapi_examples=[{
              "name": "Foo",
              "description": "A very nice Item one in query",
              "price": 35.4,
              "tax": 3.2,
            },
            {
              "name": "Foo",
              "description": "A very nice Item two in query",
              "price": 35.4,
              "tax": 3.2,
            }]
)]) -> FilterParam:
  return filter_param

class Pagination(BaseModel):
    limit: int = Field(10, ge=1)
    offset: int = Field(0, ge=0)


class Filters(BaseModel):
    tags: list[str] = []


@app.get("/query-items/")
def read_items(
    pagination: Annotated[Pagination, Query()],
    filters: Annotated[Filters, Query()],
    search: str | None = None,
):
    return {"pagination": pagination, "filters": filters, "search": search}



class Item(BaseModel):
  name: str
  description: str | None = None
  price:  Annotated[Decimal, Field(max_digits=25, decimal_places=2, gt=0)]

class User(BaseModel):
  username: str
  full_name: str | None = None

class UserItem(BaseModel):
  user: User
  item: Item

@app.put("/new-items/{item_id}")
async def update_item(item_id: int, item: Item, user: User):
    results = {"item_id": item_id, "item": item, "user": user}
    return results    

@app.put("/new-items2/{item_id}")
async def update_item_2(item_id: int, user_item: UserItem):
    return {"item_id": item_id, "user": user_item.user, "item": user_item.item}

class Item1(BaseModel):
    name: str
    description: str | None = None
    price: Annotated[Decimal, Field(max_digits=25, decimal_places=2)]
    tax: Annotated[Decimal | None, Field(max_digits=25, decimal_places=2)] = None


@app.put("/items-body/{item_id}")
async def update_item_body(
    *,
    item_id: int,
    item: Annotated[
        Item1,
        Body(
            examples=[
                {
                    "name": "Foo",
                    "description": "A very nice Item",
                    "price": 35.4,
                    "tax": 3.2,
                },
                {
                    "name": "Bar",
                    "price": "35.4",
                },
                {
                    "name": "Baz",
                    "price": "thirty five point four",
                },
            ],
        ),
    ],
):
    results = {"item_id": item_id, "item": item}
    return results


@app.put("/items-timed/{item_id}")
async def read_items_timed(
    item_id: UUID,
    start_datetime: Annotated[datetime, Body()],
    end_datetime: Annotated[datetime, Body()],
    process_after: Annotated[timedelta, Body()],
    repeat_at: Annotated[time | None, Body()] = None,
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "process_after": process_after,
        "repeat_at": repeat_at,
        "start_process": start_process,
        "duration": duration,
    }

@app.get("/cookie")
async def read_cookie(session_id: Annotated[str, Cookie()]) -> str:
  return f"cookie is: {session_id}"


@overload
def test(param: str) -> str: ...
@overload
def test(param: int) -> int: ...
def test(param: Any) -> Any:
  return param;



class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: str | None = None


class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


@app.post("/user/", response_model=UserOut)
async def create_user(user: UserIn) -> Any:
    return user

class BaseUser(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserIn2(BaseUser):
    password: str


@app.post("/user2/")
async def create_user2(user: UserIn2) -> BaseUser:
    return user

@app.get("/response", response_model=None)
def get_response(redirect: Annotated[bool, Query()] = False) -> Response | dict:
  if redirect:
      return RedirectResponse("https://www.sina.com.cn")

  return {"message": "hello world"}

class Item3(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float = 10.5
    tags: list[str] = []


items3 = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {"name": "Bar", "description": "The bartenders", "price": 62, "tax": 20.2},
    "baz": {"name": "Baz", "description": None, "price": 50.2, "tax": 10.5, "tags": []},
}


@app.get("/items/{item_id}", response_model=Item3, response_model_exclude_defaults=True)
async def read_item3(item_id: str):
    return items3[item_id]

class BaseItem(BaseModel):
    description: str
    type: str


class CarItem(BaseItem):
    type: str = "car"


class PlaneItem(BaseItem):
    type: str = "plane"
    size: int


items4 = {
    "item1": {"description": "All my friends drive a low rider", "type": "car"},
    "item2": {
        "description": "Music is my aeroplane, it's my aeroplane",
        "type": "plane",
        "size": 5,
    },
}


@app.get("/items4/{item_id}", response_model=PlaneItem | CarItem)
async def read_item4(item_id: str):
    return items4[item_id]


class Person(BaseModel):
  kind: Literal["person"]
  name: str


class Company(BaseModel):
  kind: Literal["company"]
  company_name: str


@app.post("/contacts", response_model=Person|Company|None)
async def create_contact(contact: Annotated[Person | Company | None, Form(discriminator="kind")] = None):
  return contact

@app.post("/upload")
async def upload_files(file1: Annotated[UploadFile, Form(alias="file1")], file2: Annotated[UploadFile, Form(alias="file2")]):
  dest_path = f"./{file1.filename}"
  with open(dest_path, "wb") as f_out:
    await asyncio.to_thread(shutil.copyfileobj, file1.file, f_out)

  dest_path = f"./{file2.filename}"
  with open(dest_path, "wb") as f_out:
    await asyncio.to_thread(shutil.copyfileobj, file2.file, f_out)


if __name__ == "__main__":
  uvicorn.run("__main__:app", host="127.0.0.1", port=8000, reload=True)
  
