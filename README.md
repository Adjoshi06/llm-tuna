# LLM Tuna

A web platform that makes fine-tuning open-source LLMs accessible to developers without ML expertise. This MVP focuses on simplicity, clean code, and the core value proposition: easy comparison between base and fine-tuned models.

## 🎯 Core Objective

Enable users to:

1. **Upload training data** - Simple JSONL format with drag-and-drop interface
2. **Fine-tune Llama 3.1 8B** - Using LoRA (Low-Rank Adaptation) for efficient training
3. **Evaluate models side-by-side** - Compare base vs fine-tuned model outputs
4. **See clear metrics** - Track improvement, cost, and latency differences

## ✨ Features

### Dataset Management
- Drag-and-drop JSONL file upload
- Automatic validation with detailed feedback
- Dataset preview (first 5 examples)
- Quality checks and recommendations
- Dataset statistics and metadata

### Fine-tuning Pipeline
- LoRA-based fine-tuning for efficient training
- Real-time training progress monitoring
- Training loss visualization
- Configurable hyperparameters
- Automatic checkpoint saving

### Model Evaluation
- Side-by-side comparison of base vs fine-tuned models
- Comprehensive metrics (latency, cost, response length)
- Interactive example navigation
- User preference voting system
- Summary statistics dashboard

### Inference API
- Simple REST API for model inference
- Support for fine-tuned models
- Latency and token usage tracking

## 🛠 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and settings management
- **Hugging Face Transformers** - Model loading and training
- **PEFT (LoRA)** - Parameter-efficient fine-tuning
- **PyTorch** - Deep learning framework

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Recharts** - Data visualization library
- **Axios** - HTTP client

### Infrastructure
- **Docker & Docker Compose** - Containerization and orchestration
- **Local filesystem** - File storage (S3-ready for production)

## 📁 Project Structure

```
finetune-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # SQLAlchemy database models
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── database.py          # Database connection and session
│   │   ├── routers/
│   │   │   ├── datasets.py      # Dataset management endpoints
│   │   │   ├── training.py      # Training job endpoints
│   │   │   ├── evaluation.py    # Evaluation endpoints
│   │   │   └── inference.py     # Inference API endpoints
│   │   └── ml/
│   │       ├── data_validator.py   # Dataset validation logic
│   │       ├── trainer.py          # LoRA fine-tuning implementation
│   │       ├── evaluator.py        # Model comparison logic
│   │       └── inference.py        # Model inference logic
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx                # Dashboard
│   │   ├── datasets/
│   │   │   └── page.tsx            # Dataset management page
│   │   ├── training/
│   │   │   └── [id]/page.tsx      # Training progress page
│   │   └── evaluation/
│   │       └── [id]/page.tsx      # Model comparison page
│   ├── components/
│   │   ├── DatasetUpload.tsx       # File upload component
│   │   ├── TrainingProgress.tsx    # Training monitor component
│   │   ├── ModelComparison.tsx     # Side-by-side comparison
│   │   └── MetricsCard.tsx         # Metrics display component
│   ├── lib/
│   │   └── api.ts                  # API client configuration
│   ├── package.json
│   └── Dockerfile
├── datasets/                       # Uploaded training data (gitignored)
├── models/                         # Model checkpoints (gitignored)
├── docker-compose.yml
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git for cloning the repository
- (Optional) NVIDIA GPU with CUDA support for faster training

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd llm-tuna
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - PostgreSQL database on port 5432
   - FastAPI backend on port 8000
   - Next.js frontend on port 3000

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Initial Setup

The database tables will be automatically created on first startup. No additional setup required!

## 📖 Usage Guide

### 1. Prepare Training Data

Create a JSONL file where each line is a JSON object with `prompt` and `completion` fields:

```jsonl
{"prompt": "Summarize: Patient complains of headache and nausea...", "completion": "Chief complaint: Headache with nausea. Duration: 3 days..."}
{"prompt": "Summarize: Follow-up visit for hypertension...", "completion": "Follow-up: HTN management. BP: 140/90..."}
```

**Requirements:**
- File must have `.jsonl` extension
- Each line must be valid JSON
- Must contain `prompt` and `completion` fields
- Recommended: 50+ examples for good results
- Prompt/completion should be 10-2048 tokens each

### 2. Upload Dataset

1. Navigate to the **Datasets** page
2. Click **Upload Dataset** or drag-and-drop your JSONL file
3. Review the validation results:
   - Number of examples
   - Average prompt/completion lengths
   - Any issues or recommendations
4. If validation passes, the dataset is ready for training

### 3. Start Fine-tuning

1. From the **Datasets** page, click **Train** on a valid dataset
2. Training will start automatically with default LoRA configuration:
   - LoRA rank: 8
   - LoRA alpha: 16
   - Epochs: 3
   - Batch size: 4
   - Learning rate: 2e-4
3. Monitor progress on the training page:
   - Real-time loss chart
   - Current step and epoch
   - Estimated time remaining

### 4. Evaluate Models

1. Once training completes, click **Evaluate Model** from the training page
2. The system will:
   - Use the last 20% of your dataset as test examples
   - Run both base and fine-tuned models on the same prompts
   - Calculate metrics and display side-by-side comparisons
3. Navigate through examples and vote on which model performs better
4. Review summary metrics showing improvements

### 5. Use Fine-tuned Model

Use the inference API to generate text with your fine-tuned model:

```bash
curl -X POST http://localhost:8000/api/inference \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 1,
    "prompt": "Summarize this medical report...",
    "max_tokens": 256
  }'
```

## 📡 API Documentation

### Datasets

- `POST /api/datasets` - Upload a dataset (multipart/form-data)
- `GET /api/datasets` - List all datasets
- `GET /api/datasets/{id}` - Get dataset details
- `DELETE /api/datasets/{id}` - Delete a dataset

### Training

- `GET /api/training` - List all training jobs
- `POST /api/training/start` - Start a new training job
- `GET /api/training/{id}` - Get training job status and logs
- `DELETE /api/training/{id}` - Cancel a training job

### Evaluation

- `POST /api/evaluation/run` - Run evaluation comparing models
- `GET /api/evaluation/{id}` - Get evaluation results
- `POST /api/evaluation/{id}/rate` - Submit user rating

### Inference

- `POST /api/inference` - Generate text with a fine-tuned model

Full interactive API documentation available at `/docs` when the backend is running.

## 🏗 Architecture Overview

### Backend Architecture

- **FastAPI** handles HTTP requests and routing
- **SQLAlchemy** manages database operations with PostgreSQL
- **Pydantic** validates all request/response data
- **Background tasks** run training and evaluation asynchronously
- **Model caching** keeps loaded models in memory for faster inference

### Frontend Architecture

- **Next.js App Router** for file-based routing
- **Server Components** for static content
- **Client Components** for interactive features
- **Real-time updates** via polling (WebSocket-ready for future)
- **Responsive design** with Tailwind CSS

### Data Flow

1. **Upload**: User uploads JSONL → Backend validates → Stores in database
2. **Training**: User starts job → Background task loads model → Applies LoRA → Trains → Saves checkpoint
3. **Evaluation**: User triggers → Loads both models → Runs on test set → Stores results
4. **Inference**: API request → Loads fine-tuned model → Generates text → Returns result

## 🔧 Configuration

### Environment Variables

**Backend** (set in `docker-compose.yml` or `.env`):
- `DATABASE_URL` - PostgreSQL connection string
- `HUGGINGFACE_HUB_CACHE` - Cache directory for models

**Frontend** (set in `docker-compose.yml` or `.env.local`):
- `NEXT_PUBLIC_API_URL` - Backend API URL

### Training Configuration

Default LoRA configuration (can be customized via API):

```python
LORA_CONFIG = {
    "r": 8,                    # LoRA rank
    "lora_alpha": 16,
    "target_modules": ["q_proj", "v_proj"],
    "lora_dropout": 0.05,
    "bias": "none",
}

TRAINING_CONFIG = {
    "base_model": "meta-llama/Llama-3.1-8B",
    "num_epochs": 3,
    "batch_size": 4,
    "learning_rate": 2e-4,
    "max_seq_length": 512,
}
```

## 🧪 Development

### Running Locally (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Database:**
```bash
# Start PostgreSQL locally or use Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=finetune postgres:15-alpine
```

### Database Migrations

The application uses SQLAlchemy's `create_all()` for simplicity. For production, consider using Alembic for migrations.

### Code Quality

- Type hints throughout Python code
- TypeScript for all frontend code
- Pydantic schemas for API validation
- Error handling with meaningful messages
- Logging for debugging

## 📊 Database Schema

### Tables

- **datasets** - Stores uploaded dataset metadata
- **training_jobs** - Tracks training progress and configuration
- **evaluations** - Stores model comparison results
- **user_ratings** - User preferences for model outputs

See `backend/app/models.py` for full schema definitions.

## 🚧 Limitations & Simplifications (MVP)

- **Single base model**: Llama 3.1 8B only
- **Local training**: CPU/GPU on single machine (no distributed training)
- **No authentication**: Single-user system
- **Simple metrics**: No BLEU/ROUGE scores
- **Manual comparison**: No automated quality scoring
- **No model versioning**: Can't rollback to previous versions
- **Local storage**: Files stored on filesystem (not S3)

## 🔮 Future Improvements

- [ ] Support for multiple base models
- [ ] User authentication and multi-tenancy
- [ ] Advanced hyperparameter tuning
- [ ] Distributed training support
- [ ] Cloud GPU orchestration (AWS/GCP)
- [ ] S3 integration for file storage
- [ ] WebSocket for real-time updates
- [ ] Automated quality metrics (BLEU, ROUGE, BERTScore)
- [ ] Model versioning and rollback
- [ ] Export fine-tuned models to HuggingFace Hub
- [ ] Batch inference API
- [ ] Training job scheduling
- [ ] Cost estimation before training
- [ ] Dataset augmentation tools

## 🐛 Troubleshooting

### Training fails with CUDA errors
- Ensure you have compatible CUDA drivers
- Try reducing batch size in training config
- Check available GPU memory

### Database connection errors
- Verify PostgreSQL is running: `docker-compose ps`
- Check database credentials in `docker-compose.yml`
- Ensure database container is healthy

### Frontend can't connect to backend
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS settings in `backend/app/main.py`
- Ensure backend is running on port 8000

### Model download issues
- Check internet connection (models download from HuggingFace)
- Verify HuggingFace token if using private models
- Check disk space for model cache

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📧 Support

[Add support contact information here]

---

**Built with ❤️ for developers who want to fine-tune LLMs without ML expertise**

