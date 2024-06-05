import requests
import time


def fetch(url, retry_count=5, time_sleep=3, **kwargs):
    proxies = kwargs.get("proxies", {})
    while retry_count > 0:
        try:
            response = requests.get(url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            retry_count -= 1
            if retry_count <= 0:
                return None
            if not proxies:
                time.sleep(time_sleep*(6-retry_count))
            else:
                time.sleep(time_sleep)
