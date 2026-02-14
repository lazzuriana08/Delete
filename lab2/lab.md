# Lab 02 - RPC com gRPC

Para continuar o que fizemos no primeiro laboratório, desta vez vamos implementar o gerenciador de tarefas usando gRPC.

Aproveitando o conteúdo de Docker das aulas anteriores, desta vez os códigos que vamos implementar serão executados de dentro dos containers.

Como teremos um cliente e um servidor executando códigos diferentes, teremos dois Dockerfiles e um docker-compose.yaml, que executará os containers.

## Classes usando Protobuf

O primeiro passo é criar o arquivo `.proto` que possui as definições das funções que vamos implementar no servidor e que o cliente pode executar. Neste caso, o nosso serviço deve possuir as funções de criar, ler uma tarefa, listar todas as tarefas, atualizar e deletar, além de uma função para testar a conexão com o banco.

O arquivo `.proto` que cria esta classe (stub) encontra-se a seguir. Ele apresenta a definição de todas as funções que serão implementadas e os objetos que serão enviados nas mensagens trocadas entre cliente e servidor.
```proto
syntax = "proto3";

package task_manager;

service TaskManager {
  rpc Create (CreateRequest) returns (Task);
  rpc Get (GetRequest) returns (Task);
  rpc List (ListRequest) returns (ListResponse);
  rpc Update (UpdateRequest) returns (Task);
  rpc Delete (DeleteRequest) returns (Empty);
  rpc ConnectionTest (ConnRequest) returns (ConnReply);
}

message ConnRequest {
    string message = 1;
}

message ConnReply {
    string message = 1;
}

message Task {
  string id = 1;
  string title = 2;
  string description = 3;
  string status = 4;
}

message CreateRequest {
  string title = 1;
  string description = 2;
}

message GetRequest {
  string id = 1;
}

message ListRequest {
}

message ListResponse {
  repeated Task tasks = 1;
}

message UpdateRequest {
  string id = 1;
  string title = 2;
  string description = 3;
  string status = 4;
}

message DeleteRequest {
  string id = 1;
}

message Empty{}
```

Os arquivos de stub que serão usados pelo cliente e o servicer usado pelo servidor, serão gerados dentro da imagem, quando fazemos a construção do container. Para usar estes arquivos, vamos ter um código para o servidor e outro para o cliente.

## Implementação do servidor

O servidor que usa o arquivo criado a partir da compilação do `Protobuf` deve implementar todas as funções descritas no arquivo `.proto` e a inicialização do servidor.

A da classe `TaskManagerService` herda de `task_managder_pb2_grpc` para poder implementar as funções usando os objetos de requisição certos e implementas os seguintes métodos abaixo:
```py
def ConnectionTest(self, request, context):
    print(f"Mensagem do cliente: {request.message}",flush=True)
    return task_manager_pb2.ConnReply(message="ACK")

def Create(self, request, context):
    self.counter += 1
    id = str(self.counter)
    task = task_manager_pb2.Task(id=id, title=request.title, description=request.description, status="não completo")
    self.tasks[id] = task
    return task

def Get(self, request, context):
    id = request.id
    if id in self.tasks:
        return self.tasks[id]
    else:
        context.abort(grpc.StatusCode.NOT_FOUND, "ERRO: tarefa não encontrada")

def List(self, request, context):
    return task_manager_pb2.ListResponse(tasks=self.tasks.values())

def Update(self, request, context):
    id = request.id
    if id in self.tasks:
        task = self.tasks[id]
        task.title = request.title
        task.description = request.description
        task.status = request.status
        return task
    else:
        context.abort(grpc.StatusCode.NOT_FOUND, "ERRO: tarefa não encontrada")

def Delete(self, request, context):
    id = request.id
    if id in self.tasks:
        del self.tasks[id]
        return task_manager_pb2.Empty()
    else:
        context.abort(grpc.StatusCode.NOT_FOUND, "ERRO: tarefa não encontrada")
```

O primeiro método faz apenas o teste de conexão entre cliente e servidor, sem realizar nenhuma operação relacionada as tarefas. O segundo método cria uma nota tarefa a partir dos dados recebidos no `request`, adiciona esta tarefa no dicionário de tarefas usando o `id` dela como chame e incrementa o contador de tarefas da classe.

A função `Get` recebe um `request` com o `id` da tarefa e retorna toda a tarefa, caso ela exista. Senão retorna um erro ao cliente. A função seguinte retorna toda a lista de tarefas que foi criada a partir dos valores do dicionário de tarefas.

O `Update` atualiza todos os dados da tarefa usando o `id` como critério de busca para a tarefa e o `Delete` deleta a tarefa a partir do `id` recebido. Caso a tarefa escolhida não esteja no dicionário, os dois métodos retornam erro ao cliente.

O final do código instancía um objeto do gerenciador de tarefas que aceita conexão de qualquer endereço na porta 50051.

```py
endereco = "[::]:50051"
servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
task_manager_pb2_grpc.add_TaskManagerServicer_to_server(TaskManagerService(), servidor)

servidor.add_insecure_port(endereco)
servidor.start()
print(f"Servidor escutando em {endereco}", flush=True)
servidor.wait_for_termination()
```

O código completo desta classe fica:
```py
import grpc
import task_manager_pb2
import task_manager_pb2_grpc
from concurrent import futures

class TaskManagerService(task_manager_pb2_grpc.TaskManagerServicer):
    def __init__(self):
        self.tasks = {}
        self.counter = 0

    def ConnectionTest(self, request, context):
        print(f"Mensagem do cliente: {request.message}",flush=True)
        return task_manager_pb2.ConnReply(message="ACK")

    def Create(self, request, context):
        self.counter += 1
        id = str(self.counter)
        task = task_manager_pb2.Task(id=id, title=request.title, description=request.description, status="não completo")
        self.tasks[id] = task
        return task

    def Get(self, request, context):
        id = request.id
        if id in self.tasks:
            return self.tasks[id]
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "ERRO: tarefa não encontrada")

    def List(self, request, context):
        return task_manager_pb2.ListResponse(tasks=self.tasks.values())

    def Update(self, request, context):
        id = request.id
        if id in self.tasks:
            task = self.tasks[id]
            task.title = request.title
            task.description = request.description
            task.status = request.status
            return task
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "ERRO: tarefa não encontrada")

    def Delete(self, request, context):
        id = request.id
        if id in self.tasks:
            del self.tasks[id]
            return task_manager_pb2.Empty()
        else:
            context.abort(grpc.StatusCode.NOT_FOUND, "ERRO: tarefa não encontrada")

endereco = "[::]:50051"
servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
task_manager_pb2_grpc.add_TaskManagerServicer_to_server(TaskManagerService(), servidor)

servidor.add_insecure_port(endereco)
servidor.start()
print(f"Servidor escutando em {endereco}", flush=True)
servidor.wait_for_termination()
```

Para testar o servidor, precisamos primeiro implementar o cliente que usa o stub deste servicer.

## Implementação do cliente

O código do cliente usa o stub que possui a descrição dos métodos que podem ser executados e será gerado pelo protobuf na classe `TaskManagerStub` implementada em `task_manager_pb2_grpc`

Este cliente implementa funções que recebem um stub e informações sobre o tipo de função que será executada no servidor e faz o tratamento e envio da mensagem no formato correto esperado pelo servicer, como mostram as funções a seguir:

```py
def connection_test(stub):
    print("Testando conexão com servidor")
    request = task_manager_pb2.ConnRequest(message="SYN")
    response = stub.ConnectionTest(request)
    print(f"Resposta: {response}", flush=True)

def create_task(stub, title, description):
    request = task_manager_pb2.CreateRequest(title=title, description=description)
    response = stub.Create(request)
    print(f"Tarefa criada: {response}", flush=True)
    return response.id

def get_task(stub, id):
    request = task_manager_pb2.GetRequest(id=str(id))
    try:
        response = stub.Get(request)
        print(f"Tarefa: {response}", flush=True)
    except grpc.RpcError as e:
        print(e.details(), flush=True)

def list_tasks(stub):
    request = task_manager_pb2.ListRequest()
    response = stub.List(request)
    print("Lista de tarefas:", flush=True)
    for task in response.tasks:
        print(task, flush=True)

def update_task(stub, id, title, description, status):
    request = task_manager_pb2.UpdateRequest(id=str(id), title=title, description=description, status=status)
    try:
        response = stub.Update(request)
        print(f"Tarefa atualizada: {response}", flush=True)
    except grpc.RpcError as e:
        print(e.details(), flush=True)

def delete_task(stub, id):
    request = task_manager_pb2.DeleteRequest(id=str(id))
    try:
        stub.Delete(request)
        print("Tarefa apagada", flush=True)
    except grpc.RpcError as e:
        print(e.details(), flush=True)
```

A primeira função é usada para fazer o teste de conexão e as demais para usar os métodos de CRUD implementados no servidor. Apesar de realizarem tarefas diferentes, estas funções possuem o mesmo formato:
1. recebem os dados necessários para realizar a chamada do método (e.g., id, título, descrição e estado para criar uma tarefa, mas somente o id para buscar a tarefa)
2. constroem um objeto do tipo que o método do cliente espera receber (nas linhas `request = ...` em todos os métodosx)
3. faz a chamada do método no servidor
4. exibe o resultado retornado pelo servidor
5. as chamadas são executadas dentro de um bloco ```try...except...``` para tratar os erros fornecidos pela execução no servidor.

O final do código segue a mesma lógica do servidor: inancia um objeto do cliente e faz a conexão com o servidor, mas desta vez também faz as chamadas das funções usando RPC:

```py
print("Cliente conectando com o servidor",flush=True)
porta = "50051"
endereco = "servidor"
with grpc.insecure_channel(f"{endereco}:{porta}") as channel:
    stub = task_manager_pb2_grpc.TaskManagerStub(channel)
    connection_test(stub)

    create_task(stub, "teste", "teste de tarefa")
    get_task(stub, 1)
    list_tasks(stub)
    update_task(stub, 1, "atualizacao", "teste de update", "completa")
    list_tasks(stub)
    delete_task(stub, 1)
    list_tasks(stub)
```

A versão final do código fica:
```py
import grpc
import task_manager_pb2
import task_manager_pb2_grpc

def connection_test(stub):
    print("Testando conexão com servidor")
    request = task_manager_pb2.ConnRequest(message="SYN")
    response = stub.ConnectionTest(request)
    print(f"Resposta: {response}", flush=True)

def create_task(stub, title, description):
    request = task_manager_pb2.CreateRequest(title=title, description=description)
    response = stub.Create(request)
    print(f"Tarefa criada: {response}", flush=True)
    return response.id

def get_task(stub, id):
    request = task_manager_pb2.GetRequest(id=str(id))
    try:
        response = stub.Get(request)
        print(f"Tarefa: {response}", flush=True)
    except grpc.RpcError as e:
        print(e.details(), flush=True)

def list_tasks(stub):
    request = task_manager_pb2.ListRequest()
    response = stub.List(request)
    print("Lista de tarefas:", flush=True)
    for task in response.tasks:
        print(task, flush=True)

def update_task(stub, id, title, description, status):
    request = task_manager_pb2.UpdateRequest(id=str(id), title=title, description=description, status=status)
    try:
        response = stub.Update(request)
        print(f"Tarefa atualizada: {response}", flush=True)
    except grpc.RpcError as e:
        print(e.details(), flush=True)

def delete_task(stub, id):
    request = task_manager_pb2.DeleteRequest(id=str(id))
    try:
        stub.Delete(request)
        print("Tarefa apagada", flush=True)
    except grpc.RpcError as e:
        print(e.details(), flush=True)

print("Cliente conectando com o servidor",flush=True)
porta = "50051"
endereco = "servidor"
with grpc.insecure_channel(f"{endereco}:{porta}") as channel:
    stub = task_manager_pb2_grpc.TaskManagerStub(channel)
    connection_test(stub)

    create_task(stub, "teste", "teste de tarefa")
    get_task(stub, 1)
    list_tasks(stub)
    update_task(stub, 1, "atualizacao", "teste de update", "completa")
    list_tasks(stub)
    delete_task(stub, 1)
    list_tasks(stub)
```

## Dockerfiles e docker-compose

Para executarmos o código usaremos containers, pois será possível dividir o cliente e o servidor e fazer a conexão entre máquinas diferentes.

Como cada parte usa um código diferente, teremos 2 Dockerfiles, que se encontram a seguir:

```dockerfile
FROM python:3.13.7-alpine3.21

WORKDIR /app

RUN pip install grpcio grpcio-tools

COPY ./task_manager.proto .

RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. task_manager.proto

COPY ./cliente.py .

CMD ["python", "cliente.py"]
````

```dockerfile
FROM python:3.13.7-alpine3.21

WORKDIR /app

RUN pip install grpcio grpcio-tools

COPY ./task_manager.proto .

RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. task_manager.proto

COPY ./servidor.py .

CMD ["python", "servidor.py"]
```

Os dois Dockerfiles são parecidos, com diferenças apenas nas últimas linhas em que o do servidor copia e executa o código do servidor, enquanto o cliente copia e executa o código do cliente.

Para facilitar a execução do servidor e do cliente, usaremos o docker compose e o arquivo a seguir:
```yaml
services:
  servidor:
    build:
      context: .
      dockerfile: Dockerfile_servidor
    container_name: servidor
    ports:
      - 50051:50051

  cliente:
    build:
      context: .
      dockerfile: Dockerfile_cliente
    container_name: cliente
    depends_on:
      - servidor
```

Por fim, para fazer o build das imagens dos containers e executar servidor e cliente precisamos executar o `docker compose up` na linha de comando.

## Extra: FastAPI + gRPC

Para adicionar o FastAPI ao container do cliente precisamos fazer 3 alterações:
1. Adicionar a instalação do `"fastapi[standard]"` no Dockerfile_cliente
2. Alterar a entrada do cliente no `docker-compose.yaml` para permitir o acesso a porta 8000 do container
3. Alterar o código do cliente para fazer as chamadas dos métodos disponíveis pelo gRPC de dentro dos endpoints do FastAPI. Uma forma de fazer isto está no código a seguir.
```py
import json

import grpc
import task_manager_pb2
import task_manager_pb2_grpc
from google.protobuf.json_format import MessageToJson

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse

print("Cliente conectando com o servidor",flush=True)
porta = "50051"
endereco = "servidor"
channel = grpc.insecure_channel(f"{endereco}:{porta}")
stub = task_manager_pb2_grpc.TaskManagerStub(channel)

print("Inicializando FastAPI", flush=True)
app = FastAPI()

class Tarefa(BaseModel):
    titulo: str
    descricao: str
    status: str

@app.get("/")
def list_tasks():
    request = task_manager_pb2.ListRequest()
    response = MessageToJson(stub.List(request))
    return JSONResponse(content=json.loads(response))

@app.get("/test")
def connection_test():
    print("Testando conexão com servidor")
    request = task_manager_pb2.ConnRequest(message="SYN")
    response = stub.ConnectionTest(request)
    return response.message

@app.put("/adicionar/")
def create_task(tarefa: Tarefa):
    request = task_manager_pb2.CreateRequest(
        title=tarefa.titulo,
        description=tarefa.descricao,
    )
    response = stub.Create(request)
    return response.id

@app.get("/tarefa/{pos}")
def get_task(id: int):
    request = task_manager_pb2.GetRequest(id=str(id))
    try:
        response = MessageToJson(stub.Get(request))
        return JSONResponse(content=json.loads(response))
    except grpc.RpcError as e:
        print(e.details(), flush=True)


@app.put("/atualizar/")
def update_task(tarefa: Tarefa, id: int):
    request = task_manager_pb2.UpdateRequest(
        id=str(id),
        title=tarefa.titulo,
        description=tarefa.descricao,
        status=tarefa.status
    )
    try:
        response = stub.Update(request)
        print(f"Tarefa atualizada: {response}", flush=True)
    except grpc.RpcError as e:
        print(e.details(), flush=True)

@app.delete("/deletar/{pos}")
def delete_task(id: int):
    request = task_manager_pb2.DeleteRequest(id=str(id))
    try:
        stub.Delete(request)
        return "Tarefa apagada"
    except grpc.RpcError as e:
        print(e.details(), flush=True)
```

Após estas alterações, a execução do projeto pode ser feita pelo `docker compose up`.
