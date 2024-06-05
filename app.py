import random
from fastapi import FastAPI, Depends, Response
from tasks import enqueue_task, stop_task, get_all_jobs, get_task_status
import os
import uvicorn
from models import StandardResponse, UserRegisterForm, TaskItem, LoginForm, User
from common.MySecurity import authenticate_user, create_access_token, register_user, get_current_user, check_user_permission
from common.MyEmail import send_email
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:63342",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/sendAuthCode")
async def send_auth_code(email: str):
    codes = "0123456789QWERTYUIOPASDFGHJKLZXCVBNM"
    auth_code = random.sample(codes, 6)
    result = send_email(email, "邮箱验证码", "".join(auth_code))
    if result:
        return StandardResponse(code=0, message="success", data={})
    return StandardResponse(code=1, message="failed", data={})


@app.post("/login")
async def login(login_form: LoginForm, response: Response):
    user = authenticate_user(login_form.username, login_form.password)
    if not user:
        return StandardResponse(code=1, message="error", data={})
    access_token = create_access_token(data={"sub": login_form.username})
    response.set_cookie(key="bearer", value=f'{access_token}', httponly=True, max_age=60*60*24*7, expires=60*60*24*7)
    return StandardResponse(code=0, message="success", data={"access_token": access_token, "token_type": "bearer"})


@app.post("/register")
async def register(user_form: UserRegisterForm):
    user = register_user(user_form.username, user_form.password, user_form.email, user_form.auth_code)
    if not user:
        return StandardResponse(code=1, message="error", data={})
    else:
        return StandardResponse(code=0, message="success", data={})


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    if not current_user:
        return StandardResponse(code=1, message="error", data={})
    user_dict = {
        "id": current_user[0],
        "username": current_user[1],
        "email": current_user[2],
        "avatar_url": current_user[3]
    }
    if check_user_permission(current_user[0], "user_me"):
        return StandardResponse(code=0, message="success", data={"user": user_dict})
    return StandardResponse(code=1, message="error", data={"user": {}})


@app.get("/")
async def root():
    return StandardResponse(code=0, message="Welcome to the FastAPI + RQ crawler!")


if __name__ == "__main__":
    uvicorn.run(app)
