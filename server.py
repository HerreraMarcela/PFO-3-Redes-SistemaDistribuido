import json
import queue
import socket
import threading
import uuid

CLIENT_HOST = "127.0.0.1"
CLIENT_PORT = 5000

WORKER_HOST = "127.0.0.1"
WORKER_PORT = 6000

BUFFER_SIZE = 4096

workers = []
workers_lock = threading.Lock()
worker_index = 0

pending_requests = {}
pending_lock = threading.Lock()


class Worker:
    def __init__(self, name, sock, lock, buffer):
        self.name = name
        self.sock = sock
        self.lock = lock
        self.buffer = buffer


# ----------------------------------
# Utils de Red
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
# Workers Logic (Tu bloque)
# ----------------------------------
def register_worker(worker):
    global worker_index
    with workers_lock:
        workers.append(worker)
        print(f"[SERVER] Worker registrado: {worker.name}")


def choose_worker():
    global worker_index
    with workers_lock:
        if not workers:
            raise Exception("No hay workers disponibles")
        worker = workers[worker_index % len(workers)]
        worker_index += 1
        return worker


def worker_reader(worker):
    try:
        while True:
            response = recv_json(worker.sock, worker.buffer)
            if response is None:
                break
            
            request_id = response.get("request_id")
            if request_id:
                with pending_lock:
                    queue_obj = pending_requests.get(request_id)
                if queue_obj:
                    queue_obj.put(response)
    except Exception as e:
        print(f"[ERROR] Worker {worker.name}: {e}")
    finally:
        with workers_lock:
            if worker in workers:
                workers.remove(worker)
        worker.sock.close()
        print(f"[SERVER] Worker desconectado: {worker.name}")


def worker_listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((WORKER_HOST, WORKER_PORT))
    server.listen()

    print(f"[SERVER] Workers en {WORKER_HOST}:{WORKER_PORT}")

    while True:
        worker_sock, addr = server.accept()
        buffer = bytearray()

        hello = recv_json(worker_sock, buffer)
        if not hello:
            worker_sock.close()
            continue

        worker = Worker(
            name=hello.get("name", "Worker"),
            sock=worker_sock,
            lock=threading.Lock(),
            buffer=buffer
        )

        register_worker(worker)

        send_json(worker_sock, {
            "type": "registered"
        })

        threading.Thread(
            target=worker_reader,
            args=(worker,),
            daemon=True
        ).start()


# ----------------------------------
# Clientes (Tu bloque)
# ----------------------------------
def dispatch_request(payload):
    worker = choose_worker()
    response_queue = queue.Queue(maxsize=1)
    request_id = str(uuid.uuid4())
    payload["request_id"] = request_id

    with pending_lock:
        pending_requests[request_id] = response_queue

    send_json(worker.sock, payload, worker.lock)

    response = response_queue.get(timeout=30)

    with pending_lock:
        pending_requests.pop(request_id, None)

    return response


def handle_client(client_sock):
    buffer = bytearray()

    try:
        request = recv_json(client_sock, buffer)

        if request is None:
            return

        response = dispatch_request(request)

        send_json(client_sock, response)

    except Exception as e:
        send_json(client_sock, {
            "ok": False,
            "message": str(e)
        })

    finally:
        client_sock.close()


def client_listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((CLIENT_HOST, CLIENT_PORT))
    server.listen()

    print(f"[SERVER] Clientes en {CLIENT_HOST}:{CLIENT_PORT}")

    while True:
        client_sock, addr = server.accept()
        print(f"[SERVER] Cliente conectado: {addr}")

        threading.Thread(
            target=handle_client,
            args=(client_sock,),
            daemon=True
        ).start()


# ----------------------------------
# Main (Tu bloque)
# ----------------------------------
if __name__ == "__main__":
    threading.Thread(target=worker_listener, daemon=True).start()
    client_listener()