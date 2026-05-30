# Modulo de RH

Documentacao do modulo de RH desenvolvido para o Projeto de DOS.

Stack principal: Django, Django REST Framework e Supabase/PostgreSQL.

## Visao Geral

O modulo gerencia funcionarios, departamentos, cargos, registros de ponto, solicitacoes de ferias e usuarios internos que acessam o sistema.

O projeto oferece duas superficies:

- Telas HTML com login, dashboard e CRUDs principais.
- API REST em `/api/v1/` para integracao com outros modulos via API no futuro.

## Tecnologias

| Tecnologia | Uso |
|---|---|
| Python 3.10+ | Linguagem principal |
| Django 4.2+ | Framework web e ORM |
| Django REST Framework | API REST |
| Supabase/PostgreSQL | Banco de dados |
| django-filter | Filtros nos endpoints |
| python-dotenv | Leitura do arquivo `.env` |

## Estrutura

```text
rh_module/
  core/             configuracoes do projeto
  autenticacao/     login, logout, dashboard e usuarios do sistema
  departamentos/    CRUD e API de departamentos
  cargo/            CRUD e API de cargos
  funcionarios/     CRUD e API de funcionarios
  ponto/            registros de ponto
  ferias/           solicitacoes, aprovacao e recusa de ferias
  templates/        telas HTML
  static/           CSS centralizado
```

## Organizacao

Em Django, cada app possui arquivos de "controle", que definem as rotas, telas e regras.
Neste projeto, os principais são `models.py`, `views.py`, `urls.py`/`web_urls.py` e `forms.py`/`serializers.py`

- models.py
```
  Define as tabelas do BD e as regras centrais dos dados, sendo um dos arquivos mais importantes do projeto.
```

- views.py
```
  Define o que acontece quando o user acessa uma tela ou endpoint, controlando as regras de fluxo
```

- urls.py/web_urls.py
```
  Mapeiam os endereços para a views (API REST e Telas HTML)
```

- forms.py
```
  Utilizados principalmente nas telas HTML, definem quais campos aparecem no formulário e como eles são validados
```

- serializers.py
```
  Equivalente ao forms.py, porém, opera para API REST, transformando models em JSON e validando os dados que chegaria via API (no futuro)
```

Outros arquivos que também são importantes para a estruturação do projeto a seguir.

- admin.py
```
  Configura como os models aparecem no painel /admin/ do Django
```

- apps.py
```
  Configuração do app Django
```

- signals.py
```
  Utilizado na criação de funcionário, propõe regras e execuções automáticas quando algo acontece no BD
```


## Autenticacao e Permissoes

O sistema usa a autenticacao nativa do Django.

| Modelo | Funcao |
|---|---|
| `Funcionario` | Colaborador cadastrado no RH |
| `User` | Usuario que faz login no sistema |
| `UserProfile` | Vincula `User` a funcionario, setor, permissao de gerente e primeiro acesso |

Regras principais:

- Usuarios do setor RH acessam o dashboard e os modulos internos.
- Usuário da "empresa" podem acessar módulos do RH de acordo da necessidade (Ex: Ponto)
- Gerentes do RH gerenciam usuarios do sistema.
- O primeiro acesso obriga troca de senha.
- A tela de usuarios usa o fluxo real: criar, editar e desativar.

## Ferias

As solicitacoes de ferias seguem estas regras:

- Periodo minimo de 5 dias corridos.
- Data final precisa ser posterior a data inicial.
- Nao permite sobreposicao com ferias ja aprovadas do mesmo funcionario.
- Usuarios do RH visualizam as solicitacoes.
- Usuarios do RH vinculados a cargo de nivel 4, 5 ou 6 podem aprovar ou recusar.

## Ponto

O registro de ponto valida a sequencia das marcacoes:

- Nao permite saida sem entrada anterior.
- Nao permite duas entradas seguidas.
- O espelho mensal retorna os registros do funcionario no mes.

## API

Todos os endpoints seguem o padrao `/api/v1/<recurso>/`.

| Recurso | Endpoint |
|---|---|
| Departamentos | `/api/v1/departamentos/` |
| Cargos | `/api/v1/cargo/` |
| Funcionarios | `/api/v1/funcionarios/` |
| Ponto | `/api/v1/ponto/` |
| Ferias | `/api/v1/ferias/` |

Endpoints adicionais:

- `/api/v1/departamentos/{id}/funcionarios/`
- `/api/v1/funcionarios/relatorio/`
- `/api/v1/ponto/espelho/`
- `/api/v1/ferias/{id}/aprovar/`
- `/api/v1/ferias/{id}/recusar/`

## Como Rodar

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate --fake-initial
python manage.py createsuperuser
python manage.py runserver
```

No Linux, ative o ambiente com:

```bash
source venv/bin/activate
```

## Variaveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=sua_senha_supabase
DB_HOST=db.xxxx.supabase.co
DB_PORT=5432
```

## URLs Locais

| URL | Descricao |
|---|---|
| `http://localhost:8000/login/` | Login |
| `http://localhost:8000/dashboard/` | Dashboard |
| `http://localhost:8000/admin/` | Django Admin |
| `http://localhost:8000/api/v1/` | API REST |

## Verificacao

Use:

```bash
python manage.py check
```
