import zmq
import json

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://broker:5555")

print("Cliente iniciado. Conectado ao broker.")

MENU = """
Escolha uma opção:
1 - adicionar tarefa
2 - listar tarefas
3 - remover tarefa
4 - sair
"""

while True:
    try:
        opt = input(MENU).strip()
    except EOFError:
        break

    if opt == "1":
        title = input("Título: ").strip()
        desc = input("Descrição: ").strip()
        req = {"action": "add", "title": title, "description": desc}
        socket.send_string(json.dumps(req))
        resp = socket.recv_string()
        result = json.loads(resp)
        if result.get("status") == "ok":
            print(f"Tarefa criada com id {result.get('id')}")
        else:
            print("Erro ao criar tarefa:", result.get("message"))
    elif opt == "2":
        req = {"action": "list"}
        socket.send_string(json.dumps(req))
        resp = socket.recv_string()
        result = json.loads(resp)
        if result.get("status") == "ok":
            tasks = result.get("tasks", [])
            if not tasks:
                print("Nenhuma tarefa cadastrada")
            else:
                for t in tasks:
                    print(f"{t['id']}: {t['title']} - {t['description']}")
        else:
            print("Erro ao listar:", result.get("message"))
    elif opt == "3":
        tid = input("ID da tarefa a remover: ").strip()
        req = {"action": "remove", "id": tid}
        socket.send_string(json.dumps(req))
        resp = socket.recv_string()
        result = json.loads(resp)
        if result.get("status") == "ok":
            print("Tarefa removida")
        else:
            print("Erro:", result.get("message"))
    elif opt == "4":
        print("Encerrando cliente")
        break
    else:
        print("Opção inválida")

print("Fim")
