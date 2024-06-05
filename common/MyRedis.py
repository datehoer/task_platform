from redis import Redis


class RedisSingleton:
    _instance = None

    def __new__(cls, host='localhost', port=6379, db=0, password=None, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RedisSingleton, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_connection(host, port, db, password)
        return cls._instance

    def _init_connection(self, host, port, db, password):
        self.redis = Redis(
            host=host,
            port=port,
            db=db,
            password=password
        )

    def get_connection(self):
        return self.redis