from useMySQL import MySQLDatabase
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from MyRedis import RedisSingleton
from config import REDIS_CONFIG, MYSQL_CONFIG
from fastapi import Cookie
redis_conn = RedisSingleton(host=REDIS_CONFIG['host'], password=REDIS_CONFIG['password'], db=REDIS_CONFIG['db']).get_connection()
SECRET_KEY = "09d25e094faa6ca2as6c818166b7a9563b93w9099f6f0f4caa6cf63b88e8d3e7"
db = MySQLDatabase(MYSQL_CONFIG)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def verify_password(password, db_password):
    return pwd_context.verify(password, db_password)


def authenticate_user(username, password):
    find_user_name = db.execute("select password from users where username=%s", [username], fetch=True)
    if not find_user_name:
        return False
    db_password = find_user_name[0][0]
    if not verify_password(password, db_password):
        return False
    return True


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return False
        return username
    except JWTError:
        return False


def verification_auth_code(email, auth_code):
    stored_code = redis_conn.get(email)
    if stored_code and stored_code.decode("utf-8") == auth_code:
        return True
    else:
        return False


def register_user(username, password, email, auth_code):
    if len(username) <= 0 or len(username) > 32:
        return False
    if verification_auth_code("email:"+email, auth_code) is False:
        return False
    else:
        redis_conn.delete("email:"+email)
    find_user_name = db.execute("select count(1) from users where username=%s", [username], fetch=True)
    if find_user_name[0][0] > 0:
        return False
    hash_password = pwd_context.hash(password)
    user_id = db.execute("insert into users (username, password, email, avatar_url, created_at, updated_at) values(%s, %s, %s, %s, %s, %s)",
               [username, hash_password, email, "https://github.com/gfriends/gfriends/blob/master/Content/0-Hand-Storage/%E6%B0%B4%E9%87%8E%E6%9C%9D%E9%99%BD.jpg?raw=true", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m-%d %H:%M:%S")], lastrowid=True)
    if not user_id:
        return False
    db.execute("insert into user_roles (user_id, role_id) values(%s, %s)", [user_id, 1])
    return True


def get_current_user(bearer: str = Cookie(None)):
    if bearer is None:
        return False
    username = decode_access_token(bearer)
    if username is False:
        return False
    user = db.execute("select id, username, email, avatar_url from users where username=%s", [username], fetch=True)
    if not user:
        return False
    return user[0]


def check_user_permission(user_id, permission):
    user_role = db.execute("select role_id from user_roles where user_id=%s", [user_id], fetch=True)
    if not user_role:
        return False
    role_id = user_role[0][0]
    role_permission = db.execute("select permission_id from roles_permissions where role_id=%s", [role_id], fetch=True)
    if not role_permission:
        return False
    role_permission = ",".join([str(i[0]) for i in role_permission])
    permissions = db.execute("select permission_name from permissions where permission_id in (%s)" % role_permission, fetch=True)
    if not permissions:
        return False
    permissions = [i[0] for i in permissions]
    if permission in permissions:
        return True
    return False
