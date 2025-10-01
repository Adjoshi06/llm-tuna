"""SQLAlchemy database models."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Dataset(Base):
    """Dataset model for storing training data metadata."""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    num_examples = Column(Integer)
    validation_status = Column(String(50))  # 'valid', 'invalid', 'pending'
    validation_report = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())

    training_jobs = relationship("TrainingJob", back_populates="dataset")


class TrainingJob(Base):
    """Training job model for tracking fine-tuning progress."""
    __tablename__ = "training_jobs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    status = Column(String(50))  # 'queued', 'training', 'completed', 'failed'
    config = Column(JSON)
    model_path = Column(Text)
    training_logs = Column(JSON)  # Array of {step, loss, timestamp}
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    error_message = Column(Text)

    dataset = relationship("Dataset", back_populates="training_jobs")
    evaluations = relationship("Evaluation", back_populates="training_job")


class Evaluation(Base):
    """Evaluation model for storing model comparison results."""
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    training_job_id = Column(Integer, ForeignKey("training_jobs.id"), nullable=False)
    test_results = Column(JSON)  # Stores all comparison results
    metrics = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())

    training_job = relationship("TrainingJob", back_populates="evaluations")
    user_ratings = relationship("UserRating", back_populates="evaluation")


class UserRating(Base):
    """User rating model for tracking which model users prefer."""
    __tablename__ = "user_ratings"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False)
    example_index = Column(Integer, nullable=False)
    preferred_model = Column(String(50))  # 'base' or 'finetuned'
    created_at = Column(TIMESTAMP, server_default=func.now())

    evaluation = relationship("Evaluation", back_populates="user_ratings")

