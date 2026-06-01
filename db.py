import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()  # carga variables del archivo .env

def get_connection():
    db_url = os.getenv("DATABASE_URL")
    return psycopg2.connect(db_url)
