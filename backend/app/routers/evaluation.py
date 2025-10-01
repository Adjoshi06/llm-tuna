"""Evaluation endpoints."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Evaluation, TrainingJob, Dataset, UserRating
from app.schemas import (
    EvaluationCreate,
    EvaluationResponse,
    UserRatingCreate,
    UserRatingResponse,
    TestExample,
    EvaluationMetrics
)
from app.ml.evaluator import evaluate_models
import asyncio

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


async def run_evaluation_task(
    evaluation_id: int,
    dataset_path: str,
    base_model_name: str,
    finetuned_model_path: str,
    test_size: int,
    db: Session
):
    """Background task for running evaluation."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        return
    
    try:
        # Run evaluation
        results = await evaluate_models(
            dataset_path,
            base_model_name,
            finetuned_model_path,
            test_size
        )
        
        # Store results
        evaluation.test_results = results["test_results"]
        evaluation.metrics = results["metrics"]
        db.commit()
        
    except Exception as e:
        evaluation.metrics = {"error": str(e)}
        db.commit()


@router.post("/run", response_model=EvaluationResponse, status_code=201)
async def run_evaluation(
    request: EvaluationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Run evaluation comparing base and fine-tuned models."""
    # Get training job
    training_job = db.query(TrainingJob).filter(
        TrainingJob.id == request.training_job_id
    ).first()
    
    if not training_job:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    if training_job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Training job not completed (status: {training_job.status})"
        )
    
    if not training_job.model_path:
        raise HTTPException(status_code=400, detail="Model path not found")
    
    # Get dataset
    dataset = db.query(Dataset).filter(Dataset.id == training_job.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Get base model name from config
    base_model_name = training_job.config.get("base_model", "meta-llama/Llama-3.1-8B")
    
    # Create evaluation record
    evaluation = Evaluation(
        training_job_id=request.training_job_id,
        test_results=[],
        metrics={}
    )
    
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    
    # Run evaluation in background
    asyncio.create_task(
        run_evaluation_task(
            evaluation.id,
            dataset.file_path,
            base_model_name,
            training_job.model_path,
            request.test_size,
            db
        )
    )
    
    # Wait a bit for initial results
    await asyncio.sleep(2)
    
    # Refresh to get updated results
    db.refresh(evaluation)
    
    return evaluation


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    """Get evaluation results."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Convert test_results to proper format
    if evaluation.test_results:
        test_examples = [
            TestExample(**result) for result in evaluation.test_results
        ]
    else:
        test_examples = []
    
    # Convert metrics
    if evaluation.metrics:
        metrics = EvaluationMetrics(**evaluation.metrics)
    else:
        metrics = EvaluationMetrics(
            base_model={},
            finetuned_model={}
        )
    
    return {
        "id": evaluation.id,
        "training_job_id": evaluation.training_job_id,
        "test_results": test_examples,
        "metrics": metrics,
        "created_at": evaluation.created_at
    }


@router.post("/{evaluation_id}/rate", response_model=UserRatingResponse, status_code=201)
def submit_rating(
    evaluation_id: int,
    request: UserRatingCreate,
    db: Session = Depends(get_db)
):
    """Submit a user rating for a model comparison."""
    # Verify evaluation exists
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Create rating
    rating = UserRating(
        evaluation_id=evaluation_id,
        example_index=request.example_index,
        preferred_model=request.preferred_model
    )
    
    db.add(rating)
    db.commit()
    db.refresh(rating)
    
    return rating

