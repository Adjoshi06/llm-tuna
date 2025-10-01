"""Model evaluation and comparison logic."""
import json
import asyncio
from typing import Dict, Any, List
from app.ml.inference import generate_text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def evaluate_models(
    dataset_path: str,
    base_model_name: str,
    finetuned_model_path: str,
    test_size: int = 50
) -> Dict[str, Any]:
    """
    Compare base model vs fine-tuned model.
    
    Args:
        dataset_path: Path to JSONL dataset
        base_model_name: Name of base model
        finetuned_model_path: Path to fine-tuned model
        test_size: Number of test examples to use
        
    Returns:
        Dictionary with test_results and metrics
    """
    # Load test examples
    test_examples = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # Use last test_size examples as test set
        test_lines = lines[-test_size:] if len(lines) > test_size else lines
        
        for line in test_lines:
            line = line.strip()
            if not line:
                continue
            example = json.loads(line)
            test_examples.append(example)
    
    logger.info(f"Evaluating on {len(test_examples)} test examples")
    
    # Run inference on both models
    test_results = []
    base_latencies = []
    finetuned_latencies = []
    base_lengths = []
    finetuned_lengths = []
    
    for i, example in enumerate(test_examples):
        prompt = example.get("prompt", "")
        
        if not prompt:
            continue
        
        logger.info(f"Processing example {i+1}/{len(test_examples)}")
        
        # Run base model
        try:
            base_result = generate_text(
                base_model_name,
                prompt,
                max_tokens=256
            )
            base_output = base_result["output"]
            base_latency = base_result["latency_ms"]
            base_tokens = base_result["tokens_used"]
        except Exception as e:
            logger.error(f"Base model error: {str(e)}")
            base_output = f"Error: {str(e)}"
            base_latency = 0
            base_tokens = 0
        
        # Run fine-tuned model
        try:
            finetuned_result = generate_text(
                finetuned_model_path,
                prompt,
                max_tokens=256,
                base_model_name=base_model_name
            )
            finetuned_output = finetuned_result["output"]
            finetuned_latency = finetuned_result["latency_ms"]
            finetuned_tokens = finetuned_result["tokens_used"]
        except Exception as e:
            logger.error(f"Fine-tuned model error: {str(e)}")
            finetuned_output = f"Error: {str(e)}"
            finetuned_latency = 0
            finetuned_tokens = 0
        
        test_results.append({
            "prompt": prompt,
            "base_output": base_output,
            "finetuned_output": finetuned_output,
            "base_latency_ms": base_latency,
            "finetuned_latency_ms": finetuned_latency,
            "base_tokens": base_tokens,
            "finetuned_tokens": finetuned_tokens,
        })
        
        base_latencies.append(base_latency)
        finetuned_latencies.append(finetuned_latency)
        base_lengths.append(base_tokens)
        finetuned_lengths.append(finetuned_tokens)
        
        # Small delay to avoid overwhelming the system
        await asyncio.sleep(0.1)
    
    # Calculate metrics
    avg_base_latency = sum(base_latencies) / len(base_latencies) if base_latencies else 0
    avg_finetuned_latency = sum(finetuned_latencies) / len(finetuned_latencies) if finetuned_latencies else 0
    avg_base_length = sum(base_lengths) / len(base_lengths) if base_lengths else 0
    avg_finetuned_length = sum(finetuned_lengths) / len(finetuned_lengths) if finetuned_lengths else 0
    
    # Estimate cost (rough estimate: $15 per 1M tokens for base, $2 per 1M tokens for fine-tuned)
    base_cost_per_1m = 15.0
    finetuned_cost_per_1m = 2.0
    
    metrics = {
        "base_model": {
            "avg_latency_ms": round(avg_base_latency, 2),
            "avg_length": round(avg_base_length, 2),
            "cost_per_1m_tokens": base_cost_per_1m,
        },
        "finetuned_model": {
            "avg_latency_ms": round(avg_finetuned_latency, 2),
            "avg_length": round(avg_finetuned_length, 2),
            "cost_per_1m_tokens": finetuned_cost_per_1m,
        },
        "improvements": {
            "latency_improvement": round((avg_base_latency - avg_finetuned_latency) / avg_base_latency * 100, 1) if avg_base_latency > 0 else 0,
            "cost_improvement": round((base_cost_per_1m - finetuned_cost_per_1m) / base_cost_per_1m * 100, 1),
        }
    }
    
    return {
        "test_results": test_results,
        "metrics": metrics
    }

