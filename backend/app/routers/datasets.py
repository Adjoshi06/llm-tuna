"""Dataset management endpoints."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime

from app.database import get_db
from app.models import Dataset
from app.schemas import DatasetResponse, DatasetCreate, ValidationReport
from app.ml.data_validator import validate_dataset

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

# Ensure datasets directory exists
DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets")
os.makedirs(DATASETS_DIR, exist_ok=True)


@router.post("", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a training dataset in JSONL format.
    
    Expected format: {"prompt": "...", "completion": "..."}
    """
    if not file.filename.endswith('.jsonl'):
        raise HTTPException(status_code=400, detail="File must be a .jsonl file")
    
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(DATASETS_DIR, f"{timestamp}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Validate dataset
    validation_result = validate_dataset(file_path)
    
    # Create dataset record
    dataset = Dataset(
        name=file.filename,
        file_path=file_path,
        num_examples=validation_result["num_examples"],
        validation_status="valid" if validation_result["valid"] else "invalid",
        validation_report=validation_result
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    return dataset


@router.get("", response_model=List[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)):
    """List all uploaded datasets."""
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Get dataset details by ID."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """Delete a dataset and its file."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Delete file if it exists
    if os.path.exists(dataset.file_path):
        try:
            os.remove(dataset.file_path)
        except Exception as e:
            pass  # Continue even if file deletion fails
    
    db.delete(dataset)
    db.commit()
    return None

