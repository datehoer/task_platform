import time


def collect(url):
    print("task_start:", url)
    time.sleep(60)
    print("task_stop")
    return "ok"
