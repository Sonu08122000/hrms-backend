from fastapi import APIRouter
from datetime import date

from database import employees_collection, attendance_collection
from schemas import DashboardStats

router = APIRouter()


@router.get("/", response_model=DashboardStats)
def get_dashboard():
    today = date.today().isoformat()  # "YYYY-MM-DD"

    total_employees = employees_collection.count_documents({})

    today_records = list(attendance_collection.find({"date": today}))
    total_present_today = sum(1 for r in today_records if r["status"] == "Present")
    total_absent_today = sum(1 for r in today_records if r["status"] == "Absent")

    attendance_rate = (
        round((total_present_today / total_employees) * 100, 1)
        if total_employees > 0
        else 0.0
    )

    # Department breakdown using aggregation
    pipeline = [
        {"$group": {"_id": "$department", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    dept_results = list(employees_collection.aggregate(pipeline))
    departments = [{"name": d["_id"], "count": d["count"]} for d in dept_results]

    return DashboardStats(
        total_employees=total_employees,
        total_present_today=total_present_today,
        total_absent_today=total_absent_today,
        attendance_rate_today=attendance_rate,
        departments=departments,
    )
