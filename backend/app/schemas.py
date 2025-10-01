"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Dataset Schemas
class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class DatasetResponse(BaseModel):
    id: int
    name: str
    file_path: str
    num_examples: Optional[int]
    validation_status: Optional[str]
    validation_report: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationReport(BaseModel):
    valid: bool
    num_examples: int
    avg_prompt_length: float
    avg_completion_length: float
    issues: List[str]
    recommendations: List[str]


# Training Schemas
class TrainingConfig(BaseModel):
    base_model: str = "meta-llama/Llama-3.1-8B"
    num_epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-4
    max_seq_length: int = 512
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05


class TrainingJobCreate(BaseModel):
    dataset_id: int
    config: Optional[TrainingConfig] = None


class TrainingLog(BaseModel):
    step: int
    loss: float
    timestamp: datetime


class TrainingJobResponse(BaseModel):
    id: int
    dataset_id: int
    status: str
    config: Optional[Dict[str, Any]]
    model_path: Optional[str]
    training_logs: Optional[List[Dict[str, Any]]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


# Evaluation Schemas
class TestExample(BaseModel):
    prompt: str
    base_output: str
    finetuned_output: str
    base_latency_ms: int
    finetuned_latency_ms: int


class EvaluationMetrics(BaseModel):
    base_model: Dict[str, Any]
    finetuned_model: Dict[str, Any]


class EvaluationCreate(BaseModel):
    training_job_id: int
    test_size: int = 50


class EvaluationResponse(BaseModel):
    id: int
    training_job_id: int
    test_results: List[TestExample]
    metrics: EvaluationMetrics
    created_at: datetime

    class Config:
        from_attributes = True


# Inference Schemas
class InferenceRequest(BaseModel):
    model_id: int  # training_job_id
    prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(256, ge=1, le=2048)


class InferenceResponse(BaseModel):
    output: str
    latency_ms: int
    tokens_used: int


# User Rating Schemas
class UserRatingCreate(BaseModel):
    evaluation_id: int
    example_index: int
    preferred_model: str = Field(..., pattern="^(base|finetuned)$")


class UserRatingResponse(BaseModel):
    id: int
    evaluation_id: int
    example_index: int
    preferred_model: str
    created_at: datetime

    class Config:
        from_attributes = True

