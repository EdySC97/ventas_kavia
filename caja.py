import pandas as pd
from sqlalchemy import text
from database.conexion import engine


def obtener_turno_activo():
    """
    Retorna los datos del turno de caja activo ('ABIERTO') en un diccionario.
    Si no hay ninguno abierto, retorna None.
    """
    query = text("""
        SELECT id_turno, monto_inicial, fecha_apertura, estado
        FROM caja_turnos
        WHERE estado = 'ABIERTO'
        ORDER BY id_turno DESC
        LIMIT 1;
    """)
    with engine.connect() as conn:
        res = conn.execute(query).mappings().first()
        return dict(res) if res else None


def abrir_caja(monto_inicial):
    """
    Abre un nuevo turno de caja registrando el monto inicial.
    """
    query = text("""
        INSERT INTO caja_turnos (monto_inicial, estado)
        VALUES (:monto_inicial, 'ABIERTO');
    """)
    with engine.begin() as conn:
        conn.execute(query, {"monto_inicial": monto_inicial})


def cerrar_caja(id_turno, monto_final_real, ventas_efectivo=0.0, gastos_efectivo=0.0):
    """
    Calcula el total esperado en caja (monto_inicial + ventas_efectivo - gastos_efectivo)
    y registra la conciliación de cierre.
    """
    # 1. Obtenemos el monto inicial del turno
    query_turno = text("SELECT monto_inicial FROM caja_turnos WHERE id_turno = :id_turno;")
    with engine.connect() as conn:
        res = conn.execute(query_turno, {"id_turno": id_turno}).first()
        monto_inicial = float(res.monto_inicial) if res else 0.0

    # 2. Cálculo teórico esperado en efectivo
    monto_esperado = monto_inicial + ventas_efectivo - gastos_efectivo
    diferencia = monto_final_real - monto_esperado

    # 3. Guardar el cierre del turno
    query_cierre = text("""
        UPDATE caja_turnos
        SET monto_final_esperado = :monto_esperado,
            monto_final_real = :monto_real,
            diferencia = :diferencia,
            fecha_cierre = CURRENT_TIMESTAMP,
            estado = 'CERRADO'
        WHERE id_turno = :id_turno;
    """)
    with engine.begin() as conn:
        conn.execute(
            query_cierre,
            {
                "monto_esperado": monto_esperado,
                "monto_real": monto_final_real,
                "diferencia": diferencia,
                "id_turno": id_turno,
            },
        )


def obtener_historial_cajas():
    """
    Obtiene el historial de turnos de caja cerrados para reportes.
    """
    query = text("""
        SELECT 
            id_turno,
            monto_inicial,
            monto_final_esperado,
            monto_final_real,
            diferencia,
            fecha_apertura,
            fecha_cierre,
            estado
        FROM caja_turnos
        ORDER BY id_turno DESC;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)