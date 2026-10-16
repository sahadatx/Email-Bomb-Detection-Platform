#!/usr/bin/env python3

"""
Synthetic Normal Email Generator
=================================

Generate large batches of unique synthetic normal emails.

The generator creates realistic-looking normal business/work emails
with optional CC, BCC, and Reply-To headers.

Example:
    python src/generators/normal_generator.py --count 500

Output:
    data/raw/normal/normal_00001.eml
    data/raw/normal/normal_00002.eml
    ...

Email characteristics:
    - Ground-truth class: NORMAL
    - From / To
    - Optional CC
    - Optional BCC
    - Optional Reply-To
    - Subject
    - Date
    - Message-ID
    - MIME-Version
    - Content-Type
    - Content-Transfer-Encoding
    - Synthetic dataset metadata
    - Realistic business-style body
    - Distributed timestamps
    - Duplicate protection

Locked Feature Alignment:
    F1  Sender Email
    F2  Known Domain Indicator
    F3  Message-ID Presence
    F4  Auto-Submitted Header
    F5  Precedence Bulk Indicator
    F6  List-Id Header
    F7  X-BeenThere Header
    F8  X-Anti-Abuse Header
    F9  Keyword-Based Content Features
    F10 Subject Length
    F11 Emails Per Minute
    F12 Emails Per Hour

Normal mail occasionally includes automated or mailing-list headers
that overlap with bombing indicators. Their rates are configurable so
the classes do not have perfectly separated synthetic header patterns.

CC, BCC and Reply-To are metadata only.
They are NOT part of F1-F12.
"""

from __future__ import annotations

import argparse
import hashlib
import random
import string
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path


# ============================================================================
# PROJECT PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "normal"
)


# ============================================================================
# SYNTHETIC DATA
# ============================================================================

FIRST_NAMES = (
    "James",
    "Michael",
    "Robert",
    "David",
    "John",
    "Daniel",
    "William",
    "Thomas",
    "Matthew",
    "Christopher",
    "Andrew",
    "Joseph",
    "Emma",
    "Olivia",
    "Sophia",
    "Emily",
    "Grace",
    "Hannah",
    "Mia",
    "Sarah",
    "Charlotte",
    "Amelia",
    "Evelyn",
    "Harper",
    "Ella",
)


LAST_NAMES = (
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Miller",
    "Davis",
    "Wilson",
    "Taylor",
    "Anderson",
    "Thomas",
    "Jackson",
    "White",
    "Harris",
    "Martin",
    "Thompson",
    "Garcia",
    "Martinez",
    "Robinson",
    "Clark",
)


# ============================================================================
# NORMAL EMAIL DOMAINS
# ============================================================================

DOMAINS = (
    "example.com",
    "example.org",
    "company.example",
    "office.example",
    "business.example",
    "organization.example",
    "internal.example",
)


# ============================================================================
# BUSINESS CONTENT
# ============================================================================

TEAMS = (
    "Engineering",
    "Security",
    "Operations",
    "Finance",
    "Human Resources",
    "Marketing",
    "Research",
    "Development",
    "Infrastructure",
    "Support",
)


PROJECTS = (
    "platform migration",
    "security review",
    "application update",
    "infrastructure project",
    "documentation project",
    "internal portal",
    "development cycle",
    "deployment process",
    "testing phase",
    "monitoring project",
)


SUBJECT_PREFIXES = (
    "",
    "Weekly",
    "Monthly",
    "Project",
    "Team",
    "Internal",
    "Development",
    "Engineering",
    "Operations",
    "Planning",
    "Technical",
)


SUBJECT_CORES = (
    "Progress Report",
    "Status Update",
    "Meeting Notes",
    "Project Update",
    "Work Summary",
    "Schedule Update",
    "Task Update",
    "Team Discussion",
    "Development Update",
    "Planning Notes",
    "Technical Discussion",
    "Work Review",
    "Project Planning",
    "Maintenance Information",
    "Deployment Update",
    "Testing Update",
    "Documentation Update",
)


OPENINGS = (
    "Hello {recipient},",
    "Hi {recipient},",
    "Good morning {recipient},",
    "Good afternoon {recipient},",
    "Hello team,",
    "Hi team,",
)


MAIN_SENTENCES = (
    "I wanted to share a quick update regarding the current work.",
    "The team has completed the planned tasks for this period.",
    "The current work is progressing according to the schedule.",
    "We reviewed the latest project status during the team discussion.",
    "The remaining tasks are being reviewed before the next cycle.",
    "The development work is continuing as planned.",
    "The team has reviewed the current requirements and next steps.",
    "The latest changes have been reviewed by the team.",
    "The current implementation is moving forward without major issues.",
    "The project status was reviewed during the latest internal meeting.",
)


DETAIL_SENTENCES = (
    "The remaining items will be handled during the next work cycle.",
    "Additional details will be discussed during the next team meeting.",
    "The responsible team members are continuing with their assigned work.",
    "We will review the open items before the next update.",
    "The current schedule remains unchanged.",
    "The team will provide another update when the remaining work is completed.",
    "The documentation will be updated as the work progresses.",
    "The next review will focus on the outstanding technical items.",
    "No major changes are expected at this stage.",
    "The current plan will remain in place for the next few days.",
)


CLOSINGS = (
    "Best regards,",
    "Kind regards,",
    "Regards,",
    "Best,",
    "Thank you,",
    "Thanks,",
)


FOOTERS = (
    "",
    "Please let me know if you have any questions.",
    "Let me know if you need any additional information.",
    "Please feel free to contact me if anything needs clarification.",
    "I will share another update when there is new information.",
)


# ============================================================================
# OPTIONAL CC / BCC / REPLY-TO DISTRIBUTION
# ============================================================================
#
# These fields are NOT part of F1-F12.
# They only improve raw-email realism.
#
# Approximate distribution:
#
# CC        -> 25%
# BCC       -> 5%
# Reply-To  -> 15%
#
# These are intentionally configurable constants.

CC_PROBABILITY = 0.25
BCC_PROBABILITY = 0.05
REPLY_TO_PROBABILITY = 0.15

# Legitimate automated and mailing-list messages can share a few header
# indicators with bomb campaigns. Keep those cases present but uncommon.
AUTO_SUBMITTED_PROBABILITY = 0.10  # F4
PRECEDENCE_BULK_PROBABILITY = 0.03  # F5
LIST_ID_PROBABILITY = 0.12  # F6
X_BEENTHERE_PROBABILITY = 0.04  # F7
X_ANTI_ABUSE_PROBABILITY = 0.02  # F8

CC_MIN_RECIPIENTS = 1
CC_MAX_RECIPIENTS = 2

BCC_MIN_RECIPIENTS = 1
BCC_MAX_RECIPIENTS = 1


# ============================================================================
# RANDOM HELPERS
# ============================================================================

def random_token(
    length: int = 16,
) -> str:
    """
    Generate a random lowercase alphanumeric token.
    """

    alphabet = (
        string.ascii_lowercase
        + string.digits
    )

    return "".join(
        random.choices(
            alphabet,
            k=length,
        )
    )


def random_person() -> tuple[str, str]:
    """
    Generate a synthetic first and last name.
    """

    return (
        random.choice(
            FIRST_NAMES
        ),
        random.choice(
            LAST_NAMES
        ),
    )


def build_address(
    first_name: str,
    last_name: str,
    domain: str,
) -> str:
    """
    Generate a synthetic email address.
    """

    suffix = random.randint(
        1,
        9999,
    )

    return (
        f"{first_name.lower()}."
        f"{last_name.lower()}"
        f"{suffix}@{domain}"
    )


def build_person_address() -> tuple[str, str]:
    """
    Generate a synthetic display name and email address.
    """

    first_name, last_name = (
        random_person()
    )

    domain = random.choice(
        DOMAINS
    )

    address = build_address(
        first_name=first_name,
        last_name=last_name,
        domain=domain,
    )

    display_name = (
        f"{first_name} {last_name}"
    )

    return (
        display_name,
        address,
    )


# ============================================================================
# MESSAGE-ID GENERATION
# ============================================================================

def generate_message_id(
    sender: str,
    index: int,
) -> str:
    """
    Generate a syntactically valid-looking Message-ID.

    F3:
        Message-ID is intentionally present.
    """

    token = (
        f"{sender}:"
        f"{index}:"
        f"{random_token(24)}"
    )

    digest = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    domain = sender.split(
        "@",
        1,
    )[-1]

    return (
        f"<{digest[:20]}."
        f"{random_token(10)}@{domain}>"
    )


# ============================================================================
# SUBJECT GENERATION
# ============================================================================

def generate_subject() -> str:
    """
    Generate a normal business/work subject.

    F10:
        Subject length naturally varies between samples.
    """

    prefix = random.choice(
        SUBJECT_PREFIXES
    )

    core = random.choice(
        SUBJECT_CORES
    )

    if prefix:
        return f"{prefix} {core}"

    return core


# ============================================================================
# OPTIONAL RECIPIENT GENERATION
# ============================================================================

def generate_optional_recipients(
    min_count: int,
    max_count: int,
    exclude_addresses: set[str] | None = None,
) -> list[str]:
    """
    Generate unique optional recipients.

    Addresses in exclude_addresses are not reused.
    """

    excluded = set(
        exclude_addresses or set()
    )

    target_count = random.randint(
        min_count,
        max_count,
    )

    recipients: list[str] = []

    attempts = 0

    max_attempts = max(
        target_count * 10,
        20,
    )

    while len(recipients) < target_count:
        attempts += 1

        if attempts > max_attempts:
            break

        _, address = (
            build_person_address()
        )

        if address in excluded:
            continue

        if address in recipients:
            continue

        recipients.append(
            address
        )

    return recipients


# ============================================================================
# REPLY-TO GENERATION
# ============================================================================

def generate_reply_to(
    sender_name: str,
) -> str:
    """
    Generate a normal Reply-To address.

    Reply-To is metadata only and is NOT an F1-F12 feature.
    """

    name_parts = sender_name.split()

    first_name = (
        name_parts[0].lower()
        if name_parts
        else "user"
    )

    last_name = (
        name_parts[-1].lower()
        if len(name_parts) > 1
        else "support"
    )

    local_part = (
        f"{first_name}.{last_name}"
    )

    reply_prefix = random.choice(
        (
            "reply",
            "responses",
            "team",
            "contact",
        )
    )

    domain = random.choice(
        DOMAINS
    )

    return (
        f"{reply_prefix}+"
        f"{local_part}@{domain}"
    )


# ============================================================================
# BODY GENERATION
# ============================================================================

def generate_body(
    sender_first: str,
    sender_last: str,
    recipient_first: str,
    recipient_last: str,
) -> str:
    """
    Generate a normal business-style plain-text body.

    F9:
        Normal samples use ordinary business/work language. Common terms
        such as "update" may still overlap with configured F9 keywords.
    """

    sender_name = (
        f"{sender_first} {sender_last}"
    )

    opening = random.choice(
        OPENINGS
    ).format(
        recipient=recipient_first
    )

    sentence_one = random.choice(
        MAIN_SENTENCES
    )

    sentence_two = random.choice(
        DETAIL_SENTENCES
    )

    footer = random.choice(
        FOOTERS
    )

    team = random.choice(
        TEAMS
    )

    project = random.choice(
        PROJECTS
    )

    paragraphs = [
        opening,
        "",
        sentence_one,
        (
            f"The {team} team is currently "
            f"working on the {project}."
        ),
        sentence_two,
    ]

    if footer:
        paragraphs.extend(
            [
                "",
                footer,
            ]
        )

    paragraphs.extend(
        [
            "",
            random.choice(
                CLOSINGS
            ),
            sender_name,
        ]
    )

    return "\n".join(
        paragraphs
    )


# ============================================================================
# TIMESTAMP GENERATION
# ============================================================================

def generate_timestamp(
    index: int,
) -> datetime:
    """
    Generate a distributed UTC timestamp.

    F11:
        received_at is used for per-minute email counts.

    F12:
        received_at is used for per-hour email counts.

    Samples are distributed across approximately 30 days.
    """

    now = datetime.now(
        timezone.utc
    )

    random_minutes = random.randint(
        0,
        30 * 24 * 60,
    )

    index_offset = (
        index
        * random.randint(
            1,
            7,
        )
    )

    total_minutes = (
        random_minutes
        + index_offset
    )

    return (
        now
        - timedelta(
            minutes=total_minutes,
            seconds=random.randint(
                0,
                59,
            ),
        )
    )


# ============================================================================
# EMAIL CREATION
# ============================================================================

def create_normal_email(
    index: int,
) -> EmailMessage:
    """
    Create one synthetic normal email.
    """

    sender_first, sender_last = (
        random_person()
    )

    recipient_first, recipient_last = (
        random_person()
    )

    sender_domain = random.choice(
        DOMAINS
    )

    recipient_domain = random.choice(
        DOMAINS
    )

    sender = build_address(
        first_name=sender_first,
        last_name=sender_last,
        domain=sender_domain,
    )

    recipient = build_address(
        first_name=recipient_first,
        last_name=recipient_last,
        domain=recipient_domain,
    )

    sender_name = (
        f"{sender_first} {sender_last}"
    )

    recipient_name = (
        f"{recipient_first} {recipient_last}"
    )

    subject = generate_subject()

    body = generate_body(
        sender_first=sender_first,
        sender_last=sender_last,
        recipient_first=recipient_first,
        recipient_last=recipient_last,
    )

    timestamp = generate_timestamp(
        index
    )

    message_id = generate_message_id(
        sender=sender,
        index=index,
    )

    message = EmailMessage()

    # ------------------------------------------------------------------
    # CORE HEADERS
    # ------------------------------------------------------------------

    message["From"] = (
        f"{sender_name} <{sender}>"
    )

    message["To"] = (
        f"{recipient_name} <{recipient}>"
    )

    message["Subject"] = (
        subject
    )

    message["Date"] = timestamp.strftime(
        "%a, %d %b %Y %H:%M:%S %z"
    )

    message["Message-ID"] = (
        message_id
    )

    message["MIME-Version"] = "1.0"

    # ------------------------------------------------------------------
    # OPTIONAL CC
    # ------------------------------------------------------------------

    if random.random() < CC_PROBABILITY:
        cc_recipients = (
            generate_optional_recipients(
                min_count=CC_MIN_RECIPIENTS,
                max_count=CC_MAX_RECIPIENTS,
                exclude_addresses={
                    sender,
                    recipient,
                },
            )
        )

        if cc_recipients:
            message["Cc"] = (
                ", ".join(
                    cc_recipients
                )
            )

    # ------------------------------------------------------------------
    # OPTIONAL BCC
    # ------------------------------------------------------------------

    if random.random() < BCC_PROBABILITY:
        existing_addresses = {
            sender,
            recipient,
        }

        # Cc header may contain display/address strings.
        # For this synthetic generator, generated CC values
        # are raw addresses, so we can safely exclude them.
        existing_addresses.update(
            message.get_all(
                "Cc",
                [],
            )
        )

        bcc_recipients = (
            generate_optional_recipients(
                min_count=BCC_MIN_RECIPIENTS,
                max_count=BCC_MAX_RECIPIENTS,
                exclude_addresses=existing_addresses,
            )
        )

        if bcc_recipients:
            message["Bcc"] = (
                ", ".join(
                    bcc_recipients
                )
            )

    # ------------------------------------------------------------------
    # OPTIONAL REPLY-TO
    # ------------------------------------------------------------------

    if (
        random.random()
        < REPLY_TO_PROBABILITY
    ):
        message["Reply-To"] = (
            generate_reply_to(
                sender_name=sender_name,
            )
        )

    # ------------------------------------------------------------------
    # OCCASIONAL LEGITIMATE AUTOMATION / LIST HEADERS (F4-F8)
    # ------------------------------------------------------------------

    if random.random() < AUTO_SUBMITTED_PROBABILITY:
        message["Auto-Submitted"] = random.choice(
            ("auto-generated", "auto-replied")
        )

    if random.random() < PRECEDENCE_BULK_PROBABILITY:
        message["Precedence"] = "bulk"

    has_list_id = random.random() < LIST_ID_PROBABILITY
    if has_list_id:
        list_name = random.choice(TEAMS).lower().replace(" ", "-")
        message["List-Id"] = f"<{list_name}.lists.example>"

    # X-BeenThere is more likely on a list message, but some gateways
    # attach it independently of List-Id.
    if (has_list_id and random.random() < 0.30) or (
        not has_list_id and random.random() < X_BEENTHERE_PROBABILITY
    ):
        message["X-BeenThere"] = recipient

    if random.random() < X_ANTI_ABUSE_PROBABILITY:
        message["X-Anti-Abuse"] = f"abuse-contact@{sender_domain}"

    # ------------------------------------------------------------------
    # DATASET METADATA
    # ------------------------------------------------------------------

    message["X-Dataset-Class"] = (
        "normal"
    )

    message["X-Dataset-Sample"] = (
        f"normal_{index:05d}"
    )

    message["X-Generator"] = (
        "Email-Bomb-Detection-Synthetic-Normal-v3"
    )

    # ------------------------------------------------------------------
    # BODY
    #
    # EmailMessage.set_content() automatically creates:
    #   Content-Type
    #   Content-Transfer-Encoding
    # ------------------------------------------------------------------

    message.set_content(
        body
    )

    return message


# ============================================================================
# DUPLICATE PROTECTION
# ============================================================================

def content_fingerprint(
    message: EmailMessage,
) -> str:
    """
    Create a SHA-256 fingerprint of the complete raw email.
    """

    raw = message.as_bytes()

    return hashlib.sha256(
        raw
    ).hexdigest()


def load_existing_fingerprints(
    output_dir: Path,
) -> set[str]:
    """
    Load fingerprints from existing .eml files.

    This prevents exact duplicate raw emails across
    different generator runs.
    """

    fingerprints: set[str] = set()

    if not output_dir.exists():
        return fingerprints

    for path in output_dir.glob(
        "*.eml"
    ):
        try:
            raw_bytes = path.read_bytes()

            fingerprint = hashlib.sha256(
                raw_bytes
            ).hexdigest()

            fingerprints.add(
                fingerprint
            )

        except OSError:
            continue

    return fingerprints


# ============================================================================
# BATCH GENERATION
# ============================================================================

def generate_batch(
    count: int,
    output_dir: Path,
    start_index: int,
) -> tuple[int, int]:
    """
    Generate a batch of unique normal emails.

    Existing files are never overwritten.
    Existing email fingerprints are also respected.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    fingerprints = (
        load_existing_fingerprints(
            output_dir
        )
    )

    generated = 0
    attempts = 0
    target = start_index

    max_attempts = max(
        count * 20,
        100,
    )

    while generated < count:
        attempts += 1

        if attempts > max_attempts:
            raise RuntimeError(
                "Unable to generate enough "
                "unique emails."
            )

        message = create_normal_email(
            target
        )

        fingerprint = (
            content_fingerprint(
                message
            )
        )

        # --------------------------------------------------------
        # Exact duplicate protection
        # --------------------------------------------------------

        if fingerprint in fingerprints:
            target += 1
            continue

        filename = (
            f"normal_{target:05d}.eml"
        )

        output_path = (
            output_dir
            / filename
        )

        # --------------------------------------------------------
        # Never overwrite existing files
        # --------------------------------------------------------

        if output_path.exists():
            target += 1
            continue

        output_path.write_bytes(
            message.as_bytes()
        )

        fingerprints.add(
            fingerprint
        )

        generated += 1
        target += 1

    return (
        generated,
        target - 1,
    )


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    """
    Build command-line argument parser.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Generate unique synthetic "
            "normal emails for the "
            "Email-Bomb-Detection-Platform."
        )
    )

    parser.add_argument(
        "--count",
        type=int,
        default=500,
        help=(
            "Number of emails to generate. "
            "Default: 500."
        ),
    )

    parser.add_argument(
        "--start-index",
        type=int,
        default=1,
        help=(
            "Starting sample/file index. "
            "Default: 1."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=(
            "Output directory for "
            "generated .eml files."
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=(
            "Optional random seed for "
            "reproducible generation. "
            "Omit for maximum variation."
        ),
    )

    return parser


# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    """
    CLI entry point.
    """

    parser = build_parser()
    args = parser.parse_args()

    if args.count <= 0:
        parser.error(
            "--count must be greater than zero."
        )

    if args.start_index <= 0:
        parser.error(
            "--start-index must be greater than zero."
        )

    if args.seed is not None:
        random.seed(
            args.seed
        )

    generated, last_index = (
        generate_batch(
            count=args.count,
            output_dir=args.output_dir,
            start_index=args.start_index,
        )
    )

    print()
    print("=" * 64)
    print(
        "NORMAL EMAIL GENERATION COMPLETE"
    )
    print("=" * 64)

    print(
        f"Generated       : {generated}"
    )

    print(
        f"First index     : {args.start_index}"
    )

    print(
        f"Last index      : {last_index}"
    )

    print(
        f"Output directory: {args.output_dir}"
    )

    print(
        "Ground truth    : NORMAL"
    )

    print(
        "Feature set     : F1-F12 LOCKED"
    )

    print("=" * 64)
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
