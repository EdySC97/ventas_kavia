import pandas as pd
from sqlalchemy import text
from database.conexion import engine


def obtener_estado_mesas(id_turno, total_mesas=14):
    query = text("""
        SELECT DISTINCT numero_mesa 
        FROM ventas 
        WHERE id_turno = :id_turno AND estado = 'ABIERTA';
    """)
    with engine.connect() as conn:
        res = conn.execute(query, {"id_turno": id_turno}).fetchall()
        mesas_ocupadas = {row[0] for row in res}
    
    estados = {}
    for i in range(1, total_mesas + 1):
        nombre_mesa = f"Mesa {i}"
        estados[nombre_mesa] = "Ocupada" if nombre_mesa in mesas_ocupadas else "Disponible"
    
    estados["Barra 1"] = "Ocupada" if "Barra 1" in mesas_ocupadas else "Disponible"
    estados["Barra 2"] = "Ocupada" if "Barra 2" in mesas_ocupadas else "Disponible"
    
    return estados


def obtener_comandas_abiertas(id_turno):
    query = text("""
        SELECT 
            v.id_venta, 
            v.numero_mesa, 
            v.tipo_pedido, 
            v.total, 
            v.fecha_venta, 
            COALESCE(u.nombre, 'Caja/Admin') AS mesero
        FROM ventas v
        LEFT JOIN usuarios u ON v.id_mesero = u.id_usuario
        WHERE v.id_turno = :id_turno AND v.estado = 'ABIERTA'
        ORDER BY v.fecha_venta ASC;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"id_turno": id_turno})

def obtener_detalle_comanda(id_venta):
    query = text("""
        SELECT 
            dv.id_producto,
            p.nombre_producto AS nombre,
            dv.cantidad,
            dv.precio_unitario AS precio_venta,
            dv.subtotal
        FROM detalle_ventas dv
        JOIN productos p ON dv.id_producto = p.id_productos
        WHERE dv.id_venta = :id_venta;
    """)
    with engine.connect() as conn:
        res = conn.execute(query, {"id_venta": id_venta}).mappings().all()
        detalles = []
        for row in res:
            detalles.append({
                "id_producto": row["id_producto"],
                "nombre": row["nombre"],
                "cantidad": int(row["cantidad"]),
                "precio_venta": float(row["precio_venta"]),
                "subtotal": float(row["subtotal"])
            })
        return detalles


def guardar_o_actualizar_comanda(id_turno, numero_mesa, tipo_pedido, carrito, id_mesero, id_venta_existente=None):
    if not carrito:
        raise ValueError("El carrito está vacío.")

    total_venta = sum(item["subtotal"] for item in carrito)

    with engine.begin() as conn:
        if id_venta_existente:
            id_venta = id_venta_existente
            conn.execute(
                text("UPDATE ventas SET total = :total, id_mesero = :id_mesero WHERE id_venta = :id_venta;"),
                {"total": total_venta, "id_mesero": id_mesero, "id_venta": id_venta},
            )
            conn.execute(
                text("DELETE FROM detalle_ventas WHERE id_venta = :id_venta;"),
                {"id_venta": id_venta},
            )
        else:
            query_venta = text("""
                INSERT INTO ventas (id_turno, total, metodo_pago, numero_mesa, tipo_pedido, estado, id_mesero)
                VALUES (:id_turno, :total, 'Pendiente', :numero_mesa, :tipo_pedido, 'ABIERTA', :id_mesero)
                RETURNING id_venta;
            """)
            id_venta = conn.execute(
                query_venta,
                {
                    "id_turno": id_turno,
                    "total": total_venta,
                    "numero_mesa": numero_mesa,
                    "tipo_pedido": tipo_pedido,
                    "id_mesero": id_mesero,
                },
            ).scalar()

        for item in carrito:
            query_detalle = text("""
                INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario, subtotal)
                VALUES (:id_venta, :id_producto, :cantidad, :precio, :subtotal);
            """)
            conn.execute(
                query_detalle,
                {
                    "id_venta": id_venta,
                    "id_producto": item["id_producto"],
                    "cantidad": item["cantidad"],
                    "precio": item["precio_venta"],
                    "subtotal": item["subtotal"],
                },
            )

    return id_venta


def cobrar_comanda(id_venta, metodo_pago, pago_con=0.0, cambio=0.0):
    with engine.begin() as conn:
        query_cobro = text("""
            UPDATE ventas
            SET estado = 'PAGADA', 
                metodo_pago = :metodo_pago,
                pago_con = :pago_con,
                cambio = :cambio
            WHERE id_venta = :id_venta;
        """)
        conn.execute(
            query_cobro,
            {
                "metodo_pago": metodo_pago,
                "pago_con": pago_con,
                "cambio": cambio,
                "id_venta": id_venta,
            },
        )

        query_items = text("SELECT id_producto, cantidad FROM detalle_ventas WHERE id_venta = :id_venta;")
        items = conn.execute(query_items, {"id_venta": id_venta}).mappings().all()

        for item in items:
            query_receta = text("""
                SELECT insumo_id, cantidad_insumo 
                FROM recetas 
                WHERE producto_id = :id_producto;
            """)
            receta_items = conn.execute(query_receta, {"id_producto": item["id_producto"]}).mappings().all()

            for ingrediente in receta_items:
                cant_descuento = float(ingrediente["cantidad_insumo"]) * item["cantidad"]
                conn.execute(
                    text("UPDATE insumos SET stock_actual = stock_actual - :cant WHERE id_insumo = :id_insumo;"),
                    {"cant": cant_descuento, "id_insumo": ingrediente["insumo_id"]},
                )