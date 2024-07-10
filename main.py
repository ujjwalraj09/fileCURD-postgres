from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, LargeBinary
import os

DATABASE_URL = "your database"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class FileModel(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(LargeBinary)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    async with SessionLocal() as session:
        content = await file.read()
        file_model = FileModel(filename=file.filename, content=content)
        session.add(file_model)
        await session.commit()
    return {"Successfully uploaded": file.filename}

@app.get("/retrieve/{filename}")
async def read_file(filename: str):
    async with SessionLocal() as session:
        result = await session.execute(select(FileModel).where(FileModel.filename == filename))
        file_model = result.scalars().first()
        if file_model is None:
            raise HTTPException(status_code=404, detail="File not found")
        
        temp_file_path = f"/tmp/{file_model.filename}"
        try:
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(file_model.content)
            
            print(f"media_type=application/octet-stream")
            print(f"Content-Disposition=attachment; filename={file_model.filename}")
            print(f"content={file_model.content.decode('utf-8', errors='ignore')}")
            
            return FileResponse(path=temp_file_path, filename=file_model.filename, media_type="application/octet-stream")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
        finally:
            
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

@app.get("/files/")
async def list_files():
    async with SessionLocal() as session:
        result = await session.execute(select(FileModel))
        files = result.scalars().all()
        return [{"id": file.id, "filename": file.filename} for file in files]

@app.delete("/delete_file/{filename}")
async def delete_file(filename: str):
    async with SessionLocal() as session:
        result = await session.execute(select(FileModel).where(FileModel.filename == filename))
        file_models = result.scalars().all()
        if not file_models:
            raise HTTPException(status_code=404, detail="File not found")
        for file_model in file_models:
            await session.delete(file_model)
        await session.commit()
    return {"Message": f"Deleted all occurrences of {filename}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)