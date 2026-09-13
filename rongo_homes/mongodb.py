import os
from dotenv import load_dotenv
from mongoengine import connect


load_dotenv()


MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/rongo_homes_dev"
)


connect(host=MONGO_URI)