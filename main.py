from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, LargeBinary
import io

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/mydatabase"
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

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_model = FileModel(filename=file.filename, content=content)
        async with SessionLocal() as session:
            session.add(file_model)
            await session.commit()

        return {"Successfully uploaded": file.filename}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@app.get("/retrieve/{filename}")
async def read_file(filename: str):
    async with SessionLocal() as session:
        result = await session.execute(select(FileModel).where(FileModel.filename == filename))
        file_model = result.scalars().first()
        if file_model is None:
            raise HTTPException(status_code=404, detail="File not found")
        print(f"Retrieved file: {file_model.filename} with size: {len(file_model.content)} bytes")
        if not file_model.content:
            raise HTTPException(status_code=500, detail="File content is empty")

        file_like = io.BytesIO(file_model.content)
        response = StreamingResponse(file_like, media_type="application/octet-stream")
        response.headers["Content-Disposition"] = f"attachment; filename={file_model.filename}"
        
        print(f"Response headers: {response.headers}")
        return response


@app.get("/files")
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
