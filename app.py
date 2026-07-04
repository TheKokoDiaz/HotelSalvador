""" COMANDO PARA EJECUTAR LA APLICACIÓN """
# flask --app app run

""" LIBRERÍAS """
import pymysql
from flask import Flask, jsonify, request, session, render_template

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
        password = "",  #La conexión no lleva contraseña
        database = "DB_SistemaHotelero",
        port     = 3306
    )

""" FUNCIONES """
# Verifica el ID para ver si ya se inicio sesión
def isLogged():
    id = session.get("id")
    print(id)

    if(id == 0 or id == None):
        return False
    else:
        return True

""" FUNCIONES DE FLASK """
# Página Principal
@app.route("/")
def index():
    if(isLogged()):
        return render_template("index.html")
    else:
        return render_template("login.html")

# Inicio de Sesión
@app.route('/login', methods=["POST"])
def login():
    # NOTA: POR EL MOMENTO ESTE LOGIN SOLO PERMITE A "CLIENTES" INGRESAR,
    # SE DEBE MODIFICAR EL PROCEDIMIENTO ALMACENADO.

    # Recuperamos los datos del formulario
    email = request.form["correo"]
    password = request.form["contrasenia"]

    # Ejecutamos nuestro procedimiento almacenado
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.callproc("SP_IniciarSesion", [email, password])
    query = cursor.fetchall()[0]    # Solo se recupera 1 renglón
    cursor.close()
    conn.close()

    # 0 -> ID 
    # 1 -> Nombre
    # 2 -> Direccion (Correo)
    # 3 -> Telefono

    if(query[0] == 0):
        return render_template("login.html", alert="Correo o contraseña incorrectos")
    else:
        return render_template("index.html")