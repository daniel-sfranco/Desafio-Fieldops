import sys
from pathlib import Path

# Garante que o diretório 'src' esteja no PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.database import engine, base, sessionLocal
from utils.security import get_password_hash
from models.Usuario import Usuario
from models.OS import OS
from models.Checklist import Checklist
from models.Auditoria import Auditoria
from models.enums.UsuarioRole import UsuarioRole
from models.enums.Status import Status
from models.enums.Priority import Priority


def seed_database(reset: bool = True):
    if reset:
        print("🗑️ Apagando tabelas antigas e resolvendo conflitos de schema...")
        try:
            base.metadata.drop_all(bind=engine)
            print("  [✓] Tabelas antigas removidas com sucesso.")
        except Exception as e:
            print(f"  [!] Aviso ao apagar tabelas: {e}")

    print("🌱 Criando tabelas limpas no banco de dados...")
    base.metadata.create_all(bind=engine)

    db = sessionLocal()
    try:
        # 1. Usuários Obrigatórios (Seed especificado no desafio)
        users_data = [
            {
                "email": "tech-a@fieldops.eval",
                "password": get_password_hash("password123"),
                "name": "Técnico Alpha",
                "role": UsuarioRole.TECHNICIAN,
                "teamId": "team-alpha",
            },
            {
                "email": "tech-b@fieldops.eval",
                "password": get_password_hash("password123"),
                "name": "Técnico Beta",
                "role": UsuarioRole.TECHNICIAN,
                "teamId": "team-beta",
            },
            {
                "email": "supervisor-a@fieldops.eval",
                "password": get_password_hash("password123"),
                "name": "Supervisor Alpha",
                "role": UsuarioRole.SUPERVISOR,
                "teamId": "team-alpha",
            },
            {
                "email": "admin@fieldops.eval",
                "password": get_password_hash("password123"),
                "name": "Administrador Sistema",
                "role": UsuarioRole.ADMIN,
                "teamId": None,
            },
        ]

        created_users = {}
        for u in users_data:
            user = Usuario(
                email=u["email"],
                password=u["password"],
                name=u["name"],
                teamId=u["teamId"],
                role=u["role"],
            )
            db.add(user)
            db.flush()
            created_users[u["email"]] = user
            print(f"  [+] Usuário criado: {u['email']} ({u['role'].value})")

        db.commit()

        # 2. Ordens de Serviço Fictícias para Testes no Postman
        tech_a = created_users["tech-a@fieldops.eval"]
        tech_b = created_users["tech-b@fieldops.eval"]
        sup_a = created_users["supervisor-a@fieldops.eval"]

        # OS 1: Aberta, baixa prioridade (Team Alpha)
        os1 = OS(
            title="Manutenção Preventiva - Ar Condicionado Servidor",
            description="Troca de filtros HEPA e verificação de nível de gás refrigerante no rack principal.",
            status=Status.OPEN,
            priority=Priority.LOW,
            assigneeId=tech_a.id,
            teamId="team-alpha",
            version=1,
        )
        os1.checkList.append(Checklist(label="Desligar a alimentação da unidade de ar", completed=False))
        os1.checkList.append(Checklist(label="Limpar a calha de condensação", completed=False))
        os1.checkList.append(Checklist(label="Medir pressão de gás refrigerante", completed=False))
        db.add(os1)

        # OS 2: Em andamento, ALTA prioridade (Team Alpha)
        os2 = OS(
            title="Reparo Urgente - Nobreak do Data Center",
            description="Bateria B2 apresentando queda brusca de tensão durante teste de carga.",
            status=Status.IN_PROGRESS,
            priority=Priority.HIGH,
            assigneeId=tech_a.id,
            teamId="team-alpha",
            version=2,
        )
        os2.checkList.append(Checklist(label="Isolar o módulo de bateria B2", completed=True))
        os2.checkList.append(Checklist(label="Instalar bateria sobressalente de 12V 45Ah", completed=False))
        os2.checkList.append(Checklist(label="Realizar teste de autonomia de 15 min", completed=False))
        os2.auditList.append(Auditoria(actorId=sup_a.id, fromStatus=Status.OPEN, toStatus=Status.IN_PROGRESS))
        db.add(os2)

        # OS 3: Concluída (Team Alpha)
        os3 = OS(
            title="Substituição de Cordão Óptico no Patch Panel 32",
            description="Troca de cordão óptico no patch panel 32 do rack B.",
            status=Status.DONE,
            priority=Priority.LOW,
            resolutionNotes="Cordão óptico substituído e fusão validada com OTDR. Sinal restaurado dentro do padrão.",
            assigneeId=tech_a.id,
            teamId="team-alpha",
            version=3,
        )
        os3.checkList.append(Checklist(label="Inspecionar conector LC/UPC com microscópio", completed=True))
        os3.checkList.append(Checklist(label="Efetuar fusão de fibra de 50 microns", completed=True))
        os3.auditList.append(Auditoria(actorId=tech_a.id, fromStatus=Status.OPEN, toStatus=Status.IN_PROGRESS))
        os3.auditList.append(Auditoria(actorId=tech_a.id, fromStatus=Status.IN_PROGRESS, toStatus=Status.DONE))
        db.add(os3)

        # OS 4: Aberta, baixa prioridade (Team Beta)
        os4 = OS(
            title="Inspeção nos Painéis Solares da Subestação",
            description="Verificação térmica de pontos quentes na string #4.",
            status=Status.OPEN,
            priority=Priority.LOW,
            assigneeId=tech_b.id,
            teamId="team-beta",
            version=1,
        )
        os4.checkList.append(Checklist(label="Mapeamento com câmera termográfica", completed=False))
        os4.checkList.append(Checklist(label="Reaperto de conectores MC4", completed=False))
        db.add(os4)

        # OS 5: Em andamento (Team Beta)
        os5 = OS(
            title="Calibração de Sensores de Pressão da Válvula 4B",
            description="Ajuste do transdutor 4-20mA no duto principal.",
            status=Status.IN_PROGRESS,
            priority=Priority.LOW,
            assigneeId=tech_b.id,
            teamId="team-beta",
            version=2,
        )
        os5.checkList.append(Checklist(label="Coletar amostra de pressão zero", completed=True))
        os5.checkList.append(Checklist(label="Ajustar span para 10 bar", completed=False))
        os5.auditList.append(Auditoria(actorId=tech_b.id, fromStatus=Status.OPEN, toStatus=Status.IN_PROGRESS))
        db.add(os5)

        db.commit()
        print("  [+] Banco de dados recriado do zero com 5 Ordens de Serviço fictícias!")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao povoar o banco: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(reset=True)
