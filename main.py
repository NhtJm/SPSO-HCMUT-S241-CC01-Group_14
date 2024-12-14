from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import user, admin
from database import connect_to_database

app = FastAPI(title="Smart Printing Service API")

# Connect to MongoDB
db = connect_to_database()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user.router, prefix="/user", tags=["User APIs"])
app.include_router(admin.router, prefix="/admin", tags=["Admin APIs"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Smart Printing Service API!"}

@app.on_event("startup")
async def initialize_printers():
    # Define default printers
    default_printers = [
    {"name": "B1-01", "status": "AVAILABLE"},
    {"name": "B1-02", "status": "AVAILABLE"},
    {"name": "B1-03", "status": "AVAILABLE"},
    {"name": "B1-04", "status": "AVAILABLE"},
    {"name": "B1-05", "status": "AVAILABLE"},
    {"name": "A4-01", "status": "AVAILABLE"},
    {"name": "A4-02", "status": "AVAILABLE"},
    {"name": "A4-03", "status": "AVAILABLE"},
    {"name": "B4-01", "status": "AVAILABLE"},
    {"name": "B4-02", "status": "AVAILABLE"},
    {"name": "C4-01", "status": "AVAILABLE"},
    {"name": "C4-02", "status": "AVAILABLE"},
    {"name": "C6-01", "status": "AVAILABLE"},
    {"name": "B10-01", "status": "AVAILABLE"}
]
    
    # Ensure the printers collection is initialized
    for printer in default_printers:
        db["printers"].update_one(
            {"name": printer["name"]},  # Match by printer name
            {"$set": printer},          # Set or update printer status
            upsert=True                 # Insert if not found
        )
    print("Printers initialized with AVAILABLE status")
