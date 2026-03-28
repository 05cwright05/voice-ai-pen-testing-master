from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sys
from typing import Any

from pymongo import ASCENDING, MongoClient

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import get_settings

DB_NAME = "medical_office"


def _build_patients() -> list[dict[str, Any]]:
    created_at = datetime.now(tz=UTC).isoformat()
    return [
        {
            "first_name": "Emma",
            "last_name": "Johnson",
            "date_of_birth": "1988-04-12",
            "phone": "+1-812-555-0101",
            "email": "emma.johnson@example.com",
            "address": {
                "street": "142 Magnolia Ln",
                "city": "Bloomington",
                "state": "IN",
                "zip": "47401",
            },
            "insurance_provider": "Blue Cross Blue Shield",
            "insurance_id": "BCBS-1847291",
            "allergies": ["penicillin"],
            "created_at": created_at,
        },
        {
            "first_name": "Liam",
            "last_name": "Carter",
            "date_of_birth": "1975-11-03",
            "phone": "+1-812-555-0102",
            "email": "liam.carter@example.com",
            "address": {
                "street": "88 Walnut St",
                "city": "Nashville",
                "state": "IN",
                "zip": "47448",
            },
            "insurance_provider": "Aetna",
            "insurance_id": "AET-9920017",
            "allergies": [],
            "created_at": created_at,
        },
        {
            "first_name": "Sophia",
            "last_name": "Martinez",
            "date_of_birth": "1993-02-27",
            "phone": "+1-812-555-0103",
            "email": "sophia.martinez@example.com",
            "address": {
                "street": "310 Cedar Ave",
                "city": "Bedford",
                "state": "IN",
                "zip": "47421",
            },
            "insurance_provider": "UnitedHealthcare",
            "insurance_id": "UHC-5511022",
            "allergies": ["latex"],
            "created_at": created_at,
        },
        {
            "first_name": "Noah",
            "last_name": "Bennett",
            "date_of_birth": "1981-07-09",
            "phone": "+1-812-555-0104",
            "email": "noah.bennett@example.com",
            "address": {
                "street": "19 River Rd",
                "city": "Martinsville",
                "state": "IN",
                "zip": "46151",
            },
            "insurance_provider": "Cigna",
            "insurance_id": "CIG-7490033",
            "allergies": ["shellfish"],
            "created_at": created_at,
        },
        {
            "first_name": "Olivia",
            "last_name": "Price",
            "date_of_birth": "1969-12-16",
            "phone": "+1-812-555-0105",
            "email": "olivia.price@example.com",
            "address": {
                "street": "740 Pine View Dr",
                "city": "Bloomington",
                "state": "IN",
                "zip": "47403",
            },
            "insurance_provider": "Humana",
            "insurance_id": "HUM-8829931",
            "allergies": ["aspirin"],
            "created_at": created_at,
        },
        {
            "first_name": "Ethan",
            "last_name": "Reed",
            "date_of_birth": "2000-05-22",
            "phone": "+1-812-555-0106",
            "email": "ethan.reed@example.com",
            "address": {
                "street": "5 Orchard Ct",
                "city": "Ellettsville",
                "state": "IN",
                "zip": "47429",
            },
            "insurance_provider": "Anthem",
            "insurance_id": "ANT-3250147",
            "allergies": [],
            "created_at": created_at,
        },
        {
            "first_name": "Ava",
            "last_name": "King",
            "date_of_birth": "1998-09-14",
            "phone": "+1-812-555-0107",
            "email": "ava.king@example.com",
            "address": {
                "street": "224 Sycamore St",
                "city": "Bloomington",
                "state": "IN",
                "zip": "47404",
            },
            "insurance_provider": "Medicaid",
            "insurance_id": "MCD-1092881",
            "allergies": ["peanuts"],
            "created_at": created_at,
        },
        {
            "first_name": "Mason",
            "last_name": "Young",
            "date_of_birth": "1958-01-30",
            "phone": "+1-812-555-0108",
            "email": "mason.young@example.com",
            "address": {
                "street": "460 Lakeview Blvd",
                "city": "Bloomington",
                "state": "IN",
                "zip": "47408",
            },
            "insurance_provider": "Medicare",
            "insurance_id": "MCR-7781220",
            "allergies": ["sulfa drugs"],
            "created_at": created_at,
        },
        {
            "first_name": "Isabella",
            "last_name": "Turner",
            "date_of_birth": "1986-06-18",
            "phone": "+1-812-555-0109",
            "email": "isabella.turner@example.com",
            "address": {
                "street": "901 Willow Pkwy",
                "city": "Spencer",
                "state": "IN",
                "zip": "47460",
            },
            "insurance_provider": "Blue Cross Blue Shield",
            "insurance_id": "BCBS-5008712",
            "allergies": [],
            "created_at": created_at,
        },
        {
            "first_name": "James",
            "last_name": "Foster",
            "date_of_birth": "1991-03-04",
            "phone": "+1-812-555-0110",
            "email": "james.foster@example.com",
            "address": {
                "street": "33 Meadowbrook Way",
                "city": "Bloomington",
                "state": "IN",
                "zip": "47406",
            },
            "insurance_provider": "UnitedHealthcare",
            "insurance_id": "UHC-9026651",
            "allergies": ["ibuprofen"],
            "created_at": created_at,
        },
    ]


def _build_appointments() -> list[dict[str, Any]]:
    return [
        {
            "patient_key": "Emma Johnson",
            "date": "2026-04-01",
            "time": "09:00",
            "duration_minutes": 30,
            "provider": "Dr. Rebecca Harrison",
            "reason": "Annual physical",
            "status": "scheduled",
            "notes": "",
        },
        {
            "patient_key": "Liam Carter",
            "date": "2026-04-01",
            "time": "10:00",
            "duration_minutes": 30,
            "provider": "Dr. Rebecca Harrison",
            "reason": "Blood pressure follow-up",
            "status": "scheduled",
            "notes": "",
        },
        {
            "patient_key": "Sophia Martinez",
            "date": "2026-04-01",
            "time": "11:30",
            "duration_minutes": 30,
            "provider": "Dr. Maya Patel",
            "reason": "Migraine consultation",
            "status": "scheduled",
            "notes": "",
        },
        {
            "patient_key": "Noah Bennett",
            "date": "2026-04-02",
            "time": "09:30",
            "duration_minutes": 30,
            "provider": "Dr. Rebecca Harrison",
            "reason": "Diabetes check",
            "status": "scheduled",
            "notes": "",
        },
        {
            "patient_key": "Olivia Price",
            "date": "2026-04-02",
            "time": "14:00",
            "duration_minutes": 30,
            "provider": "Dr. Maya Patel",
            "reason": "Medication refill review",
            "status": "scheduled",
            "notes": "",
        },
        {
            "patient_key": "Ethan Reed",
            "date": "2026-04-03",
            "time": "08:30",
            "duration_minutes": 30,
            "provider": "Dr. Jordan Lee",
            "reason": "Sports physical",
            "status": "scheduled",
            "notes": "",
        },
        {
            "patient_key": "Ava King",
            "date": "2026-04-03",
            "time": "15:00",
            "duration_minutes": 30,
            "provider": "Dr. Jordan Lee",
            "reason": "Allergy follow-up",
            "status": "scheduled",
            "notes": "",
        },
        {
            "patient_key": "Mason Young",
            "date": "2026-04-04",
            "time": "10:30",
            "duration_minutes": 45,
            "provider": "Dr. Rebecca Harrison",
            "reason": "Joint pain consultation",
            "status": "scheduled",
            "notes": "",
        },
        {
            "patient_key": "Isabella Turner",
            "date": "2026-04-04",
            "time": "13:30",
            "duration_minutes": 30,
            "provider": "Dr. Maya Patel",
            "reason": "Lab results review",
            "status": "scheduled",
            "notes": "",
        },
        {
            "patient_key": "James Foster",
            "date": "2026-04-04",
            "time": "16:00",
            "duration_minutes": 30,
            "provider": "Dr. Jordan Lee",
            "reason": "Flu symptoms",
            "status": "scheduled",
            "notes": "",
        },
        {
            "patient_key": "Emma Johnson",
            "date": "2026-03-20",
            "time": "09:00",
            "duration_minutes": 30,
            "provider": "Dr. Rebecca Harrison",
            "reason": "Annual physical",
            "status": "completed",
            "notes": "Routine exam completed.",
        },
        {
            "patient_key": "Liam Carter",
            "date": "2026-03-22",
            "time": "10:30",
            "duration_minutes": 30,
            "provider": "Dr. Maya Patel",
            "reason": "Headache concern",
            "status": "completed",
            "notes": "Hydration and sleep guidance provided.",
        },
        {
            "patient_key": "Sophia Martinez",
            "date": "2026-03-23",
            "time": "14:30",
            "duration_minutes": 30,
            "provider": "Dr. Jordan Lee",
            "reason": "Skin rash",
            "status": "completed",
            "notes": "Topical treatment prescribed.",
        },
        {
            "patient_key": "Noah Bennett",
            "date": "2026-03-24",
            "time": "08:30",
            "duration_minutes": 30,
            "provider": "Dr. Rebecca Harrison",
            "reason": "Prescription follow-up",
            "status": "cancelled",
            "notes": "Cancelled by patient due to travel.",
        },
        {
            "patient_key": "Olivia Price",
            "date": "2026-03-26",
            "time": "11:00",
            "duration_minutes": 30,
            "provider": "Dr. Maya Patel",
            "reason": "Routine check-up",
            "status": "completed",
            "notes": "Routine care plan reviewed.",
        },
        {
            "patient_key": "Ethan Reed",
            "date": "2026-03-27",
            "time": "13:00",
            "duration_minutes": 30,
            "provider": "Dr. Jordan Lee",
            "reason": "Ankle pain",
            "status": "completed",
            "notes": "Recommended rest and imaging if no improvement.",
        },
        {
            "patient_key": "Ava King",
            "date": "2026-03-28",
            "time": "15:30",
            "duration_minutes": 30,
            "provider": "Dr. Rebecca Harrison",
            "reason": "Follow-up bloodwork",
            "status": "cancelled",
            "notes": "Cancelled due to weather.",
        },
        {
            "patient_key": "James Foster",
            "date": "2026-03-29",
            "time": "16:30",
            "duration_minutes": 30,
            "provider": "Dr. Maya Patel",
            "reason": "Cough and congestion",
            "status": "completed",
            "notes": "Viral symptoms, supportive care advised.",
        },
    ]


def main() -> int:
    settings = get_settings()
    print("Seeding MongoDB data structure and sample records...")

    with MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000) as client:
        db = client[DB_NAME]
        patients = db["patients"]
        appointments = db["appointments"]

        patients.create_index(
            [("first_name", ASCENDING), ("last_name", ASCENDING), ("date_of_birth", ASCENDING)],
            unique=True,
            name="uniq_patient_name_dob",
        )
        appointments.create_index([("date", ASCENDING), ("time", ASCENDING)], name="idx_appt_date_time")
        appointments.create_index([("patient_id", ASCENDING)], name="idx_appt_patient_id")

        patients.delete_many({})
        appointments.delete_many({})

        patient_docs = _build_patients()
        patient_result = patients.insert_many(patient_docs)
        patient_ids = {
            f"{doc['first_name']} {doc['last_name']}": inserted_id
            for doc, inserted_id in zip(patient_docs, patient_result.inserted_ids)
        }

        appointment_docs = []
        for raw in _build_appointments():
            appointment_docs.append(
                {
                    "patient_id": patient_ids[raw["patient_key"]],
                    "date": raw["date"],
                    "time": raw["time"],
                    "duration_minutes": raw["duration_minutes"],
                    "provider": raw["provider"],
                    "reason": raw["reason"],
                    "status": raw["status"],
                    "notes": raw["notes"],
                    "created_at": datetime.now(tz=UTC).isoformat(),
                }
            )

        appointments.insert_many(appointment_docs)

    print("Seed complete.")
    print(f"Inserted patients: {len(patient_docs)}")
    print(f"Inserted appointments: {len(appointment_docs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

