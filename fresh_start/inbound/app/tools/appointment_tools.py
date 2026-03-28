from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from bson import ObjectId
from livekit.agents.llm import ToolError, function_tool

from app.db import get_database


def _validate_date(date: str) -> str:
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as exc:
        raise ToolError("date must be in YYYY-MM-DD format.") from exc
    return date


def _validate_time(time: str) -> str:
    try:
        datetime.strptime(time, "%H:%M")
    except ValueError as exc:
        raise ToolError("time must be in HH:MM 24-hour format.") from exc
    return time


def _validate_patient_id(patient_id: str) -> ObjectId:
    if not ObjectId.is_valid(patient_id):
        raise ToolError("Invalid patient_id format.")
    return ObjectId(patient_id)


@function_tool(
    description=(
        "Fetch a verified patient's upcoming scheduled appointments. "
        "Requires the patient's MongoDB patient_id."
    )
)
async def get_appointments(patient_id: str) -> dict[str, Any]:
    """Return upcoming scheduled appointments for a patient."""
    db = get_database()
    appointments = db["appointments"]
    patient_object_id = _validate_patient_id(patient_id)
    today = datetime.now(tz=UTC).date().isoformat()

    cursor = appointments.find(
        {"patient_id": patient_object_id, "status": "scheduled", "date": {"$gte": today}}
    ).sort([("date", 1), ("time", 1)])

    upcoming = await cursor.to_list(length=20)
    if not upcoming:
        return {"appointments": [], "message": "No upcoming scheduled appointments were found."}

    return {
        "appointments": [
            {
                "appointment_id": str(item["_id"]),
                "date": item.get("date", ""),
                "time": item.get("time", ""),
                "provider": item.get("provider", ""),
                "reason": item.get("reason", ""),
                "status": item.get("status", ""),
            }
            for item in upcoming
        ],
        "message": f"Found {len(upcoming)} upcoming appointment(s).",
    }


@function_tool(
    description=(
        "Schedule a new appointment for a verified patient. "
        "Checks for provider and patient conflicts at the same date/time."
    )
)
async def schedule_appointment(
    patient_id: str,
    date: str,
    time: str,
    provider: str,
    reason: str,
    duration_minutes: int = 30,
) -> dict[str, Any]:
    """Create a new scheduled appointment for the patient."""
    db = get_database()
    patients = db["patients"]
    appointments = db["appointments"]

    patient_object_id = _validate_patient_id(patient_id)
    date = _validate_date(date)
    time = _validate_time(time)

    patient = await patients.find_one({"_id": patient_object_id})
    if not patient:
        raise ToolError("No patient found for that patient_id.")

    provider_conflict = await appointments.find_one(
        {"date": date, "time": time, "provider": provider.strip(), "status": "scheduled"}
    )
    if provider_conflict:
        return {
            "scheduled": False,
            "message": "That provider already has a scheduled appointment at that time.",
        }

    patient_conflict = await appointments.find_one(
        {"date": date, "time": time, "patient_id": patient_object_id, "status": "scheduled"}
    )
    if patient_conflict:
        return {
            "scheduled": False,
            "message": "This patient already has a scheduled appointment at that time.",
        }

    appointment_doc = {
        "patient_id": patient_object_id,
        "date": date,
        "time": time,
        "duration_minutes": max(15, int(duration_minutes)),
        "provider": provider.strip(),
        "reason": reason.strip(),
        "status": "scheduled",
        "notes": "",
        "created_at": datetime.now(tz=UTC).isoformat(),
    }
    insert_result = await appointments.insert_one(appointment_doc)

    return {
        "scheduled": True,
        "appointment_id": str(insert_result.inserted_id),
        "message": f"Appointment scheduled for {date} at {time} with {provider.strip()}.",
    }


@function_tool(
    description=(
        "Get available 30-minute appointment slots for a provider on a date. "
        "Office hours are 09:00 to 17:00."
    )
)
async def get_available_slots(date: str, provider: str) -> dict[str, Any]:
    """Return available appointment times for a provider on a date."""
    db = get_database()
    appointments = db["appointments"]
    date = _validate_date(date)
    provider_clean = provider.strip()

    day_start = datetime.strptime("09:00", "%H:%M")
    slot_times = [
        (day_start + timedelta(minutes=30 * i)).strftime("%H:%M")
        for i in range(16)
    ]

    booked_cursor = appointments.find(
        {"date": date, "provider": provider_clean, "status": "scheduled"},
        {"time": 1, "_id": 0},
    )
    booked_docs = await booked_cursor.to_list(length=100)
    booked_times = {doc.get("time", "") for doc in booked_docs}
    available = [slot for slot in slot_times if slot not in booked_times]

    return {
        "date": date,
        "provider": provider_clean,
        "available_slots": available,
        "message": f"Found {len(available)} open slot(s).",
    }

