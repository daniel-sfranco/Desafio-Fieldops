import pytest
from utils.security import create_access_token
from models.enums.UsuarioRole import UsuarioRole


def create_user(client, email, name, role, team_id=None):
    """Helper fixture/função para registrar um usuário e retornar o token e dados."""
    payload = {
        "email": email,
        "password": "password123",
        "name": name,
        "role": role,
        "teamId": team_id
    }
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 201
    token = res.json()["access_token"]
    
    # Faz login ou usa o token cadastrado
    login_res = client.post("/auth/login", json={"email": email, "password": "password123"})
    token = login_res.json()["access_token"]
    
    return token, payload


def get_user_id_from_token(token):
    from utils.security import decode_access_token
    return int(decode_access_token(token)["sub"])


def test_create_work_order_success_as_supervisor(client):
    """Testa a criação de OS por um Supervisor para sua própria equipe."""
    sup_token, _ = create_user(client, "sup1@fieldops.eval", "Supervisor 1", "supervisor", "team-alpha")
    tech_token, _ = create_user(client, "tech1@fieldops.eval", "Técnico 1", "technician", "team-alpha")
    tech_id = get_user_id_from_token(tech_token)

    payload = {
        "title": "Manutenção de Ar Condicionado",
        "description": "Limpeza de filtros e verificação de gás",
        "priority": "low",
        "teamId": "team-alpha",
        "assigneeId": tech_id,
        "initialChecklist": [
            {"label": "Desligar a energia"},
            {"label": "Limpar o filtro principal"},
            {"label": "Testar temperatura final"}
        ]
    }

    headers = {"Authorization": f"Bearer {sup_token}"}
    response = client.post("/work-orders/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["status"] == "open"
    assert data["priority"] == "low"
    assert data["teamId"] == "team-alpha"
    assert data["assigneeId"] == tech_id
    assert len(data["checkList"]) == 3
    assert data["checkList"][0]["label"] == "Desligar a energia"
    assert data["checkList"][0]["completed"] is False


def test_create_work_order_success_as_admin(client):
    """Testa a criação de OS por um Administrador para qualquer equipe."""
    admin_token, _ = create_user(client, "admin1@fieldops.eval", "Admin", "admin", None)

    payload = {
        "title": "Vistoria Geral de TI",
        "description": "Verificação de servidores",
        "priority": "high",
        "teamId": "team-beta",
        "initialChecklist": [
            {"label": "Checar no-break"}
        ]
    }

    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post("/work-orders/", json=payload, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Vistoria Geral de TI"
    assert data["teamId"] == "team-beta"


def test_create_work_order_as_technician_fails(client):
    """Testa se um Técnico é proibido de criar Ordens de Serviço (HTTP 403)."""
    tech_token, _ = create_user(client, "tech_creator@fieldops.eval", "Técnico", "technician", "team-alpha")

    payload = {
        "title": "OS Não Autorizada",
        "teamId": "team-alpha",
        "initialChecklist": [{"label": "Item 1"}]
    }

    headers = {"Authorization": f"Bearer {tech_token}"}
    response = client.post("/work-orders/", json=payload, headers=headers)

    assert response.status_code == 403
    error = response.json()
    assert error["error"]["code"] == "FLX_FORBIDDEN"


def test_create_work_order_supervisor_other_team_fails(client):
    """Testa se Supervisor tentando criar OS para outra equipe é bloqueado (HTTP 403)."""
    sup_token, _ = create_user(client, "sup_beta@fieldops.eval", "Supervisor Beta", "supervisor", "team-beta")

    payload = {
        "title": "OS para outra equipe",
        "teamId": "team-alpha", # Supervisor é de team-beta
        "initialChecklist": [{"label": "Item 1"}]
    }

    headers = {"Authorization": f"Bearer {sup_token}"}
    response = client.post("/work-orders/", json=payload, headers=headers)

    assert response.status_code == 403
    error = response.json()
    assert error["error"]["code"] == "FLX_FORBIDDEN"


def test_create_work_order_assignee_other_team_fails(client):
    """Testa se Supervisor tentando designar um técnico de outra equipe é bloqueado (HTTP 403)."""
    sup_token, _ = create_user(client, "sup_alpha2@fieldops.eval", "Supervisor Alpha", "supervisor", "team-alpha")
    tech_beta_token, _ = create_user(client, "tech_beta2@fieldops.eval", "Técnico Beta", "technician", "team-beta")
    tech_beta_id = get_user_id_from_token(tech_beta_token)

    payload = {
        "title": "OS Designação Inválida",
        "teamId": "team-alpha",
        "assigneeId": tech_beta_id, # Técnico é da team-beta
        "initialChecklist": [{"label": "Item 1"}]
    }

    headers = {"Authorization": f"Bearer {sup_token}"}
    response = client.post("/work-orders/", json=payload, headers=headers)

    assert response.status_code == 403
    error = response.json()
    assert error["error"]["code"] == "FLX_FORBIDDEN"


def test_create_work_order_assignee_not_technician_fails(client):
    """Testa se tentar designar a OS para um usuário que não é técnico falha (HTTP 422)."""
    sup_token, _ = create_user(client, "sup_owner@fieldops.eval", "Supervisor Owner", "supervisor", "team-alpha")
    other_sup_token, _ = create_user(client, "other_sup@fieldops.eval", "Outro Supervisor", "supervisor", "team-alpha")
    other_sup_id = get_user_id_from_token(other_sup_token)

    payload = {
        "title": "OS Designada para Supervisor",
        "teamId": "team-alpha",
        "assigneeId": other_sup_id, # Designado é supervisor, não técnico
        "initialChecklist": [{"label": "Item 1"}]
    }

    headers = {"Authorization": f"Bearer {sup_token}"}
    response = client.post("/work-orders/", json=payload, headers=headers)

    assert response.status_code == 422
    error = response.json()
    assert error["error"]["code"] == "FLX_VALIDATION_ERROR"


def test_create_work_order_empty_checklist_fails(client):
    """Testa se enviar initialChecklist vazia retorna erro de validação (HTTP 422)."""
    sup_token, _ = create_user(client, "sup_empty_check@fieldops.eval", "Supervisor", "supervisor", "team-alpha")

    payload = {
        "title": "OS Sem Checklist",
        "teamId": "team-alpha",
        "initialChecklist": [] # Rejeitado pelo schema (min_length=1)
    }

    headers = {"Authorization": f"Bearer {sup_token}"}
    response = client.post("/work-orders/", json=payload, headers=headers)

    assert response.status_code == 400
