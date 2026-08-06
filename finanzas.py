import pandas as pd
from sqlalchemy import text
from database.conexion import engine


def obtener_gastos():
    """
    Obtiene todos los registros de gastos desde la vista en PostgreSQL.
    """
    query = text("SELECT * FROM vista_historial_gastos;")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        return df


def obtener_dict_gastos():
    """
    Retorna un diccionario {nombre_gasto: id_gasto} de la tabla catálogo 'tipo_gasto'.
    """
    query = text("SELECT id_gasto, nombre_gasto FROM tipo_gasto;")
    with engine.connect() as conn:
        resultado = conn.execute(query)
        return {row.nombre_gasto: row.id_gasto for row in resultado}


def registrar_movimiento_gasto(tipo_gasto, cantidad):
    """
    Inserta un nuevo gasto registrado.
    """
    query = text(
        "INSERT INTO gastos (tipo_gasto, cantidad) VALUES (:tipo_gasto, :cantidad);"
    )
    with engine.begin() as conn:
        conn.execute(query, {"tipo_gasto": tipo_gasto, "cantidad": cantidad})


def obtener_dic_productos():
    """
    Retorna un diccionario {nombre_producto: id_productos} desde la tabla 'productos'.
    """
    query = text("SELECT id_productos, nombre_producto FROM productos ORDER BY nombre_producto ASC;")
    with engine.connect() as conn:
        resultado = conn.execute(query)
        return {row.nombre_producto: row.id_productos for row in resultado}

def obtener_dic_productos():
    """
    Retorna un diccionario {nombre_producto: id_productos} desde la tabla 'productos'.
    """
    # 👇 AQUÍ ESTÁ EL CAMBIO IMPORTANTE (id_productos) 👇
    query = text("SELECT id_productos, nombre_producto FROM productos ORDER BY nombre_producto ASC;")
    with engine.connect() as conn:
        resultado = conn.execute(query)
        return {row.nombre_producto: row.id_productos for row in resultado}

def insertar_productos(nombre_producto, precio_venta):
    """
    Inserta un nuevo producto final en el catálogo.
    """
    query = text("""
        INSERT INTO productos (nombre_producto, precio_venta) 
        VALUES (:nombre_producto, :precio_venta);
    """)
    with engine.begin() as conn:
        conn.execute(
            query, {"nombre_producto": nombre_producto, "precio_venta": precio_venta}
        )