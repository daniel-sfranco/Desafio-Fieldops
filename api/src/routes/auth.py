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


def validate_existing_email(user_email: str, db: Session, wanted: bool):
    user = db.scalar(select(Usuario).where(Usuario.email == user_email))
    if wanted and user is None:
        raise FlxException(
            code="FLX_UNAUTHORIZED",
            message="Esse email não está em uso.",
            status_code=401
        )
    if not wanted and user is not None:
        raise FlxException(
            code="FLX_UNAUTHORIZED",
            message="Esse email já está em uso.",
            status_code=401
        )
    return user


def validate_non_admin_team(user: RegisterRequest):
    if user.role != UsuarioRole.ADMIN and not user.teamId:
        raise FlxException(
            code="FLX_VALIDATION_ERROR",
            message="Esse usuário precisa cadastrar um time.",
            status_code=422
        )


def validate_correct_password(plain_password: str, hashed_password: str):
    if not security.verify_password(plain_password, hashed_password):
        raise FlxException(
            code="FLX_UNAUTHORIZED",
            message="Senha incorreta.",
            status_code=401
        )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user: RegisterRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    validate_existing_email(user.email, db, False)
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
    user = validate_existing_email(data.email, db, True)
    validate_correct_password(data.password, user.password)

    token = security.create_access_token({
        "sub": str(user.id),
        "role": user.role,
        "teamId": user.teamId
    })
    return TokenResponse(access_token=token)
