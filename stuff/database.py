import psycopg2
import os 
from dotenv import load_dotenv

load_dotenv()

def make_db():
    password = ""
    conn = psycopg2.connect(dbname = os.getenv("db_name"), user = os.getenv("user"), password=password)
    cursor = conn.cursor()
    return (conn,cursor)