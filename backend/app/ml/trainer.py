"""Fine-tuning logic using LoRA."""
import os
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset as HFDataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Default LoRA config
LORA_CONFIG = {
    "r": 8,
    "lora_alpha": 16,
    "target_modules": ["q_proj", "v_proj"],
    "lora_dropout": 0.05,
    "bias": "none",
}

# Default training config
DEFAULT_TRAINING_CONFIG = {
    "base_model": "meta-llama/Llama-3.1-8B",
    "num_epochs": 3,
    "batch_size": 4,
    "learning_rate": 2e-4,
    "max_seq_length": 512,
}


def load_dataset_from_jsonl(file_path: str) -> HFDataset:
    """Load dataset from JSONL file."""
    examples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            example = json.loads(line)
            examples.append(example)
    
    return HFDataset.from_list(examples)


def format_prompt_completion(example: Dict[str, str]) -> str:
    """Format prompt and completion into a single text string."""
    prompt = example.get("prompt", "")
    completion = example.get("completion", "")
    return f"{prompt}{completion}"


def tokenize_function(examples, tokenizer, max_length: int):
    """Tokenize examples for training."""
    texts = [format_prompt_completion(ex) for ex in zip(examples["prompt"], examples["completion"])]
    tokenized = tokenizer(
        texts,
        truncation=True,
        max_length=max_length,
        padding="max_length",
        return_tensors="pt"
    )
    tokenized["labels"] = tokenized["input_ids"].clone()
    return tokenized


async def start_training(
    dataset_id: int,
    dataset_path: str,
    config: Dict[str, Any],
    progress_callback: Optional[callable] = None
) -> str:
    """
    Start fine-tuning job.
    
    Args:
        dataset_id: ID of the dataset
        dataset_path: Path to JSONL dataset file
        config: Training configuration
        progress_callback: Optional callback function(step, loss, epoch)
        
    Returns:
        Path to saved model
    """
    try:
        # Merge configs
        training_config = {**DEFAULT_TRAINING_CONFIG, **config}
        lora_config_dict = {**LORA_CONFIG, **config.get("lora", {})}
        
        base_model_name = training_config["base_model"]
        logger.info(f"Loading base model: {base_model_name}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
        )
        
        # Apply LoRA
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_config_dict["r"],
            lora_alpha=lora_config_dict["lora_alpha"],
            target_modules=lora_config_dict["target_modules"],
            lora_dropout=lora_config_dict["lora_dropout"],
            bias=lora_config_dict["bias"],
        )
        
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        
        # Load dataset
        logger.info(f"Loading dataset from {dataset_path}")
        dataset = load_dataset_from_jsonl(dataset_path)
        
        # Tokenize dataset
        def tokenize(examples):
            return tokenize_function(examples, tokenizer, training_config["max_seq_length"])
        
        tokenized_dataset = dataset.map(
            tokenize,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        # Setup training arguments
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "models",
            f"checkpoint_{dataset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        os.makedirs(output_dir, exist_ok=True)
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=training_config["num_epochs"],
            per_device_train_batch_size=training_config["batch_size"],
            learning_rate=training_config["learning_rate"],
            logging_steps=10,
            save_steps=100,
            save_total_limit=3,
            fp16=torch.cuda.is_available(),
            report_to=None,  # Disable wandb/tensorboard for MVP
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False
        )
        
        # Custom trainer with progress callback
        class ProgressTrainer(Trainer):
            def log(self, logs: Dict[str, float]) -> None:
                super().log(logs)
                if progress_callback and "loss" in logs:
                    step = logs.get("step", 0)
                    loss = logs.get("loss", 0.0)
                    epoch = logs.get("epoch", 0.0)
                    if progress_callback:
                        asyncio.create_task(progress_callback(step, loss, epoch))
        
        # Create trainer
        trainer = ProgressTrainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
        )
        
        # Train
        logger.info("Starting training...")
        trainer.train()
        
        # Save final model
        final_model_path = os.path.join(output_dir, "final_model")
        trainer.save_model(final_model_path)
        tokenizer.save_pretrained(final_model_path)
        
        logger.info(f"Training completed. Model saved to {final_model_path}")
        return final_model_path
        
    except Exception as e:
        logger.error(f"Training error: {str(e)}", exc_info=True)
        raise

