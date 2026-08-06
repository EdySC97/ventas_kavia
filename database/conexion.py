import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text

USER = "postgres"
PASSWORD = "S6363cf59710"
HOST = "db.jfjlasaxvictckwwzbqv.supabase.co"
PORT = "6543"  # <--- Cambiar del puerto 5432 al 6543 (Pooler)
DB_NAME = "postgres"

DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
