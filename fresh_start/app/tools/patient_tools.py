from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from livekit.agents.llm import ToolError, function_tool

from app.db import get_database


@function_tool(
    description=(
        "Verify a patient identity using full name and date of birth. "
        "Use this before accessing appointments or medical office records."
    )
)
async def verify_patient(first_name: str, last_name: str, date_of_birth: str) -> dict[str, Any]:
    """Verify patient identity by full name and DOB."""
    try:
        datetime.strptime(date_of_birth, "%Y-%m-%d")
    except ValueError as exc:
        raise ToolError("date_of_birth must be in YYYY-MM-DD format.") from exc

    db = get_database()
    patients = db["patients"]

    patient = await patients.find_one(
        {
            "first_name": {"$regex": f"^{re.escape(first_name.strip())}$", "$options": "i"},
            "last_name": {"$regex": f"^{re.escape(last_name.strip())}$", "$options": "i"},
            "date_of_birth": date_of_birth.strip(),
        }
    )

    if not patient:
        return {
            "verified": False,
            "message": (
                "No patient record matched that full name and date of birth. "
                "Please re-confirm details."
            ),
        }

    return {
        "verified": True,
        "patient_id": str(patient["_id"]),
        "full_name": f"{patient.get('first_name', '').strip()} {patient.get('last_name', '').strip()}",
        "date_of_birth": patient.get("date_of_birth", ""),
        "phone": patient.get("phone", ""),
        "message": "Patient verified successfully.",
    }

