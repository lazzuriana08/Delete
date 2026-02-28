import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REP)

socket.connect("tcp://broker:5556")

print("Servidor de tarefas rodando e conectando ao broker...", flush=True)


tasks = {}
counter = 0

while True:
    msg = socket.recv_string()
    print(f"[servidor] recebido: {msg}", flush=True)
    try:
        req = json.loads(msg)
    except json.JSONDecodeError:
        reply = {"status": "error", "message": "json inválido"}
        socket.send_string(json.dumps(reply))
        continue

    action = req.get("action")
    if action == "add":
        titulo = req.get("title")
        descricao = req.get("description")
        counter += 1
        task_id = str(counter)
        tasks[task_id] = {"id": task_id, "title": titulo, "description": descricao}
        reply = {"status": "ok", "id": task_id}
    elif action == "list":
        reply = {"status": "ok", "tasks": list(tasks.values())}
    elif action == "remove":
        tid = req.get("id")
        if tid in tasks:
            del tasks[tid]
            reply = {"status": "ok"}
        else:
            reply = {"status": "error", "message": "tarefa não encontrada"}
    else:
        reply = {"status": "error", "message": "ação desconhecida"}

    print(f"[servidor] respondendo: {reply}", flush=True)
    socket.send_string(json.dumps(reply))
