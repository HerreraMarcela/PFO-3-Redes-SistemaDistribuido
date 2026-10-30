import sqlite3

DATABASE = "database.db"


# ----------------------------------
# Conexión
# ----------------------------------
def get_connection():
    return sqlite3.connect(DATABASE)


# ----------------------------------
# Inicializar DB
# ----------------------------------
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        )
        """
    )

    conn.commit()
    conn.close()


# ----------------------------------
# Usuarios
# ----------------------------------
def register_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()

        return {
            "ok": True,
            "message": "Usuario registrado"
        }

    except sqlite3.IntegrityError:
        return {
            "ok": False,
            "message": "El usuario ya existe"
        }

    finally:
        conn.close()



def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return {
            "ok": True,
            "message": "Login exitoso"
        }

    return {
        "ok": False,
        "message": "Credenciales incorrectas"
    }


# ----------------------------------
# Tareas
# ----------------------------------
def create_task(username, title):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO tasks (username, title) VALUES (?, ?)",
        (username, title)
    )

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "message": "Tarea creada"
    }



def list_tasks(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title, completed FROM tasks WHERE username=?",
        (username,)
    )

    rows = cursor.fetchall()

    conn.close()

    tasks = []

    for row in rows:
        tasks.append({
            "id": row[0],
            "title": row[1],
            "completed": bool(row[2])
        })

    return {
        "ok": True,
        "tasks": tasks
    }



def delete_task(task_id, username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id=? AND username=?",
        (task_id, username)
    )

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    if deleted:
        return {
            "ok": True,
            "message": "Tarea eliminada"
        }

    return {
        "ok": False,
        "message": "Tarea no encontrada"
    }