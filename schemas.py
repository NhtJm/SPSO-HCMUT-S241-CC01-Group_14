from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId as BsonObjectId
from typing import Optional

        
class StatusEnum(str, Enum):
    COMPLETE = "COMPLETE"
    WAITING = "WAITING"
    ONGOING = "ONGOING"
    NOT_START = "NOT START"
    ENDED = "ENDED"

class PersonalInfo(BaseModel):
    name: str
    studentId: str
    email: str
    faculty: str
    numberOfA4: int
    numberOfPrintedDocs: int

class PrintHistory(BaseModel):
    time: str
    fileName: str
    pages: int
    printer: str
    copies: int 
    fileId: str

class WaitingSession(BaseModel):
    fileId: Optional[str]
    time: Optional[str]
    expected_time: Optional[str]
    studentName: str
    studentId: str
    fileName: str
    pages: int
    printer: str
    place: str
    copies: int
    area: str
    status: str
    submission_time: str
    completion_time: Optional[str]

class Transaction(BaseModel):
    time: str
    transaction_id: str
    title: str
    payment: str

class PrinterStatus(BaseModel):
    available: bool

class FileType(BaseModel):
    type: str

class Maintenance(BaseModel):
    title: str
    description: str
    startTime: str
    createdBy: str
    duration: int
    status: StatusEnum

class PrintRequest(BaseModel):
    fileName: str
    pages: int
    printer: str
    copy: int

class ConfirmPrintRequest(BaseModel):
    session_id: str
    delete: bool

class TogglePrinterRequest(BaseModel):
    printerId: str

class AddFileTypeRequest(BaseModel):
    fileType: str

class AddMaintenanceRequest(BaseModel):
    title: str
    description: str
    startTime: str
    duration: int

class CreateTransactionRequest(BaseModel):
    numberOfPages: int

class DeleteSessionRequest(BaseModel):
    session_id: str

class PrintingHistory(BaseModel):
    docName: str
    printTime: str
    studentName: str
    copies: int
    printer: str
    area: str
    studentId: str
    place: str

class CancelPrintRequest(BaseModel):
    session_id: str
