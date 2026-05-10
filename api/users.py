from datetime import timedelta
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordRequestForm

from core.auth import authenticate_user, create_access_token, get_current_user
from core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from schemas.users import Token, User, UserPublic

token_router = APIRouter(
    prefix="/token",
    tags=["auth"],
)


@token_router.post("/")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    При успешной аутентификации возвращает токен, содержащий роль пользователя в качестве scope.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Определяем scopes по роли (если роли нет – пустой список)
    scopes = []
    if user.role:
        scopes.append(user.role.name)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.user_name}, expires_delta=access_token_expires, scopes=scopes
    )
    return Token(access_token=access_token, token_type="bearer")


users_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@users_router.get("/me/", response_model=UserPublic)
async def read_users_me(
        current_user: Annotated[User, Security(get_current_user, scopes=[])]  # любой аутентифицированный
) -> UserPublic:
    """Возвращает информацию о текущем пользователе."""
    return current_user


# Пример admin-ручки – просмотр всех пользователей
@users_router.get("/", response_model=List[UserPublic])
async def read_all_users(
        current_user: Annotated[User, Security(get_current_user, scopes=["admin"])],
) -> List[UserPublic]:
    """Только для администраторов."""
    from core.database import get_session
    from sqlmodel import select
    with next(get_session()) as session:
        users = session.exec(select(User)).all()
    return users
