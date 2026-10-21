# Sistema de Adoção de Animais com gRPC na Google Cloud

Sistema distribuído de adoção de animais construído com **gRPC** e **Protocol Buffers**, sendo hospedado no **GPC**.

## 1. Objetivo

O projeto representa um sistema simplificado de adoção de animais. Uma pessoa informa o próprio nome e o identificador do animal que deseja adotar. O pedido é recebido pelo Microsserviço de Adoção, que consulta o Microsserviço de Animais por gRPC para verificar a existência e a disponibilidade do animal.

O foco do trabalho é demonstrar:

- comunicação entre dois microsserviços;
- chamadas RPC síncronas;
- mensagens estruturadas definidas em arquivo `.proto`;
- serialização com Protocol Buffers;
- execução em infraestrutura da Google Cloud;
- configuração de conectividade e firewall da VPC;
- retorno correto das requisições ao cliente.

## 2. Tema e regra de negócio

O tema escolhido é **adoção de animais**.

A regra principal é:

1. o cliente solicita a adoção informando o nome do adotante e o ID do animal;
2. o Microsserviço de Adoção recebe o pedido;
3. o Microsserviço de Adoção consulta o Microsserviço de Animais;
4. o Microsserviço de Animais procura o animal e verifica a disponibilidade;
5. se o animal estiver disponível, a adoção é registrada;
6. se o animal já estiver indisponível, a solicitação é recusada;
7. a resposta retorna ao cliente.

Os dados são mantidos em memória durante a execução. Banco de dados não foi utilizado porque não é necessário para o objetivo desta demonstração. Ao reiniciar o Microsserviço de Animais, o estado inicial dos animais é restaurado.

## 3. Componentes

### 3.1 Cliente gRPC

Responsável por:

- solicitar o nome do adotante;
- solicitar o ID do animal;
- criar a mensagem definida pelo Protocol Buffers;
- enviar a requisição ao Microsserviço de Adoção;
- apresentar a resposta ao usuário.

**Microsserviço A (Cliente/Interface):** Responsável por coletar os dados, empacotar a mensagem via Protocol Buffers e disparar a requisição gRPC pela rede VPC até o servidor.

### 3.2 Microsserviço de Adoção

Responsável por:

- receber as solicitações do cliente;
- atuar como servidor gRPC na porta `9091`;
- atuar como cliente gRPC do Microsserviço de Animais;
- consultar o animal solicitado;
- solicitar o registro da adoção;
- devolver o resultado ao cliente.

### 3.3 Microsserviço de Animais

Responsável por:

- atuar como servidor gRPC na porta `9090`;
- manter os animais disponíveis em memória;
- localizar um animal pelo ID;
- informar o nome e a disponibilidade;
- registrar a adoção;
- tornar o animal indisponível depois de uma adoção bem-sucedida.

## 4. Arquitetura implantada

O sistema distribui a carga em duas VMs, a **vm-adocao** (onde roda o Cliente) e a **vm-adotai** (onde rodam os serviços de backend).

```text
VM vm-adocao
└── Cliente gRPC
        |
        | Requisição pela rede VPC
        | TCP 9091
        v
VM vm-adotai
├── Microsserviço de Adoção
│   ├── Servidor gRPC na porta 9091
│   └── Cliente gRPC do serviço de Animais
│           |
│           | gRPC interno
│           | TCP 9090
│           v
└── Microsserviço de Animais
    └── Servidor gRPC na porta 9090
```

A comunicação externa cruza a rede VPC do GCP na porta 9091. Internamente, o backend separa o serviço de Adoção e de Animais isolando portas (9090 e 9091).

## 5. Fluxo da comunicação

```text
Cliente
  -> Microsserviço de Adoção
  -> Microsserviço de Animais
  -> Microsserviço de Adoção
  -> Cliente
```

Exemplo de resposta de negócio:

```text
Animal não está disponível.
```

Essa mensagem representa uma resposta válida do sistema, e não uma falha de comunicação.

## 6. Tecnologias

- Python 3;
- gRPC;
- Protocol Buffers;
- Google Compute Engine;
- Google Cloud VPC;
- Linux Debian nas VMs;
- Git e GitHub.

## 7. Estrutura do projeto

```text
SD2026/
├── README.md
└── adocao-grpc/
    ├── adocao/
    │   ├── cliente.py
    │   └── servidor.py
    ├── animais/
    │   └── servidor.py
    ├── proto/
    │   └── adocao.proto
    ├── adocao_pb2.py
    ├── adocao_pb2_grpc.py
    └── requirements.txt
```

Os arquivos `adocao_pb2.py` e `adocao_pb2_grpc.py` são gerados automaticamente a partir do contrato `proto/adocao.proto`.

## 8. Pré-requisitos

### Windows

- Python 3 instalado;
- Git instalado;
- acesso ao PowerShell ou Prompt de Comando.

### Linux nas VMs

- Python 3;
- `python3-venv`;
- `python3-pip`;
- Git.

Instalação no Debian ou Ubuntu:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git netcat-openbsd
```

## 9. Clonagem do repositório

```bash
git clone https://github.com/Rodrigo-Yuji/SD2026.git
cd SD2026/adocao-grpc
```

## 10. Ambiente virtual e dependências

### Linux

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install grpcio grpcio-tools protobuf
```

Se o arquivo `requirements.txt` estiver disponível:

```bash
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install grpcio grpcio-tools protobuf
```

## 11. Compilação do contrato Protocol Buffers

Sempre que o arquivo `proto/adocao.proto` for alterado, execute o comando abaixo dentro da pasta `adocao-grpc`:

### Linux

```bash
python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/adocao.proto
```

### Windows

```powershell
python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/adocao.proto
```

Confirme que foram gerados:

```text
adocao_pb2.py
adocao_pb2_grpc.py
```

Não edite esses dois arquivos manualmente.

## 12. Execução local

Para testar tudo em uma única máquina, abra três terminais dentro da pasta `adocao-grpc`.

### Terminal 1: Microsserviço de Animais

```bash
python -m animais.servidor
```

Resultado esperado:

```text
Microsserviço de Animais ouvindo na porta 9090
```

### Terminal 2: Microsserviço de Adoção

```bash
python -m adocao.servidor
```

Resultado esperado:

```text
Microsserviço de Adoção ouvindo na porta 9091
```

### Terminal 3: cliente

```bash
python -m adocao.cliente
```

## 13. Execução validada na Google Cloud

### 13.1 VM servidora: `vm-adotai`

Na VM servidora, entre na pasta e atualize o projeto:

```bash
cd ~/Adotai/adocao-grpc
git pull
```

Inicie o Microsserviço de Animais em um terminal:

```bash
PYTHONPATH=. python3 -u animais/servidor.py
```

Resultado esperado:

```text
Microsserviço de Animais ouvindo na porta 9090
```

Abra outro terminal SSH na mesma VM e inicie o Microsserviço de Adoção:

```bash
cd ~/Adotai/adocao-grpc
PYTHONPATH=. python3 -u adocao/servidor.py
```

Resultado esperado:

```text
Microsserviço de Adoção ouvindo na porta 9091
```

Também é possível executar o serviço de Animais em segundo plano:

```bash
PYTHONPATH=. python3 -u animais/servidor.py &
```

Para a apresentação, recomenda-se um terminal separado para cada microsserviço, pois isso facilita a visualização dos logs.

### 13.2 VM cliente: `vm-adocao`

Na VM cliente:

```bash
cd ~/Adotai/adocao-grpc
git pull
PYTHONPATH=. python3 adocao/cliente.py
```

Informe o nome e o ID solicitado quando o programa pedir.

> A configuração do cliente deve apontar para o endereço interno da VM `vm-adotai` na porta `9091`.

## 14. Portas utilizadas

- `9090/TCP`: Microsserviço de Animais;
- `9091/TCP`: Microsserviço de Adoção;
- `22/TCP`: administração das VMs por SSH.

Na arquitetura validada, a porta `9091` é usada pela VM cliente para acessar o Microsserviço de Adoção na VM servidora.

A porta `9090` é usada internamente na VM servidora para a comunicação gRPC entre os dois microsserviços. A porta `9090` não precisa ser exposta para a internet.

## 15. Regra de firewall da VPC

A regra necessária para a comunicação entre as VMs deve permitir:

```text
Origem: VM vm-adocao
Destino: VM vm-adotai
Protocolo: TCP
Porta: 9091
Ação: permitir
Direção: entrada
```

Recomenda-se restringir a origem ao IP interno da VM cliente com máscara `/32` ou utilizar tags de rede específicas.

Exemplo conceitual:

```text
Nome: allow-grpc-adocao-9091
Rede: mesma VPC das duas VMs
Direção: entrada
Ação: permitir
Origem: IP_INTERNO_DA_VM_CLIENTE/32
Alvo: VM servidora ou tag de rede da VM servidora
Protocolo e porta: tcp:9091
```

Evite liberar a porta para `0.0.0.0/0` sem necessidade.

## 16. Teste de conectividade

Na VM cliente, teste a porta do Microsserviço de Adoção:

```bash
nc -zv -w 5 IP_INTERNO_DA_VM_ADOTAI 9091
```

Resultado esperado:

```text
Connection to IP_INTERNO_DA_VM_ADOTAI 9091 port [tcp/*] succeeded!
```

Esse teste comprova a conectividade TCP. A execução do cliente comprova o funcionamento da chamada gRPC.

## 17. Testes funcionais

### 17.1 Adoção bem-sucedida

1. inicie os dois microsserviços;
2. execute o cliente;
3. informe um animal disponível;
4. confirme a resposta de sucesso.

Exemplo:

```text
Adoção de Thor realizada com sucesso!
```

### 17.2 Animal indisponível

Sem reiniciar o Microsserviço de Animais, execute novamente o cliente e solicite o mesmo animal.

Resultado esperado:

```text
Animal não está disponível.
```

Esse teste demonstra que o estado foi atualizado e que a resposta não é fixa.

### 17.3 Animal inexistente

Informe um ID que não pertença à lista de animais.

Resultado esperado:

```text
Animal não encontrado.
```

### 17.4 Falha de comunicação

Interrompa temporariamente o Microsserviço de Animais e envie uma nova solicitação. O Microsserviço de Adoção deve retornar uma falha de comunicação compreensível, sem permanecer bloqueado indefinidamente.

## 18. Testes de Execução

No teste realizado:

```text
Adotante: Stella lopes
Animal solicitado: 3
Animal encontrado: Bob
Situação: indisponível
Resposta ao cliente: Animal não está disponível.
```

O teste comprova que:

- o cliente executado na VM `vm-adocao` alcançou a VM `vm-adotai`;
- o Microsserviço de Adoção recebeu os mesmos dados enviados pelo cliente;
- o Microsserviço de Adoção consultou o Microsserviço de Animais;
- o Microsserviço de Animais localizou Bob;
- a regra de disponibilidade foi aplicada;
- a resposta retornou corretamente ao cliente.

## 19. Limitações conhecidas

- os dados dos animais são mantidos em memória;
- o estado é reiniciado quando o Microsserviço de Animais é reiniciado;
- o projeto não utiliza banco de dados;
- não há interface gráfica;
- a finalidade é demonstrar comunicação gRPC, e não implementar uma plataforma completa de adoção.

## 20. Demonstração recomendada

Durante a apresentação:

1. mostre as duas VMs em execução;
2. mostre a regra de firewall TCP `9091`;
3. mostre o Microsserviço de Animais ouvindo na porta `9090`;
4. mostre o Microsserviço de Adoção ouvindo na porta `9091`;
5. execute uma adoção bem-sucedida;
6. repita a solicitação e mostre o animal indisponível;
7. explique que as mensagens são definidas no `.proto` e serializadas pelo Protocol Buffers.

Não é necessário mostrar o código durante a apresentação.

## 21. Segurança

- não publique senhas, tokens, chaves SSH ou credenciais da Google Cloud;
- restrinja as regras de firewall às portas e origens necessárias;
- não envie arquivos `.env` com segredos;
- desligue as VMs depois da apresentação para evitar custos desnecessários.

## 22. Autores

```text
Integrante 1: Stella Lopes Moreira
Integrante 2: Rodrigo Yuji Okida Tamoto
Integrante 3: Humberto Henry Gontijo Braga
```

## 23. Repositório

https://github.com/Rodrigo-Yuji/SD2026
