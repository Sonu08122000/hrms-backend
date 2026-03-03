from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import employees, attendance, dashboard

app = FastAPI(
    title="HRMS Lite API",
    description="Lightweight Human Resource Management System — MongoDB backend",
    version="1.0.0",
    docs_url="/hrms/lite/microservices/docs",  # Custom Swagger UI URL
    redoc_url="/hrms/lite/microservices/redoc",  # Optional: disable ReDoc (remove if you want default /redoc)
    openapi_url="/hrms/lite/microservices/openapi.json"  # Optional but recommended
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["Attendance"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "HRMS Lite API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
