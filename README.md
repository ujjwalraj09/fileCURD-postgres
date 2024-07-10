# FastAPI File Server

This is a simple file server built with FastAPI and SQLAlchemy.

## Features

- Upload files 
- Retrieve files
- List all files
- Delete files

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up postgres in docker `docker pull postgres`
4. Create the server from postgres image `docker run --name mypostgres -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=mydatabase -p 5432:5432 -d postgres`
5. Set up your PostgreSQL database and update the `DATABASE_URL` in the code
6. Run the server: `python main.py` or `uvicorn main:app --host 0.0.0.0 --port 8000`

## API Endpoints

- POST /upload/ - Upload a file
- GET /retrieve/{filename} - Retrieve a file
- GET /files/ - List all files
- DELETE /delete_file/{filename} - Delete a file