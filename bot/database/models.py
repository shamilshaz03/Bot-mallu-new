"""
Central place documenting the shape of every document in MongoDB, plus
the default documents that get seeded on first run so the bot is usable
out of the box (admin edits everything afterwards from the panel).
"""
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc)


DEFAULT_PLANS = [
    {
        "plan_id": "199",
        "title": "Starter Plan",
        "description": "Get access to our starter premium collection.",
        "price": 199,
        "currency": "INR",
        "category_browsing": False,
    },
    {
        "plan_id": "299",
        "title": "Plus Plan",
        "description": "A bigger premium collection with more content.",
        "price": 299,
        "currency": "INR",
        "category_browsing": False,
    },
    {
        "plan_id": "799",
        "title": "All Access Plan",
        "description": "Unlock everything — full library, all categories.",
        "price": 799,
        "currency": "INR",
        "category_browsing": True,
    },
]

DEFAULT_SETTINGS = [
    {"key": "welcome_photo", "value": None},
    {"key": "welcome_message", "value": "👋 Welcome! Choose a plan below to get started."},
    {"key": "payment_qr", "value": None},
    {"key": "payment_details", "value": "UPI: your-upi-id@bank"},
    {"key": "contact_admin", "value": "@your_admin_username"},
    {"key": "maintenance_mode", "value": False},
]


def new_user_doc(user_id: int, username: str | None, first_name: str | None) -> dict:
    return {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "current_plan": None,
        "previous_plans": [],
        "activation_date": None,
        "last_active_date": now(),
        "subscription_status": "inactive",
    }


def new_key_doc(key: str, plan: str, created_by: int, expiry: datetime | None = None) -> dict:
    return {
        "key": key,
        "plan": plan,
        "created_date": now(),
        "created_by": created_by,
        "status": "unused",
        "used_by": None,
        "used_date": None,
        "expiry": expiry,
    }


def new_content_doc(
    plan: str,
    category: str | None,
    file_id: str,
    file_type: str,
    caption: str,
    preview_file_id: str | None,
    preview_caption: str | None,
    thumbnail: str | None,
    uploaded_by: int,
) -> dict:
    return {
        "plan": plan,
        "category": category,  # only meaningful for the 799 plan
        "file_id": file_id,
        "file_type": file_type,  # video | photo | document
        "caption": caption,
        "preview_file_id": preview_file_id,
        "preview_caption": preview_caption,
        "thumbnail": thumbnail,
        "upload_date": now(),
        "uploaded_by": uploaded_by,
    }


def new_sample_doc(plan: str, file_id: str, file_type: str, caption: str, added_by: int) -> dict:
    return {
        "plan": plan,
        "file_id": file_id,
        "file_type": file_type,
        "caption": caption,
        "added_by": added_by,
        "added_date": now(),
    }
