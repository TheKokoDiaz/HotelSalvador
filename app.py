""" LIBRERÍAS """
import pymysql
from flask import Flask, jsonify, request, render_template

""" VARIABLES GLOBALES """
app = Flask(__name__)

""" BASE DE DATOS """
# MySQL
def get_db_connection():
    # ESTO SE DEFINE DESPUÉS
    return pymysql.connect(
        host     = "127.0.0.1",
        user     = "",
        password = "",
        database = "",
        port     = 0
    )

""" FUNCIONES DE FLASK """
@app.route("/")
def index():
    return "Hello World"