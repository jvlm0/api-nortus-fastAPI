# API Nortus

API REST em **FastAPI** para o aplicativo Nortus, que dá acesso móvel ao sistema de gestão de oficinas. Ela autentica os usuários do app e, para cada um, lê e grava no **banco Firebird da empresa** (clientes, veículos, ordens de serviço, produtos, financeiro e comissões).

## Arquitetura

```
App / painel admin
        │  HTTPS + JWT
        ▼
┌──────────────┐     ┌──────────────────────────┐
│ Nginx (:80)  │────▶│ FastAPI (uvicorn :8000)  │
│ /static/     │     └────────────┬─────────────┘
│   uploads/   │                  │
└──────────────┘     ┌────────────┴──────────────────────┐
                     ▼                                   ▼
          Banco do app (APPUSERS.FDB)         Banco de cada empresa
          tabela USUARIO: login, hash,        (DSN em USUARIO.CAMINHO_BANCO)
          admin e caminho do banco            clientes, OS, produtos...
```

- **Banco do app**: um Firebird próprio (o container `firebird` do `docker-compose`). Guarda só os usuários do aplicativo.
- **Banco da empresa**: cada usuário aponta, pelo campo `CAMINHO_BANCO`, para o DSN Firebird do sistema da empresa dele (por exemplo `192.168.0.10:C:/Sistema/Bancos/empresa.GDB`). A cada requisição, a API descobre esse DSN a partir do `sub` do token e usa um pool de conexões separado por DSN ([app/database.py](app/database.py)).
- **Consulta de placa**: se um veículo não existe no banco da empresa, a API consulta um serviço externo de placas e cadastra o veículo automaticamente ([app/utils/consulta_placa.py](app/utils/consulta_placa.py)).
- **Imagens das ordens**: ficam salvas em `uploads/<cod_ordem>/` e são servidas em `/static/uploads/...`. Em produção quem serve é o Nginx, diretamente do volume `uploads_data`.

## Estrutura

```
app/
├── main.py           # cria o app, CORS, routers e arquivos estáticos
├── database.py       # pool de conexões Firebird (app + bancos das empresas)
├── routes/           # endpoints (um arquivo por recurso)
├── repositories/     # SQL de cada recurso
├── schemas/          # modelos Pydantic de entrada/saída
├── db_utils/         # consultas auxiliares (produto, serviço, vendedor)
└── utils/            # JWT, hash de senha, imagens, cálculo de OS, placa
static/admin_users.html   # painel web de administração de usuários (/admin)
migrations/               # scripts SQL do banco do app
nginx/nginx.conf          # proxy reverso + arquivos de upload
```

## Configuração

Crie um arquivo `.env` na raiz. Ele já está no `.gitignore`, **nunca o commite**.

| Variável | Descrição | Exemplo |
|---|---|---|
| `DSN` | DSN do banco do app | `firebird:/firebird/data/APPUSERS.FDB` |
| `DB_USER` | usuário Firebird (usado no banco do app **e** nos bancos das empresas) | `SYSDBA` |
| `DB_PASSWORD` | senha desse usuário | — |
| `SECRET_KEY` | chave de assinatura dos JWT | gere com `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ALGORITHM` | algoritmo do JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | validade padrão do token renovado em `/auth/refresh` | `30` |
| `URL_API_PLACAS` | URL base do serviço de consulta de placas | — |
| `KEY_PLACAS` | chave desse serviço | — |

A API monta a URL da consulta como `{URL_API_PLACAS}/{placa}/{KEY_PLACAS}`.

## Banco do app

O repositório não traz o script de criação da tabela `USUARIO`. Os campos abaixo são os que o código usa (Firebird 2.5, que não tem coluna identity, por isso o generator e o trigger):

```sql
CREATE TABLE USUARIO (
  ID            INTEGER NOT NULL PRIMARY KEY,
  USERNAME      VARCHAR(50)  NOT NULL UNIQUE,
  NOME          VARCHAR(100) NOT NULL,
  SENHA_HASH    VARCHAR(255) NOT NULL,
  CAMINHO_BANCO VARCHAR(255) NOT NULL,
  IS_ADMIN      SMALLINT DEFAULT 0 NOT NULL
);

CREATE GENERATOR GEN_USUARIO_ID;

SET TERM ^ ;
CREATE TRIGGER USUARIO_BI FOR USUARIO
ACTIVE BEFORE INSERT AS
BEGIN
  IF (NEW.ID IS NULL) THEN NEW.ID = GEN_ID(GEN_USUARIO_ID, 1);
END^
SET TERM ; ^
```

Em bancos que já existiam antes do controle de admin, rode [migrations/add_is_admin_usuario.sql](migrations/add_is_admin_usuario.sql).

As senhas são guardadas com **argon2** ([app/utils/security.py](app/utils/security.py)). Para criar o primeiro administrador, insira um usuário com um hash gerado assim:

```bash
python -c "from app.utils.security import hash_password; print(hash_password('SUA_SENHA'))"
```

e depois marque `IS_ADMIN = 1`. A partir daí os outros usuários podem ser criados pelo painel `/admin` ou pela rota `POST /users`.

## Como rodar

### Com Docker (produção)

```bash
docker compose up -d --build
```

Isso sobe três containers: `firebird_db` (Firebird 2.5, com os dados em `./firebird_data`), `fastapi_app` (a API) e `nginx_proxy`.

> O serviço `nginx` só faz `expose: 80` na rede interna. Para acessá-lo de fora, adicione um mapeamento `ports` (por exemplo `"80:80"`) ou coloque um proxy/TLS na frente.
>
> O `docker-compose.yml` define `ISC_PASSWORD: masterkey` e publica a porta `3050`. Em produção, troque a senha (de preferência lendo do `.env`) e remova o mapeamento da porta se o banco não precisar ser acessado de fora do Docker.

### Local (desenvolvimento)

Pré-requisitos: Python 3.12+ e a biblioteca cliente do Firebird (`fbclient.dll` no Windows, `libfbclient2` no Linux).

```bash
python -m venv venv
venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

A documentação interativa fica em `http://localhost:8000/docs`.

## Autenticação

1. `POST /auth/login` com `{"username": "...", "senha": "..."}`. A resposta traz `access_token` (válido por 30 min), `refresh_token` (7 dias), `nome` e `is_admin`.
2. Nas demais rotas, envie o cabeçalho `Authorization: Bearer <access_token>`.
3. Quando o access token expirar, chame `POST /auth/refresh` enviando o **refresh token** como Bearer para receber um novo access token.

As rotas de `/users` exigem `is_admin = true` no token. As demais exigem apenas um token válido.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth/login` | login, retorna os tokens |
| `POST` | `/auth/refresh` | renova o access token |
| `GET` | `/clientes?q=&page=&page_size=` | busca clientes por nome ou telefone |
| `POST` | `/clientes` | cadastra um cliente |
| `PUT` | `/clientes/{cod_cliente}` | atualiza um cliente |
| `GET` | `/veiculos/{placa}` | busca o veículo; se não existir, consulta a API de placas e cadastra |
| `POST` | `/veiculos` | cadastra um veículo |
| `PATCH` | `/veiculos` | atualiza um veículo |
| `GET` | `/ordens?page=&page_size=` | lista ordens de serviço (paginado) |
| `GET` | `/ordens/{cod_ordem}` | detalha uma ordem |
| `POST` | `/ordens` | cria uma ordem (multipart: `dados` em JSON + `imagens`) |
| `PATCH` | `/ordens` | atualiza uma ordem (multipart: `dados` em JSON + `imagens`) |
| `DELETE` | `/ordens/{cod_ordem}?trust=n\|y` | exclui; com itens e `trust=n` só retorna a quantidade de itens, com `trust=y` exclui mesmo assim |
| `GET` | `/ordens/fechadas?data_inicio=&data_fim=` | ordens fechadas no período |
| `GET` | `/ordens/faturadas?data_inicio=&data_fim=` | ordens faturadas no período |
| `GET` | `/produtos?q=&page=&page_size=` | busca produtos por nome |
| `GET` | `/vendedores` | lista vendedores |
| `GET` | `/equipes` | lista equipes |
| `GET` | `/contas-a-pagar?data_inicio=&data_fim=` | contas a pagar no período |
| `GET` | `/contas-a-receber?data_inicio=&data_fim=` | contas a receber no período |
| `GET` | `/comissoes?data_inicio=&data_fim=` | comissões no período |
| `POST` | `/uploads/temp` | envia uma imagem temporária (JPEG/PNG/WEBP/GIF, até 10 MB) |
| `GET/POST` | `/users` | lista / cria usuários do app *(admin)* |
| `GET/PUT/DELETE` | `/users/{user_id}` | consulta / altera / remove um usuário *(admin)* |
| `GET` | `/admin` | redireciona para o painel de administração |

Datas usam o formato `YYYY-MM-DD`.

### Exemplo: criar uma ordem de serviço

```bash
curl -X POST http://localhost:8000/ordens \
  -H "Authorization: Bearer $TOKEN" \
  -F 'dados={
        "cod_cliente": 123,
        "cod_veiculo": 456,
        "observacao": "Barulho na suspensão",
        "problemas": [{"descricao": "Barulho dianteiro"}],
        "servicos": [{"descricao": "Troca de bieleta", "quantidade": 1,
                      "valorUnitario": 150, "desconto": 0,
                      "cod_equipe": 1, "cods_vendedores": [2]}],
        "produtos": [{"cod_subproduto": 789, "quantidade": 2,
                      "valorUnitario": 80, "desconto": 0,
                      "cods_vendedores": [2]}]
      }' \
  -F "imagens=@foto1.jpg" \
  -F "imagens=@foto2.jpg"
```

## Tecnologias

FastAPI · Uvicorn · Pydantic 2 · firebird-driver · python-jose (JWT) · passlib + argon2 · httpx · Docker · Nginx
