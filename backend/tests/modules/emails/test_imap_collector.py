from __future__ import annotations

import imaplib
from unittest.mock import MagicMock, patch

import pytest

from app.modules.emails.imap_collector import (
    IMAPCollectionConfig,
    IMAPCollector,
    IMAPConnectionError,
    IMAPFetchError,
    IMAPMailboxError,
)


@pytest.fixture
def config() -> IMAPCollectionConfig:
    return IMAPCollectionConfig(
        server="imap.example.com",
        username="analyst@example.com",
        password="SecretPassword123!",
        mailbox="INBOX",
        retries=2,
        timeout=30,
    )


@pytest.fixture
def collector(config: IMAPCollectionConfig) -> IMAPCollector:
    return IMAPCollector(config)


# ---------------------------------------------------------------------------
# Connection Tests
# ---------------------------------------------------------------------------


def test_test_connection_success(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()
    mail.login.return_value = ("OK", [b"Logged in"])
    mail.select.return_value = ("OK", [b"10"])

    with patch(
        "app.modules.emails.imap_collector.imaplib.IMAP4_SSL",
        return_value=mail,
    ) as imap_mock:
        assert collector.test_connection() is True

    imap_mock.assert_called_once_with(
        host="imap.example.com",
        port=993,
        timeout=30,
    )

    mail.login.assert_called_once_with(
        "analyst@example.com",
        "SecretPassword123!",
    )

    mail.select.assert_called_once_with(
        mailbox="INBOX",
        readonly=True,
    )

    mail.close.assert_called_once()
    mail.logout.assert_called_once()


def test_test_connection_returns_false_when_authentication_fails(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()
    mail.login.return_value = ("NO", [b"Authentication failed"])

    with patch(
        "app.modules.emails.imap_collector.imaplib.IMAP4_SSL",
        return_value=mail,
    ) as imap_mock:
        assert collector.test_connection() is False

    # retries=2 means:
    # initial attempt + 2 retries = 3 connection attempts.
    assert imap_mock.call_count == 3
    assert mail.login.call_count == 3

    for call in mail.login.call_args_list:
        assert call.args == (
            "analyst@example.com",
            "SecretPassword123!",
        )


def test_test_connection_returns_false_when_mailbox_selection_fails(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()
    mail.login.return_value = ("OK", [b"Logged in"])
    mail.select.return_value = ("NO", [b"Mailbox unavailable"])

    with patch(
        "app.modules.emails.imap_collector.imaplib.IMAP4_SSL",
        return_value=mail,
    ):
        assert collector.test_connection() is False

    mail.login.assert_called_once_with(
        "analyst@example.com",
        "SecretPassword123!",
    )

    mail.select.assert_called_once_with(
        mailbox="INBOX",
        readonly=True,
    )

    mail.close.assert_called_once()
    mail.logout.assert_called_once()


def test_connect_retries_after_transient_connection_failure(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()
    mail.login.return_value = ("OK", [b"Logged in"])

    with patch(
        "app.modules.emails.imap_collector.imaplib.IMAP4_SSL",
        side_effect=[
            OSError("temporary failure"),
            mail,
        ],
    ) as imap_mock, patch(
        "app.modules.emails.imap_collector.time.sleep",
    ) as sleep_mock:
        connected = collector._connect()

    assert connected is mail

    assert imap_mock.call_count == 2
    sleep_mock.assert_called_once_with(0.5)

    mail.login.assert_called_once_with(
        "analyst@example.com",
        "SecretPassword123!",
    )


def test_connect_raises_after_all_retries_fail(
    collector: IMAPCollector,
) -> None:
    with patch(
        "app.modules.emails.imap_collector.imaplib.IMAP4_SSL",
        side_effect=OSError("connection failed"),
    ) as imap_mock, patch(
        "app.modules.emails.imap_collector.time.sleep",
    ) as sleep_mock:
        with pytest.raises(
            IMAPConnectionError,
            match="Unable to connect or authenticate",
        ):
            collector._connect()

    # retries=2:
    # 1 initial attempt + 2 retries = 3 attempts.
    assert imap_mock.call_count == 3
    assert sleep_mock.call_count == 2


# ---------------------------------------------------------------------------
# Mailbox Tests
# ---------------------------------------------------------------------------


def test_select_mailbox_success(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()
    mail.select.return_value = ("OK", [b"10"])

    collector._select_mailbox(mail)

    mail.select.assert_called_once_with(
        mailbox="INBOX",
        readonly=True,
    )


def test_select_mailbox_raises_for_imap_error(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()
    mail.select.side_effect = imaplib.IMAP4.error(
        "Mailbox error",
    )

    with pytest.raises(IMAPMailboxError):
        collector._select_mailbox(mail)


def test_select_mailbox_raises_when_server_returns_failure(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()
    mail.select.return_value = (
        "NO",
        [b"Mailbox unavailable"],
    )

    with pytest.raises(
        IMAPMailboxError,
        match="Unable to select mailbox",
    ):
        collector._select_mailbox(mail)


# ---------------------------------------------------------------------------
# Message Search Tests
# ---------------------------------------------------------------------------


def test_search_messages_returns_message_ids(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()
    mail.search.return_value = (
        "OK",
        [b"10 20 30"],
    )

    result = collector._search_messages(mail)

    assert result == [
        "10",
        "20",
        "30",
    ]

    mail.search.assert_called_once_with(
        None,
        "ALL",
    )


def test_search_messages_returns_empty_list_for_empty_mailbox(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()
    mail.search.return_value = (
        "OK",
        [b""],
    )

    result = collector._search_messages(mail)

    assert result == []


def test_search_messages_raises_for_failed_search(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()
    mail.search.return_value = (
        "NO",
        [b"Search failed"],
    )

    with pytest.raises(IMAPFetchError):
        collector._search_messages(mail)


def test_search_messages_raises_for_imap_error(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()
    mail.search.side_effect = imaplib.IMAP4.error(
        "Search failed",
    )

    with pytest.raises(IMAPFetchError):
        collector._search_messages(mail)


# ---------------------------------------------------------------------------
# Message Fetch Tests
# ---------------------------------------------------------------------------


def test_fetch_message_returns_rfc822_content(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()

    raw_email = (
        b"From: sender@example.com\r\n"
        b"Subject: Test\r\n"
        b"\r\n"
        b"Hello"
    )

    mail.fetch.return_value = (
        "OK",
        [
            (
                b"1 (RFC822 {45})",
                raw_email,
            ),
        ],
    )

    result = collector._fetch_message(
        mail,
        "42",
    )

    assert result == raw_email

    mail.fetch.assert_called_once_with(
        "42",
        "(RFC822)",
    )


def test_fetch_message_raises_when_server_returns_failure(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()

    mail.fetch.return_value = (
        "NO",
        [b"Fetch failed"],
    )

    with pytest.raises(
        IMAPFetchError,
        match="Unable to fetch message",
    ):
        collector._fetch_message(
            mail,
            "42",
        )


def test_fetch_message_raises_when_imap_error_occurs(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()

    mail.fetch.side_effect = imaplib.IMAP4.error(
        "Fetch failed",
    )

    with pytest.raises(IMAPFetchError):
        collector._fetch_message(
            mail,
            "42",
        )


def test_fetch_message_raises_when_rfc822_content_is_missing(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()

    mail.fetch.return_value = (
        "OK",
        [
            b"1 (FLAGS ())",
        ],
    )

    with pytest.raises(
        IMAPFetchError,
        match="No RFC822 content",
    ):
        collector._fetch_message(
            mail,
            "42",
        )


# ---------------------------------------------------------------------------
# Collection Tests
# ---------------------------------------------------------------------------


def test_collect_returns_newest_messages_first(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()

    mail.login.return_value = (
        "OK",
        [b"Logged in"],
    )

    mail.select.return_value = (
        "OK",
        [b"5"],
    )

    mail.search.return_value = (
        "OK",
        [b"1 2 3 4 5"],
    )

    def fetch_message(
        message_id: str,
        _: str,
    ) -> tuple[str, list[tuple[bytes, bytes]]]:
        return (
            "OK",
            [
                (
                    b"RFC822",
                    (
                        f"Subject: Test {message_id}\r\n\r\n"
                        "Body"
                    ).encode(),
                ),
            ],
        )

    mail.fetch.side_effect = fetch_message

    with patch(
        "app.modules.emails.imap_collector.imaplib.IMAP4_SSL",
        return_value=mail,
    ):
        result = collector.collect(limit=3)

    assert result.requested == 3
    assert result.fetched == 3

    assert [
        message.message_id
        for message in result.messages
    ] == [
        "5",
        "4",
        "3",
    ]

    assert mail.fetch.call_count == 3

    mail.close.assert_called_once()
    mail.logout.assert_called_once()


def test_collect_respects_limit_when_fewer_messages_exist(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()

    mail.login.return_value = (
        "OK",
        [b"Logged in"],
    )

    mail.select.return_value = (
        "OK",
        [b"2"],
    )

    mail.search.return_value = (
        "OK",
        [b"1 2"],
    )

    mail.fetch.side_effect = [
        (
            "OK",
            [(b"RFC822", b"Message 2")],
        ),
        (
            "OK",
            [(b"RFC822", b"Message 1")],
        ),
    ]

    with patch(
        "app.modules.emails.imap_collector.imaplib.IMAP4_SSL",
        return_value=mail,
    ):
        result = collector.collect(limit=10)

    assert result.requested == 2
    assert result.fetched == 2
    assert len(result.messages) == 2

    mail.fetch.assert_any_call(
        "2",
        "(RFC822)",
    )

    mail.fetch.assert_any_call(
        "1",
        "(RFC822)",
    )


def test_collect_returns_empty_result_for_empty_mailbox(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()

    mail.login.return_value = (
        "OK",
        [b"Logged in"],
    )

    mail.select.return_value = (
        "OK",
        [b"0"],
    )

    mail.search.return_value = (
        "OK",
        [b""],
    )

    with patch(
        "app.modules.emails.imap_collector.imaplib.IMAP4_SSL",
        return_value=mail,
    ):
        result = collector.collect(limit=10)

    assert result.requested == 0
    assert result.fetched == 0
    assert result.messages == ()

    mail.fetch.assert_not_called()


def test_collect_skips_failed_individual_message(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()

    mail.login.return_value = (
        "OK",
        [b"Logged in"],
    )

    mail.select.return_value = (
        "OK",
        [b"3"],
    )

    mail.search.return_value = (
        "OK",
        [b"1 2 3"],
    )

    mail.fetch.side_effect = [
        (
            "OK",
            [(b"RFC822", b"Message 3")],
        ),
        (
            "NO",
            [b"Fetch failed"],
        ),
        (
            "OK",
            [(b"RFC822", b"Message 1")],
        ),
    ]

    with patch(
        "app.modules.emails.imap_collector.imaplib.IMAP4_SSL",
        return_value=mail,
    ):
        result = collector.collect(limit=3)

    assert result.requested == 3
    assert result.fetched == 2

    assert [
        message.message_id
        for message in result.messages
    ] == [
        "3",
        "1",
    ]

    assert mail.fetch.call_count == 3


def test_collect_rejects_invalid_limit(
    collector: IMAPCollector,
) -> None:
    with pytest.raises(
        ValueError,
        match="Collection limit must be greater than zero",
    ):
        collector.collect(0)


def test_collect_closes_connection_when_collection_fails(
    collector: IMAPCollector,
) -> None:
    mail = MagicMock()

    mail.login.return_value = (
        "OK",
        [b"Logged in"],
    )

    mail.select.return_value = (
        "OK",
        [b"5"],
    )

    mail.search.return_value = (
        "NO",
        [b"Search failed"],
    )

    with patch(
        "app.modules.emails.imap_collector.imaplib.IMAP4_SSL",
        return_value=mail,
    ):
        with pytest.raises(IMAPFetchError):
            collector.collect(limit=5)

    mail.close.assert_called_once()
    mail.logout.assert_called_once()


# ---------------------------------------------------------------------------
# Cleanup Tests
# ---------------------------------------------------------------------------


def test_close_safely_handles_connection_errors() -> None:
    mail = MagicMock()

    mail.close.side_effect = OSError(
        "close failed",
    )

    mail.logout.side_effect = imaplib.IMAP4.error(
        "logout failed",
    )

    IMAPCollector._close(mail)

    mail.close.assert_called_once()
    mail.logout.assert_called_once()


def test_close_accepts_none() -> None:
    IMAPCollector._close(None)