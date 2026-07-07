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
        password = "",
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
    return "Vista de menú (SIS_Platillo / SIS_Pedido) — pendiente."

@app.route("/cliente/cuenta")
def cliente_cuenta():
    return "Vista de la cuenta del cliente — pendiente."


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