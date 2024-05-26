from pydantic import BaseModel
from typing import Optional, Any


class TaskItem(BaseModel):
    script_name: str
    data: Optional[dict] = {}
    job_name: str
    job_description: Optional[str] = ""


class StandardResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


class UserRegisterForm(BaseModel):
    username: str
    password: str
    email: str
    auth_code: str


class LoginForm(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: int
    username: str
    email: str
    avatar_url: str
