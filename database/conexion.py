import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text

# Forzamos la codificación del cliente para evitar errores de caracteres en Windows
os.environ["PGCLIENTENCODING"] = "utf-8"

# ==========================================
# 1. TUS CREDENCIALES DE POSTGRESQL
# ==========================================
USER = "postgres"
PASSWORD = "S6363cf59710"
HOST = "db.jfjlasaxvictckwwzbqv.supabase.co"
PORT = "5432"
DB_NAME = "postgres"

DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
# ==========================================
