from fastapi import APIRouter, HTTPException, status
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from datetime import datetime, timezone

from database import employees_collection, attendance_collection
from schemas import EmployeeCreate, EmployeeResponse

router = APIRouter()


def _serialize(emp: dict) -> EmployeeResponse:
    """Convert a MongoDB document to EmployeeResponse."""
    total_present = attendance_collection.count_documents({
        "employee_id": str(emp["_id"]),
        "status": "Present",
    })
    return EmployeeResponse(
        id=str(emp["_id"]),
        employee_id=emp["employee_id"],
        full_name=emp["full_name"],
        email=emp["email"],
        department=emp["department"],
        created_at=emp["created_at"],
        total_present=total_present,
    )


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate):
    # Manual duplicate checks for clear error messages
    if employees_collection.find_one({"employee_id": payload.employee_id.strip()}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee ID '{payload.employee_id}' already exists.",
        )
    if employees_collection.find_one({"email": payload.email.lower()}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{payload.email}' is already registered.",
        )

    doc = {
        "employee_id": payload.employee_id.strip(),
        "full_name": payload.full_name.strip(),
        "email": payload.email.lower(),
        "department": payload.department.strip(),
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = employees_collection.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID or email already exists.",
        )

    created = employees_collection.find_one({"_id": result.inserted_id})
    return _serialize(created)


@router.get("/", response_model=list[EmployeeResponse])
def list_employees():
    employees = list(employees_collection.find().sort("created_at", -1))
    return [_serialize(e) for e in employees]


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: str):
    try:
        emp = employees_collection.find_one({"_id": ObjectId(employee_id)})
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee ID.")
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    return _serialize(emp)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: str):
    try:
        oid = ObjectId(employee_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid employee ID.")

    emp = employees_collection.find_one({"_id": oid})
    if not emp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")

    # Cascade delete attendance records
    attendance_collection.delete_many({"employee_id": employee_id})
    employees_collection.delete_one({"_id": oid})
