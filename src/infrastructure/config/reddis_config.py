import os
from redis import Redis
from typing import Optional
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

class RedisConfig:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD", None)
        self.decode_responses = os.getenv("REDIS_DECODE_RESPONSES", "False").lower() == "true"

    def get_client(self) -> Redis:
        return Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=self.decode_responses
        )
