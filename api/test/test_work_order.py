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
    """Testa se enviar initialChecklist vazia retorna erro de validação (HTTP 400)."""
    sup_token, _ = create_user(client, "sup_empty_check@fieldops.eval", "Supervisor", "supervisor", "team-alpha")

    payload = {
        "title": "OS Sem Checklist",
        "teamId": "team-alpha",
        "initialChecklist": [] # Rejeitado pelo schema (min_length=1)
    }

    headers = {"Authorization": f"Bearer {sup_token}"}
    response = client.post("/work-orders/", json=payload, headers=headers)

    assert response.status_code == 400


# ==========================================
# TESTES DE LISTAGEM PAGINADA E ESCOPO RBAC
# ==========================================

def test_list_work_orders_pagination_per_page(client):
    """Testa a paginação com parâmetro perPage e cálculos do meta."""
    admin_token, _ = create_user(client, "admin_list@fieldops.eval", "Admin", "admin", None)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Criar 5 OSs
    for i in range(5):
        payload = {
            "title": f"OS {i+1}",
            "priority": "low",
            "teamId": "team-alpha",
            "initialChecklist": [{"label": "Check"}]
        }
        client.post("/work-orders/", json=payload, headers=headers)

    # Página 1 com perPage=2
    res_p1 = client.get("/work-orders/?page=1&perPage=2", headers=headers)
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert len(data_p1["data"]) == 2
    assert data_p1["meta"]["page"] == 1
    assert data_p1["meta"]["limit"] == 2
    assert data_p1["meta"]["total"] == 5
    assert data_p1["meta"]["totalPages"] == 3

    # Página 3 com perPage=2 (deve vir apenas 1 item restante)
    res_p3 = client.get("/work-orders/?page=3&perPage=2", headers=headers)
    assert res_p3.status_code == 200
    data_p3 = res_p3.json()
    assert len(data_p3["data"]) == 1


def test_list_work_orders_filters_priority(client):
    """Testa a filtragem por priority."""
    admin_token, _ = create_user(client, "admin_filter@fieldops.eval", "Admin", "admin", None)
    headers = {"Authorization": f"Bearer {admin_token}"}

    client.post("/work-orders/", json={
        "title": "OS Baixa Prioridade", "priority": "low", "teamId": "team-alpha", "initialChecklist": [{"label": "C"}]
    }, headers=headers)

    client.post("/work-orders/", json={
        "title": "OS Alta Prioridade", "priority": "high", "teamId": "team-alpha", "initialChecklist": [{"label": "C"}]
    }, headers=headers)

    # Filtra apenas high
    response = client.get("/work-orders/?priority=high", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["priority"] == "high"
    assert data["meta"]["total"] == 1


def test_list_work_orders_scope_by_role(client):
    """Testa o escopo de listagem por papel (Technician vs Supervisor vs Admin)."""
    # 1. Usuários
    sup_token, _ = create_user(client, "sup_scope@fieldops.eval", "Supervisor Alpha", "supervisor", "team-alpha")
    tech1_token, _ = create_user(client, "tech1_scope@fieldops.eval", "Técnico 1", "technician", "team-alpha")
    tech2_token, _ = create_user(client, "tech2_scope@fieldops.eval", "Técnico 2", "technician", "team-alpha")
    admin_token, _ = create_user(client, "admin_scope@fieldops.eval", "Admin Scope", "admin", None)

    tech1_id = get_user_id_from_token(tech1_token)
    tech2_id = get_user_id_from_token(tech2_token)

    # 2. Criar 2 OSs para team-alpha (uma designada a tech1, outra a tech2)
    client.post("/work-orders/", json={
        "title": "OS Tech 1", "priority": "low", "teamId": "team-alpha", "assigneeId": tech1_id, "initialChecklist": [{"label": "C"}]
    }, headers={"Authorization": f"Bearer {sup_token}"})

    client.post("/work-orders/", json={
        "title": "OS Tech 2", "priority": "low", "teamId": "team-alpha", "assigneeId": tech2_id, "initialChecklist": [{"label": "C"}]
    }, headers={"Authorization": f"Bearer {sup_token}"})

    # 3. Técnico 1 lista -> deve ver APENAS a sua OS (1 item)
    res_tech1 = client.get("/work-orders/", headers={"Authorization": f"Bearer {tech1_token}"})
    assert res_tech1.status_code == 200
    assert len(res_tech1.json()["data"]) == 1
    assert res_tech1.json()["data"][0]["assigneeId"] == tech1_id

    # 4. Supervisor Alpha lista -> deve ver TODAS do seu time (2 itens)
    res_sup = client.get("/work-orders/", headers={"Authorization": f"Bearer {sup_token}"})
    assert res_sup.status_code == 200
    assert len(res_sup.json()["data"]) == 2

    # 5. Admin lista -> deve ver todas (2 itens)
    res_admin = client.get("/work-orders/", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert len(res_admin.json()["data"]) == 2


def test_list_work_orders_out_of_bounds_page_returns_empty_list(client):
    """Testa se consultar uma página além do total retorna data: [] com HTTP 200 (sem erro 500)."""
    admin_token, _ = create_user(client, "admin_oob@fieldops.eval", "Admin", "admin", None)
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get("/work-orders/?page=999&perPage=20", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["meta"]["page"] == 999
