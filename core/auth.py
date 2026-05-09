from datetime import timedelta, datetime, timezone
from typing import Annotated, List, Optional

import jwt
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlmodel import select

from core.config import SECRET_KEY, ALGORITHM, SCOPES
from core.database import get_session
from schemas.users import TokenData, User, UserPublic, UserPublicWithRole

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("dummypassword")

# Схема с поддержкой scopes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scopes=SCOPES)


def verify_password(plain_password, hashed_password) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    return password_hash.hash(password)


def get_user(username: str | None) -> User | None:
    if username is None:
        return None
    with next(get_session()) as session:
        user = session.exec(select(User).where(User.user_name == username)).first()
    return user


def authenticate_user(username: str, password: str) -> UserPublicWithRole | None:
    user = get_user(username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    with next(get_session()) as session:
        user_with_role: UserPublicWithRole = session.get(User, user.id)
        _ = user_with_role.role.name
    return user_with_role


def create_access_token(data: dict, expires_delta: timedelta | None = None, scopes: List[str] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    # Сохраняем scopes как строку через пробел (стандарт JWT scope)
    if scopes:
        to_encode["scope"] = " ".join(scopes)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserPublic:
    """
    Проверяет токен и требуемые права (scopes).
    Для доступа достаточно иметь **любой** из запрошенных scopes.
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scope", "").split()
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    # Проверка прав: нужен хотя бы один scope из запрошенных
    if security_scopes.scopes and not any(scope in token_scopes for scope in security_scopes.scopes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
            headers={"WWW-Authenticate": authenticate_value},
        )

    # Загружаем пользователя
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception

    return user
