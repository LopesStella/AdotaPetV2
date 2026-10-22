# AdotaPet

Sistema de adoção de animais desenvolvido como projeto acadêmico do curso de Sistemas de Informação da Universidade Federal de Goiás (UFG).

## 1. Sobre o projeto

O AdotaPet é um sistema que utiliza uma arquitetura baseada em microsserviços para organizar as funcionalidades relacionadas a animais e adoções.

## 2. Arquitetura

O projeto possui os seguintes componentes:

- **Gateway (FastAPI):** recebe as requisições HTTP do frontend e encaminha as chamadas aos microsserviços.
- **Microsserviço de Animais:** responsável pelas operações relacionadas aos animais.
- **Microsserviço de Adoções:** responsável pelas operações relacionadas às adoções.
- **gRPC:** tecnologia utilizada na comunicação entre o Gateway e os microsserviços.
- **Protocol Buffers (Protobuf):** define as mensagens e os contratos de comunicação gRPC.
- **PostgreSQL (Supabase):** banco de dados da aplicação.

### Fluxo da aplicação

```text
Frontend → Gateway → Microsserviço → PostgreSQL (Supabase)
```

O Gateway encaminha as requisições, os microsserviços executam as operações e as respostas retornam ao frontend.

## 3. Infraestrutura

A aplicação está configurada em duas máquinas virtuais no Google Cloud:

| Máquina virtual | Responsabilidade |
|---|---|
| `vm-adotai` | Gateway FastAPI |
| `vm-adocao` | Microsserviços de Animais e Adoções |

O banco de dados PostgreSQL é hospedado separadamente no Supabase.

## 4. Tecnologias utilizadas

- Python
- FastAPI
- Uvicorn
- gRPC
- Protocol Buffers (Protobuf)
- PostgreSQL
- Supabase
- Google Cloud Compute Engine

## 5. Instalação

Clone o repositório:

```bash
git clone https://github.com/LopesStella/AdotaiV2.git
cd AdotaiV2/adocao-animais
```

Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Configure as variáveis de ambiente necessárias no arquivo `.env`, de acordo com o código do projeto.

**Importante:** não compartilhe o arquivo `.env` nem publique senhas, tokens ou chaves secretas no Git.

## 6. Como executar

Os serviços devem ser iniciados separadamente e permanecer em execução.

### Gateway — VM `vm-adotai`

```bash
cd ~/AdotaiV2/adocao-animais
source .venv/bin/activate
uvicorn gateway.main:app --host 0.0.0.0 --port 8000
```

### Microsserviço de Animais — VM `vm-adocao`

```bash
cd ~/AdotaiV2/adocao-animais
source .venv/bin/activate
python -m microsservicos.animais.servidor
```

### Microsserviço de Adoções — VM `vm-adocao`

Em outro terminal da mesma VM:

```bash
cd ~/AdotaiV2/adocao-animais
source .venv/bin/activate
python -m microsservicos.adocao.servidor
```

As portas gRPC devem corresponder às configurações utilizadas no código.

## 7. Testando a API

Com o Gateway em execução, acesse a documentação interativa do FastAPI:

http://136.80.227.249:8000/docs

Nessa página, é possível selecionar uma rota, clicar em **Try it out**, preencher os dados e executar a requisição. A resposta apresenta o código HTTP e o conteúdo retornado.

O acesso depende de a VM estar ligada, o serviço estar funcionando e a porta 8000 estar liberada no firewall.

## 8. Tratamento de erros

Alguns códigos HTTP que podem ser utilizados pela aplicação:

- **200 — OK:** requisição concluída com sucesso.
- **201 — Created:** recurso criado com sucesso.
- **400 — Bad Request:** requisição inválida.
- **401 — Unauthorized:** autenticação necessária ou inválida.
- **503 — Service Unavailable:** serviço necessário indisponível.

Os códigos efetivamente retornados dependem da implementação de cada rota.

## 9. Segurança

- Senhas de usuários devem ser armazenadas por meio de um algoritmo apropriado de hash de senhas, nunca em texto puro.
- Credenciais do banco e chaves secretas devem ser mantidas em variáveis de ambiente.
- As portas de rede devem ser liberadas somente quando necessário.
- Para uso em produção, é necessário configurar HTTPS e revisar os mecanismos de autenticação e autorização.

## 10. Contexto acadêmico

Projeto desenvolvido no curso de Sistemas de Informação da Universidade Federal de Goiás (UFG), com o objetivo de aplicar conceitos de APIs, comunicação entre microsserviços, banco de dados e implantação em nuvem.
