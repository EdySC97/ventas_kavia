from sqlalchemy import text
from database.conexion import engine

def validar_login(pin):
    """
    Verifica si el PIN existe y está activo.
    Retorna el diccionario con datos del usuario o None.
    """
    query = text("""
        SELECT id_usuario, nombre, rol 
        FROM usuarios 
        WHERE pin = :pin AND activo = TRUE;
    """)
    with engine.connect() as conn:
        res = conn.execute(query, {"pin": pin}).mappings().first()
        return dict(res) if res else None
