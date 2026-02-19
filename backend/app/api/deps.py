"""FastAPI dependencies: database session, authentication, authorization."""

from collections.abc import AsyncGenerator, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session

security = HTTPBearer()


class UserClaims(BaseModel):
    """JWT token claims representing the authenticated user."""

    sub: str
    email: str = ""
    name: str = ""
    role: str = "fournisseur"
    realm_access: dict | None = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session.

    Used as a FastAPI dependency to inject DB sessions into route handlers.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
) -> UserClaims:
    """Decode and validate the JWT bearer token.

    Args:
        token: The HTTP Bearer token from the Authorization header.

    Returns:
        Decoded user claims.

    Raises:
        HTTPException: 401 if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},
        )
        return UserClaims(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*roles: str) -> Callable:
    """Factory that creates a dependency enforcing role-based access.

    Args:
        roles: Allowed role names (e.g. "admin", "rssi").

    Returns:
        A FastAPI dependency function that validates the user's role.
    """
    async def role_checker(
        user: UserClaims = Depends(get_current_user),
    ) -> UserClaims:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    return role_checker
