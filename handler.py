from main import app
from mangum import Mangum
import os

os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', '')
os.environ['REDIS_HOST'] = os.getenv('REDIS_HOST', '')
os.environ['RABBITMQ_URL'] = os.getenv('RABBITMQ_URL', '')

handler = Mangum(app)