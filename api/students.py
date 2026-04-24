from fastapi import APIRouter, HTTPException

from schemas.students import StudentUpdate

router = APIRouter(
    prefix="/students",
    tags=["students"],
)


@router.get("/")
async def read_students():
    return [{"id": 1, "name": "Иванов"}, {"id": 2, "name": "Петров"}]


@router.get("/{student_id}", responses={404: {"description": "Not found"}},)
async def read_student(student_id: int):
    if id == 0:
        raise HTTPException(
            status_code=404, detail="Student not found"
        )
    return {"student_id": student_id, "name": f"{student_id}-Иванов"}

@router.put("/{student_id}")
async def update_student(student_id: int, student: StudentUpdate):
    return {"student_id": student_id, **student.model_dump()}