import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text

USER = "postgres"
PASSWORD = "S6363cf59710"
HOST = "db.jfjlasaxvictckwwzbqv.supabase.co"
PORT = "5432"  # Volvemos al puerto 5432 directo (que es el que reconoce este host por defecto)
DB_NAME = "postgres"

# Construcción segura de la URL con codificación de contraseña por si acaso
DATABASE_URL = f"postgresql://{USER}:{quote_plus(PASSWORD)}@{HOST}:{PORT}/{DB_NAME}"

# Crear el motor de SQLAlchemy
engine = create_engine(DATABASE_URL)
