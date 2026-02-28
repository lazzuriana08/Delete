import zmq


context = zmq.Context()

client_socket = context.socket(zmq.ROUTER)

client_socket.bind("tcp://*:5555")

server_socket = context.socket(zmq.DEALER)

server_socket.bind("tcp://*:5556")


poller = zmq.Poller()
poller.register(client_socket, zmq.POLLIN)
poller.register(server_socket, zmq.POLLIN)

print("Broker iniciado, aguardando mensagens...", flush=True)

while True:
    socks = dict(poller.poll())

    if socks.get(client_socket) == zmq.POLLIN:

        message = client_socket.recv_multipart()
        server_socket.send_multipart(message)
        print("encaminhando requisição do cliente", flush=True)

    if socks.get(server_socket) == zmq.POLLIN:

        message = server_socket.recv_multipart()
        client_socket.send_multipart(message)
        print("encaminhando resposta do servidor", flush=True)
