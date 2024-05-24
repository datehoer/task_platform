import json
import time
from rq import Queue
from redis import Redis
import importlib
from rq.command import send_stop_job_command
from config import REDIS_CONFIG, MYSQL_CONFIG
import sys
import os
from useMySQL import MySQLDatabase
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
db = MySQLDatabase(MYSQL_CONFIG)
redis_conn = Redis(host=REDIS_CONFIG['host'], password=REDIS_CONFIG['password'], db=REDIS_CONFIG['db'])
q = Queue(connection=redis_conn)
select_sql = "select id, job_id, status, result, job_name, job_description, created_time, updated_time, script_name, script_data from job_status where is_deleted = 0 LIMIT %s OFFSET %s"
select_job_info_sql = "select id, job_id, status, result, job_name, job_description, created_time, updated_time, script_name, script_data from job_status where is_deleted = 0 and id=%s"
select_job_id_sql = "select job_id from job_status where id=%s"
insert_sql = "insert into job_status(job_name, job_description, created_time, updated_time, script_name, script_data) values(%s, %s, %s, %s, %s, %s)"
update_sql = "update job_status set 1=1, updated_time=%s where id = %s"
# CREATE TABLE `job_status` (
#   `id` bigint NOT NULL AUTO_INCREMENT,
#   `job_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '任务id',
#   `status` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '任务状态',
#   `result` varchar(100) DEFAULT NULL COMMENT '任务结果返回值',
#   `job_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '任务名称',
#   `job_description` varchar(255) DEFAULT NULL COMMENT '任务描述',
#   `created_time` timestamp NOT NULL,
#   `updated_time` timestamp NOT NULL,
#   `script_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '脚本名称',
#   `script_data` varchar(255) DEFAULT NULL COMMENT '脚本传参',
#   `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
#   PRIMARY KEY (`id`) USING BTREE
# ) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

def fetch_url(script_name, data, last_rowid):
    module = importlib.import_module(f'scripts.{script_name}')
    print(script_name)
    status = module.collect(data)
    print(status)
    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    db.execute(update_sql.replace("1=1", "result=%s, status=%s"), [status, "finished", now_time, last_rowid])
    return status


def enqueue_task(script_name, data, job_name, job_description):
    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    last_rowid = db.execute(insert_sql, [job_name, job_description, now_time, now_time, script_name, json.dumps(data)], lastrowid=True)
    job = q.enqueue(fetch_url, script_name, data, last_rowid)
    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    db.execute(update_sql.replace("1=1", "job_id=%s, status=%s"), [job.id, job.get_status(), now_time, last_rowid])
    return last_rowid


def stop_task(task_id):
    job_id = db.execute(select_job_id_sql, [task_id], fetch=True)
    if len(job_id) == 0:
        return {"msg": "task not exist"}
    job_id = job_id[0][0]
    if job_id not in q.jobs:
        return "job not exist"
    send_stop_job_command(redis_conn, job_id)
    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    db.execute(update_sql.replace("1=1", "status=%s"), ["stopped", now_time, task_id])
    return "stopped"


def analyze_data(data):
    return_data = []
    for select_data in data:
        return_data.append({
            "id": select_data[0],
            "job_id": select_data[1],
            "status": select_data[2],
            "result": select_data[3],
            "job_name": select_data[4],
            "job_description": select_data[5],
            "created_time": select_data[6],
            "updated_time": select_data[7],
            "script_name": select_data[8],
            "script_data": json.loads(select_data[9]),
        })
    return return_data


def get_all_jobs(page):
    if page < 1:
        page = 1
    elif page > 100:
        page = 100
    total_count = db.execute("select count(1) from job_status where is_deleted = 0", [])
    select_data = db.execute(select_sql, [10, page], fetch=True)
    return_data = analyze_data(select_data)
    return page, total_count[0][0], return_data


def get_task_status(task_id):
    select_data = db.execute(select_job_info_sql, [task_id], fetch=True)
    return_data = analyze_data(select_data)
    return return_data
