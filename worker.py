import argparse
import concurrent.futures
import json
import socket
import threading

from database import (
    register_user,
    login_user,
    create_task,
    list_tasks,
    delete_task
)

BUFFER_SIZE = 4096


# ----------------------------------
# Utils
# ----------------------------------
def send_json(sock, payload, lock=None):
    data = (json.dumps(payload) + "\n").encode()

    if lock:
        with lock:
            sock.sendall(data)
    else:
        sock.sendall(data)


def recv_json(sock, buffer):
    while True:
        if b"\n" in buffer:
            raw, _, rest = buffer.partition(b"\n")
            buffer[:] = rest

            return json.loads(raw.decode())

        chunk = sock.recv(BUFFER_SIZE)

        if not chunk:
            return None

        buffer.extend(chunk)


# ----------------------------------
# Requests
# ----------------------------------
def process_request(request):
    action = request.get("action")

    if action == "register":
        return register_user(
            request["username"],
            request["password"]
        )

    if action == "login":
        return login_user(
            request["username"],
            request["password"]
        )

    if action == "create_task":
        return create_task(
            request["username"],
            request["title"]
        )

    if action == "list_tasks":
        return list_tasks(
            request["username"]
        )

    if action == "delete_task":
        return delete_task(
            request["task_id"],
            request["username"]
        )

    return {
        "ok": False,
        "message": "Acción inválida"
    }


# ----------------------------------
# Worker
# ----------------------------------
def handle_request(request, sock, lock, worker_name):
    response = process_request(request)

    response["worker"] = worker_name
    response["request_id"] = request["request_id"]

    send_json(sock, response, lock)


parser = argparse.ArgumentParser(description="Worker")

parser.add_argument("--name", required=True)
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=6000)
parser.add_argument("--threads", type=int, default=5)

args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((args.host, args.port))

lock = threading.Lock()

send_json(sock, {
    "type": "register",
    "name": args.name
}, lock)

buffer = bytearray()

ack = recv_json(sock, buffer)

if ack["type"] != "registered":
    raise RuntimeError("Registro rechazado")

print(f"[{args.name}] Worker conectado")

executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=args.threads
)

try:
    while True:
        request = recv_json(sock, buffer)

        if request is None:
            break

        executor.submit(
            handle_request,
            request,
            sock,
            lock,
            args.name
        )

except KeyboardInterrupt:
    pass

finally:
    executor.shutdown(wait=True)
    sock.close()