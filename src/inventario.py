import pandas as pd
from sqlalchemy import text
from database.conexion import engine


def obtener_df_insumos():
    query = text("select * from insumos order by id_insumo ASC;")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        return df


def obtener_dict_insumos():
    query = text(
        "SELECT id_insumo,nombre_insumo FROM insumos ORDER BY nombre_insumo ASC;"
    )
    with engine.connect() as conn:
        resultado = conn.execute(query)
        return {row.nombre_insumo: row.id_insumo for row in resultado}


def agregar_insumo(nombre_insumo, unidad, stock, costo):
    query = text(
        "INSERT INTO insumos(nombre_insumo,unidad_medida,stock_actual,costo_unidad) VALUES (:nombre,:unidad,:stock,:costo);"
    )
    with engine.connect() as conn:
        conn.execute(
            query,
            {"nombre": nombre_insumo, "unidad": unidad, "stock": stock, "costo": costo},
        )
        conn.commit()
def registrar_movimiento_stock(insumo_id, usuario_id, tipo_movimiento, cantidad, costo_unitario, comentarios):
    with engine.begin() as conn:
        # 1. Actualizar el stock actual e insumo en la tabla insumos
        if "Entrada" in tipo_movimiento or tipo_movimiento == "ENTRADA":
            conn.execute(
                text("UPDATE insumos SET stock_actual = stock_actual + :cant, costo_unidad = :costo WHERE id_insumo = :id"),
                {"cant": float(cantidad), "costo": float(costo_unitario), "id": insumo_id}
            )
            tipo_bd = "ENTRADA"
        else:
            conn.execute(
                text("UPDATE insumos SET stock_actual = stock_actual - :cant WHERE id_insumo = :id"),
                {"cant": float(cantidad), "id": insumo_id}
            )
            tipo_bd = "SALIDA"

        # 2. Insertar usando exactamente los 8 campos de tu tabla de movimientos
        conn.execute(
            text("""
                INSERT INTO movimientos (insumo_id, usuario_id, tipo_movimiento, cantidad, costo_unitario, comentarios)
                VALUES (:insumo_id, :usuario_id, :tipo_movimiento, :cantidad, :costo_unitario, :comentarios);
            """),
            {
                "insumo_id": insumo_id,
                "usuario_id": usuario_id,
                "tipo_movimiento": tipo_bd,
                "cantidad": float(cantidad),
                "costo_unitario": float(costo_unitario),
                "comentarios": comentarios
            }
        )