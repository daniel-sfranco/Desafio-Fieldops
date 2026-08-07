import pytest
from utils.security import decode_access_token


def test_register_technician_success(client):
    """Testa o cadastro com sucesso de um técnico com time."""
    payload = {
        "email": "tech1@fieldops.eval",
        "password": "password123",
        "name": "Técnico Silva",
        "role": "technician",
        "teamId": "team-alpha"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Valida as claims do JWT
    token_claims = decode_access_token(data["access_token"])
    assert token_claims["role"] == "technician"
    assert token_claims["teamId"] == "team-alpha"
    assert "sub" in token_claims


def test_register_admin_without_team_success(client):
    """Testa o cadastro de um administrador sem time."""
    payload = {
        "email": "admin1@fieldops.eval",
        "password": "password123",
        "name": "Admin Silva",
        "role": "admin",
        "teamId": None
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert "access_token" in data
    
    token_claims = decode_access_token(data["access_token"])
    assert token_claims["role"] == "admin"
    assert token_claims["teamId"] is None


def test_register_duplicate_email_fails(client):
    """Testa se o cadastro rejeita e-mails duplicados."""
    payload = {
        "email": "tech2@fieldops.eval",
        "password": "password123",
        "name": "Técnico 2",
        "role": "technician",
        "teamId": "team-alpha"
    }
    # Primeiro cadastro
    res1 = client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    # Tentativa com o mesmo e-mail
    res2 = client.post("/auth/register", json=payload)
    assert res2.status_code == 401
    error_data = res2.json()
    assert error_data["error"]["code"] == "FLX_UNAUTHORIZED"
    assert "já está em uso" in error_data["error"]["message"]


def test_register_non_admin_without_team_fails(client):
    """Testa se técnico sem teamId é rejeitado no cadastro."""
    payload = {
        "email": "noteam@fieldops.eval",
        "password": "password123",
        "name": "Técnico Sem Time",
        "role": "technician",
        "teamId": None
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    error_data = response.json()
    assert error_data["error"]["code"] == "FLX_VALIDATION_ERROR"
    assert "precisa cadastrar um time" in error_data["error"]["message"]


def test_login_success(client):
    """Testa o login realizado com sucesso."""
    # 1. Cadastra o usuário
    reg_payload = {
        "email": "userlogin@fieldops.eval",
        "password": "mysecretpassword",
        "name": "Usuário Login",
        "role": "supervisor",
        "teamId": "team-beta"
    }
    client.post("/auth/register", json=reg_payload)

    # 2. Faz o login
    login_payload = {
        "email": "userlogin@fieldops.eval",
        "password": "mysecretpassword"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    
    token_claims = decode_access_token(data["access_token"])
    assert token_claims["role"] == "supervisor"
    assert token_claims["teamId"] == "team-beta"


def test_login_unregistered_email_fails(client):
    """Testa a tentativa de login com e-mail que não existe."""
    login_payload = {
        "email": "notfound@fieldops.eval",
        "password": "anypassword"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    error_data = response.json()
    assert error_data["error"]["code"] == "FLX_UNAUTHORIZED"


def test_login_wrong_password_fails(client):
    """Testa a tentativa de login com a senha errada."""
    # 1. Cadastra o usuário
    reg_payload = {
        "email": "userwrongpwd@fieldops.eval",
        "password": "correctpassword",
        "name": "Usuário Teste",
        "role": "technician",
        "teamId": "team-alpha"
    }
    client.post("/auth/register", json=reg_payload)

    # 2. Tenta logar com senha incorreta
    login_payload = {
        "email": "userwrongpwd@fieldops.eval",
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=login_payload)
    assert response.status_code == 401
    error_data = response.json()
    assert error_data["error"]["code"] == "FLX_UNAUTHORIZED"
    assert "Senha incorreta" in error_data["error"]["message"]
