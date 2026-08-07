from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from models.enums.UsuarioRole import UsuarioRole
from utils import security
from utils.database import get_db
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from models.Usuario import Usuario
from utils.exceptions import FlxException

router = APIRouter(
    prefix="/auth",
    tags=["Auth Module"]
)


def validate_existing_email(user, db, wanted):
    email_query = select(Usuario.email)
    emails = db.execute(email_query).scalars().all()
    email_error = (
        (user.email in emails and not wanted) or
        (user.email not in emails and wanted)
    )
    if email_error:
        keyword = "não" if wanted else "já"
        raise FlxException(
            code="FLX_UNAUTHORIZED",
            message=f"Esse email {keyword} está em uso.",
            status_code=401
        )


def validate_non_admin_team(user):
    if user.role != UsuarioRole.ADMIN and user.teamId is None:
        raise FlxException(
            code="FLX_VALIDATION_ERROR",
            message="Esse usuário precisa cadastrar um time.",
            status_code=400
        )


def validate_correct_password(data, db, user):
    if not security.verify_password(data.password, user.password):
        raise FlxException(
            code="FLX_UNAUTHORIZED",
            message="Senha incorreta.",
            status_code=401
        )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user: RegisterRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    validate_existing_email(user, db, False)
    validate_non_admin_team(user)

    new_user = Usuario(
        email=user.email,
        password=security.get_password_hash(user.password),
        name=user.name,
        teamId=user.teamId,
        role=user.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = security.create_access_token({
        "sub": str(new_user.id),
        "role": new_user.role,
        "teamId": new_user.teamId
    })
    return TokenResponse(access_token=token)


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    data: LoginRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    validate_existing_email(data, db, True)

    user_query = select(Usuario).where(Usuario.email == data.email)
    user = db.execute(user_query).scalars().first()

    validate_correct_password(data, db, user)

    token = security.create_access_token({
        "sub": str(user.id),
        "role": user.role,
        "teamId": user.teamId
    })
    return TokenResponse(access_token=token)
