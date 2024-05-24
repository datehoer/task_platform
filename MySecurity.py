from config import REDIS_CONFIG, MYSQL_CONFIG
from useMySQL import MySQLDatabase
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
db = MySQLDatabase(MYSQL_CONFIG)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username, password):
    find_user_name = db.execute("select password from users where username=%s", [username])
    if len(find_user_name) == 0:
        return False
    db_password = find_user_name[0][0]
    if not verify_password(db_password, password):
        return False
    return True


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
