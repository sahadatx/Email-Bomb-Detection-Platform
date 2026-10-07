from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.models import User, UserSession


class AuthRepository:
    """Database operations used by the authentication service."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.scalar(statement)

    def get_user_by_id(self, user_id: str) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.db.scalar(statement)

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def create_session(
        self,
        *,
        user_id: str,
        token_jti: str,
        ip_address: str | None,
        user_agent: str | None,
        expires_at: datetime,
    ) -> UserSession:
        session = UserSession(
            user_id=user_id,
            token_jti=token_jti,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        self.db.add(session)
        self.db.flush()

        return session

    def get_session_by_jti(self, token_jti: str) -> UserSession | None:
        statement = select(UserSession).where(
            UserSession.token_jti == token_jti
        )
        return self.db.scalar(statement)

    def get_session_by_id(
        self,
        *,
        session_id: str,
        user_id: str,
    ) -> UserSession | None:
        statement = select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
        return self.db.scalar(statement)

    def list_user_sessions(
        self,
        *,
        user_id: str,
    ) -> list[UserSession]:
        statement = (
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.created_at.desc())
        )

        return list(self.db.scalars(statement).all())

    def revoke_session(
        self,
        session: UserSession,
        *,
        revoked_at: datetime,
    ) -> UserSession:
        session.revoked_at = revoked_at
        self.db.flush()

        return session

    def revoke_all_user_sessions(
        self,
        *,
        user_id: str,
        revoked_at: datetime,
    ) -> int:
        sessions = self.list_user_sessions(user_id=user_id)

        count = 0

        for session in sessions:
            if session.revoked_at is None:
                session.revoked_at = revoked_at
                count += 1

        self.db.flush()

        return count

    # ------------------------------------------------------------------
    # Transaction
    # ------------------------------------------------------------------

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)