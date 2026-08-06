import pandas as pd
import streamlit as st

from src.auth import validar_login
from src.inventario import obtener_df_insumos, agregar_insumo, obtener_dict_insumos, registrar_movimiento_stock
from src.recetas import asociar_insumo_a_receta, eliminar_insumo_de_receta, obtener_receta_producto
from src.finanzas import obtener_gastos, obtener_dict_gastos, registrar_movimiento_gasto, obtener_dic_productos, insertar_productos
from src.caja import obtener_turno_activo, abrir_caja, cerrar_caja, obtener_historial_cajas
from src.pos import obtener_comandas_abiertas, obtener_detalle_comanda, guardar_o_actualizar_comanda, cobrar_comanda, obtener_estado_mesas
from src.ticket import generar_pdf_ticket

st.set_page_config(page_title="Bar Kavia - POS", page_icon="🍸", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { border-radius: 12px !important; border: 1px solid #e0e0e0 !important; font-weight: 600 !important; padding: 12px 10px !important; }
    .total-banner { background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%); color: white; padding: 15px; border-radius: 12px; text-align: center; font-size: 22px; font-weight: bold; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

if "usuario" not in st.session_state: st.session_state["usuario"] = None
if "carrito" not in st.session_state: st.session_state["carrito"] = []
if "mesa_activa" not in st.session_state: st.session_state["mesa_activa"] = None
if "id_venta_activa" not in st.session_state: st.session_state["id_venta_activa"] = None

# =========================================================
# PANTALLA DE LOGIN
# =========================================================
if st.session_state["usuario"] is None:
    st.title("🍸 Bar Kavia - POS")
    st.subheader("Acceso por PIN")
    col_box, _ = st.columns([1, 1])
    with col_box:
        with st.form("form_login"):
            pin_input = st.text_input("Ingresa tu PIN:", type="password", placeholder="****")
            if st.form_submit_button("Ingresar", type="primary", use_container_width=True):
                user_data = validar_login(pin_input)
                if user_data:
                    st.session_state["usuario"] = user_data
                    st.rerun()
                else:
                    st.error("❌ PIN incorrecto o usuario inactivo.")
else:
    user = st.session_state["usuario"]

    st.sidebar.title(f"👤 {user['nombre']}")
    st.sidebar.caption(f"Rol: **{user['rol']}**")
    
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.sidebar.markdown("---")

    if user["rol"] == "Mesero":
        opciones_menu = ["📝 Tomar Comanda"]
    else:
        opciones_menu = [
            "🍸 Punto de Venta (POS)", 
            "💵 Caja y Turnos", 
            "📋 Inventario e Insumos", 
            "👨‍🍳 Recetas y Productos", 
            "📉 Gastos"
        ]

    opcion = st.sidebar.radio("Navegación", opciones_menu)

    # =========================================================
    # 1. MÓDULO DE PUNTO DE VENTA (POS Y COMANDAS)
    # =========================================================
    if opcion in ["📝 Tomar Comanda", "🍸 Punto de Venta (POS)"]:
        turno_activo = obtener_turno_activo()

        if turno_activo is None:
            st.error("🚫 **CAJA CERRADA**: El administrador debe abrir turno de caja para operar el POS.")
        else:
            is_mesero = (user["rol"] == "Mesero")
            
            if is_mesero:
                st.title(f"📱 Comandas — Mesero: {user['nombre']}")
                tab_pos, tab_mesas = st.tabs(["📝 Tomar Pedido", "🍽️ Mesas Abiertas"])
            else:
                st.title("🍸 Punto de Venta - Barra / Caja")
                tab_pos, tab_mesas = st.tabs(["🛒 POS / Barra", "🍽️ Cuentas Abiertas"])

            with tab_pos:
                tipo_pedido = st.radio("Servicio:", ["Comer Aquí", "Para Llevar"], horizontal=True, key="radio_tipo_pedido")
                
                mesa_input = None
                if tipo_pedido == "Comer Aquí":
                    with st.expander("📍 Mapa de Mesas y Barras", expanded=True):
                        estados_mesas = obtener_estado_mesas(turno_activo["id_turno"])
                        cols = st.columns(4)
                        for i, (nom_m, est_m) in enumerate(estados_mesas.items()):
                            with cols[i % 4]:
                                if est_m == "Ocupada" and st.session_state["mesa_activa"] != nom_m:
                                    st.button(f"🔴 {nom_m}\n(Ocupada)", key=f"occ_{nom_m}", disabled=True, use_container_width=True)
                                elif est_m == "Ocupada" and st.session_state["mesa_activa"] == nom_m:
                                    st.button(f"🟡 {nom_m}\n(Editando)", key=f"edit_{nom_m}", use_container_width=True)
                                else:
                                    if st.button(f"🟢 {nom_m}\n(Libre)", key=f"free_{nom_m}", use_container_width=True):
                                        st.session_state["mesa_activa"] = nom_m
                                        st.session_state["id_venta_activa"] = None
                                        st.rerun()
                                        
                    if st.session_state["mesa_activa"]:
                        mesa_input = st.session_state["mesa_activa"]
                        st.info(f"📍 Mesa seleccionada: **{mesa_input}**")
                else:
                    mesa_input = "Venta Rápida"
                    st.session_state["mesa_activa"] = None
                    st.session_state["id_venta_activa"] = None

                st.divider()

                if mesa_input:
                    col_izq, col_der = st.columns([1.2, 0.8]) if not is_mesero else st.columns([1, 1])

                    with col_izq:
                        st.subheader("Carta / Bebidas")
                        busqueda = st.text_input("🔍 Buscar bebida o producto:", placeholder="Ej. Cantarito...", key="input_busq_prod")
                        
                        from database.conexion import engine
                        from sqlalchemy import text
                        with engine.connect() as conn:
                            df_prods = pd.read_sql(text("SELECT * FROM productos ORDER BY nombre_producto ASC;"), conn)

                        if busqueda.strip():
                            df_prods = df_prods[df_prods["nombre_producto"].str.contains(busqueda, case=False, na=False)]

                        grid_cat = st.columns(3 if not is_mesero else 2)
                        for idx, row in df_prods.reset_index(drop=True).iterrows():
                            with grid_cat[idx % (3 if not is_mesero else 2)]:
                                p_id, p_nom, p_prec = int(row["id_productos"]), row["nombre_producto"], float(row["precio_venta"])
                                if st.button(f"🍹 {p_nom}\n${p_prec:.2f}", key=f"cat_{p_id}", use_container_width=True):
                                    encontrado = False
                                    for item in st.session_state["carrito"]:
                                        if item["id_producto"] == p_id:
                                            item["cantidad"] += 1
                                            item["subtotal"] = item["cantidad"] * item["precio_venta"]
                                            encontrado = True
                                            break
                                    if not encontrado:
                                        st.session_state["carrito"].append({
                                            "id_producto": p_id, "nombre": p_nom, "precio_venta": p_prec, "cantidad": 1, "subtotal": p_prec
                                        })
                                    st.rerun()

                    with col_der:
                        st.subheader("📋 Pedido actual")
                        total_cuenta = 0.0
                        if not st.session_state["carrito"]:
                            st.warning("Carrito vacío.")
                        else:
                            for idx, item in enumerate(st.session_state["carrito"]):
                                c_p, c_c, c_s = st.columns([2, 1.5, 1])
                                c_p.write(f"**{item['nombre']}**")
                                b_sub, b_num, b_add = c_c.columns(3)
                                if b_sub.button("➖", key=f"d_{idx}"):
                                    item["cantidad"] -= 1
                                    if item["cantidad"] <= 0: st.session_state["carrito"].pop(idx)
                                    else: item["subtotal"] = item["cantidad"] * item["precio_venta"]
                                    st.rerun()
                                b_num.write(f"`{item['cantidad']}`")
                                if b_add.button("➕", key=f"i_{idx}"):
                                    item["cantidad"] += 1
                                    item["subtotal"] = item["cantidad"] * item["precio_venta"]
                                    st.rerun()
                                c_s.write(f"${float(item['subtotal']):.2f}")
                                total_cuenta += float(item["subtotal"])

                        st.markdown(f"<div class='total-banner'>TOTAL: ${total_cuenta:.2f} MXN</div>", unsafe_allow_html=True)
                        
                        if st.button("🗑️ Vaciar Carrito", use_container_width=True, key="btn_vaciar_carrito"):
                            st.session_state["carrito"] = []
                            st.rerun()

                        if is_mesero:
                            if st.button("🚀 ENVIAR A BARRA / GUARDAR", type="primary", use_container_width=True):
                                guardar_o_actualizar_comanda(
                                    turno_activo["id_turno"], mesa_input, tipo_pedido, 
                                    st.session_state["carrito"], user["id_usuario"], st.session_state["id_venta_activa"]
                                )
                                st.balloons()
                                st.success(f"¡Comanda enviada a `{mesa_input}` por {user['nombre']}!")
                                st.session_state["carrito"], st.session_state["mesa_activa"], st.session_state["id_venta_activa"] = [], None, None
                                st.rerun()
                        else:
                            if tipo_pedido == "Comer Aquí":
                                if st.button("💾 Guardar Mesa", use_container_width=True):
                                    guardar_o_actualizar_comanda(
                                        turno_activo["id_turno"], mesa_input, tipo_pedido, 
                                        st.session_state["carrito"], user["id_usuario"], st.session_state["id_venta_activa"]
                                    )
                                    st.success("Mesa guardada correctamente.")
                                    st.session_state["carrito"], st.session_state["mesa_activa"], st.session_state["id_venta_activa"] = [], None, None
                                    st.rerun()

                            st.divider()
                            metodo_pago = st.selectbox("Método de Pago:", ["Efectivo", "Tarjeta", "Transferencia"], key="sel_met_pago")
                            pago_con, cambio = (total_cuenta, 0.0)
                            if metodo_pago == "Efectivo":
                                pago_con = st.number_input("Efectivo Recibido ($):", min_value=0.0, value=float(total_cuenta), key="num_efectivo_recibido")
                                cambio = pago_con - total_cuenta

                            es_valido = True if (metodo_pago != "Efectivo" or cambio >= 0) else False

                            if st.button("✅ COBRAR Y GENERAR TICKET", type="primary", use_container_width=True, disabled=not es_valido):
                                id_v = guardar_o_actualizar_comanda(
                                    turno_activo["id_turno"], mesa_input, tipo_pedido, 
                                    st.session_state["carrito"], user["id_usuario"], st.session_state["id_venta_activa"]
                                )
                                cobrar_comanda(id_v, metodo_pago, pago_con=pago_con, cambio=cambio)
                                _, pdf_bytes = generar_pdf_ticket(id_v, mesa_input, tipo_pedido, metodo_pago, total_cuenta, pago_con, cambio, st.session_state["carrito"], nombre_mesero=user["nombre"])
                                st.success("🎉 Venta cobrada con éxito.")
                                st.download_button("📄 Descargar Ticket PDF", data=pdf_bytes, file_name=f"ticket_{id_v}.pdf", mime="application/pdf", use_container_width=True, key="dl_pdf_main")
                                st.session_state["carrito"], st.session_state["mesa_activa"], st.session_state["id_venta_activa"] = [], None, None
                else:
                    st.info("👆 Selecciona una mesa libre (verde) en el mapa superior para comenzar.")

            with tab_mesas:
                df_mesas = obtener_comandas_abiertas(turno_activo["id_turno"])
                if df_mesas.empty:
                    st.info("No hay mesas o cuentas abiertas en este turno.")
                else:
                    for _, row in df_mesas.iterrows():
                        mesero_txt = f" (Atiende: {row['mesero']})" if row['mesero'] else ""
                        with st.expander(f"🍽️ **{row['numero_mesa']}**{mesero_txt} — Total: ${float(row['total']):.2f}"):
                            detalles = obtener_detalle_comanda(row["id_venta"])
                            st.dataframe(pd.DataFrame(detalles)[["nombre", "cantidad", "subtotal"]], use_container_width=True, hide_index=True)

                            if is_mesero:
                                if st.button(f"✏️ Agregar Productos a {row['numero_mesa']}", key=f"m_add_{row['id_venta']}", type="primary", use_container_width=True):
                                    st.session_state["carrito"] = detalles
                                    st.session_state["mesa_activa"] = row["numero_mesa"]
                                    st.session_state["id_venta_activa"] = row["id_venta"]
                                    st.rerun()
                            else:
                                c1, c2 = st.columns(2)
                                with c1:
                                    if st.button(f"✏️ Editar Cuenta", key=f"c_add_{row['id_venta']}", use_container_width=True):
                                        st.session_state["carrito"] = detalles
                                        st.session_state["mesa_activa"] = row["numero_mesa"]
                                        st.session_state["id_venta_activa"] = row["id_venta"]
                                        st.rerun()
                                with c2:
                                    m_pago = st.selectbox("Cobro:", ["Efectivo", "Tarjeta", "Transferencia"], key=f"m_cob_{row['id_venta']}")
                                    pago_m = st.number_input(f"Efectivo:", min_value=0.0, value=float(row["total"]), key=f"i_pay_{row['id_venta']}") if m_pago == "Efectivo" else float(row["total"])
                                    cambio_m = pago_m - float(row["total"])
                                    
                                    if st.button(f"💰 Cobrar Cuenta", key=f"b_pay_{row['id_venta']}", type="primary", use_container_width=True):
                                        cobrar_comanda(row["id_venta"], m_pago, pago_con=pago_m, cambio=cambio_m)
                                        _, pdf_bytes = generar_pdf_ticket(
                                            row["id_venta"], row["numero_mesa"], row["tipo_pedido"], m_pago, 
                                            float(row["total"]), pago_m, cambio_m, detalles, nombre_mesero=row['mesero'] or "Caja/Admin"
                                        )
                                        st.success("🎉 Cuenta cobrada.")
                                        st.download_button(label="📄 Descargar Ticket PDF", data=pdf_bytes, file_name=f"ticket_{row['id_venta']}.pdf", mime="application/pdf", key=f"dl_{row['id_venta']}", use_container_width=True)

    # =========================================================
    # 2. MÓDULO DE CAJA Y TURNOS
    # =========================================================
    elif opcion == "💵 Caja y Turnos":
        st.title("💵 Gestión de Caja y Turnos")
        turno_activo = obtener_turno_activo()

        if turno_activo is None:
            st.warning("⚠️ No hay ningún turno de caja abierto actualmente.")
            with st.form("form_apertura_caja"):
                monto_inicial = st.number_input("Fondo Inicial en Caja ($):", min_value=0.0, value=500.0)
                if st.form_submit_button("🟢 Abrir Turno de Caja", type="primary"):
                    abrir_caja(monto_inicial)
                    st.success("¡Turno abierto correctamente!")
                    st.rerun()
        else:
            st.success(f"🟢 Caja Abierta actualmente (Turno ID: #{turno_activo['id_turno']})")
            st.info(f"Fondo inicial registrado: ${turno_activo['monto_inicial']:.2f}")

            with st.form("form_cierre_caja"):
                st.subheader("Cierre de Caja")
                efectivo_contado = st.number_input("Efectivo real contado en caja ($):", min_value=0.0, value=0.0)
                if st.form_submit_button("🔴 Cerrar Turno y Conciliar", type="primary"):
                    cerrar_caja(turno_activo['id_turno'], efectivo_contado)
                    st.success("Turno cerrado y registrado con éxito.")
                    st.rerun()

        st.markdown("---")
        st.subheader("📜 Historial de Turnos de Caja")
        st.dataframe(obtener_historial_cajas(), use_container_width=True)

    # =========================================================
    # 3. MÓDULO DE INVENTARIO E INSUMOS
    # =========================================================
    elif opcion == "📋 Inventario e Insumos":
        st.title("📋 Control de Inventario y Botellas/Insumos")
        
        tab_inv_lista, tab_inv_nuevo, tab_inv_mov = st.tabs(["📦 Stock Actual", "➕ Registrar Insumo Base", "🔄 Movimiento de Stock"])

        with tab_inv_lista:
            st.subheader("Insumos en Almacén / Barra")
            st.dataframe(obtener_df_insumos(), use_container_width=True)

        with tab_inv_nuevo:
            st.subheader("Crear Nuevo Insumo Base (Materia Prima / Botella)")
            with st.form("form_nuevo_insumo", clear_on_submit=True):
                nombre_ins = st.text_input("Nombre del Insumo:", placeholder="Ej. Tequila Blanco, Limón, Hielo...")
                unidad_med = st.selectbox("Unidad de Medida:", ["mililitros", "gramos", "piezas"])
                stock_act = st.number_input("Stock Inicial:", min_value=0.0, value=0.0)
                costo_ins = st.number_input("Costo Unitario ($):", min_value=0.0, value=0.0)

                if st.form_submit_button("Guardar Insumo", type="primary"):
                    if nombre_ins.strip():
                        agregar_insumo(nombre_ins, unidad_med, stock_act, costo_ins)
                        st.success(f"¡Insumo `{nombre_ins}` registrado exitosamente!")
                    else:
                        st.error("El nombre del insumo no puede estar vacío.")

        with tab_inv_mov:
            st.subheader("Entrada / Salida de Stock (Compras o Merma)")
            dict_ins = obtener_dict_insumos()
            if not dict_ins:
                st.warning("No hay insumos registrados para mover.")
            else:
                with st.form("form_mov_stock", clear_on_submit=True):
                    insumo_sel = st.selectbox("Seleccionar Insumo:", list(dict_ins.keys()))
                    id_ins = dict_ins[insumo_sel]

                    # Consultar costo actual de la BD para sugerirlo en el input
                    from database.conexion import engine
                    from sqlalchemy import text
                    with engine.begin() as conn:
                        res_c = conn.execute(text("SELECT costo_unidad FROM insumos WHERE id_insumo = :id"), {"id": id_ins}).fetchone()
                        costo_base = float(res_c[0]) if res_c else 0.0

                    tipo_mov = st.radio("Tipo de Movimiento:", ["Entrada (Compra)", "Salida (Merma/Ajuste)"], horizontal=True)
                    cantidad_mov = st.number_input("Cantidad:", min_value=0.01, value=1.0)
                    costo_unitario_mov = st.number_input("Costo Unitario ($):", min_value=0.0, value=costo_base)
                    
                    comentarios_mov = st.text_input("Comentarios / Proveedor:", placeholder="Ej. Factura #123 o merma por caducidad...")

                    if st.form_submit_button("Registrar Movimiento", type="primary"):
                        if comentarios_mov.strip():
                            registrar_movimiento_stock(
                                insumo_id=id_ins,
                                usuario_id=user["id_usuario"],
                                tipo_movimiento=tipo_mov,
                                cantidad=cantidad_mov,
                                costo_unitario=costo_unitario_mov,
                                comentarios=comentarios_mov
                            )
                            st.success("¡Movimiento registrado con éxito en la base de datos!")
                        else:
                            st.error("Debes ingresar un comentario o proveedor válido.")

    # =========================================================
    # 4. MÓDULO DE RECETAS Y PRODUCTOS
    # =========================================================
    elif opcion == "👨‍🍳 Recetas y Productos":
        st.title("👨‍🍳 Catálogo de Bebidas y Recetas (BOM)")

        tab_rec_ver, tab_rec_crear, tab_prod_nuevo = st.tabs(["📖 Ver Recetarios", "🔗 Asociar Insumo a Bebida", "🍸 Nueva Bebida/Plato"])

        with tab_rec_ver:
            st.subheader("Explorar Receta de una Bebida")
            d_p = obtener_dic_productos()
            if not d_p:
                st.warning("No hay productos creados.")
            else:
                prod_sel = st.selectbox("Selecciona Bebida:", list(d_p.keys()), key="sel_ver_receta")
                id_p_sel = d_p[prod_sel]
                df_rec = obtener_receta_producto(id_p_sel)
                if df_rec.empty:
                    st.info(f"El producto `{prod_sel}` no tiene insumos asociados en su receta.")
                else:
                    st.dataframe(df_rec, use_container_width=True)

        with tab_rec_crear:
            st.subheader("Vincular Insumos Base a una Bebida (Explosión de Inventario)")
            d_p = obtener_dic_productos()
            dict_ins = obtener_dict_insumos()
            
            if not d_p or not dict_ins:
                st.warning("Asegúrate de tener productos y al menos un insumo registrado.")
            else:
                with st.form("form_asociar_receta", clear_on_submit=True):
                    p_receta = st.selectbox("Bebida de Venta:", list(d_p.keys()))
                    i_receta = st.selectbox("Insumo Base:", list(dict_ins.keys()))
                    cant_usada = st.number_input("Cantidad requerida por porción:", min_value=0.001, value=50.0)

                    if st.form_submit_button("Guardar Asociación en Receta", type="primary"):
                        asociar_insumo_a_receta(d_p[p_receta], dict_ins[i_receta], cant_usada)
                        st.success("¡Receta actualizada con éxito!")

        with tab_prod_nuevo:
            st.subheader("Registrar Nueva Bebida o Plato al Menú")
            with st.form("form_nuevo_producto", clear_on_submit=True):
                nom_prod = st.text_input("Nombre de la Bebida:", placeholder="Ej. Cantarito Especial...")
                precio_venta = st.number_input("Precio de Venta al Público ($):", min_value=0.0, value=120.0)

                if st.form_submit_button("Crear Producto", type="primary"):
                    if nom_prod.strip():
                        insertar_productos(nom_prod, precio_venta)
                        st.success(f"¡Producto `{nom_prod}` agregado al menú exitosamente!")
                    else:
                        st.error("El nombre del producto no puede estar vacío.")

    # =========================================================
    # 5. MÓDULO DE GASTOS
    # =========================================================
    elif opcion == "📉 Gastos":
        st.title("📉 Control de Gastos Operativos")
        
        tab_g_ver, tab_g_nuevo = st.tabs(["📊 Historial de Gastos", "➕ Registrar Gasto"])

        with tab_g_ver:
            st.dataframe(obtener_gastos(), use_container_width=True)

        with tab_g_nuevo:
            with st.form("form_nuevo_gasto", clear_on_submit=True):
                desc_gasto = st.text_input("Descripción del Gasto:", placeholder="Ej. Compra de hielo, gas, luz...")
                monto_gasto = st.number_input("Monto ($):", min_value=0.01, value=100.0)

                if st.form_submit_button("Registrar Gasto", type="primary"):
                    if desc_gasto.strip():
                        registrar_movimiento_gasto(desc_gasto, monto_gasto, user["id_usuario"])
                        st.success("¡Gasto registrado de manera exitosa!")
                    else:
                        st.error("Ingresa una descripción válida.")
