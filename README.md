# Backend Setup Guide

This guide provides step-by-step instructions to set up and run the backend of the project.

---

# Table of Contents

1. [Backend Setup Guide](#backend-setup-guide)
2. [Prerequisites](#prerequisites)
3. [Backend Setup](#backend-setup)
   - [Clone the Repository](#clone-the-repository)
   - [Switch to the Backend Branch (if applicable)](#switch-to-the-backend-branch-if-applicable)
   - [Navigate to the Backend Directory](#navigate-to-the-backend-directory)
   - [Set Up Environment Variables](#set-up-environment-variables)
   - [Run the FastAPI Server](#run-the-fastapi-server)
4. [Usage](#usage)
   - [Backend Server Information](#backend-server-information)
   - [MongoDB Connection](#mongodb-connection)
5. [API Endpoints](#api-endpoints)
   - [User APIs](#user-apis)
   - [Admin APIs](#admin-apis)

---

## Prerequisites

Ensure you have the following installed on your system:
- **Git**: For cloning the repository and managing branches
- **Python 3.8+**: Required to run the backend
- **MongoDB**: For the database

---

## Backend Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd <repository-name>

2. **Switch to the Backend Branch (if applicable)**
   ```bash
   git checkout <branch-name>

3. **Navigate to this Backend Directory**
   ```bash
   cd SPSO-HCMUT-S241-CC01-Group_14
   
4. **Set Up Environment Variables:**
    Create a .env file in the Backend directory with the following content: 
    ```bash
    MONGO_URI=<your-mongo-uri>
    DATABASE_NAME=<your-database-name>

5. **Run the FastAPI Server:**
    The backend server will be available at: http://localhost:8000 
    ```bash
    uvicorn main:app --reload

---

## Usage

- Ensure the backend server is running at [http://localhost:8000](http://localhost:8000).
- The connection to MongoDB is managed in the `Backend/database.py` file. Verify your `.env` file contains the correct `MONGO_URI` and `DATABASE_NAME` values.

---

## API Endpoints

### User APIs
- **GET `/user/...`**  
  User-related endpoints (details to be added based on specific functionality).

### Admin APIs
- **GET `/admin/student_information`**  
  Retrieves student information.




