from flask_sqlalchemy import SQLAlchemy
from redis import Redis

db = SQLAlchemy()

class RedisClient:
    def __init__(self):
        self.client = None

    def init_app(self, app):
        self.client = Redis.from_url(app.config["REDIS_URL"])

redis_client = RedisClient()
