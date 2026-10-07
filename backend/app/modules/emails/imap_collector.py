from __future__ import annotations

import imaplib
import time
from dataclasses import dataclass
from typing import Final


DEFAULT_IMAP_PORT: Final[int] = 993
DEFAULT_TIMEOUT: Final[int] = 30
DEFAULT_RETRIES: Final[int] = 2
DEFAULT_MAILBOX: Final[str] = "INBOX"


class IMAPCollectorError(Exception):
    """Base exception for IMAP collection failures."""


class IMAPConnectionError(IMAPCollectorError):
    """Raised when an IMAP connection or authentication fails."""


class IMAPMailboxError(IMAPCollectorError):
    """Raised when the requested mailbox cannot be selected."""


class IMAPFetchError(IMAPCollectorError):
    """Raised when email messages cannot be fetched."""


@dataclass(frozen=True)
class IMAPCollectionConfig:
    """Configuration required to connect to an IMAP mailbox."""

    server: str
    username: str
    password: str
    port: int = DEFAULT_IMAP_PORT
    mailbox: str = DEFAULT_MAILBOX
    timeout: int = DEFAULT_TIMEOUT
    retries: int = DEFAULT_RETRIES


@dataclass(frozen=True)
class IMAPMessage:
    """Raw email message fetched from an IMAP mailbox."""

    message_id: str
    raw_content: bytes


@dataclass(frozen=True)
class IMAPCollectionResult:
    """Result of an IMAP collection operation."""

    requested: int
    fetched: int
    messages: tuple[IMAPMessage, ...]


class IMAPCollector:
    """
    Collect raw email messages from an IMAP mailbox.

    Responsibilities:
    - Establish secure IMAP connection.
    - Authenticate against the mailbox.
    - Select the requested mailbox.
    - Discover available message IDs.
    - Fetch raw RFC822 messages.
    - Respect collection limits.
    - Retry transient connection/fetch failures.
    - Close the IMAP connection safely.

    Parsing, normalization, feature extraction, and detection are
    intentionally outside this class.
    """

    def __init__(self, config: IMAPCollectionConfig) -> None:
        self.config = config

    def test_connection(self) -> bool:
        """
        Verify that the configured IMAP server can be reached,
        authenticated, and the requested mailbox can be selected.
        """

        mail: imaplib.IMAP4_SSL | None = None

        try:
            mail = self._connect()
            self._select_mailbox(mail)
            return True

        except (IMAPConnectionError, IMAPMailboxError):
            return False

        finally:
            self._close(mail)

    def collect(self, limit: int) -> IMAPCollectionResult:
        """
        Fetch up to ``limit`` messages from the configured mailbox.

        Messages are fetched from newest to oldest.

        A failure affecting one individual message does not prevent
        other messages from being collected.
        """

        if limit < 1:
            raise ValueError("Collection limit must be greater than zero.")

        mail = self._connect()

        try:
            self._select_mailbox(mail)

            message_ids = self._search_messages(mail)

            selected_ids = message_ids[-limit:]
            selected_ids.reverse()

            messages: list[IMAPMessage] = []

            for message_id in selected_ids:
                try:
                    raw_content = self._fetch_message(
                        mail,
                        message_id,
                    )

                    messages.append(
                        IMAPMessage(
                            message_id=message_id,
                            raw_content=raw_content,
                        )
                    )

                except IMAPFetchError:
                    # One malformed/unavailable message should not
                    # terminate the complete collection operation.
                    continue

            return IMAPCollectionResult(
                requested=len(selected_ids),
                fetched=len(messages),
                messages=tuple(messages),
            )

        finally:
            self._close(mail)

    def _connect(self) -> imaplib.IMAP4_SSL:
        """
        Establish and authenticate an SSL-protected IMAP connection.
        """

        last_error: Exception | None = None

        for attempt in range(self.config.retries + 1):
            try:
                mail = imaplib.IMAP4_SSL(
                    host=self.config.server,
                    port=self.config.port,
                    timeout=self.config.timeout,
                )

                status, response = mail.login(
                    self.config.username,
                    self.config.password,
                )

                if status != "OK":
                    self._close(mail)

                    raise IMAPConnectionError(
                        self._format_response(
                            "IMAP authentication failed",
                            response,
                        )
                    )

                return mail

            except (
                OSError,
                imaplib.IMAP4.error,
                IMAPCollectorError,
            ) as exc:
                last_error = exc

                if attempt < self.config.retries:
                    time.sleep(
                        0.5 * (attempt + 1)
                    )
                    continue

                break

        detail = (
            str(last_error)
            if last_error is not None
            else "Unknown connection error"
        )

        raise IMAPConnectionError(
            f"Unable to connect or authenticate with "
            f"IMAP server '{self.config.server}': {detail}"
        ) from last_error

    def _select_mailbox(
        self,
        mail: imaplib.IMAP4_SSL,
    ) -> None:
        """Select the configured mailbox."""

        try:
            status, response = mail.select(
                mailbox=self.config.mailbox,
                readonly=True,
            )

        except imaplib.IMAP4.error as exc:
            raise IMAPMailboxError(
                f"Unable to select mailbox '{self.config.mailbox}'."
            ) from exc

        if status != "OK":
            raise IMAPMailboxError(
                self._format_response(
                    f"Unable to select mailbox '{self.config.mailbox}'",
                    response,
                )
            )

    @staticmethod
    def _search_messages(
        mail: imaplib.IMAP4_SSL,
    ) -> list[str]:
        """Return message IDs available in the selected mailbox."""

        try:
            status, response = mail.search(None, "ALL")

        except imaplib.IMAP4.error as exc:
            raise IMAPFetchError(
                "Unable to search messages in the mailbox."
            ) from exc

        if status != "OK" or not response:
            raise IMAPFetchError(
                "Unable to search messages in the mailbox."
            )

        raw_ids = response[0]

        if not raw_ids:
            return []

        return raw_ids.decode("ascii", errors="ignore").split()

    @staticmethod
    def _fetch_message(
        mail: imaplib.IMAP4_SSL,
        message_id: str,
    ) -> bytes:
        """Fetch one message as raw RFC822 bytes."""

        try:
            status, response = mail.fetch(
                message_id,
                "(RFC822)",
            )

        except imaplib.IMAP4.error as exc:
            raise IMAPFetchError(
                f"Unable to fetch message '{message_id}'."
            ) from exc

        if status != "OK":
            raise IMAPFetchError(
                f"Unable to fetch message '{message_id}'."
            )

        for item in response:
            if (
                isinstance(item, tuple)
                and len(item) >= 2
                and isinstance(item[1], bytes)
            ):
                return item[1]

        raise IMAPFetchError(
            f"No RFC822 content was returned for message '{message_id}'."
        )

    @staticmethod
    def _format_response(
        message: str,
        response: object,
    ) -> str:
        """Create a safe error message without exposing credentials."""

        if not response:
            return message

        return f"{message}: {response!r}"

    @staticmethod
    def _close(
        mail: imaplib.IMAP4_SSL | None,
    ) -> None:
        """Safely close and logout from an IMAP connection."""

        if mail is None:
            return

        try:
            try:
                mail.close()
            except (imaplib.IMAP4.error, OSError):
                pass

            try:
                mail.logout()
            except (imaplib.IMAP4.error, OSError):
                pass

        except Exception:
            # Cleanup must never hide the original collection error.
            pass