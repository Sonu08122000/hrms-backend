from fastapi import APIRouter, HTTPException, status, Query
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from datetime import datetime, timezone
from typing import Optional

from database import employees_collection, attendance_collection
from schemas import AttendanceCreate, AttendanceResponse

router = APIRouter()


def _serialize(record: dict) -> AttendanceResponse:
    """Convert a MongoDB attendance document to AttendanceResponse."""
    emp = employees_collection.find_one({"_id": ObjectId(record["employee_id"])})
    return AttendanceResponse(
        id=str(record["_id"]),
        employee_id=record["employee_id"],
        date=record["date"],
        status=record["status"],
        employee_name=emp["full_name"] if emp else "Unknown",
        employee_emp_id=emp["employee_id"] if emp else "—",
        created_at=record["created_at"],
    )


@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def mark_attendance(payload: AttendanceCreate):
    # Validate employee exists
    try:
        emp = employees_collection.find_one({"_id": ObjectId(payload.employee_id)})
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee ID.")
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")

    # Check duplicate attendance for same employee + date
    if attendance_collection.find_one({"employee_id": payload.employee_id, "date": payload.date}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Attendance for {emp['full_name']} on {payload.date} is already recorded.",
        )

    doc = {
        "employee_id": payload.employee_id,
        "date": payload.date,
        "status": payload.status.value,
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = attendance_collection.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already recorded for this employee on this date.",
        )

    created = attendance_collection.find_one({"_id": result.inserted_id})
    return _serialize(created)


@router.get("/", response_model=list[AttendanceResponse])
def list_attendance(
    employee_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    query: dict = {}
    if employee_id:
        query["employee_id"] = employee_id
    if date_from or date_to:
        query["date"] = {}
        if date_from:
            query["date"]["$gte"] = date_from
        if date_to:
            query["date"]["$lte"] = date_to

    records = list(attendance_collection.find(query).sort("date", -1))
    return [_serialize(r) for r in records]


@router.get("/employee/{employee_id}", response_model=list[AttendanceResponse])
def get_employee_attendance(
    employee_id: str,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    try:
        emp = employees_collection.find_one({"_id": ObjectId(employee_id)})
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee ID.")
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")

    query: dict = {"employee_id": employee_id}
    if date_from or date_to:
        query["date"] = {}
        if date_from:
            query["date"]["$gte"] = date_from
        if date_to:
            query["date"]["$lte"] = date_to

    records = list(attendance_collection.find(query).sort("date", -1))
    return [_serialize(r) for r in records]


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(attendance_id: str):
    try:
        oid = ObjectId(attendance_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attendance ID.")

    record = attendance_collection.find_one({"_id": oid})
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found.")

    attendance_collection.delete_one({"_id": oid})
