"""Inference endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TrainingJob
from app.schemas import InferenceRequest, InferenceResponse
from app.ml.inference import generate_text

router = APIRouter(prefix="/api/inference", tags=["inference"])


@router.post("", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest,
    db: Session = Depends(get_db)
):
    """Generate text using a fine-tuned model."""
    # Get training job
    training_job = db.query(TrainingJob).filter(TrainingJob.id == request.model_id).first()
    
    if not training_job:
        raise HTTPException(status_code=404, detail="Model not found")
    
    if training_job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Model not ready (status: {training_job.status})"
        )
    
    if not training_job.model_path:
        raise HTTPException(status_code=400, detail="Model path not found")
    
    # Get base model name from config
    base_model_name = training_job.config.get("base_model", "meta-llama/Llama-3.1-8B")
    
    try:
        # Run inference
        result = generate_text(
            training_job.model_path,
            request.prompt,
            max_tokens=request.max_tokens,
            base_model_name=base_model_name
        )
        
        return InferenceResponse(
            output=result["output"],
            latency_ms=result["latency_ms"],
            tokens_used=result["tokens_used"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

