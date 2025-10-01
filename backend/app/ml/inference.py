"""Inference logic for running models."""
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import time
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Cache for loaded models
_model_cache: Dict[str, Any] = {}
_tokenizer_cache: Dict[str, Any] = {}


def load_model(model_path: str, base_model_name: Optional[str] = None) -> tuple:
    """
    Load model and tokenizer, with caching.
    
    Args:
        model_path: Path to model (either base model name or fine-tuned model path)
        base_model_name: Base model name if model_path is a fine-tuned LoRA model
        
    Returns:
        Tuple of (model, tokenizer)
    """
    cache_key = model_path
    
    if cache_key in _model_cache:
        logger.info(f"Using cached model: {cache_key}")
        return _model_cache[cache_key], _tokenizer_cache[cache_key]
    
    logger.info(f"Loading model: {model_path}")
    
    # Load tokenizer
    if base_model_name:
        tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model
    if base_model_name and os.path.exists(model_path):
        # Load base model first, then apply LoRA
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
        )
        model = PeftModel.from_pretrained(base_model, model_path)
        model = model.merge_and_unload()  # Merge LoRA weights for inference
    elif os.path.exists(model_path):
        # Direct model path
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
        )
    else:
        # Assume it's a HuggingFace model name
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
        )
    
    model.eval()
    
    # Cache models
    _model_cache[cache_key] = model
    _tokenizer_cache[cache_key] = tokenizer
    
    return model, tokenizer


def generate_text(
    model_path: str,
    prompt: str,
    max_tokens: int = 256,
    base_model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate text using a model.
    
    Args:
        model_path: Path to model or model name
        prompt: Input prompt
        max_tokens: Maximum tokens to generate
        base_model_name: Base model name if using LoRA fine-tuned model
        
    Returns:
        Dictionary with output, latency_ms, and tokens_used
    """
    start_time = time.time()
    
    try:
        model, tokenizer = load_model(model_path, base_model_name)
        
        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.pad_token_id,
            )
        
        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove prompt from output
        if generated_text.startswith(prompt):
            output = generated_text[len(prompt):].strip()
        else:
            output = generated_text.strip()
        
        # Calculate metrics
        latency_ms = int((time.time() - start_time) * 1000)
        tokens_used = len(outputs[0]) - len(inputs["input_ids"][0])
        
        return {
            "output": output,
            "latency_ms": latency_ms,
            "tokens_used": tokens_used
        }
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}", exc_info=True)
        raise


def clear_model_cache():
    """Clear the model cache to free memory."""
    global _model_cache, _tokenizer_cache
    _model_cache.clear()
    _tokenizer_cache.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

