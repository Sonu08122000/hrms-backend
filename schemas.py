from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class AttendanceStatus(str, Enum):
    present = "Present"
    absent = "Absent"


# ── Employee Schemas ─────────────────────────────────────────────────────────

class EmployeeCreate(BaseModel):
    employee_id: str
    full_name: str
    email: EmailStr
    department: str

    @field_validator("employee_id")
    @classmethod
    def strip_employee_id(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Employee ID cannot be empty")
        return v

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Full name cannot be empty")
        return v

    @field_validator("department")
    @classmethod
    def strip_department(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Department cannot be empty")
        return v


class EmployeeResponse(BaseModel):
    id: str
    employee_id: str
    full_name: str
    email: str
    department: str
    created_at: datetime
    total_present: Optional[int] = 0


# ── Attendance Schemas ───────────────────────────────────────────────────────

class AttendanceCreate(BaseModel):
    employee_id: str          # MongoDB _id of the employee (string)
    date: str                 # ISO date string: "YYYY-MM-DD"
    status: AttendanceStatus

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v):
        from datetime import date as date_type
        try:
            date_type.fromisoformat(v)
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class AttendanceResponse(BaseModel):
    id: str
    employee_id: str
    date: str
    status: str
    employee_name: Optional[str] = None
    employee_emp_id: Optional[str] = None
    created_at: datetime


# ── Dashboard Schema ─────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_employees: int
    total_present_today: int
    total_absent_today: int
    attendance_rate_today: float
    departments: list[dict]
