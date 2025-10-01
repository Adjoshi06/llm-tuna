"""Training job management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
from typing import Dict, Any, List

from app.database import get_db
from app.models import TrainingJob, Dataset
from app.schemas import TrainingJobCreate, TrainingJobResponse, TrainingConfig
from app.ml.trainer import start_training

router = APIRouter(prefix="/api/training", tags=["training"])

# Store active training tasks
_active_training_tasks: Dict[int, asyncio.Task] = {}


async def update_training_progress(
    job_id: int,
    step: int,
    loss: float,
    epoch: float,
    db: Session
):
    """Update training progress in database."""
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if not job:
        return
    
    # Initialize training_logs if needed
    if job.training_logs is None:
        job.training_logs = []
    
    # Add new log entry
    log_entry = {
        "step": step,
        "loss": float(loss),
        "epoch": float(epoch),
        "timestamp": datetime.now().isoformat()
    }
    
    job.training_logs.append(log_entry)
    db.commit()


async def run_training_task(
    job_id: int,
    dataset_path: str,
    config: Dict[str, Any],
    db: Session
):
    """Background task for running training."""
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if not job:
        return
    
    try:
        job.status = "training"
        job.started_at = datetime.now()
        db.commit()
        
        # Progress callback
        async def progress_callback(step: int, loss: float, epoch: float):
            await update_training_progress(job_id, step, loss, epoch, db)
        
        # Run training
        model_path = await start_training(
            job_id,
            dataset_path,
            config,
            progress_callback
        )
        
        # Update job status
        job.status = "completed"
        job.model_path = model_path
        job.completed_at = datetime.now()
        db.commit()
        
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.now()
        db.commit()
    finally:
        # Remove from active tasks
        if job_id in _active_training_tasks:
            del _active_training_tasks[job_id]


@router.get("", response_model=List[TrainingJobResponse])
def list_training_jobs(db: Session = Depends(get_db)):
    """List all training jobs."""
    jobs = db.query(TrainingJob).order_by(TrainingJob.created_at.desc()).all()
    return jobs


@router.post("/start", response_model=TrainingJobResponse, status_code=201)
async def start_training_job(
    request: TrainingJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new fine-tuning job."""
    # Verify dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if dataset.validation_status != "valid":
        raise HTTPException(status_code=400, detail="Dataset validation failed")
    
    # Prepare config
    config = {}
    if request.config:
        config = request.config.dict()
    else:
        # Use defaults
        config = TrainingConfig().dict()
    
    # Create training job
    job = TrainingJob(
        dataset_id=request.dataset_id,
        status="queued",
        config=config,
        training_logs=[]
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start training in background
    task = asyncio.create_task(
        run_training_task(job.id, dataset.file_path, config, db)
    )
    _active_training_tasks[job.id] = task
    
    return job


@router.get("/{job_id}", response_model=TrainingJobResponse)
def get_training_job(job_id: int, db: Session = Depends(get_db)):
    """Get training job status and logs."""
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    return job


@router.delete("/{job_id}", status_code=204)
def cancel_training_job(job_id: int, db: Session = Depends(get_db)):
    """Cancel a training job."""
    job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    if job.status in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed or failed job")
    
    # Cancel task if running
    if job_id in _active_training_tasks:
        task = _active_training_tasks[job_id]
        task.cancel()
        del _active_training_tasks[job_id]
    
    job.status = "failed"
    job.error_message = "Cancelled by user"
    job.completed_at = datetime.now()
    db.commit()
    
    return None

