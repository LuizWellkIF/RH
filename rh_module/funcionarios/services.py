from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import base64
import json

from django.conf import settings


class FuncionariosAPIError(Exception):
    pass


def _api_get(path, params=None):
    headers = {'Accept': 'application/json'}
    if settings.FUNCIONARIOS_API_TOKEN:
        headers['Authorization'] = f'Token {settings.FUNCIONARIOS_API_TOKEN}'
    elif settings.FUNCIONARIOS_API_USER and settings.FUNCIONARIOS_API_PASS:
        credentials = f'{settings.FUNCIONARIOS_API_USER}:{settings.FUNCIONARIOS_API_PASS}'
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('ascii')
        headers['Authorization'] = f'Basic {encoded_credentials}'
    else:
        raise FuncionariosAPIError('Credenciais da API de funcionarios nao configuradas.')

    query = f'?{urlencode(params)}' if params else ''
    url = f'{settings.FUNCIONARIOS_API_BASE_URL}/{path.strip("/")}/{query}'
    request = Request(
        url,
        headers=headers,
    )

    try:
        with urlopen(request, timeout=settings.FUNCIONARIOS_API_TIMEOUT) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        raise FuncionariosAPIError(f'API respondeu com status {exc.code}.') from exc
    except URLError as exc:
        raise FuncionariosAPIError(f'Nao foi possivel conectar na API: {exc.reason}.') from exc
    except json.JSONDecodeError as exc:
        raise FuncionariosAPIError('API retornou uma resposta que nao e JSON valido.') from exc

    return payload.get('results', payload) if isinstance(payload, dict) else payload


def _pick(data, *keys, default=None):
    for key in keys:
        if isinstance(data, dict) and data.get(key) not in (None, ''):
            return data[key]
    return default


def _object(**kwargs):
    return SimpleNamespace(**kwargs)


def _normalize_departamento(raw):
    if isinstance(raw, dict):
        dep_id = _pick(raw, 'id_departamento', 'id')
        nome = _pick(raw, 'nome', 'departamento_nome', 'sigla', default='Sem departamento')
        sigla = _pick(raw, 'sigla', default=nome)
        return _object(id_departamento=dep_id, pk=dep_id, nome=nome, sigla=sigla)
    return _object(id_departamento=raw, pk=raw, nome=str(raw or 'Sem departamento'), sigla=str(raw or '-'))


def _normalize_cargo(raw, funcionarios_count=0, nome=None, departamento=None):
    if not isinstance(raw, dict):
        raw = {'id_cargo': raw, 'nome': nome}

    departamento = _normalize_departamento(
        departamento or _pick(raw, 'id_departamento', 'departamento', default={})
    )
    cargo_id = _pick(raw, 'id_cargo', 'id')
    nivel = _pick(raw, 'nivel')
    nivel_display = _pick(raw, 'nivel_display', 'nivel_nome', default=nivel or '-')
    return _object(
        id_cargo=cargo_id,
        pk=cargo_id,
        nome=_pick(raw, 'nome', 'cargo_nome', default=nome or 'Sem cargo'),
        descricao=_pick(raw, 'descricao', default=''),
        nivel=nivel,
        nivel_display=nivel_display,
        get_nivel_display=nivel_display,
        id_departamento=departamento,
        funcionarios=_object(count=funcionarios_count),
    )


def _normalize_funcionario(raw):
    departamento = _normalize_departamento(_pick(raw, 'id_departamento', 'departamento', default={
        'id_departamento': _pick(raw, 'departamento_id'),
        'nome': _pick(raw, 'departamento_nome', default='Sem departamento'),
    }))
    cargo = _normalize_cargo(
        _pick(raw, 'id_cargo', 'cargo', default=_pick(raw, 'cargo_id')),
        nome=_pick(raw, 'cargo_nome', default='Sem cargo'),
        departamento=departamento,
    )
    return _object(
        id_funcionario=_pick(raw, 'id_funcionario', 'id'),
        pk=_pick(raw, 'id_funcionario', 'id'),
        nome=_pick(raw, 'nome', default='Sem nome'),
        cpf=_pick(raw, 'cpf', default=''),
        email=_pick(raw, 'email', default=''),
        telefone=_pick(raw, 'telefone', default=''),
        data_admissao=_pick(raw, 'data_admissao'),
        salario=_pick(raw, 'salario'),
        status=_pick(raw, 'status', default='ativo'),
        id_cargo=cargo,
        id_departamento=departamento,
    )


def listar_funcionarios(params=None):
    return [_normalize_funcionario(item) for item in _api_get('funcionarios/', params=params)]


def listar_cargos(params=None, funcionarios=None):
    cargos = [_normalize_cargo(item) for item in _api_get('cargos/', params=params)]

    if funcionarios is None:
        return cargos

    totais = {}
    for funcionario in funcionarios:
        cargo_id = getattr(funcionario.id_cargo, 'id_cargo', None)
        totais[cargo_id] = totais.get(cargo_id, 0) + 1

    for cargo in cargos:
        cargo.funcionarios.count = totais.get(cargo.id_cargo, 0)

    return cargos


def preencher_cargos_funcionarios(funcionarios, cargos):
    cargos_por_id = {cargo.id_cargo: cargo for cargo in cargos}

    for funcionario in funcionarios:
        cargo = cargos_por_id.get(funcionario.id_cargo.id_cargo)
        if cargo:
            funcionario.id_cargo = cargo

    return funcionarios


def funcionario_to_dict(funcionario):
    return {
        'id_funcionario': funcionario.id_funcionario,
        'nome': funcionario.nome,
        'cpf': funcionario.cpf,
        'email': funcionario.email,
        'telefone': funcionario.telefone,
        'data_admissao': funcionario.data_admissao,
        'salario': funcionario.salario,
        'status': funcionario.status,
        'id_cargo': funcionario.id_cargo.id_cargo,
        'cargo_nome': funcionario.id_cargo.nome,
        'id_departamento': funcionario.id_departamento.id_departamento,
        'departamento_nome': funcionario.id_departamento.nome,
    }


def cargo_to_dict(cargo):
    return {
        'id_cargo': cargo.id_cargo,
        'id_departamento': cargo.id_departamento.id_departamento,
        'departamento_nome': cargo.id_departamento.nome,
        'nome': cargo.nome,
        'descricao': cargo.descricao,
        'nivel': cargo.nivel,
        'nivel_display': cargo.nivel_display,
    }
