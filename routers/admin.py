from schemas import Maintenance, AddMaintenanceRequest, AddFileTypeRequest, TogglePrinterRequest, PersonalInfo
from database import connect_to_database
from schemas import PrintingHistory
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import pytz
import asyncio

router = APIRouter()
db = connect_to_database()

@router.get("/student_information", response_model=PersonalInfo)
async def get_student_information(studentId: str):
    student = db["students"].find_one({"studentId": studentId})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.get("/get_maintenances", response_model=list[Maintenance])
async def get_maintenances(ended: bool = None):
    status_filter = {"status": "ENDED"} if ended else {}
    maintenances = db["maintenances"].find(status_filter)
    return list(maintenances)


@router.post("/add_maintenance")
async def add_maintenance(request: AddMaintenanceRequest):
    db["maintenances"].insert_one({
        "title": request.title,
        "description": request.description,
        "startTime": request.startTime,
        "duration": request.duration,
        "status": "NOT START",
    })
    return {"message": "Maintenance added successfully"}


@router.post("/add_file_type")
async def add_file_type(request: AddFileTypeRequest):
    db["file_types"].insert_one({"type": request.fileType})
    return {"message": "File type added successfully"}


@router.post("/toggle_status")
async def toggle_printer_status(request: TogglePrinterRequest):
    printer = db["printers"].find_one({"printerId": request.printerId})
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    new_status = "available" if printer["status"] == "unavailable" else "unavailable"
    db["printers"].update_one({"printerId": request.printerId}, {
                              "$set": {"status": new_status}})
    return {"message": f"Printer {request.printerId} status updated to {new_status}"}


@router.get("/printing_history", response_model=list[PrintingHistory])
async def get_printing_history(area: Optional[str] = None, printer: Optional[str] = None,
                               studentId: Optional[str] = None, time_filter: Optional[str] = None):
    # Build the query filter
    filters = {}
    if area:
        filters["area"] = area
    if printer:
        filters["printer"] = printer
    if studentId:
        filters["studentId"] = studentId
    if time_filter:
        timezone_utc_plus_7 = pytz.timezone('Asia/Bangkok')
        current_time = datetime.utcnow().replace(
            tzinfo=pytz.utc).astimezone(timezone_utc_plus_7)

        if time_filter == "Since 1 day":
            filters["time"] = {
                "$gte": (current_time - timedelta(days=1)).isoformat()}
        elif time_filter == "Since 1 week":
            filters["time"] = {
                "$gte": (current_time - timedelta(weeks=1)).isoformat()}
        elif time_filter == "Since 1 month":
            filters["time"] = {
                "$gte": (current_time - timedelta(days=30)).isoformat()}
        elif time_filter == "Since 3 months":
            filters["time"] = {
                "$gte": (current_time - timedelta(days=90)).isoformat()}
        elif time_filter == "Since 1 year":
            filters["time"] = {
                "$gte": (current_time - timedelta(days=365)).isoformat()}

    # Fetch the data from the database
    printing_history = list(db["admin_printing_history"].find(filters))
    if not printing_history:
        return []

    # Ensure all required fields are present
    for record in printing_history:
        record.setdefault("docName", record.get("fileName", "Unknown"))
        record.setdefault("printTime", record.get("time", "Unknown"))
        record.setdefault("studentName", record.get("studentId", "Unknown"))
        record.setdefault("copies", record.get("copy", 1))
        record.setdefault("place", record.get("printer", "Unknown"))

    return printing_history


@router.get("/get_all_printers_status")
async def get_all_printers_status():
    # Project only name, status, and Note
    printers = db["printers"].find(
        {}, {"_id": 0, "name": 1, "status": 1, "Note": 1})
    return list(printers)


@router.post("/toggle_printer_status/{printer_name}")
async def toggle_printer_status(printer_name: str):
    """
    Toggle the printer's status between 'AVAILABLE' and 'UNAVAILABLE'.
    If the printer is already 'UNAVAILABLE', wait for 35 seconds and recheck.
    """
    try:
        # Find the printer by name
        printer = db["printers"].find_one({"name": printer_name})

        if not printer:
            raise HTTPException(status_code=404, detail=f"Printer '{
                                printer_name}' not found")

        # Toggle logic
        if printer["status"] == "AVAILABLE":
            # Update to UNAVAILABLE immediately
            db["printers"].update_one(
                {"name": printer_name},
                {"$set": {"status": "UNAVAILABLE"}}
            )
            return {"message": f"Printer '{printer_name}' is now UNAVAILABLE"}
        elif printer["status"] == "UNAVAILABLE":

            # Re-fetch the printer's current status
            updated_printer = db["printers"].find_one({"name": printer_name})

            if updated_printer["status"] == "AVAILABLE":
                # Change to UNAVAILABLE if now available
                db["printers"].update_one(
                    {"name": printer_name},
                    {"$set": {"status": "UNAVAILABLE"}}
                )
                return {"message": f"Printer '{printer_name}' was AVAILABLE but is now set to UNAVAILABLE"}
            else:
                db["printers"].update_one(
                    {"name": printer_name},
                    {"$set": {"status": "AVAILABLE"}}
                )
                return {"message": f"Printer '{printer_name}' is NOW AVAILABLE"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")
