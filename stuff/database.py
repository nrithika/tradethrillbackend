import psycopg2
import os 
from dotenv import load_dotenv

load_dotenv()

def make_db():
    conn = psycopg2.connect(dbname = os.getenv("db_name"), user = os.getenv("user"), password=os.getenv("password"), host='localhost', port='5432')
    cursor = conn.cursor()
    return (conn,cursor)
