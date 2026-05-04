import sqlite3
from pathlib import Path

DB_PATH = Path("app/database/trax.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profesionales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            servicio TEXT NOT NULL,
            zona TEXT NOT NULL,
            telefono TEXT,
            descripcion TEXT
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solicitudes_rubros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_rubro TEXT NOT NULL,
        descripcion TEXT,
        email_notificacion TEXT,
        estado TEXT DEFAULT 'PENDIENTE'
    )
""")

    conn.commit()
    conn.close()


def insertar_datos_demo():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM profesionales")
    cantidad = cursor.fetchone()[0]

    if cantidad == 0:
        profesionales = [
            ("Juan Electricista", "Electricidad", "Palermo", "1122334455", "Instalaciones eléctricas domiciliarias."),
            ("Técnicos Frío Sur", "Refrigeración A/C", "Caballito", "1133445566", "Reparación e instalación de aire acondicionado."),
            ("Herrería López", "Herrería", "Quilmes", "1144556677", "Rejas, portones y estructuras metálicas."),
            ("Plomería Express", "Plomería", "Flores", "1155667788", "Urgencias y mantenimiento."),
            ("Gasista Matriculado Norte", "Gas domiciliario", "Belgrano", "1166778899", "Instalaciones y reparaciones de gas.")
        ]

        cursor.executemany("""
            INSERT INTO profesionales (nombre, servicio, zona, telefono, descripcion)
            VALUES (?, ?, ?, ?, ?)
        """, profesionales)

    conn.commit()
    conn.close()


def buscar_profesionales(servicio, zona):
    conn = get_connection()
    cursor = conn.cursor()

def crear_profesional(nombre, servicio, zona, telefono, descripcion):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO profesionales (nombre, servicio, zona, telefono, descripcion)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre, servicio, zona, telefono, descripcion))

    conn.commit()
    conn.close()

    cursor.execute("""
        SELECT * FROM profesionales
        WHERE servicio LIKE ?
        AND zona LIKE ?
    """, (f"%{servicio}%", f"%{zona}%"))

    resultados = cursor.fetchall()
    conn.close()

    return resultados
def solicitar_rubro(nombre_rubro, descripcion, email_notificacion):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO solicitudes_rubros (nombre_rubro, descripcion, email_notificacion)
        VALUES (?, ?, ?)
    """, (nombre_rubro, descripcion, email_notificacion))

    conn.commit()

    cursor.execute("""
        SELECT COUNT(*) FROM solicitudes_rubros
        WHERE LOWER(nombre_rubro) = LOWER(?)
    """, (nombre_rubro,))

    cantidad = cursor.fetchone()[0]

    if cantidad >= 10:
        cursor.execute("""
            UPDATE solicitudes_rubros
            SET estado = 'NOTIFICAR_ADMIN'
            WHERE LOWER(nombre_rubro) = LOWER(?)
        """, (nombre_rubro,))
        conn.commit()

    conn.close()

    return cantidad