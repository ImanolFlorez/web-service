import os
import sys
import sqlite3
import traceback
from sqlite3 import Error
import logging

class SQLiteConnection():
    
    def __init__(self, db: str):
        self.db = db

    def db_connection(self)-> sqlite3.Connection:
        """
        Crea conexión a unaa base de datos SQLite, en caso de no existir un archivo de base
        de datos, lo crea, y devuelve el objeto de conexión.\n
        Retorna:\n
        Objeto de conexión a la base de datos de SQLite.
        """
        try:
            conn = sqlite3.connect(self.db)
            return conn
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    # Crea una tabla para llevar control de la inserción de datos en las  de las tablas de Área y
    # Parametros.Tambien se controlará si es la primera vez que se corre el entorno en R. Y en general
    # puede ser usada para llevar control de algún procedimiento que deba actuar de dos formas diferentes
    # una primera vez y las demás veces consecutivas y se necesite guardar ese estado.
    def create_flag_table(self, connection: sqlite3.Connection):
        """
        Crea tabla de banderas.\n
        Crea las banderas para controlar cuando se ejecutó el entorno de R.\n
        Parametros:\n
        connection: objeto de conexión a la base de datos.\n
        """
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Flags';")
            flags_exists = cursor.fetchone()
            if not flags_exists:
                cursor.executescript(
                    """CREATE TABLE IF NOT EXISTS Flags (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(20), value VARCHAR(20) NOT NULL);
                    -- Inserta una bandera para controlar si se ejecutó el entorno de R.
                    INSERT INTO Flags (name, value) VALUES ('DEBUG', '1');
                    INSERT INTO Flags (name, value) VALUES ('LOG', '0');
                    INSERT INTO Flags (name, value) VALUES ('WIDTH', '300');
                    INSERT INTO Flags (name, value) VALUES ('HEIGHT', '300');
                    INSERT INTO Flags (name, value) VALUES ('NUM_PAG', '3');
                    INSERT INTO Flags (name, value) VALUES ('OUT_IMAGE', 'png');"""
                )
                connection.commit()
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def select_flag(self, connection: sqlite3.Connection, name: str):
        """
        Hace una consulta a la base de datos SQLite para obtener el registro de una bandera específica.\n
        Parametros:\n
        connection: objeto de conexión a la base de datos.\n
        name: nombre de la bandera que estamos buscando.\n
        Retorna:\n
        Registro de la tabla de Flags para la bandera especifica.
        """
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, name, value FROM Flags WHERE name = ?;", [name])
            row = cursor.fetchone()
            return row
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def update_flag(self, connection: sqlite3.Connection, values: list):
        """
        Actualiza el campo value de una bandera especifica.\n
        Parametros:\n
        connection: objeto de conexión a la base de datos.\n
        values: lista con el nombre de la bandera y nuevo valor del campo.
        """
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE Flags SET value = ? WHERE name = ?;", values)
            connection.commit()
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def create_parameters_table(self, connection:sqlite3.Connection):
        """
        Crea tabla de parametros.\n
        Parametros:\n
        connection: objeto de conexión a la base de datos.\n
        """
        try:
            cursor = connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS Parameters (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(20), value REAL, UNIQUE(name));""")
            connection.commit()
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def create_area_table(self, connection:sqlite3.Connection):
        """
        Crea tabla de áreas.\n
        Parametros:\n
        connection: objeto de conexión a la base de datos.\n
        """
        try:
            cursor = connection.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS Areas (id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(20), timesChosen INTEGER);""")
            connection.commit()
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def select_all_area(self, connection: sqlite3.Connection):
        """
        Hace una consulta para a la base de datos SQLite para obtener todos los registros de la
        tabla Áreas.\n
        Parametros:\n
        connection: objeto de conexión a la base de datos.\n
        Retorna:\n
        Todos los registros de la tabla de Áreas.
        """
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, name, timesChosen FROM Areas;")
            rows = cursor.fetchall()
            return rows
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def select_area(self, connection: sqlite3.Connection, name: str):
        """
        Hace una consulta a la base de datos SQLite para obtener el registro de un área específica.\n
        Parametros:\n
        connection: objeto de conexión a la base de datos.\n
        name: nombre del área que estamos buscando.\n
        Retorna:\n
        Registro de la tabla de Áreas para el área especifica.
        """
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, name, timesChosen FROM Areas WHERE name = ?;", [name])
            row = cursor.fetchone()
            return row
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def insert_area(self, connection: sqlite3.Connection, value: str):
        """
        Crea un nuevo registro de una área.\n
        Parametros:\n
        connection: objeto de conexión a la base de datos.\n
        value: nombre del área que se insertará.
        """
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO Areas (name, timesChosen) VALUES (?, 0);", [value])
            connection.commit()
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def update_area(self, connection: sqlite3.Connection, values: list):
        """
        Actualiza el campo de 'timesChosen' de un área en especifico.\n
        Parametros:\n
        connection: objeto de conexión a la base de datos.\n
        values: lista con el nombre del área y nuevo valor del campo.
        """
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE Areas SET timesChosen = ? WHERE name = ?;", values)
            connection.commit()
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def select_parameter(self, connection: sqlite3.Connection, name: str):
        """
        Hace una consulta a la base de datos SQLite para obtener el registro de un parametro específico.\n
        Parametros:\n
        connection: objeto de conexión a la base de datos.\n
        value:
        Retorna:\n
        Registro de la tabla de Parametros para el parametro especifico.
        """
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, name, value FROM Parameters WHERE name = ?;", [name])
            row = cursor.fetchone()
            return row
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))

    def insert_parameter(self, connection: sqlite3.Connection, values: list):
        """
        Crea un nuevo registro de una área.\n
        Parametros:\n
        connection: objeto de conexión a la base de datos.\n
        values: lista con el nombre y valor del parametro que se insertará.
        """
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO Parameters (name, value) VALUES (?, ?);", values)
            connection.commit()
        except Error:
            print("SQLite traceback: ")
            exc_type, exc_value, exc_tb = sys.exc_info()
            print(traceback.format_exception(exc_type, exc_value, exc_tb))