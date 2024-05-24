#!/bin/bash

# 激活 Conda 环境
source ~/miniconda3/etc/profile.d/conda.sh
conda activate task_platform

# 启动 FastAPI 应用
nohup uvicorn app:app --host 0.0.0.0 --port 8000 --reload > task_platform_log.log
nohup rq worker -u redis://:@localhost:6379/3 > task_platform_rq_log.log