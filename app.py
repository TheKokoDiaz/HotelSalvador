""" COMANDO PARA EJECUTAR LA APLICACIÓN """
# flask --app app run

""" LIBRERÍAS """
import pymysql
from flask import Flask, jsonify, request, session, render_template, redirect, url_for
from datetime import datetime

""" VARIABLES GLOBALES """
app = Flask(__name__)
# Contraseña para las variables de sesión
app.secret_key = "poiuytrewqasdfghjklmnbvcxz"

""" BASE DE DATOS """
# MySQL
def get_db_connection():
    return pymysql.connect(
        host     = "127.0.0.1",
        user     = "root",
        password = "12345",
        database = "DB_SistemaHotelero",
        port     = 3306,
        cursorclass = pymysql.cursors.DictCursor # Transforma las tuplas en diccionarios para Jinja
    )

""" FUNCIONES """
# Verifica el ID para ver si ya se inicio sesión
# y recupera el Rol para reedirigir
def isLogged():
    id = session.get("id")

    if(id == 0 or id == None):
        return 0    # 0 de nada
    else:
        rol = session.get("rol")

        if(rol == "Cliente"):
            return 1
        
        if(rol == "Administrador"):
            return 2


""" FUNCIONES DE FLASK """
# Página Principal
@app.route("/")
def index():
    if(isLogged() == 1):
        return render_template("cliente_principal.html")
    elif(isLogged() == 2):
        return render_template("admin_principal.html")
    else:
        return render_template("index.html")

# Inicio de Sesión
@app.route('/login')
def login():
    return render_template("login.html")

# Operaciones del Inicio de Sesión
@app.route('/tryLogin', methods=["POST"])
def tryLogin():
    # Recuperamos los datos del formulario
    email = request.form["correo"]
    password = request.form["contrasenia"]

    # Ejecutamos nuestro procedimiento almacenado
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.callproc("SP_IniciarSesion", [email, password])
    query = cursor.fetchall()[0] # Recuperamos la fila resultante
    cursor.close()
    conn.close()

    # El procedimiento devuelve que el ID es 0 o está vacío
    if not query or query.get('Id') == 0:
        return render_template("login.html", alert=True)
    else:
        # Guardamos los datos generales
        session["id"] = query.get('Id')
        session["rol"] = query.get('Rol')
        session["nombre"] = query.get('Nombre')
        session["correo"] = query.get('Direccion')

        # Revisamos el rol
        if(query.get('Rol') == "Administrador"):
            return render_template("admin_principal.html")
        else:
            # El telefono es la unica variable extra que posee el cliente
            session["telefono"] = query.get('Telefono')
            return render_template("cliente_principal.html")
        
# Registrarse
@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/tryRegister', methods=["POST"])
def tryRegister():
    # Recuperamos los datos del formulario
    nombre = request.form["nombre"]
    email = request.form["correo"]
    telefono = request.form["telefono"]
    contrasenia = request.form["contrasenia"]

    # Procedimiento almacenado
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.callproc("SP_RegistrarCliente", [nombre, email, telefono, contrasenia])
    query = cursor.fetchall()[0]
    conn.commit()   # Confirmamos inserción
    cursor.close()
    conn.close()

    # Checamos si se registró correctamente
    if not query or query.get('Id') == 0:
        return render_template("register.html", alert=query.get('Alerta'))
    else:
        # Guardamos su información en la sesión
        session["id"] = query.get('Id')
        session["rol"] = "Cliente"
        session["nombre"] = nombre
        session["correo"] = email
        session["telefono"] = telefono
        
        return render_template("cliente_principal.html")

# Cierre de Sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# =====================================================================
# RUTAS DEL MÓDULO DE CLIENTE
# =====================================================================

@app.route("/cliente/habitaciones")
def cliente_habitaciones():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT HAB_id, HAB_numero, HAB_tipo_habitacion, HAB_tipo_cama,
                  HAB_precio, HAB_estado, HAB_foto
           FROM SIS_Habitacion
           WHERE HAB_estado = 'Disponible'"""
    )
    habitaciones_db = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        "cliente_habitaciones.html",
        habitaciones=habitaciones_db,
        active="habitaciones",
    )
# --------------------------------------------------------------------------
# REEMPLAZA tu ruta actual de "cliente_reservaciones" (la del texto plano)
# por esta versión real, y AGREGA la nueva ruta "cancelar_reservacion".
# --------------------------------------------------------------------------

@app.route("/cliente/reservaciones")
def cliente_reservaciones():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT r.RES_id, r.RES_num_dias, r.RES_total,
                  h.HAB_numero, h.HAB_tipo_habitacion, h.HAB_tipo_cama
           FROM SIS_Reservacion r
           JOIN SIS_Habitacion h ON r.HAB_id_fk = h.HAB_id
           WHERE r.CLI_id_fk = %s
           ORDER BY r.RES_id DESC""",
        (session["id"],)
    )
    reservaciones_db = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        "cliente_reservaciones.html",
        reservaciones=reservaciones_db,
        active="reservaciones",
    )


# Cancela (elimina) una reservación, solo si le pertenece al cliente en sesión
@app.route("/cliente/reservaciones/<int:res_id>/cancelar", methods=["POST"])
def cancelar_reservacion(res_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # El "AND CLI_id_fk = %s" evita que un cliente cancele la reservación de otro
    cursor.execute(
        "DELETE FROM SIS_Reservacion WHERE RES_id = %s AND CLI_id_fk = %s",
        (res_id, session["id"])
    )
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("cliente_reservaciones"))

@app.route("/cliente/menu")
def cliente_menu():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT PLA_id, PLA_nombre, PLA_tipo, PLA_precio, PLA_foto
           FROM SIS_Platillo
           ORDER BY PLA_tipo, PLA_nombre"""
    )
    platillos_db = cursor.fetchall()
    cursor.close()
    conn.close()

    # Categorías únicas (en orden de aparición) para armar los botones de filtro
    categorias = []
    for p in platillos_db:
        if p["PLA_tipo"] not in categorias:
            categorias.append(p["PLA_tipo"])

    return render_template(
        "cliente_menu.html",
        platillos=platillos_db,
        categorias=categorias,
        active="menu",
    )
"""
=====================================================================
 RUTAS DEL CHECKOUT / "SU CUENTA"
 Reemplaza tu ruta placeholder:

    @app.route("/cliente/cuenta")
    def cliente_cuenta():
        return "Vista de la cuenta del cliente — pendiente."

 por TODO el bloque de abajo.
=====================================================================
"""

# -------------------------------------------------------------------
# Vista principal de checkout: reservación activa + pedido activo
# -------------------------------------------------------------------
@app.route("/cliente/cuenta")
def cliente_cuenta():
    cliente_id = session.get("id")
    if not cliente_id:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Reservación activa: la más reciente que aún no tiene un recibo asociado
    cursor.execute(
        """SELECT r.RES_id, r.RES_num_dias, r.RES_total,
                  h.HAB_numero, h.HAB_tipo_habitacion, h.HAB_tipo_cama, h.HAB_precio
           FROM SIS_Reservacion r
           JOIN SIS_Habitacion h ON r.HAB_id_fk = h.HAB_id
           WHERE r.CLI_id_fk = %s
           AND r.RES_id NOT IN (SELECT RES_id_fk FROM SIS_Recibo WHERE RES_id_fk IS NOT NULL)
           ORDER BY r.RES_id DESC LIMIT 1""",
        (cliente_id,)
    )
    reservacion = cursor.fetchone()

    # Pedido activo: el más reciente que aún no tiene un recibo asociado
    cursor.execute(
        """SELECT PED_id, PED_total FROM SIS_Pedido
           WHERE CLI_id_fk = %s
           AND PED_id NOT IN (SELECT PED_id_fk FROM SIS_Recibo WHERE PED_id_fk IS NOT NULL)
           ORDER BY PED_id DESC LIMIT 1""",
        (cliente_id,)
    )
    pedido = cursor.fetchone()

    detalle_platillos = []
    if pedido:
        cursor.execute(
            """SELECT p.PLA_id, p.PLA_nombre, p.PLA_tipo, p.PLA_precio, dp.DET_cantidad,
                      (p.PLA_precio * dp.DET_cantidad) AS subtotal
               FROM SIS_Detalle_Pedido dp
               JOIN SIS_Platillo p ON dp.PLA_id_fk = p.PLA_id
               WHERE dp.PED_id_fk = %s""",
            (pedido["PED_id"],)
        )
        detalle_platillos = cursor.fetchall()

    cursor.close()
    conn.close()

    costo_habitacion = float(reservacion["RES_total"]) if reservacion else 0.0
    costo_comida = float(pedido["PED_total"]) if pedido else 0.0
    total_general = costo_habitacion + costo_comida

    return render_template(
        "cliente_cuenta.html",
        reservacion=reservacion,
        pedido=pedido,
        platillos=detalle_platillos,
        costo_habitacion=costo_habitacion,
        costo_comida=costo_comida,
        total_general=total_general,
        active="cuenta",
    )


# -------------------------------------------------------------------
# Agrega un platillo al pedido activo del cliente (llamado desde el
# botón "Agregar" en cliente_menu.html vía fetch/AJAX)
# -------------------------------------------------------------------
@app.route("/cliente/pedido/agregar/<int:pla_id>", methods=["POST"])
def agregar_platillo(pla_id):
    cliente_id = session.get("id")
    if not cliente_id or session.get("rol") != "Cliente":
        return jsonify({"ok": False, "mensaje": "Debes iniciar sesión como cliente."}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    # Buscamos si ya tiene un pedido abierto (sin recibo asociado)
    cursor.execute(
        """SELECT PED_id FROM SIS_Pedido
           WHERE CLI_id_fk = %s
           AND PED_id NOT IN (SELECT PED_id_fk FROM SIS_Recibo WHERE PED_id_fk IS NOT NULL)
           ORDER BY PED_id DESC LIMIT 1""",
        (cliente_id,)
    )
    pedido = cursor.fetchone()

    if pedido:
        ped_id = pedido["PED_id"]
    else:
        cursor.execute("INSERT INTO SIS_Pedido (CLI_id_fk, PED_total) VALUES (%s, 0)", (cliente_id,))
        ped_id = cursor.lastrowid

    # Si el platillo ya estaba en el pedido, solo incrementamos la cantidad
    cursor.execute(
        "SELECT DET_cantidad FROM SIS_Detalle_Pedido WHERE PED_id_fk = %s AND PLA_id_fk = %s",
        (ped_id, pla_id)
    )
    detalle = cursor.fetchone()

    if detalle:
        cursor.execute(
            "UPDATE SIS_Detalle_Pedido SET DET_cantidad = DET_cantidad + 1 WHERE PED_id_fk = %s AND PLA_id_fk = %s",
            (ped_id, pla_id)
        )
    else:
        cursor.execute(
            "INSERT INTO SIS_Detalle_Pedido (PED_id_fk, PLA_id_fk, DET_cantidad) VALUES (%s, %s, 1)",
            (ped_id, pla_id)
        )

    # Recalculamos el total del pedido a partir del detalle
    cursor.execute(
        """UPDATE SIS_Pedido SET PED_total = (
               SELECT COALESCE(SUM(dp.DET_cantidad * pl.PLA_precio), 0)
               FROM SIS_Detalle_Pedido dp
               JOIN SIS_Platillo pl ON dp.PLA_id_fk = pl.PLA_id
               WHERE dp.PED_id_fk = %s
           ) WHERE PED_id = %s""",
        (ped_id, ped_id)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"ok": True, "mensaje": "Platillo agregado a tu cuenta."})


# -------------------------------------------------------------------
# Quita un platillo del pedido activo (botón "Quitar" en cliente_cuenta.html)
# -------------------------------------------------------------------
@app.route("/cliente/pedido/eliminar/<int:pla_id>", methods=["POST"])
def eliminar_platillo(pla_id):
    cliente_id = session.get("id")
    if not cliente_id:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT PED_id FROM SIS_Pedido
           WHERE CLI_id_fk = %s
           AND PED_id NOT IN (SELECT PED_id_fk FROM SIS_Recibo WHERE PED_id_fk IS NOT NULL)
           ORDER BY PED_id DESC LIMIT 1""",
        (cliente_id,)
    )
    pedido = cursor.fetchone()

    if pedido:
        ped_id = pedido["PED_id"]
        cursor.execute(
            "DELETE FROM SIS_Detalle_Pedido WHERE PED_id_fk = %s AND PLA_id_fk = %s",
            (ped_id, pla_id)
        )
        cursor.execute(
            """UPDATE SIS_Pedido SET PED_total = (
                   SELECT COALESCE(SUM(dp.DET_cantidad * pl.PLA_precio), 0)
                   FROM SIS_Detalle_Pedido dp
                   JOIN SIS_Platillo pl ON dp.PLA_id_fk = pl.PLA_id
                   WHERE dp.PED_id_fk = %s
               ) WHERE PED_id = %s""",
            (ped_id, ped_id)
        )
        conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("cliente_cuenta"))


# -------------------------------------------------------------------
# Quita la habitación reservada de la cuenta activa (botón "Quitar"
# junto a la habitación en cliente_cuenta.html)
# -------------------------------------------------------------------
@app.route("/cliente/cuenta/eliminar_habitacion/<int:res_id>", methods=["POST"])
def eliminar_habitacion_cuenta(res_id):
    cliente_id = session.get("id")
    if not cliente_id:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM SIS_Reservacion WHERE RES_id = %s AND CLI_id_fk = %s",
        (res_id, cliente_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("cliente_cuenta"))


# -------------------------------------------------------------------
# Confirma el pago: crea un SIS_Recibo ligado a la reservación y/o
# pedido activos, lo que los "cierra" (dejan de contar como activos)
# -------------------------------------------------------------------
@app.route("/cliente/cuenta/confirmar", methods=["POST"])
def confirmar_pago():
    cliente_id = session.get("id")
    if not cliente_id:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT RES_id, RES_total FROM SIS_Reservacion
           WHERE CLI_id_fk = %s
           AND RES_id NOT IN (SELECT RES_id_fk FROM SIS_Recibo WHERE RES_id_fk IS NOT NULL)
           ORDER BY RES_id DESC LIMIT 1""",
        (cliente_id,)
    )
    reservacion = cursor.fetchone()

    cursor.execute(
        """SELECT PED_id, PED_total FROM SIS_Pedido
           WHERE CLI_id_fk = %s
           AND PED_id NOT IN (SELECT PED_id_fk FROM SIS_Recibo WHERE PED_id_fk IS NOT NULL)
           ORDER BY PED_id DESC LIMIT 1""",
        (cliente_id,)
    )
    pedido = cursor.fetchone()

    if not reservacion and not pedido:
        cursor.close()
        conn.close()
        return redirect(url_for("cliente_cuenta"))

    costo_habitacion = float(reservacion["RES_total"]) if reservacion else 0.0
    costo_comida = float(pedido["PED_total"]) if pedido else 0.0
    total = costo_habitacion + costo_comida

    cursor.execute(
        """INSERT INTO SIS_Recibo (REC_costo_comida, REC_costo_bebidas, REC_monto_total, RES_id_fk, PED_id_fk)
           VALUES (%s, 0, %s, %s, %s)""",
        (
            costo_comida,
            total,
            reservacion["RES_id"] if reservacion else None,
            pedido["PED_id"] if pedido else None,
        )
    )
    conn.commit()
    rec_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return redirect(url_for("cliente_ticket", rec_id=rec_id))


# -------------------------------------------------------------------
# Muestra el ticket final tras confirmar el pago
# -------------------------------------------------------------------
@app.route("/cliente/ticket/<int:rec_id>")
def cliente_ticket(rec_id):
    cliente_id = session.get("id")
    if not cliente_id:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """SELECT rec.REC_id, rec.REC_monto_total, rec.RES_id_fk, rec.PED_id_fk,
                  r.RES_num_dias, r.RES_total,
                  h.HAB_numero, h.HAB_tipo_habitacion
           FROM SIS_Recibo rec
           LEFT JOIN SIS_Reservacion r ON rec.RES_id_fk = r.RES_id
           LEFT JOIN SIS_Habitacion h ON r.HAB_id_fk = h.HAB_id
           WHERE rec.REC_id = %s""",
        (rec_id,)
    )
    recibo = cursor.fetchone()

    detalle_platillos = []
    if recibo and recibo["PED_id_fk"]:
        cursor.execute(
            """SELECT p.PLA_nombre, p.PLA_precio, dp.DET_cantidad,
                      (p.PLA_precio * dp.DET_cantidad) AS subtotal
               FROM SIS_Detalle_Pedido dp
               JOIN SIS_Platillo p ON dp.PLA_id_fk = p.PLA_id
               WHERE dp.PED_id_fk = %s""",
            (recibo["PED_id_fk"],)
        )
        detalle_platillos = cursor.fetchall()

    cursor.close()
    conn.close()

    if not recibo:
        return redirect(url_for("cliente_cuenta"))

    return render_template("cliente_ticket.html", recibo=recibo, platillos=detalle_platillos)


# --------------------------------------------------------------------------
# AGREGAR ESTO A app.py
# 1. Al inicio del archivo, junto a tus demás imports, agrega:
#       from datetime import datetime
# 2. Pega estas dos rutas donde tengas las demás rutas de cliente.
# --------------------------------------------------------------------------

# Muestra el formulario de solicitud para UNA habitación específica
# (se llega aquí después de darle click a una habitación en el listado)
@app.route("/cliente/habitaciones/<int:hab_id>/solicitar", methods=["GET"])
def cliente_solicitud_habitacion(hab_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT HAB_id, HAB_numero, HAB_tipo_habitacion, HAB_tipo_cama,
                  HAB_precio, HAB_estado, HAB_foto
           FROM SIS_Habitacion WHERE HAB_id = %s""",
        (hab_id,)
    )
    habitacion = cursor.fetchone()
    cursor.close()
    conn.close()

    # Si el id no existe, regresamos al listado en vez de tronar
    if not habitacion:
        return redirect(url_for("cliente_habitaciones"))

    return render_template(
        "cliente_solicitud_habitacion.html",
        habitacion=habitacion,
        active="habitaciones",
    )


# Procesa el envío del formulario y crea la reservación real en la BD
@app.route("/cliente/habitaciones/<int:hab_id>/solicitar", methods=["POST"])
def procesar_solicitud_habitacion(hab_id):
    fecha_entrada_str = request.form["fecha_entrada"]
    fecha_salida_str = request.form["fecha_salida"]

    try:
        entrada = datetime.strptime(fecha_entrada_str, "%Y-%m-%d")
        salida = datetime.strptime(fecha_salida_str, "%Y-%m-%d")
        num_dias = (salida - entrada).days
    except (ValueError, KeyError):
        num_dias = 0

    conn = get_db_connection()
    cursor = conn.cursor()

    # Recuperamos el precio real de la habitación (nunca confiar en el precio del formulario)
    cursor.execute("SELECT HAB_precio FROM SIS_Habitacion WHERE HAB_id = %s", (hab_id,))
    habitacion = cursor.fetchone()

    if not habitacion or num_dias <= 0:
        cursor.close()
        conn.close()
        # Fecha inválida o habitación inexistente: regresamos al formulario
        return redirect(url_for("cliente_solicitud_habitacion", hab_id=hab_id))

    total = float(habitacion["HAB_precio"]) * num_dias

    cursor.execute(
        """INSERT INTO SIS_Reservacion (CLI_id_fk, HAB_id_fk, RES_num_dias, RES_total)
           VALUES (%s, %s, %s, %s)""",
        (session["id"], hab_id, num_dias, total)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("cliente_reservaciones"))
# =====================================================================
# RUTAS DEL MÓDULO DE ADMINISTRACIÓN (Mapeadas a la BD de SqlScript.sql)
# =====================================================================

# 1. Panel de Control de Alimentos (CRUD)
@app.route("/admin/comida", methods=["GET"])
def admin_comida():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Cambiado a PLA_tipo para coincidir al 100% con tu tabla SIS_Platillo
    cursor.execute("SELECT PLA_id, PLA_nombre, PLA_tipo, PLA_precio FROM SIS_Platillo")
    platillos_db = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template("admin_comida.html", platillos=platillos_db)

# Acción POST para insertar un platillo nuevo
@app.route("/admin/comida/agregar", methods=["POST"])
def agregar_comida():
    nombre = request.form["nombre"]
    tipo = request.form["tipo"] # Lee el input 'tipo' del formulario HTML
    precio = request.form["precio"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Inserción con los campos oficiales de tu script SQL
    cursor.execute(
        "INSERT INTO SIS_Platillo (PLA_nombre, PLA_tipo, PLA_precio) VALUES (%s, %s, %s)",
        (nombre, tipo, precio)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for("admin_comida"))

# Acción para eliminar un platillo por ID
@app.route("/admin/comida/eliminar/<int:id>", methods=["GET"])
def eliminar_comida(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM SIS_Platillo WHERE PLA_id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for("admin_comida"))


# 2. Monitor Resumido de Habitaciones
@app.route("/admin/habitaciones", methods=["GET"])
def admin_habitaciones():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Lee los campos oficiales de tu tabla SIS_Habitacion
    cursor.execute("SELECT HAB_id, HAB_numero, HAB_tipo_habitacion, HAB_estado FROM SIS_Habitacion")
    habitaciones_db = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template("admin_habitaciones.html", habitaciones=habitaciones_db)

# Acción POST para cambiar el estado en caliente de un cuarto
@app.route("/admin/habitaciones/cambiar-estado/<int:id>", methods=["POST"])
def cambiar_estado_habitacion(id):
    nuevo_estado = request.form["nuevo_estado"]
    
    if nuevo_estado:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE SIS_Habitacion SET HAB_estado = %s WHERE HAB_id = %s",
            (nuevo_estado, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
    return redirect(url_for("admin_habitaciones"))