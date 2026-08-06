import pandas as pd
from sqlalchemy import text
from database.conexion import engine


def asociar_insumo_a_receta(id_producto, id_insumo, cantidad_requerida):
    """
    Inserta o actualiza un ingrediente dentro de la receta de un producto en PostgreSQL.
    """
    query = text("""
        INSERT INTO recetas (producto_id, insumo_id, cantidad_insumo)
        VALUES (:id_producto, :id_insumo, :cantidad)
        ON CONFLICT (producto_id, insumo_id) 
        DO UPDATE SET cantidad_insumo = EXCLUDED.cantidad_insumo;
    """)
    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "id_producto": id_producto,
                "id_insumo": id_insumo,
                "cantidad": cantidad_requerida,
            },
        )


def eliminar_insumo_de_receta(id_producto, id_insumo):
    """
    Elimina un ingrediente de la receta de un producto en PostgreSQL.
    """
    query = text("""
        DELETE FROM recetas 
        WHERE producto_id = :id_producto AND insumo_id = :id_insumo;
    """)
    with engine.begin() as conn:
        conn.execute(
            query,
            {"id_producto": id_producto, "id_insumo": id_insumo},
        )


def obtener_receta_producto(id_producto):
    """
    Obtiene la ficha técnica del producto consultando directamente la VISTA 'vista_desglose_recetas'.
    """
    query = text("""
        SELECT 
            id_insumo,
            insumo,
            cantidad_insumo AS cantidad_requerida,
            unidad_medida,
            costo_unidad,
            costo_ingrediente
        FROM vista_desglose_recetas
        WHERE producto_id = :id_producto;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"id_producto": id_producto})