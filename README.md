# 🏢 Módulo de Recursos Humanos

> Documentação técnica do módulo de RH desenvolvido para o Projeto Integrador.
> Stack: **Django + Django REST Framework + Supabase (PostgreSQL)**

---

## 📋 Índice

1. [Visão Geral](#1-visão-geral)
2. [Banco de Dados](#2-banco-de-dados)
3. [Arquitetura do Projeto](#3-arquitetura-do-projeto)
4. [Sistema de Autenticação](#4-sistema-de-autenticação)
5. [Endpoints da API](#5-endpoints-da-api)
6. [Regras de Negócio](#6-regras-de-negócio)
7. [Como Rodar o Projeto](#7-como-rodar-o-projeto)
8. [Próximos Passos](#8-próximos-passos)

---

## 1. Visão Geral

O módulo de RH é responsável por gerenciar toda a estrutura de pessoas da empresa: funcionários, departamentos, cargos, ponto eletrônico e férias. Faz parte de um sistema empresarial integrado onde cada grupo da turma desenvolveu um módulo que se comunica com os demais via API REST.

### Stack Tecnológica

| Tecnologia | Uso |
|---|---|
| Python 3.x | Linguagem principal |
| Django 4.2+ | Framework web e ORM |
| Django REST Framework | Construção da API REST |
| Supabase (PostgreSQL) | Banco de dados na nuvem |
| django-filter | Filtros avançados nos endpoints |
| python-decouple | Gerenciamento de variáveis de ambiente |

### Contexto de Integração

Todos os endpoints seguem o padrão `/api/v1/<recurso>/`, que:

- **`/api/`** — indica que a rota retorna dados JSON, não páginas HTML
- **`/v1/`** — permite versionamento futuro sem quebrar integrações existentes

---

## 2. Banco de Dados

O banco está hospedado no **Supabase (PostgreSQL)**. As tabelas foram criadas diretamente no Supabase e o Django foi configurado para utilizá-las sem recriar a estrutura.

> ⚠️ **Atenção:** Como as tabelas já existiam antes do projeto Django ser criado, todas as migrations foram aplicadas com `--fake-initial` para evitar erros de "tabela já existe".

### Tabelas

| Tabela | Descrição |
|---|---|
| `departamentos` | Unidades organizacionais da empresa (ex: TI, Financeiro, RH) |
| `cargo` | Cargos disponíveis vinculados a um departamento e nível hierárquico |
| `funcionarios` | Todos os colaboradores da empresa — tabela central do módulo |
| `registros_ponto` | Registros de entrada, saída e pausa dos funcionários |
| `solicitacao_ferias` | Solicitações de férias com fluxo de aprovação |

### Ordem de Dependência (Foreign Keys)

```
departamentos → cargo → funcionarios → registros_ponto
                                     → solicitacao_ferias
```

Essa ordem deve ser respeitada ao rodar as migrations.

### Schema SQL

```sql
CREATE TABLE public.departamentos (
  id_departamento bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  nome character varying NOT NULL,
  sigla character varying NOT NULL UNIQUE,
  CONSTRAINT departamentos_pkey PRIMARY KEY (id_departamento)
);

CREATE TABLE public.cargo (
  id_cargo bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  id_departamento bigint,
  nome character varying NOT NULL,
  descricao text,
  nivel smallint,
  CONSTRAINT cargo_pkey PRIMARY KEY (id_cargo),
  CONSTRAINT cargo_id_departamento_fkey FOREIGN KEY (id_departamento)
    REFERENCES public.departamentos(id_departamento)
);

CREATE TABLE public.funcionarios (
  id_funcionario bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  nome character varying NOT NULL,
  cpf character NOT NULL UNIQUE,
  email character varying NOT NULL UNIQUE,
  telefone character varying,
  data_admissao timestamp without time zone NOT NULL,
  salario numeric NOT NULL,
  status character varying NOT NULL
    CHECK (status IN ('ativo', 'inativo', 'afastado')),
  id_cargo bigint NOT NULL,
  id_departamento bigint NOT NULL,
  CONSTRAINT funcionarios_pkey PRIMARY KEY (id_funcionario)
);

CREATE TABLE public.registros_ponto (
  id_registro bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  id_funcionario bigint,
  data_hora timestamp with time zone NOT NULL DEFAULT now(),
  tipo character varying NOT NULL
    CHECK (tipo IN ('entrada', 'saida', 'pausa')),
  observacao text,
  CONSTRAINT registros_ponto_pkey PRIMARY KEY (id_registro)
);

CREATE TABLE public.solicitacao_ferias (
  id_solicitacao bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  data_solicitacao timestamp with time zone NOT NULL DEFAULT now(),
  id_funcionario bigint,
  data_inicio date NOT NULL,
  data_fim date NOT NULL,
  status character varying NOT NULL
    CHECK (status IN ('pendente', 'aprovada', 'recusada')),
  observacao text,
  CONSTRAINT solicitacao_ferias_pkey PRIMARY KEY (id_solicitacao)
);
```

---

## 3. Arquitetura do Projeto

### Estrutura de Pastas

```
rh_module/
├── core/                        # Configurações globais do projeto
│   ├── settings.py              # INSTALLED_APPS, banco, DRF, static
│   ├── urls.py                  # Roteador principal (inclui todos os apps)
│   └── wsgi.py
│
├── autenticacao/                # Login, logout, dashboard, usuários do sistema
│   ├── models.py                # UserProfile (extensão do User do Django)
│   ├── forms.py                 # LoginForm, CriarUsuarioForm, AlterarSenhaForm
│   ├── views.py                 # login, logout, dashboard, CRUD de usuários
│   └── urls.py
│
├── departamentos/               # CRUD de departamentos
│   ├── models.py
│   ├── serializers.py
│   ├── views.py                 # DepartamentoViewSet + endpoint /funcionarios/
│   └── urls.py
│
├── cargo/                       # CRUD de cargos
│   ├── models.py
│   ├── serializers.py
│   ├── views.py                 # CargoViewSet com filtro por departamento e nível
│   └── urls.py
│
├── funcionarios/                # Core do módulo — CRUD completo
│   ├── models.py
│   ├── serializers.py           # Validação de CPF + campo tempo_empresa
│   ├── views.py                 # FuncionarioViewSet + endpoint /relatorio/
│   └── urls.py
│
├── ponto/                       # Ponto eletrônico
│   ├── models.py
│   ├── serializers.py           # Validação de sequência entrada/saída/pausa
│   ├── views.py                 # RegistroPontoViewSet + endpoint /espelho/
│   └── urls.py
│
├── ferias/                      # Solicitações de férias
│   ├── models.py
│   ├── serializers.py           # Validação de datas e anti-sobreposição
│   ├── views.py                 # SolicitacaoFeriasViewSet + /aprovar/ + /recusar/
│   └── urls.py
│
├── templates/                   # Templates HTML
│   ├── base.html                # Template pai: sidebar, topbar, mensagens
│   └── autenticacao/
│       ├── login.html
│       └── dashboard.html
│
└── static/
    └── css/
        └── style.css            # CSS centralizado — importado pelo base.html
```

### Padrão de Arquivos por App

Cada app segue a mesma estrutura:

| Arquivo | Responsabilidade |
|---|---|
| `models.py` | Define a tabela e seus campos, mapeando para o banco Supabase |
| `serializers.py` | Converte objetos Python ↔ JSON e valida dados de entrada |
| `views.py` | Lógica de negócio e exposição dos endpoints REST |
| `urls.py` | Define as rotas do app usando o Router do DRF |
| `admin.py` | Configura a interface de administração em `/admin/` |

### Sistema de Templates

O frontend usa o sistema de herança de templates do Django:

```
base.html          ← sidebar, topbar, mensagens, importa style.css
  └── login.html
  └── dashboard.html
  └── funcionarios/list.html    (a criar)
  └── funcionarios/form.html    (a criar)
  └── ...
```

Todo o CSS fica em `static/css/style.css` e é importado uma única vez no `base.html`. Qualquer ajuste visual reflete em todos os templates.

---

## 4. Sistema de Autenticação

Utiliza a autenticação nativa do Django (`django.contrib.auth`), sem bibliotecas externas.

### Separação de Usuários

| Tipo | Descrição |
|---|---|
| `Funcionario` (model) | Qualquer colaborador da empresa no banco. **Não acessa o sistema.** |
| `User` (Django) | Membros da equipe de RH que operam o módulo. **Faz login.** |
| `UserProfile` (model) | Extensão do User com o cargo no RH (Gerente ou Analista). |

### Níveis de Acesso

| Perfil | Permissões |
|---|---|
| **Gerente / Diretor** | Acesso total: cadastra usuários, aprova/recusa férias, vê relatórios, CRUD completo |
| **Analista de RH** | Acesso operacional: CRUD de funcionários, registros de ponto, solicitações de férias |

### Proteção de Rotas

- Todas as views (exceto login) são protegidas com `@login_required`
- Views exclusivas de gerente usam o decorator `@gerente_required`, que redireciona automaticamente para o dashboard caso o usuário não tenha permissão

### Fluxo de Acesso

```
/login/  →  autentica  →  /dashboard/  →  módulos do sistema
                ↓
         senha errada → exibe erro no formulário
```

---

## 5. Endpoints da API

### 5.1 Departamentos — `/api/v1/departamentos/`

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/departamentos/` | Lista todos |
| POST | `/api/v1/departamentos/` | Cria novo |
| GET | `/api/v1/departamentos/{id}/` | Detalhe |
| PUT/PATCH | `/api/v1/departamentos/{id}/` | Atualiza |
| DELETE | `/api/v1/departamentos/{id}/` | Remove |
| GET | `/api/v1/departamentos/{id}/funcionarios/` | Funcionários do departamento |

### 5.2 Cargos — `/api/v1/cargo/`

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/cargo/` | Lista todos |
| GET | `/api/v1/cargo/?id_departamento=1` | Filtra por departamento |
| GET | `/api/v1/cargo/?nivel=3` | Filtra por nível hierárquico |
| POST | `/api/v1/cargo/` | Cria novo |
| PUT/PATCH | `/api/v1/cargo/{id}/` | Atualiza |
| DELETE | `/api/v1/cargo/{id}/` | Remove |

### 5.3 Funcionários — `/api/v1/funcionarios/`

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/funcionarios/` | Lista todos |
| GET | `/api/v1/funcionarios/?status=ativo` | Filtra por status |
| GET | `/api/v1/funcionarios/?id_departamento=1` | Filtra por departamento |
| GET | `/api/v1/funcionarios/?search=ana` | Busca por nome, CPF ou e-mail |
| POST | `/api/v1/funcionarios/` | Cadastra novo |
| PUT/PATCH | `/api/v1/funcionarios/{id}/` | Atualiza |
| DELETE | `/api/v1/funcionarios/{id}/` | Remove |
| GET | `/api/v1/funcionarios/relatorio/` | Relatório por departamento e status |

### 5.4 Ponto Eletrônico — `/api/v1/ponto/`

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/ponto/` | Lista todos os registros |
| GET | `/api/v1/ponto/?id_funcionario=1` | Registros de um funcionário |
| GET | `/api/v1/ponto/?tipo=entrada` | Filtra por tipo |
| POST | `/api/v1/ponto/` | Registra um ponto |
| DELETE | `/api/v1/ponto/{id}/` | Remove um registro |
| GET | `/api/v1/ponto/espelho/?funcionario=1` | Espelho mensal do funcionário |

### 5.5 Férias — `/api/v1/ferias/`

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/v1/ferias/` | Lista todas as solicitações |
| GET | `/api/v1/ferias/?status=pendente` | Filtra por status |
| GET | `/api/v1/ferias/?id_funcionario=1` | Férias de um funcionário |
| POST | `/api/v1/ferias/` | Cria nova solicitação |
| PATCH | `/api/v1/ferias/{id}/aprovar/` | Aprova a solicitação |
| PATCH | `/api/v1/ferias/{id}/recusar/` | Recusa a solicitação |
| DELETE | `/api/v1/ferias/{id}/` | Remove uma solicitação |

---

## 6. Regras de Negócio

### Funcionários
- **Validação de CPF:** verifica os dígitos verificadores matematicamente no serializer
- **Status controlado:** apenas `ativo`, `inativo` ou `afastado` são aceitos
- **Unicidade:** CPF e e-mail são únicos no banco
- **Campo calculado:** `tempo_empresa` calculado a partir da data de admissão, sem armazenar no banco

### Ponto Eletrônico
- **Sequência lógica:** não é possível registrar saída sem entrada prévia, nem duas entradas seguidas
- **Pausa controlada:** pausa só pode ser registrada imediatamente após uma entrada
- **Espelho mensal:** endpoint dedicado retorna todos os registros do mês corrente

### Férias
- **Período mínimo:** solicitações com menos de 5 dias corridos são rejeitadas
- **Validação de datas:** `data_fim` deve ser posterior a `data_inicio`
- **Anti-sobreposição:** não é possível solicitar férias em período com férias já aprovadas para o mesmo funcionário
- **Fluxo de aprovação:** status começa em `pendente` → `aprovada` ou `recusada`
- **Restrição de permissão:** apenas usuários com perfil Gerente podem aprovar ou recusar

---

## 7. Como Rodar o Projeto

### Pré-requisitos
- Python 3.10+
- pip e virtualenv
- Credenciais de acesso ao Supabase

### Instalação

```bash
# 1. Clone o repositório
git clone <url-do-repo>
cd rh_module

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure o arquivo .env (veja seção abaixo)

# 5. Rode as migrations
python manage.py migrate --fake-initial

# 6. Crie o superusuário (primeiro Gerente de RH)
python manage.py createsuperuser

# 7. Suba o servidor
python manage.py runserver
```

### Arquivo `.env`

Crie um arquivo `.env` na raiz do projeto (nunca suba no Git):

```env
SECRET_KEY=sua_secret_key_aqui
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=sua_senha_supabase
DB_HOST=db.xxxx.supabase.co
DB_PORT=5432
```

### URLs de Acesso

| URL | Descrição |
|---|---|
| `http://localhost:8000/login/` | Tela de login |
| `http://localhost:8000/dashboard/` | Painel principal (requer login) |
| `http://localhost:8000/admin/` | Django Admin (requer superusuário) |
| `http://localhost:8000/api/v1/` | Raiz da API REST |

### Dependências (`requirements.txt`)

```
django>=4.2
djangorestframework
psycopg2-binary
django-filter
python-decouple
```

---

## 8. Próximos Passos

- [ ] Templates de listagem para cada app (funcionários, departamentos, cargos, ponto, férias)
- [ ] Templates de formulário de cadastro e edição
- [ ] Conectar links do dashboard às URLs reais conforme templates forem criados
- [ ] Alinhar contrato da API com os outros grupos (campos esperados, autenticação entre módulos)
- [ ] Testes unitários para validações de CPF, ponto e férias

---

