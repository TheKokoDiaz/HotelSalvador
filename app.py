""" COMANDO PARA EJECUTAR LA APLICACIÓN """
# flask --app app run

""" LIBRERÍAS """
import pymysql
from flask import Flask, jsonify, request, session, render_template, redirect, url_for

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
        password = "",  # La conexión no lleva contraseña
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
        return render_template("login.html", alert="Correo o contraseña incorrectos")
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

# Cierre de Sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


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