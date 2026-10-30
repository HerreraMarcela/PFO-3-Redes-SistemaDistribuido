import json
import socket

HOST = "127.0.0.1"
PORT = 5000


# ----------------------------------
# Utils
# ----------------------------------
def send_request(payload):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    client.sendall((json.dumps(payload) + "\n").encode())
    response = client.recv(4096).decode().strip()
    client.close()
    return json.loads(response)


# ----------------------------------
# Menú
# ----------------------------------
username = None

while True:
    print("\n=== SISTEMA DISTRIBUIDO DE TAREAS ===")

    if not username:
        print("1. Registro")
        print("2. Login")
        print("3. Salir")

        option = input("Opción: ")

        if option == "1":
            user = input("Usuario: ")
            password = input("Contraseña: ")

            response = send_request({
                "action": "register",
                "username": user,
                "password": password
            })

            print(response["message"])

        elif option == "2":
            user = input("Usuario: ")
            password = input("Contraseña: ")

            response = send_request({
                "action": "login",
                "username": user,
                "password": password
            })

            print(response["message"])

            if response["ok"]:
                username = user

        elif option == "3":
            break

    else:
        print(f"\nUsuario: {username}")
        print("1. Crear tarea")
        print("2. Ver tareas")
        print("3. Eliminar tarea")
        print("4. Logout")

        option = input("Opción: ")

        if option == "1":
            title = input("Título: ")

            response = send_request({
                "action": "create_task",
                "username": username,
                "title": title
            })

            print(response["message"])

        elif option == "2":
            response = send_request({
                "action": "list_tasks",
                "username": username
            })

            print("\n--- TAREAS ---")

            for task in response["tasks"]:
                print(f"{task['id']} - {task['title']}")

        elif option == "3":
            task_id = int(input("ID tarea: "))

            response = send_request({
                "action": "delete_task",
                "username": username,
                "task_id": task_id
            })

            print(response["message"])

        elif option == "4":
            username = None