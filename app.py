from fastapi import FastAPI, Depends
from tasks import enqueue_task, stop_task, get_all_jobs, get_task_status
from redis import Redis
import os
import uvicorn
from config import REDIS_CONFIG
from pydantic import BaseModel
from typing import Optional, Any
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from MySecurity import authenticate_user, create_access_token
app = FastAPI()
redis_conn = Redis(host=REDIS_CONFIG['host'], password=REDIS_CONFIG['password'], db=REDIS_CONFIG['db'])


class TaskItem(BaseModel):
    script_name: str
    data: Optional[dict] = {}
    job_name: str
    job_description: Optional[str] = ""


class StandardResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


def is_length_exceed_len(input_string, charset='utf8mb4', length=255):
    encoded_string = input_string.encode(charset)
    byte_length = len(encoded_string)
    return byte_length > length, byte_length


@app.get("/scripts/")
async def get_scripts():
    scripts_dir = "scripts"
    scripts = [f.replace(".py", "") for f in os.listdir(scripts_dir) if f.endswith(".py") and f != "__init__.py"]
    return StandardResponse(code=0, message="success", data={"scripts_name": scripts})


@app.get("/scripts/{script_name}")
async def view_script(script_name: str):
    try:
        with open(f"scripts/{script_name}.py", "r") as file:
            content = file.read()
        return StandardResponse(code=0, message="success", data={"script_name": script_name, "content": content})
    except FileNotFoundError:
        return StandardResponse(code=1, message="failed", data={})


@app.post("/enqueue/")
async def enqueue(task_item: TaskItem):
    script_name = task_item.script_name
    if not os.path.exists("scripts/"+script_name+".py"):
        return StandardResponse(code=1, message="failed", data={})
    data = task_item.data
    job_name = task_item.job_name
    job_description = task_item.job_description
    if is_length_exceed_len(job_description):
        return StandardResponse(code=1, message="failed", data={})
    task_id = enqueue_task(script_name, data, job_name, job_description)
    return StandardResponse(code=0, message="success", data={"task_id": task_id})


@app.post("/stop/{task_id}")
async def stop(task_id: int):
    stop_task(task_id)
    return StandardResponse(code=0, message="success", data={})


@app.get("/status/{task_id}")
async def get_status(task_id: int):
    try:
        task_info = get_task_status(task_id)
        return StandardResponse(code=0, message="success", data={"task_info": task_info})
    except Exception:
        return StandardResponse(code=1, message="failed", data={})


@app.get("/jobs/")
async def list_jobs(page: int, size: int):
    page, total_page, return_data = get_all_jobs(page)
    return StandardResponse(code=0, message="success", data={
        "total_page": total_page,
        "size": 10,
        "data": return_data,
        "page": page
    })


@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        return StandardResponse(code=1, message="error", data={})
    access_token = create_access_token(data={"sub": user.username})
    return StandardResponse(code=0, message="success", data={"access_token": access_token, "token_type": "bearer"})


@app.get("/")
async def root():
    return StandardResponse(code=0, message="Welcome to the FastAPI + RQ crawler!")


if __name__ == "__main__":
    uvicorn.run(app)
