import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text

# Forzamos la codificación del cliente para evitar errores de caracteres en Windows
os.environ["PGCLIENTENCODING"] = "utf-8"

# ==========================================
# 1. TUS CREDENCIALES DE POSTGRESQL
# ==========================================
USER = "postgres"
PASSWORD = "S6363cf59710"  # <--- Tu contraseña correcta (recuerda que me habías puesto S6363cf5 y luego S6363cf59710)
HOST = "db.jfjlasaxvictckwwzbqv.supabase.co"
PORT = "5432"
DB_NAME = "postgres"
# ==========================================
# 2. URL Y MOTOR DE SQLALCHEMY
# ==========================================
# Usamos quote_plus por seguridad y el driver psycopg2 que ya está instalado
password_segura = quote_plus(PASSWORD)
DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
# Creamos el motor de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica que la conexión responda antes de usarla
)

# ==========================================
