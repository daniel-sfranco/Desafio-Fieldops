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


# ==========================================
# TESTES DE DETALHE DE OS (GET /work-orders/:id)
# ==========================================

def test_get_work_order_details_success(client):
    """Testa a obtenção do detalhe de uma OS válida."""
    sup_token, _ = create_user(client, "sup_detail@fieldops.eval", "Supervisor", "supervisor", "team-alpha")
    headers = {"Authorization": f"Bearer {sup_token}"}

    create_res = client.post("/work-orders/", json={
        "title": "OS Detalhe Teste", "priority": "high", "teamId": "team-alpha", "initialChecklist": [{"label": "Verificar peça"}]
    }, headers=headers)
    os_id = create_res.json()["id"]

    res = client.get(f"/work-orders/{os_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == os_id
    assert data["title"] == "OS Detalhe Teste"
    assert len(data["checkList"]) == 1
    assert data["checkList"][0]["label"] == "Verificar peça"


def test_get_work_order_details_not_found(client):
    """Testa a consulta a uma OS com ID inexistente (HTTP 404)."""
    admin_token, _ = create_user(client, "admin_detail_nf@fieldops.eval", "Admin", "admin", None)
    headers = {"Authorization": f"Bearer {admin_token}"}

    res = client.get("/work-orders/99999", headers=headers)
    assert res.status_code == 404
    error = res.json()
    assert error["error"]["code"] == "FLX_NOT_FOUND"


def test_get_work_order_details_out_of_scope_returns_404(client):
    """Testa se um técnico tentando acessar detalhe de OS de outro técnico/time recebe HTTP 404."""
    sup_token, _ = create_user(client, "sup_detail_scope@fieldops.eval", "Supervisor", "supervisor", "team-alpha")
    tech1_token, _ = create_user(client, "tech1_detail@fieldops.eval", "Técnico 1", "technician", "team-alpha")
    tech2_token, _ = create_user(client, "tech2_detail@fieldops.eval", "Técnico 2", "technician", "team-alpha")

    tech2_id = get_user_id_from_token(tech2_token)

    # Cria OS para Tech 2
    create_res = client.post("/work-orders/", json={
        "title": "OS Tech 2 Exclusiva", "priority": "low", "teamId": "team-alpha", "assigneeId": tech2_id, "initialChecklist": [{"label": "C"}]
    }, headers={"Authorization": f"Bearer {sup_token}"})
    os_id = create_res.json()["id"]

    # Tech 1 tenta acessar detalhe da OS do Tech 2 -> deve retornar 404 (fora de escopo)
    res_tech1 = client.get(f"/work-orders/{os_id}", headers={"Authorization": f"Bearer {tech1_token}"})
    assert res_tech1.status_code == 404
    assert res_tech1.json()["error"]["code"] == "FLX_NOT_FOUND"


# ==========================================
# TESTES DE DELEÇÃO DE OS (DELETE /work-orders/:id)
# ==========================================

def test_delete_work_order_success(client):
    """Testa a exclusão de uma OS com sucesso (HTTP 204)."""
    sup_token, _ = create_user(client, "sup_del@fieldops.eval", "Supervisor", "supervisor", "team-alpha")
    headers = {"Authorization": f"Bearer {sup_token}"}

    create_res = client.post("/work-orders/", json={
        "title": "OS Deletar", "priority": "low", "teamId": "team-alpha", "initialChecklist": [{"label": "C"}]
    }, headers=headers)
    os_id = create_res.json()["id"]

    # Deleta a OS
    del_res = client.delete(f"/work-orders/{os_id}", headers=headers)
    assert del_res.status_code == 204

    # Confirma que a OS não existe mais
    get_res = client.get(f"/work-orders/{os_id}", headers=headers)
    assert get_res.status_code == 404
    assert get_res.json()["error"]["code"] == "FLX_NOT_FOUND"


def test_delete_work_order_not_found(client):
    """Testa a exclusão de uma OS com ID inexistente (HTTP 404)."""
    admin_token, _ = create_user(client, "admin_del_nf@fieldops.eval", "Admin", "admin", None)
    headers = {"Authorization": f"Bearer {admin_token}"}

    del_res = client.delete("/work-orders/99999", headers=headers)
    assert del_res.status_code == 404
    assert del_res.json()["error"]["code"] == "FLX_NOT_FOUND"


def test_delete_work_order_out_of_scope_fails(client):
    """Testa se um técnico tentando deletar OS de outro técnico/time recebe HTTP 404."""
    sup_token, _ = create_user(client, "sup_del_scope@fieldops.eval", "Supervisor", "supervisor", "team-alpha")
    tech1_token, _ = create_user(client, "tech1_del@fieldops.eval", "Técnico 1", "technician", "team-alpha")
    tech2_token, _ = create_user(client, "tech2_del@fieldops.eval", "Técnico 2", "technician", "team-alpha")
    tech2_id = get_user_id_from_token(tech2_token)

    # Cria OS para Tech 2
    create_res = client.post("/work-orders/", json={
        "title": "OS Tech 2 Para Deletar", "priority": "low", "teamId": "team-alpha", "assigneeId": tech2_id, "initialChecklist": [{"label": "C"}]
    }, headers={"Authorization": f"Bearer {sup_token}"})
    os_id = create_res.json()["id"]

    # Tech 1 tenta deletar a OS do Tech 2 -> bloqueado com 404
    del_res = client.delete(f"/work-orders/{os_id}", headers={"Authorization": f"Bearer {tech1_token}"})
    assert del_res.status_code == 404
    assert del_res.json()["error"]["code"] == "FLX_NOT_FOUND"


# ==========================================
# TESTES DE TRANSIÇÃO DE STATUS E CONCORRÊNCIA
# ==========================================

def test_status_transition_full_flow_and_audit(client):
    """Testa transição open -> in_progress -> done e geração de histórico de auditoria."""
    sup_token, _ = create_user(client, "sup_flow@fieldops.eval", "Supervisor", "supervisor", "team-alpha")
    tech_token, _ = create_user(client, "tech_flow@fieldops.eval", "Técnico", "technician", "team-alpha")
    tech_id = get_user_id_from_token(tech_token)

    headers_sup = {"Authorization": f"Bearer {sup_token}"}
    headers_tech = {"Authorization": f"Bearer {tech_token}"}

    # 1. Cria OS
    create_res = client.post("/work-orders/", json={
        "title": "OS Flow Test", "priority": "low", "teamId": "team-alpha", "assigneeId": tech_id, "initialChecklist": [{"label": "Task 1"}]
    }, headers=headers_sup)
    os_id = create_res.json()["id"]

    # 2. open -> in_progress (by Tech)
    patch1 = client.patch(f"/work-orders/{os_id}", json={
        "status": "in_progress",
        "version": 1
    }, headers=headers_tech)
    assert patch1.status_code == 200
    assert patch1.json()["status"] == "in_progress"
    assert patch1.json()["version"] == 2

    # 3. in_progress -> done (by Tech, priority low)
    patch2 = client.patch(f"/work-orders/{os_id}", json={
        "status": "done",
        "resolutionNotes": "Problema resolvido com sucesso após troca de peças.",
        "version": 2
    }, headers=headers_tech)
    assert patch2.status_code == 200
    assert patch2.json()["status"] == "done"
    assert patch2.json()["version"] == 3

    # 4. Verifica histórico de auditoria
    history_res = client.get(f"/work-orders/{os_id}/history", headers=headers_tech)
    assert history_res.status_code == 200
    events = history_res.json()
    assert len(events) == 2
    assert events[0]["fromStatus"] == "open"
    assert events[0]["toStatus"] == "in_progress"
    assert events[1]["fromStatus"] == "in_progress"
    assert events[1]["toStatus"] == "done"


def test_optimistic_concurrency_conflict_409(client):
    """Testa se versão incorreta retorna HTTP 409 com FLX_CONCURRENT_UPDATE."""
    sup_token, _ = create_user(client, "sup_conc@fieldops.eval", "Supervisor", "supervisor", "team-alpha")
    tech_token, _ = create_user(client, "tech_conc@fieldops.eval", "Técnico", "technician", "team-alpha")
    tech_id = get_user_id_from_token(tech_token)

    headers_sup = {"Authorization": f"Bearer {sup_token}"}

    create_res = client.post("/work-orders/", json={
        "title": "OS Concorrência", "priority": "low", "teamId": "team-alpha", "assigneeId": tech_id, "initialChecklist": [{"label": "C"}]
    }, headers=headers_sup)
    os_id = create_res.json()["id"]

    # Tenta transição com versão errada (99 em vez de 1)
    res = client.patch(f"/work-orders/{os_id}", json={
        "status": "in_progress",
        "version": 99
    }, headers=headers_sup)

    assert res.status_code == 409
    assert res.json()["error"]["code"] == "FLX_CONCURRENT_UPDATE"


def test_high_priority_done_blocked_for_technician(client):
    """Testa se técnico tentando concluir OS de alta prioridade recebe HTTP 403."""
    sup_token, _ = create_user(client, "sup_high@fieldops.eval", "Supervisor", "supervisor", "team-alpha")
    tech_token, _ = create_user(client, "tech_high@fieldops.eval", "Técnico", "technician", "team-alpha")
    tech_id = get_user_id_from_token(tech_token)

    headers_sup = {"Authorization": f"Bearer {sup_token}"}
    headers_tech = {"Authorization": f"Bearer {tech_token}"}

    # Cria OS com prioridade high
    create_res = client.post("/work-orders/", json={
        "title": "OS Alta Prioridade Crítica", "priority": "high", "teamId": "team-alpha", "assigneeId": tech_id, "initialChecklist": [{"label": "C"}]
    }, headers=headers_sup)
    os_id = create_res.json()["id"]

    # Mudar para in_progress
    client.patch(f"/work-orders/{os_id}", json={"status": "in_progress", "version": 1}, headers=headers_tech)

    # Técnico tenta concluir -> Bloqueado com 403
    res_tech = client.patch(f"/work-orders/{os_id}", json={
        "status": "done",
        "resolutionNotes": "Tentativa de conclusão pelo técnico",
        "version": 2
    }, headers=headers_tech)

    assert res_tech.status_code == 403
    assert res_tech.json()["error"]["code"] == "FLX_FORBIDDEN"

    # Supervisor tenta concluir -> Deve funcionar (200)
    res_sup = client.patch(f"/work-orders/{os_id}", json={
        "status": "done",
        "resolutionNotes": "Concluído com sucesso pelo supervisor responsável.",
        "version": 2
    }, headers=headers_sup)

    assert res_sup.status_code == 200
    assert res_sup.json()["status"] == "done"


def test_invalid_status_transition_direct_open_to_done(client):
    """Testa se transição inválida (open -> done direto) retorna HTTP 422 com FLX_INVALID_STATUS_TRANSITION."""
    sup_token, _ = create_user(client, "sup_invalid@fieldops.eval", "Supervisor", "supervisor", "team-alpha")
    headers = {"Authorization": f"Bearer {sup_token}"}

    create_res = client.post("/work-orders/", json={
        "title": "OS Transição Direta Inválida", "priority": "low", "teamId": "team-alpha", "initialChecklist": [{"label": "C"}]
    }, headers=headers)
    os_id = create_res.json()["id"]

    res = client.patch(f"/work-orders/{os_id}", json={
        "status": "done",
        "resolutionNotes": "Notas suficientes mas transição inválida",
        "version": 1
    }, headers=headers)

    assert res.status_code == 422
    assert res.json()["error"]["code"] == "FLX_INVALID_STATUS_TRANSITION"


def test_technician_cannot_reassign_assignee_id_403(client):
    """Testa se um técnico tentando transferir o assigneeId da OS recebe HTTP 403."""
    sup_token, _ = create_user(client, "sup_reassign@fieldops.eval", "Supervisor", "supervisor", "team-alpha")
    tech1_token, _ = create_user(client, "tech1_reassign@fieldops.eval", "Técnico 1", "technician", "team-alpha")
    tech2_token, _ = create_user(client, "tech2_reassign@fieldops.eval", "Técnico 2", "technician", "team-alpha")
    tech1_id = get_user_id_from_token(tech1_token)
    tech2_id = get_user_id_from_token(tech2_token)

    create_res = client.post("/work-orders/", json={
        "title": "OS Reassign Test", "priority": "low", "teamId": "team-alpha", "assigneeId": tech1_id, "initialChecklist": [{"label": "C"}]
    }, headers={"Authorization": f"Bearer {sup_token}"})
    os_id = create_res.json()["id"]

    # Tech 1 tenta mudar assigneeId para Tech 2
    res = client.patch(f"/work-orders/{os_id}", json={
        "assigneeId": tech2_id,
        "version": 1
    }, headers={"Authorization": f"Bearer {tech1_token}"})

    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FLX_FORBIDDEN"


def test_technician_cannot_modify_title_or_description_403(client):
    """Testa se um técnico tentando alterar title ou description recebe HTTP 403."""
    sup_token, _ = create_user(client, "sup_title@fieldops.eval", "Supervisor", "supervisor", "team-alpha")
    tech_token, _ = create_user(client, "tech_title@fieldops.eval", "Técnico", "technician", "team-alpha")
    tech_id = get_user_id_from_token(tech_token)

    create_res = client.post("/work-orders/", json={
        "title": "Título Original", "description": "Desc Original", "priority": "low", "teamId": "team-alpha", "assigneeId": tech_id, "initialChecklist": [{"label": "C"}]
    }, headers={"Authorization": f"Bearer {sup_token}"})
    os_id = create_res.json()["id"]

    # Tech tenta mudar o título
    res = client.patch(f"/work-orders/{os_id}", json={
        "title": "Título Alterado Pelo Técnico",
        "version": 1
    }, headers={"Authorization": f"Bearer {tech_token}"})

    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FLX_FORBIDDEN"


def test_unhandled_route_returns_flx_envelope_404(client):
    """Testa se rota inexistente retorna formato padronizado com FLX_NOT_FOUND e flxTraceId."""
    res = client.get("/rota-completamente-inexistente")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "FLX_NOT_FOUND"
    assert "flxTraceId" in data["error"]


