from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, File, UploadFile, Form
from schemas import (
    PersonalInfo,
    PrintHistory,
    WaitingSession,
    Transaction,
    PrintRequest,
    ConfirmPrintRequest,
    CreateTransactionRequest,
    CancelPrintRequest,
)
from PyPDF2 import PdfReader
from database import connect_to_database
from utils import get_student_id_from_header
import asyncio
from datetime import datetime
import pytz
import gridfs
from bson import ObjectId
import random
import string



router = APIRouter()
db = connect_to_database()
fs = gridfs.GridFS(db)
# Define the UTC+7 timezone
timezone_utc_plus_7 = pytz.timezone('Asia/Bangkok')

def generate_random_digits(length=10):
    return ''.join(random.choices(string.digits, k=length))

# Convert the current time to UTC+7 and format it
current_time_utc_plus_7 = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(timezone_utc_plus_7)
current_time_utc_plus_7 = current_time_utc_plus_7.strftime('%I:%M%p %d/%m/%Y')

@router.post("/add_personal_information")
async def add_personal_information(personal_info: PersonalInfo):
    # Check if student already exists in the database
    existing_student = db["students"].find_one({"studentId": personal_info.studentId})
    if existing_student:
        raise HTTPException(
            status_code=400, 
            detail=f"Student with ID {personal_info.studentId} already exists"
        )
    
    # Insert the new student's personal information
    db["students"].insert_one(personal_info.dict())
    
    return {"message": "Personal information added successfully", "studentId": personal_info.studentId}


@router.get("/personal_information", response_model=PersonalInfo)
async def get_personal_information(request: Request):
    student_id = get_student_id_from_header(request)
    student = db["students"].find_one({"studentId": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {
        "name": student["name"],
        "studentId": student["studentId"],
        "email": student["email"],
        "faculty": student["faculty"],
        "numberOfA4": student["numberOfA4"],
        "numberOfPrintedDocs": student["numberOfPrintedDocs"],
    }

@router.get("/printing_history", response_model=list[PrintHistory])
async def get_printing_history(request: Request):
    student_id = get_student_id_from_header(request)
    history = db["printing_history"].find({"studentId": student_id})
    return list(history)

@router.get("/waiting_sessions", response_model=list[WaitingSession])
async def get_waiting_sessions(request: Request):
    student_id = get_student_id_from_header(request)
    sessions = db["waiting_sessions"].find({"studentId": student_id})

    session_list = []
    for session in sessions:
        session_data = {
            "fileId": session.get("fileId"),  # Convert ObjectId to string
            "time": session.get("submission_time"),  # Populate if missing
            "expected_time": session.get("completion_time"),  # Populate if missing
            "studentName": session["studentName"],
            "studentId": session["studentId"],
            "fileName": session["fileName"],
            "pages": session["pages"],
            "printer": session["printer"],
            "place": session["place"],
            "copies": session.get("copies",1),
            "area": session["area"],
            "status": session["status"],
            "submission_time": session["submission_time"],
            "completion_time": session.get("completion_time"),  # Handle optional
        }
        session_list.append(session_data)

    return session_list


@router.get("/transaction_history", response_model=list[Transaction])
async def get_transaction_history(request: Request):
    student_id = get_student_id_from_header(request)
    transactions = db["transactions"].find({"studentId": student_id})
    
    # Map the _id field to transaction_id
    transaction_list = []
    for transaction in transactions:
        transaction["transaction_id"] = str(transaction.pop("_id"))
        transaction_list.append(transaction)
    
    return transaction_list

@router.get("/get_available_printers")
async def get_available_printers():
    printers = list(db["printers"].find({"status": "AVAILABLE"}, {"_id": 0, "name": 1}))
    return [printer["name"] for printer in printers]





from bson.errors import InvalidId

@router.post("/confirm_printing")
async def confirm_printing(request: Request, confirm_request: dict):
    try:
        print(f"Received payload: {confirm_request}")  # Log the received payload
        session_object_id = confirm_request["fileId"] 
        print(confirm_request["fileId"])
        # Fetch the session
        session = db["waiting_sessions"].find_one({"fileId": session_object_id})
        if not session:
            print("Session not found for fileId:", confirm_request.get("fileId"))
            raise HTTPException(status_code=404, detail="Session not found")

        if confirm_request.get("dele") == True:
            if session["status"] == "WAITING":
                db["waiting_sessions"].update_one(
                    {"fileId": session_object_id},
                    {"$set": {"status": "CANCELLED"}}
                )
                return
            result = db["waiting_sessions"].delete_one({"fileId": session_object_id})
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Failed to delete session")
            return {"message": f"Session with fileId {confirm_request.get("fileId")} successfully deleted."}
        else:
            # Handle non-deletion logic here if needed
            pass

    except Exception as e:
        print(f"Error in confirm_printing: {e}")
        raise HTTPException(status_code=500, detail=f"Error in confirm_printing: {str(e)}")





@router.post("/create_transaction")
async def create_transaction(request: Request, transaction_data: dict):
    student_id = get_student_id_from_header(request)
    quantity = transaction_data.get("quantity")
    price = transaction_data.get("price")
    print(quantity, price)
    if not quantity or not price:
        raise HTTPException(status_code=400, detail="Quantity and price are required.")

    # Find student in the database
    student = db["students"].find_one({"studentId": student_id})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    # Update the student's A4 papers
    db["students"].update_one({"studentId": student_id}, {"$inc": {"numberOfA4": quantity}})

    # Log the transaction
    db["transactions"].insert_one({
        "studentId": student_id,
        "time": current_time_utc_plus_7,
        "title": f"Bought {quantity} papers",
        "payment": f"{price} VND",
    })

    return {"message": f"Transaction created successfully. {quantity} papers added for {price} VND."}




        


PRINTERS = [
    "B1-01", "B1-02", "B1-03", "B1-04", "B1-05",
    "A4-01", "A4-02", "A4-03", "B4-01", "B4-02",
    "C4-01", "C4-02", "C6-01", "B10-01"
]

# Initialize all printers as available on startup
for printer in PRINTERS:
    db["printers"].update_one(
        {"name": printer},
        {"$set": {"status": "AVAILABLE", "Note": None}},
        upsert=True
    )

# Track if a printer is actively processing jobs
active_printers = {}

@router.post("/print_document")
async def print_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file_info: dict
):
    fileName = file_info.get("fileName")
    pages = file_info.get("pages")
    copies = file_info.get("copies")
    printer = file_info.get("printer")
    try:
        
        student_id = get_student_id_from_header(request)
        print(f"Received print request for {fileName} with {pages} pages, {copies} copies on {printer}")
        # Validate Printer Availability
        printer_status = db["printers"].find_one({"name": printer})
        if not printer_status or printer_status["status"] == "UNAVAILABLE":
            raise HTTPException(status_code=400, detail="Printer is currently unavailable.")

        total_pages = pages * copies
        
        # Check Student Balance
        student = db["students"].find_one({"studentId": student_id})
        if not student:
            raise HTTPException(status_code=404, detail="Student not found.")
        required_pages = total_pages * copies
        if student["numberOfA4"] < required_pages:
            raise HTTPException(status_code=400, detail="Not enough A4 pages.")

        # Deduct A4 Pages from Student Account
        db["students"].update_one({"studentId": student_id}, {"$inc": {"numberOfA4": -required_pages}})
        db["students"].update_one({"studentId": student_id}, {"$inc": {"numberOfPrintedDocs": copies}})

        # Save PDF to GridFS
        
        # Save Job to Waiting Queue
        area = printer.split('-')[0]
        db["waiting_sessions"].insert_one({
            "studentName": student["name"],
            "studentId": student_id,
            "fileName": fileName,
            "fileId": generate_random_digits(),  # Convert ObjectId to string
            "pages": total_pages,
            "printer": printer,
            "place": printer,
            "copies": copies,
            "area": area,
            "status": "WAITING",
            "submission_time": current_time_utc_plus_7
        })

        # Process the Printing Queue
        if not active_printers.get(printer, False):
            background_tasks.add_task(process_printer_queue, printer)

        return {"message": f"Print job for '{fileName}' added successfully with {total_pages} pages, {copies} copies."}
    except Exception as e:
        print(f"Error processing print document: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def process_printer_queue(printer: str):
    """
    Background task to process jobs in the printer queue.
    """
    global active_printers
    active_printers[printer] = True

    while True:
        # Fetch the next job in the queue
        #set null
        waiting_job = None
        waiting_job = db["waiting_sessions"].find_one(
            {"printer": printer, "status": "WAITING"}, sort=[("_id", 1)]
        )

        if not waiting_job:
            # No jobs left in the queue, mark the printer as available
            active_printers[printer] = False
            db["printers"].update_one({"name": printer}, {"$set": {"status": "AVAILABLE"}})
            break

        if waiting_job["status"] == "CANCELLED":
            # Job is not assigned to this printer, skip it
            print(f"Skipping cancelled job on {printer}: {waiting_job['fileName']}")
            db["waiting_sessions"].delete_one({"_id": waiting_job["_id"]})
            continue
        # Mark the printer as unavailable
        db["printers"].update_one({"name": printer}, {"$set": {"status": "UNAVAILABLE"}})
        # Simulate printing
        print(f"Processing job on {printer}: {waiting_job['fileName']}")
        await asyncio.sleep(30)  # Simulate 30-second processing time
        waiting_job["status"] = db["waiting_sessions"].find_one({"_id": waiting_job["_id"]})["status"]
        if waiting_job["status"] == "CANCELLED":
            # Job is not assigned to this printer, skip it
            print(f"Skipping cancelled job on {printer}: {waiting_job['fileName']}")
            db["waiting_sessions"].delete_one({"_id": waiting_job["_id"]})
            continue
        # Update job status and add to printing history
        db["waiting_sessions"].update_one(
            {"_id": waiting_job["_id"]},
            {"$set": {"status": "COMPLETE", "completion_time": current_time_utc_plus_7}}
        )
        db["printing_history"].insert_one({
            "studentId": waiting_job["studentId"],
            "time": current_time_utc_plus_7,
            "fileName": waiting_job["fileName"],
            "pages": waiting_job["pages"],
            "place": waiting_job["place"],
            "printer": waiting_job["printer"],
            "copies": waiting_job["copies"],
            "fileId": waiting_job["fileId"]
        })
        db["admin_printing_history"].insert_one({
            "studentName": waiting_job["studentName"],
            "studentId": waiting_job["studentId"],
            "time": current_time_utc_plus_7,
            "fileName": waiting_job["fileName"],
            "pages": waiting_job["pages"],
            "place": waiting_job["place"],
            "printer": waiting_job["printer"],
            "area": waiting_job["area"],
            "copies": waiting_job["copies"]
        })

        print(f"Completed job on {printer}: {waiting_job['fileName']}")

    # Set the printer to available after processing
    db["printers"].update_one({"name": printer}, {"$set": {"status": "AVAILABLE"}})


@router.get("/printer_queue")
async def get_printer_queue(printer: str):
    """
    Get the queue of waiting jobs for a specific printer.
    """
    queue = list(db["waiting_sessions"].find({"printer": printer, "status": "WAITING"}).sort("_id", 1))
    return {"printer": printer, "queue": queue}


@router.get("/completed_jobs")
async def get_completed_jobs(printer: str):
    """
    Get the list of completed jobs for a specific printer.
    """
    completed_jobs = list(db["waiting_sessions"].find({"printer": printer, "status": "COMPLETE"}))
    return {"printer": printer, "completed_jobs": completed_jobs}




from io import BytesIO
from fastapi.responses import StreamingResponse
from urllib.parse import quote

@router.get("/get_pdf/{file_id}")
async def get_pdf(file_id: str):
    try:
        # Retrieve the file from GridFS
        grid_out = fs.get(ObjectId(file_id))
        
        # Ensure file content is read correctly
        file_content = grid_out.read()
        file_stream = BytesIO(file_content)
        
        # Encode the filename for HTTP headers
        encoded_filename = quote(grid_out.filename)
        
        return StreamingResponse(
            file_stream,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={encoded_filename}"
            }
        )
    except Exception as e:
        print(f"Error retrieving PDF file: {e}")
        raise HTTPException(status_code=404, detail="File not found")
    



