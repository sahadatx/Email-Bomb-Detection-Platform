#!/usr/bin/env python3

"""
Synthetic Email-Bomb Dataset Generator
=======================================

Generate large batches of unique synthetic bombing emails.

Example:
    python src/generators/bomb_generator.py --count 500

Output:
    data/raw/bomb/bomb_00001.eml
    data/raw/bomb/bomb_00002.eml
    ...

Locked Feature Alignment
------------------------
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

Important
---------
CC, BCC and Reply-To are optional email metadata only.
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
    / "bomb"
)


# ============================================================================
# SYNTHETIC PEOPLE
# ============================================================================

FIRST_NAMES = (
    "Arif",
    "Rahim",
    "Hasan",
    "Karim",
    "Nabil",
    "Sakib",
    "Tanvir",
    "Fahim",
    "Rafi",
    "Imran",
    "Nayeem",
    "Jahid",
    "Siam",
    "Amin",
    "Rashed",
    "Mahir",
    "Adnan",
    "Shuvo",
    "Tareq",
    "Farhan",
    "Rakib",
    "Mehedi",
    "Saif",
    "Nafis",
    "Arafat",
    "Asif",
    "Anik",
    "Tamim",
    "Shakil",
    "Munna",
    "Sabbir",
    "Riyad",
    "Fardin",
    "Zubair",
    "Mahin",
    "Abrar",
    "Rahat",
    "Sohan",
    "Jisan",
    "Foysal",
    "Sajid",
    "Masud",
    "Rony",
    "Shahin",
    "Bashir",
    "Nasir",
    "Javed",
    "Mizan",
    "Rubel",
    "Alamin",
    "Rasel",
    "Tuhin",
    "Noman",
    "Irfan",
    "Tahmid",
    "Shahriar",
    "Sami",
    "Yasin",
    "Ovi",
    "Shadman",
    "Ayon",
    "Rifat",
    "Nishat",
    "Shafin",
    "Faisal",
    "Ahsan",
    "Raihan",
    "Sakib",
    "Shakib",
    "Maruf",
    "Siam",
    "Jubayer",
    "Hridoy",
    "Sifat",
    "Nayeem",
    "Sourav",
    "Joy",
    "Pavel",
)


LAST_NAMES = (
    "Rahman",
    "Hossain",
    "Ahmed",
    "Islam",
    "Khan",
    "Chowdhury",
    "Hasan",
    "Karim",
    "Mahmud",
    "Uddin",
    "Sarker",
    "Miah",
    "Kabir",
    "Alam",
    "Rashid",
    "Akter",
    "Molla",
    "Talukder",
    "Bhuiyan",
    "Haque",
    "Siddique",
    "Mannan",
    "Jamal",
    "Rahim",
    "Sikder",
    "Kamal",
    "Mostafa",
    "Begum",
    "Faruq",
    "Hakim",
    "Chakma",
    "Das",
    "Roy",
    "Paul",
    "Dutta",
    "Saha",
    "Ghosh",
    "Basu",
    "Mitra",
    "Sen",
    "Gupta",
    "Sharma",
    "Patel",
    "Mehta",
    "Rao",
    "Singh",
)


# ============================================================================
# SYNTHETIC SENDER DOMAINS
# ============================================================================

DOMAINS = (
    "promo.example",
    "offers.example",
    "marketing.example",
    "mail.example",
    "newsletter.example",
    "campaign.example",
    "notify.example",
    "updates.example",
    "messages.example",
    "alerts.example",
    "service.example",
    "account.example",
    "support.example",
    "communication.example",
    "subscription.example",
    "membership.example",
    "customer.example",
    "notification.example",
    "delivery.example",
    "engagement.example",
    "bulletin.example",
    "broadcast.example",
    "mailing.example",
    "communications.example",
    "campaigns.example",
    "promotions.example",
    "reminder.example",
    "verification.example",
    "activation.example",
    "portal.example",
    "system.example",
    "service-mail.example",
    "customer-mail.example",
    "account-notice.example",
    "member-mail.example",
    "transaction.example",
    "updates-mail.example",
    "notice.example",
    "messaging.example",
    "digital.example",
)


# ============================================================================
# RECIPIENT DOMAINS
# ============================================================================

RECIPIENT_DOMAINS = (
    "company.example",
    "office.example",
    "business.example",
    "organization.example",
    "enterprise.example",
    "corporate.example",
    "internal.example",
    "staff.example",
    "customer.example",
    "client.example",
    "team.example",
    "work.example",
    "department.example",
    "service.example",
    "users.example",
)


RECIPIENT_NAMES = (
    "user",
    "employee",
    "customer",
    "member",
    "account",
    "support",
    "admin",
    "team",
    "client",
    "subscriber",
    "customer-care",
    "service",
    "helpdesk",
    "staff",
    "contact",
    "portal",
    "account-user",
    "member-user",
    "registered-user",
)


# ============================================================================
# ORGANIZATIONS
# ============================================================================

ORGANIZATIONS = (
    "Customer Services",
    "Account Services",
    "Member Services",
    "Subscription Center",
    "Notification Center",
    "Customer Support",
    "Digital Services",
    "Online Services",
    "Account Management",
    "Communication Center",
    "Marketing Services",
    "Membership Services",
    "Service Operations",
    "Customer Care",
    "Support Operations",
    "Online Support",
    "User Services",
    "Account Support",
    "Notification Services",
    "Subscription Services",
)


DEPARTMENTS = (
    "Customer Support",
    "Account Management",
    "Customer Success",
    "Marketing",
    "Operations",
    "Service Desk",
    "Member Services",
    "Digital Services",
    "Subscription Management",
    "Communication",
    "Client Services",
    "Technical Support",
    "Account Services",
    "Notification Operations",
    "Service Administration",
)


# ============================================================================
# SUBJECT DATA
# ============================================================================

SUBJECT_PREFIXES = (
    "",
    "URGENT:",
    "IMPORTANT:",
    "ACTION REQUIRED:",
    "NOTICE:",
    "ALERT:",
    "REMINDER:",
    "ATTENTION:",
    "FINAL NOTICE:",
    "SERVICE NOTICE:",
    "ACCOUNT NOTICE:",
    "SECURITY NOTICE:",
    "CUSTOMER NOTICE:",
    "MEMBERSHIP NOTICE:",
    "SUBSCRIPTION NOTICE:",
    "IMPORTANT UPDATE:",
    "IMMEDIATE ACTION:",
    "REQUIRED ACTION:",
    "ACCOUNT ALERT:",
    "SERVICE ALERT:",
    "IMPORTANT REMINDER:",
    "PLEASE REVIEW:",
    "PLEASE CONFIRM:",
    "PLEASE VERIFY:",
    "CONFIRMATION REQUIRED:",
    "VERIFICATION REQUIRED:",
    "UPDATE REQUIRED:",
    "RENEWAL REQUIRED:",
    "ACTIVATION REQUIRED:",
)


SUBJECTS = (
    "Confirm Your Subscription",
    "Verify Your Account",
    "Activate Your Account",
    "Important Notification",
    "Security Alert",
    "Your Subscription Update",
    "Limited Time Promotion",
    "Special Promotional Offer",
    "Newsletter Confirmation",
    "Your Account Requires Verification",
    "Action Required",
    "Important Account Update",
    "Renew Your Subscription",
    "Confirm Your Email Address",
    "Service Notification",
    "Membership Confirmation",
    "Promotional Update",
    "Account Activation Required",
    "Subscription Confirmation",
    "Email Verification Required",
    "Account Confirmation",
    "Membership Update",
    "Customer Notification",
    "Service Update",
    "Important Service Information",
    "Your Account Update",
    "Account Verification Notice",
    "Subscription Renewal Notice",
    "Membership Renewal Notice",
    "Confirm Your Membership",
    "Verify Your Email",
    "Complete Your Verification",
    "Complete Your Activation",
    "Update Your Account",
    "Review Your Account",
    "Review Your Subscription",
    "Confirm Your Information",
    "Update Required for Your Account",
    "Notification Preferences Update",
    "Communication Preferences Update",
    "Service Activation Notice",
    "Membership Activation Notice",
    "Subscription Activation Notice",
    "Customer Account Notice",
    "Account Service Notification",
    "Important Customer Update",
    "Important Membership Update",
    "Important Subscription Update",
    "Important Service Update",
    "Account Security Notification",
    "Customer Security Notification",
    "Service Security Notification",
    "Verification Notification",
    "Activation Notification",
    "Subscription Notification",
    "Membership Notification",
    "Account Notification",
    "Promotional Notification",
    "Marketing Notification",
    "Newsletter Update",
    "Newsletter Subscription Notice",
    "Communication Update",
    "Customer Communication",
    "Service Communication",
    "Account Communication",
    "Membership Communication",
    "Subscription Communication",
    "Notification Center Update",
    "Customer Service Update",
    "Account Services Update",
    "Member Services Update",
    "Digital Services Update",
    "Online Services Update",
    "Important Information About Your Account",
    "Your Requested Confirmation",
    "Your Requested Verification",
    "Your Requested Activation",
    "Confirmation Request",
    "Verification Request",
    "Activation Request",
    "Subscription Request",
    "Membership Request",
    "Account Update Required",
    "Profile Update Required",
    "Contact Information Update",
    "Email Preferences Update",
    "Notification Settings Update",
    "Service Preferences Update",
    "Subscription Preferences Update",
    "Customer Preferences Update",
)


# ============================================================================
# BODY DATA
# ============================================================================

OPENINGS = (
    "Hello,",
    "Hi,",
    "Hello there,",
    "Dear Customer,",
    "Dear Member,",
    "Dear User,",
    "Dear Subscriber,",
    "Dear Account Holder,",
    "Dear Customer Member,",
    "Hello Customer,",
    "Hello Member,",
    "Hello User,",
    "Hello Subscriber,",
    "Greetings,",
    "Dear Registered User,",
    "Dear Valued Customer,",
    "Dear Valued Member,",
    "Dear Account User,",
    "Dear Service User,",
)


MAIN_MESSAGES = (
    "Please confirm your subscription using the confirmation link provided in this message.",
    "Your account requires verification before the service can continue.",
    "Please verify your email address to activate the requested service.",
    "This notification was generated because your subscription information needs to be updated.",
    "Please review the latest account information and complete the requested verification step.",
    "Your membership information is ready for confirmation.",
    "Please confirm that you would like to continue receiving these notifications.",
    "An account update requires your attention.",
    "Your communication preferences are ready to be reviewed.",
    "Please confirm the requested account information to continue using the service.",
    "Your subscription details require confirmation.",
    "Your account information is pending verification.",
    "The requested service activation is waiting for confirmation.",
    "Your membership status requires an update.",
    "Please verify your information to keep your account information current.",
    "Your notification preferences have been prepared for review.",
    "Your subscription settings are ready for confirmation.",
    "Please review the information associated with your account.",
    "Your account requires an update before the next service notification.",
    "Please confirm the information associated with your membership.",
    "Your service preferences need to be reviewed.",
    "A confirmation step is required for your current subscription.",
    "Your account verification process is not yet complete.",
    "Please complete the requested account verification.",
    "Your membership confirmation is waiting for action.",
    "Your subscription confirmation is currently pending.",
    "The notification center has an update regarding your account.",
    "A service update requires confirmation from the account holder.",
    "Your customer profile is ready for review.",
    "Your account preferences require confirmation.",
)


ACTION_MESSAGES = (
    "Confirm your subscription to continue receiving future notifications.",
    "Verify your account information to keep the service active.",
    "Activate the requested service by completing the verification process.",
    "Review the information and confirm the requested update.",
    "Use the confirmation option below to complete the requested action.",
    "Please confirm the requested information to continue.",
    "Verify the account details before continuing with the service.",
    "Complete the verification step to activate the requested feature.",
    "Confirm your email address to continue receiving service notifications.",
    "Review your subscription information and confirm the update.",
    "Complete the requested confirmation process for your account.",
    "Verify your membership details to continue using the service.",
    "Confirm the account information shown in your notification.",
    "Complete the account activation process to continue.",
    "Review and confirm your current communication preferences.",
    "Confirm the requested subscription settings.",
    "Verify the requested account information before proceeding.",
    "Complete the requested membership confirmation.",
    "Confirm your current service preferences.",
    "Review the notification details and complete the requested action.",
    "Verify your information before the service update is completed.",
    "Confirm your registration information to continue.",
    "Complete the requested email verification step.",
    "Confirm your customer information to keep your account current.",
    "Review the account update and complete the confirmation step.",
)


CONTEXT_SENTENCES = (
    "This message is part of a subscription notification process.",
    "This notification relates to your current account settings.",
    "Your confirmation helps us keep your notification preferences up to date.",
    "The requested update is associated with your registered account.",
    "The service uses confirmation messages to keep account information current.",
    "Your account information may require periodic verification.",
    "This message was generated as part of the account notification process.",
    "Your current subscription preferences are available for review.",
    "The notification system has prepared this update for your account.",
    "The requested change is waiting for confirmation.",
    "Your account remains pending until the requested step is completed.",
    "This notification contains information related to your registered service.",
    "Your membership preferences are included in this update.",
    "The service may send additional notifications related to this request.",
    "This message is associated with your current communication preferences.",
    "Your subscription information has been prepared for confirmation.",
    "The account notification process requires confirmation from the user.",
    "This service notification was generated automatically.",
    "Your account settings are available for review.",
    "This update is associated with your current membership status.",
    "Your registered email address is associated with this notification.",
    "The notification center has prepared an account-related message.",
    "This communication was generated by the service notification system.",
    "Your current service status is included in this communication.",
    "The account update process is waiting for the requested confirmation.",
)


FOLLOW_UP_MESSAGES = (
    "Please review the information carefully before confirming.",
    "You may receive additional confirmation messages related to this request.",
    "Please make sure the information associated with your account is correct.",
    "If your account information has changed, review the available update.",
    "Please complete the requested step to keep your preferences current.",
    "Your response helps us maintain accurate account information.",
    "The requested confirmation should be completed through the available service.",
    "Please review the latest notification before continuing.",
    "Your account information will remain pending until confirmation is completed.",
    "Please ensure that your current subscription information is accurate.",
    "Review your current preferences before completing the requested action.",
    "The notification system may send another reminder if confirmation is not completed.",
    "Please keep your account information up to date.",
    "Your confirmation is required to complete this service request.",
    "The requested action is associated with your current account settings.",
)


FOOTERS = (
    "Thank you for your attention.",
    "Thank you for confirming your information.",
    "Please complete the requested action at your earliest convenience.",
    "If you did not request this message, you may ignore it.",
    "Thank you.",
    "Thank you for using our service.",
    "Thank you for being a member.",
    "Thank you for your cooperation.",
    "We appreciate your attention to this notification.",
    "Thank you for keeping your account information current.",
    "Thank you for reviewing this notification.",
    "We appreciate your cooperation with the requested update.",
    "Thank you for your continued membership.",
    "Thank you for reviewing your account information.",
    "Thank you for confirming your preferences.",
)


CLOSINGS = (
    "Regards,",
    "Best regards,",
    "Kind regards,",
    "Best,",
    "Thank you,",
    "Sincerely,",
    "Customer Support",
    "Support Team",
    "Notification Service",
    "Account Services",
    "Customer Services",
    "Member Services",
    "Subscription Services",
    "Account Support",
    "Service Support",
    "Digital Services",
    "Online Services",
    "Customer Care",
    "Communication Center",
    "Notification Center",
)


CTA_LINES = (
    "Confirm your information",
    "Verify your account",
    "Activate your subscription",
    "Confirm your subscription",
    "Verify your email address",
    "Review your account",
    "Update your information",
    "Confirm your membership",
    "Complete verification",
    "Complete activation",
    "Review your subscription",
    "Confirm your preferences",
    "Verify membership information",
    "Review account settings",
    "Confirm account details",
    "Update account information",
    "Complete account confirmation",
    "Review notification preferences",
    "Confirm service information",
    "Verify service details",
)


# ============================================================================
# CAMPAIGN / SERVICE DATA
# ============================================================================

CAMPAIGN_TYPES = (
    "subscription",
    "membership",
    "account",
    "newsletter",
    "promotion",
    "notification",
    "verification",
    "activation",
    "customer-service",
    "service-update",
    "account-update",
    "communication",
    "marketing",
    "customer-notification",
    "membership-update",
    "subscription-update",
)


SERVICE_NAMES = (
    "Customer Portal",
    "Member Portal",
    "Account Center",
    "Subscription Center",
    "Notification Center",
    "Customer Service Portal",
    "Digital Service Center",
    "Online Account Center",
    "Membership Portal",
    "Communication Center",
    "Service Management Portal",
    "Account Services Portal",
    "Customer Management Center",
    "Online Services Center",
    "User Services Portal",
)


# ============================================================================
# OPTIONAL NORMAL-STYLE METADATA
# ============================================================================

# These are NOT F1-F12.
#
# They only make synthetic raw emails more realistic.

CC_PROBABILITY = 0.12
BCC_PROBABILITY = 0.02
REPLY_TO_PROBABILITY = 0.10

# Vary campaign headers so the model cannot classify synthetic samples
# from a fixed F4-F8 signature alone.
AUTO_SUBMITTED_PROBABILITY = 0.85  # F4
PRECEDENCE_BULK_PROBABILITY = 0.85  # F5
LIST_ID_PROBABILITY = 0.75  # F6
X_BEENTHERE_PROBABILITY = 0.55  # F7
X_ANTI_ABUSE_PROBABILITY = 0.45  # F8


# ============================================================================
# RANDOM HELPERS
# ============================================================================

def random_token(
    length: int = 16,
) -> str:
    """Return a random alphanumeric token."""

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
    """Return a synthetic person name."""

    return (
        random.choice(
            FIRST_NAMES
        ),
        random.choice(
            LAST_NAMES
        ),
    )


def build_sender() -> tuple[str, str]:
    """Build a synthetic sender display name and email."""

    first_name, last_name = (
        random_person()
    )

    domain = random.choice(
        DOMAINS
    )

    local_parts = (
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}",
        f"{last_name.lower()}",
        f"{first_name.lower()}.{last_name.lower()}.service",
        f"{first_name.lower()}.{last_name.lower()}.notify",
        f"notification.{first_name.lower()}",
        f"support.{last_name.lower()}",
        f"service.{first_name.lower()}",
        f"account.{last_name.lower()}",
        f"member.{first_name.lower()}",
    )

    local_part = random.choice(
        local_parts
    )

    if random.random() < 0.75:
        local_part = (
            f"{local_part}"
            f"{random.randint(10, 99999)}"
        )

    return (
        f"{first_name} {last_name}",
        f"{local_part}@{domain}",
    )


def build_recipient() -> tuple[str, str]:
    """Build a synthetic recipient display name and address."""

    recipient_name = random.choice(
        RECIPIENT_NAMES
    )

    recipient_domain = random.choice(
        RECIPIENT_DOMAINS
    )

    recipient_address = (
        f"{recipient_name}"
        f"{random.randint(1, 9999)}"
        f"@{recipient_domain}"
    )

    return (
        recipient_name,
        recipient_address,
    )


def build_additional_recipient(
    exclude: set[str],
) -> str | None:
    """Build an optional additional recipient."""

    for _ in range(20):
        _, address = build_recipient()

        if address not in exclude:
            return address

    return None


# ============================================================================
# SUBJECT GENERATION
# ============================================================================

def generate_subject() -> str:
    """
    Generate a suspicious notification-style subject.

    F9:
        Suspicious keywords intentionally occur in subjects.

    F10:
        Different subject combinations create variable lengths.
    """

    prefix = random.choice(
        SUBJECT_PREFIXES
    )

    subject = random.choice(
        SUBJECTS
    )

    variations = (
        subject,
        subject,
        subject,
        f"{subject} - Please Review",
        f"{subject} - Confirmation Required",
        f"{subject} - Action Needed",
        f"{subject} - Important Information",
        f"{subject} - Please Confirm",
        f"{subject} - Please Verify",
        f"{subject} - Service Notification",
    )

    selected = random.choice(
        variations
    )

    if prefix:
        return (
            f"{prefix} {selected}"
        )

    return selected


# ============================================================================
# MESSAGE-ID
# ============================================================================

def generate_message_id(
    sender: str,
    index: int,
) -> str:
    """
    Generate a valid-looking unique Message-ID.

    F3:
        Message-ID is intentionally present and syntactically valid.
    """

    seed = (
        f"{sender}|"
        f"{index}|"
        f"{datetime.now(timezone.utc).timestamp()}|"
        f"{random_token(32)}"
    )

    digest = hashlib.sha256(
        seed.encode("utf-8")
    ).hexdigest()

    return (
        f"<bomb-{index}-"
        f"{digest[:32]}"
        f"@synthetic.example>"
    )


# ============================================================================
# F4 - F8 HEADER GENERATION
# ============================================================================

def build_auto_submitted_header() -> str:
    """
    F4:
        Generate a non-empty Auto-Submitted header.
    """

    return random.choice(
        (
            "auto-generated",
            "auto-generated; type=notification",
            "auto-generated; type=subscription",
            "auto-generated; type=marketing",
        )
    )


def build_precedence_header() -> str:
    """
    F5:
        Generate the required bulk indicator.
    """

    return "bulk"


def build_list_id_header(
    campaign_type: str,
) -> str:
    """
    F6:
        Generate a List-Id header.
    """

    token = random.randint(
        1000,
        999999,
    )

    return (
        f"<{campaign_type}-"
        f"{token}.lists.synthetic.example>"
    )


def build_x_beenthere_header(
    recipient: str,
) -> str:
    """
    F7:
        Generate X-BeenThere header.
    """

    return recipient


def build_x_anti_abuse_header() -> str:
    """
    F8:
        Generate X-Anti-Abuse header.
    """

    token = random.randint(
        100,
        999999,
    )

    return (
        f"contact{token}"
        "@abuse.synthetic.example"
    )


# ============================================================================
# OPTIONAL CC / BCC / REPLY-TO
# ============================================================================

def maybe_add_optional_recipient_headers(
    message: EmailMessage,
    sender_email: str,
    recipient_email: str,
) -> None:
    """
    Optionally add CC/BCC/Reply-To metadata.

    These fields are NOT part of F1-F12.
    """

    existing_addresses = {
        sender_email,
        recipient_email,
    }

    # --------------------------------------------------------
    # Optional CC
    # --------------------------------------------------------

    if random.random() < CC_PROBABILITY:
        cc_address = build_additional_recipient(
            existing_addresses
        )

        if cc_address:
            message["Cc"] = cc_address
            existing_addresses.add(
                cc_address
            )

    # --------------------------------------------------------
    # Optional BCC
    # --------------------------------------------------------

    if random.random() < BCC_PROBABILITY:
        bcc_address = build_additional_recipient(
            existing_addresses
        )

        if bcc_address:
            message["Bcc"] = bcc_address
            existing_addresses.add(
                bcc_address
            )

    # --------------------------------------------------------
    # Optional Reply-To
    # --------------------------------------------------------

    if random.random() < REPLY_TO_PROBABILITY:
        reply_domain = random.choice(
            (
                "reply.example",
                "responses.example",
                "contact.example",
                "support.example",
            )
        )

        reply_local = random.choice(
            (
                "reply",
                "responses",
                "support",
                "contact",
                "notifications",
                "service",
            )
        )

        message["Reply-To"] = (
            f"{reply_local}@{reply_domain}"
        )


# ============================================================================
# BODY GENERATION
# ============================================================================

def generate_body(
    recipient_name: str,
    sender_name: str,
) -> str:
    """
    Generate a varied notification-style body.

    F9:
        The subject and body intentionally contain configured
        suspicious keywords such as confirmation, subscription,
        newsletter, verify, activate, update, renewal, etc.
    """

    organization = random.choice(
        ORGANIZATIONS
    )

    department = random.choice(
        DEPARTMENTS
    )

    campaign_type = random.choice(
        CAMPAIGN_TYPES
    )

    service_name = random.choice(
        SERVICE_NAMES
    )

    main_message = random.choice(
        MAIN_MESSAGES
    )

    action_message = random.choice(
        ACTION_MESSAGES
    )

    context_message = random.choice(
        CONTEXT_SENTENCES
    )

    footer = random.choice(
        FOOTERS
    )

    closing = random.choice(
        CLOSINGS
    )

    opening = random.choice(
        OPENINGS
    )

    cta = random.choice(
        CTA_LINES
    )

    follow_up_count = random.randint(
        1,
        4,
    )

    selected_follow_ups = random.sample(
        FOLLOW_UP_MESSAGES,
        k=follow_up_count,
    )

    campaign_templates = (
        (
            "This notification is related to "
            "your {campaign_type} settings."
        ),
        (
            "The {service_name} has prepared "
            "this {campaign_type} notification."
        ),
        (
            "This update was prepared by "
            "{department}."
        ),
        (
            "Your current information is managed "
            "through {service_name}."
        ),
        (
            "This message is associated with "
            "{organization}."
        ),
    )

    campaign_line = random.choice(
        campaign_templates
    ).format(
        campaign_type=campaign_type,
        service_name=service_name,
        department=department,
        organization=organization,
    )

    personalized_openings = (
        f"Hello {recipient_name},",
        f"Dear {recipient_name},",
        f"Hi {recipient_name},",
    )

    if random.random() < 0.45:
        opening = random.choice(
            personalized_openings
        )

    lines: list[str] = [
        opening,
        "",
        main_message,
        "",
        context_message,
        "",
        campaign_line,
        "",
        action_message,
        "",
    ]

    lines.extend(
        selected_follow_ups
    )

    lines.extend(
        [
            "",
            f"Suggested action: {cta}.",
            "",
        ]
    )

    if random.random() < 0.60:
        extra_templates = (
            (
                f"The {service_name} currently shows "
                "your information as pending confirmation."
            ),
            (
                f"Please review the information associated "
                f"with {service_name}."
            ),
            (
                f"The {organization} notification system "
                "generated this message automatically."
            ),
            (
                f"Your request is currently being handled "
                f"by {department}."
            ),
            (
                f"This notification is part of the "
                f"{campaign_type} communication process."
            ),
        )

        lines.extend(
            [
                random.choice(
                    extra_templates
                ),
                "",
            ]
        )

    lines.extend(
        [
            footer,
            "",
            closing,
            sender_name,
        ]
    )

    return "\n".join(
        lines
    )


# ============================================================================
# TIMESTAMP GENERATION
# ============================================================================

def generate_timestamp(
    index: int,
) -> datetime:
    """
    Generate distributed UTC timestamps.

    F11:
        Emails within a one-minute window can be counted.

    F12:
        Emails within a one-hour window can be counted.

    The generator intentionally distributes samples across
    approximately 30 days so the temporal features have
    meaningful variation.
    """

    now = datetime.now(
        timezone.utc
    )

    random_seconds = random.randint(
        0,
        30 * 24 * 60 * 60,
    )

    index_component = (
        index % 7200
    )

    return (
        now
        - timedelta(
            seconds=(
                random_seconds
                + index_component
            )
        )
    )


# ============================================================================
# EMAIL CREATION
# ============================================================================

def create_bomb_email(
    index: int,
) -> EmailMessage:
    """
    Create one synthetic bombing email.
    """

    sender_name, sender_email = (
        build_sender()
    )

    recipient_name, recipient_email = (
        build_recipient()
    )

    subject = generate_subject()

    timestamp = generate_timestamp(
        index
    )

    campaign_type = random.choice(
        CAMPAIGN_TYPES
    )

    message = EmailMessage()

    # ------------------------------------------------------------------
    # STANDARD EMAIL HEADERS
    # ------------------------------------------------------------------

    message["From"] = (
        f"{sender_name} "
        f"<{sender_email}>"
    )

    message["To"] = (
        recipient_email
    )

    message["Subject"] = (
        subject
    )

    message["Date"] = timestamp.strftime(
        "%a, %d %b %Y %H:%M:%S %z"
    )

    message["Message-ID"] = (
        generate_message_id(
            sender=sender_email,
            index=index,
        )
    )

    message["MIME-Version"] = "1.0"

    # ------------------------------------------------------------------
    # OPTIONAL EMAIL METADATA
    #
    # CC/BCC/Reply-To are NOT features.
    # ------------------------------------------------------------------

    maybe_add_optional_recipient_headers(
        message=message,
        sender_email=sender_email,
        recipient_email=recipient_email,
    )

    # ------------------------------------------------------------------
    # PROBABILISTIC F4-F8 CAMPAIGN HEADERS
    #
    # F4 -> Auto-Submitted
    # F5 -> Precedence
    # F6 -> List-Id
    # F7 -> X-BeenThere
    # F8 -> X-Anti-Abuse
    # ------------------------------------------------------------------

    if random.random() < AUTO_SUBMITTED_PROBABILITY:
        message["Auto-Submitted"] = build_auto_submitted_header()

    if random.random() < PRECEDENCE_BULK_PROBABILITY:
        message["Precedence"] = build_precedence_header()

    if random.random() < LIST_ID_PROBABILITY:
        message["List-Id"] = build_list_id_header(campaign_type)

    if random.random() < X_BEENTHERE_PROBABILITY:
        message["X-BeenThere"] = build_x_beenthere_header(recipient_email)

    if random.random() < X_ANTI_ABUSE_PROBABILITY:
        message["X-Anti-Abuse"] = build_x_anti_abuse_header()

    # ------------------------------------------------------------------
    # DATASET METADATA
    # ------------------------------------------------------------------

    message["X-Dataset-Class"] = (
        "bombing"
    )

    message["X-Dataset-Sample"] = (
        f"bomb_{index:05d}"
    )

    message["X-Generator"] = (
        "Email-Bomb-Detection-Synthetic-Bomb-v3"
    )

    # ------------------------------------------------------------------
    # BODY
    # ------------------------------------------------------------------

    body = generate_body(
        recipient_name=recipient_name,
        sender_name=sender_name,
    )

    message.set_content(
        body
    )

    return message


# ============================================================================
# FINGERPRINT
# ============================================================================

def content_fingerprint(
    message: EmailMessage,
) -> str:
    """
    Calculate SHA-256 fingerprint of the complete raw email.
    """

    raw_bytes = message.as_bytes()

    return hashlib.sha256(
        raw_bytes
    ).hexdigest()


# ============================================================================
# EXISTING FILE FINGERPRINTS
# ============================================================================

def load_existing_fingerprints(
    output_dir: Path,
) -> set[str]:
    """
    Load fingerprints from existing .eml files.

    This prevents exact duplicate raw emails across
    separate generator runs.
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
    Generate a batch of unique bombing emails.

    Existing files are never overwritten.
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
    index = start_index

    max_attempts = max(
        count * 30,
        500,
    )

    while (
        generated < count
        and attempts < max_attempts
    ):
        attempts += 1

        message = create_bomb_email(
            index
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
            index += 1
            continue

        output_path = (
            output_dir
            / f"bomb_{index:05d}.eml"
        )

        # --------------------------------------------------------
        # Never overwrite existing files
        # --------------------------------------------------------

        if output_path.exists():
            index += 1
            continue

        output_path.write_bytes(
            message.as_bytes()
        )

        fingerprints.add(
            fingerprint
        )

        generated += 1
        index += 1

    if generated != count:
        raise RuntimeError(
            (
                f"Could only generate "
                f"{generated} unique emails "
                f"out of requested {count} "
                f"after {attempts} attempts."
            )
        )

    return (
        generated,
        index - 1,
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
            "email-bomb samples for the "
            "Email-Bomb-Detection-Platform."
        )
    )

    parser.add_argument(
        "--count",
        type=int,
        default=500,
        help=(
            "Number of bombing emails "
            "to generate. "
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
            "reproducible generation."
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

    print()
    print("=" * 72)
    print(
        "SYNTHETIC BOMBING EMAIL GENERATOR"
    )
    print("=" * 72)

    print(
        f"Requested       : {args.count}"
    )

    print(
        f"Start index     : {args.start_index}"
    )

    print(
        f"Output directory: {args.output_dir}"
    )

    print(
        "Ground truth    : BOMBING"
    )

    print(
        "Features        : F1-F12 aligned"
    )

    print("=" * 72)
    print()

    generated, last_index = generate_batch(
        count=args.count,
        output_dir=args.output_dir,
        start_index=args.start_index,
    )

    print()
    print("=" * 72)
    print(
        "BOMBING EMAIL GENERATION COMPLETE"
    )
    print("=" * 72)

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
        "Ground truth    : BOMBING"
    )

    print(
        "Status          : SUCCESS"
    )

    print("=" * 72)
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
