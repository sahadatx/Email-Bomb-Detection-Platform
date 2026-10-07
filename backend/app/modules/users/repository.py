from __future__ import annotations

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.modules.users.models import User, UserRole


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -----------------------------------------------------------------------
    # Lookup
    # -----------------------------------------------------------------------

    def get_by_id(self, user_id: str) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.db.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.scalar(statement)

    def get_by_username(self, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return self.db.scalar(statement)

    # -----------------------------------------------------------------------
    # List
    # -----------------------------------------------------------------------

    def list_users(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
        is_locked: bool | None = None,
    ) -> list[User]:
        statement = select(User)

        if search:
            search_value = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    User.email.ilike(search_value),
                    User.username.ilike(search_value),
                    User.full_name.ilike(search_value),
                )
            )

        if role is not None:
            statement = statement.where(User.role == role)

        if is_active is not None:
            statement = statement.where(User.is_active == is_active)

        if is_locked is not None:
            statement = statement.where(User.is_locked == is_locked)

        statement = (
            statement
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_users(
        self,
        *,
        search: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
        is_locked: bool | None = None,
    ) -> int:
        statement = select(func.count()).select_from(User)

        if search:
            search_value = f"%{search.strip()}%"

            statement = statement.where(
                or_(
                    User.email.ilike(search_value),
                    User.username.ilike(search_value),
                    User.full_name.ilike(search_value),
                )
            )

        if role is not None:
            statement = statement.where(User.role == role)

        if is_active is not None:
            statement = statement.where(User.is_active == is_active)

        if is_locked is not None:
            statement = statement.where(User.is_locked == is_locked)

        return int(self.db.scalar(statement) or 0)

    def summary_counts(self) -> dict[str, int]:
        """Return global account totals, independent of the current list page."""
        row = self.db.execute(
            select(
                func.count(User.id),
                func.sum(case((User.is_active.is_(True) & User.is_locked.is_(False), 1), else_=0)),
                func.sum(case((User.is_active.is_(False), 1), else_=0)),
                func.sum(case((User.is_locked.is_(True), 1), else_=0)),
            )
        ).one()
        return {
            "total": int(row[0] or 0),
            "active": int(row[1] or 0),
            "disabled": int(row[2] or 0),
            "locked": int(row[3] or 0),
        }

    def list_sessions(self, user_id: str):
        from app.modules.users.models import UserSession
        statement = select(UserSession).where(
            UserSession.user_id == user_id
        ).order_by(UserSession.created_at.desc())
        return list(self.db.scalars(statement).all())

    def get_session(self, user_id: str, session_id: str):
        from app.modules.users.models import UserSession
        statement = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.id == session_id,
        )
        return self.db.scalar(statement)

    # -----------------------------------------------------------------------
    # Persistence
    # -----------------------------------------------------------------------

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, user: User) -> None:
        self.db.refresh(user)
