from fastapi import Request, HTTPException

def get_student_id_from_header(request: Request):
    student_id = request.headers.get("studentId")
    if not student_id:
        raise HTTPException(status_code=400, detail="Missing studentId in headers")
    return student_id
