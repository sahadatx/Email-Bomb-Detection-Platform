from __future__ import annotations

from datetime import datetime, timezone

from app.core.exceptions import (
    ConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.security import PasswordPolicyError, hash_password, validate_password_strength
from app.modules.users.models import User, UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import (
    ChangePasswordRequest,
    ChangeRoleRequest,
    CreateUserRequest,
    ForcePasswordChangeRequest,
    ResetPasswordRequest,
    UpdateUserRequest,
    UserDetailResponse,
    UserListResponse,
    UserListParams,
    UserSummaryResponse,
)


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    # -----------------------------------------------------------------------
    # List / details
    # -----------------------------------------------------------------------

    def list_users(
        self,
        params: UserListParams,
    ) -> UserListResponse:
        total = self.repository.count_users(
            search=params.search,
            role=params.role,
            is_active=params.is_active,
            is_locked=params.is_locked,
        )

        users = self.repository.list_users(
            offset=params.offset,
            limit=params.page_size,
            search=params.search,
            role=params.role,
            is_active=params.is_active,
            is_locked=params.is_locked,
        )

        pages = (
            (total + params.page_size - 1) // params.page_size
            if total
            else 0
        )

        return UserListResponse(
            items=[
                UserSummaryResponse.model_validate(user)
                for user in users
            ],
            page=params.page,
            page_size=params.page_size,
            total=total,
            pages=pages,
        )

    def summary(self) -> dict[str, int]:
        """Expose database-wide user counts for the management dashboard."""
        return self.repository.summary_counts()

    def list_sessions(self, user_id: str):
        self.get_user(user_id)
        return self.repository.list_sessions(user_id)

    def revoke_session(self, user_id: str, session_id: str) -> None:
        from datetime import datetime, timezone
        from app.core.exceptions import ResourceNotFoundError
        session = self.repository.get_session(user_id, session_id)
        if session is None:
            raise ResourceNotFoundError("Session was not found.")
        if session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            self.repository.commit()

    def revoke_all_sessions(self, user_id: str) -> int:
        from datetime import datetime, timezone
        sessions = self.repository.list_sessions(user_id)
        now = datetime.now(timezone.utc)
        count = 0
        for session in sessions:
            if session.revoked_at is None:
                session.revoked_at = now
                count += 1
        self.repository.commit()
        return count

    def get_user(self, user_id: str) -> User:
        user = self.repository.get_by_id(user_id)

        if user is None:
            raise ResourceNotFoundError(
                "User was not found."
            )

        return user

    # -----------------------------------------------------------------------
    # Create
    # -----------------------------------------------------------------------

    def create_user(
        self,
        payload: CreateUserRequest,
    ) -> User:
        email = str(payload.email).strip().lower()
        username = payload.username.strip()
        full_name = payload.full_name.strip()

        if self.repository.get_by_email(email) is not None:
            raise ConflictError(
                "A user with this email already exists."
            )

        if self.repository.get_by_username(username) is not None:
            raise ConflictError(
                "A user with this username already exists."
            )

        try:
            validate_password_strength(payload.password)
        except PasswordPolicyError as exc:
            raise ValidationError(str(exc)) from exc

        user = User(
            email=email,
            username=username,
            full_name=full_name,
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_active=payload.is_active,
            is_locked=False,
            force_password_change=payload.force_password_change,
            failed_login_attempts=0,
        )

        self.repository.create(user)
        self.repository.commit()
        self.repository.refresh(user)

        return user

    # -----------------------------------------------------------------------
    # Update
    # -----------------------------------------------------------------------

    def update_user(
        self,
        *,
        user_id: str,
        payload: UpdateUserRequest,
    ) -> User:
        user = self.get_user(user_id)

        if payload.email is not None:
            email = str(payload.email).strip().lower()

            existing = self.repository.get_by_email(email)

            if existing is not None and existing.id != user.id:
                raise ConflictError(
                    "A user with this email already exists."
                )

            user.email = email

        if payload.username is not None:
            username = payload.username.strip()

            existing = self.repository.get_by_username(username)

            if existing is not None and existing.id != user.id:
                raise ConflictError(
                    "A user with this username already exists."
                )

            user.username = username

        if payload.full_name is not None:
            user.full_name = payload.full_name.strip()

        self.repository.commit()
        self.repository.refresh(user)

        return user

    # -----------------------------------------------------------------------
    # Enable / disable
    # -----------------------------------------------------------------------

    def enable_user(self, user_id: str) -> User:
        user = self.get_user(user_id)

        user.is_active = True

        self.repository.commit()
        self.repository.refresh(user)

        return user

    def disable_user(
        self,
        *,
        user_id: str,
        acting_user_id: str,
    ) -> User:
        if user_id == acting_user_id:
            raise ValidationError(
                "You cannot disable your own account."
            )

        user = self.get_user(user_id)

        user.is_active = False

        self.repository.commit()
        self.repository.refresh(user)

        return user

    # -----------------------------------------------------------------------
    # Lock / unlock
    # -----------------------------------------------------------------------

    def lock_user(
        self,
        *,
        user_id: str,
        acting_user_id: str,
    ) -> User:
        if user_id == acting_user_id:
            raise ValidationError(
                "You cannot lock your own account."
            )

        user = self.get_user(user_id)

        user.is_locked = True
        user.locked_at = datetime.now(timezone.utc)

        self.repository.commit()
        self.repository.refresh(user)

        return user

    def unlock_user(self, user_id: str) -> User:
        user = self.get_user(user_id)

        user.is_locked = False
        user.locked_at = None
        user.failed_login_attempts = 0

        self.repository.commit()
        self.repository.refresh(user)

        return user

    # -----------------------------------------------------------------------
    # Role
    # -----------------------------------------------------------------------

    def change_role(
        self,
        *,
        user_id: str,
        payload: ChangeRoleRequest,
    ) -> User:
        user = self.get_user(user_id)

        user.role = payload.role

        self.repository.commit()
        self.repository.refresh(user)

        return user

    # -----------------------------------------------------------------------
    # Password administration
    # -----------------------------------------------------------------------

    def reset_password(
        self,
        *,
        user_id: str,
        payload: ResetPasswordRequest,
    ) -> User:
        user = self.get_user(user_id)

        try:
            validate_password_strength(payload.new_password)
        except PasswordPolicyError as exc:
            raise ValidationError(str(exc)) from exc

        user.password_hash = hash_password(payload.new_password)
        user.force_password_change = True
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_at = None

        self.repository.commit()
        self.repository.refresh(user)

        return user

    def set_force_password_change(
        self,
        *,
        user_id: str,
        payload: ForcePasswordChangeRequest,
    ) -> User:
        user = self.get_user(user_id)

        user.force_password_change = payload.force_password_change

        self.repository.commit()
        self.repository.refresh(user)

        return user

    # -----------------------------------------------------------------------
    # Self-service password
    # -----------------------------------------------------------------------

    def change_own_password(
        self,
        *,
        user: User,
        payload: ChangePasswordRequest,
    ) -> User:
        from app.core.security import verify_password

        if not verify_password(
            payload.current_password,
            user.password_hash,
        ):
            raise ValidationError(
                "Current password is incorrect."
            )

        if payload.current_password == payload.new_password:
            raise ValidationError(
                "New password must be different from the current password."
            )

        try:
            validate_password_strength(payload.new_password)
        except PasswordPolicyError as exc:
            raise ValidationError(str(exc)) from exc

        user.password_hash = hash_password(payload.new_password)
        user.force_password_change = False
        user.failed_login_attempts = 0

        self.repository.commit()
        self.repository.refresh(user)

        return user

    # -----------------------------------------------------------------------
    # Response helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def to_summary_response(user: User) -> UserSummaryResponse:
        return UserSummaryResponse.model_validate(user)

    @staticmethod
    def to_detail_response(user: User) -> UserDetailResponse:
        return UserDetailResponse.model_validate(user)
