"""Dataset validation logic."""
import json
import os
from typing import Dict, List, Any
import tiktoken


def validate_dataset(file_path: str) -> Dict[str, Any]:
    """
    Validate training data and return statistics.
    
    Args:
        file_path: Path to JSONL file
        
    Returns:
        {
            "valid": bool,
            "num_examples": int,
            "avg_prompt_length": float,
            "avg_completion_length": float,
            "issues": List[str],
            "recommendations": List[str]
        }
    """
    issues = []
    recommendations = []
    examples = []
    prompt_lengths = []
    completion_lengths = []
    seen_examples = set()
    
    # Initialize tokenizer for length estimation
    try:
        encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
    except:
        encoding = None
    
    if not os.path.exists(file_path):
        return {
            "valid": False,
            "num_examples": 0,
            "avg_prompt_length": 0.0,
            "avg_completion_length": 0.0,
            "issues": [f"File not found: {file_path}"],
            "recommendations": []
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    example = json.loads(line)
                except json.JSONDecodeError as e:
                    issues.append(f"Line {line_num}: Invalid JSON - {str(e)}")
                    continue
                
                # Check required fields
                if "prompt" not in example or "completion" not in example:
                    issues.append(f"Line {line_num}: Missing 'prompt' or 'completion' field")
                    continue
                
                prompt = str(example["prompt"])
                completion = str(example["completion"])
                
                # Check for empty fields
                if not prompt.strip():
                    issues.append(f"Line {line_num}: Empty prompt")
                    continue
                
                if not completion.strip():
                    issues.append(f"Line {line_num}: Empty completion")
                    continue
                
                # Calculate token lengths
                if encoding:
                    prompt_tokens = len(encoding.encode(prompt))
                    completion_tokens = len(encoding.encode(completion))
                else:
                    # Fallback to character count / 4 (rough estimate)
                    prompt_tokens = len(prompt) // 4
                    completion_tokens = len(completion) // 4
                
                prompt_lengths.append(prompt_tokens)
                completion_lengths.append(completion_tokens)
                
                # Check for very short examples
                if prompt_tokens < 10:
                    issues.append(f"Line {line_num}: Prompt too short ({prompt_tokens} tokens)")
                
                if completion_tokens < 10:
                    issues.append(f"Line {line_num}: Completion too short ({completion_tokens} tokens)")
                
                # Check for very long examples
                if prompt_tokens > 2048:
                    issues.append(f"Line {line_num}: Prompt too long ({prompt_tokens} tokens, max 2048)")
                
                if completion_tokens > 2048:
                    issues.append(f"Line {line_num}: Completion too long ({completion_tokens} tokens, max 2048)")
                
                # Check for duplicates
                example_key = (prompt.lower().strip(), completion.lower().strip())
                if example_key in seen_examples:
                    issues.append(f"Line {line_num}: Duplicate example")
                else:
                    seen_examples.add(example_key)
                
                examples.append(example)
        
        num_examples = len(examples)
        avg_prompt_length = sum(prompt_lengths) / num_examples if num_examples > 0 else 0.0
        avg_completion_length = sum(completion_lengths) / num_examples if num_examples > 0 else 0.0
        
        # Generate recommendations
        if num_examples < 50:
            recommendations.append(f"Dataset has only {num_examples} examples. Consider adding more (recommended: 50+)")
        
        if num_examples > 0:
            if avg_prompt_length < 20:
                recommendations.append("Average prompt length is quite short. Consider more detailed prompts.")
            
            if avg_completion_length < 20:
                recommendations.append("Average completion length is quite short. Consider more detailed completions.")
        
        # Determine validity
        valid = len(issues) == 0 and num_examples >= 10
        
        return {
            "valid": valid,
            "num_examples": num_examples,
            "avg_prompt_length": round(avg_prompt_length, 2),
            "avg_completion_length": round(avg_completion_length, 2),
            "issues": issues[:20],  # Limit to first 20 issues
            "recommendations": recommendations
        }
        
    except Exception as e:
        return {
            "valid": False,
            "num_examples": 0,
            "avg_prompt_length": 0.0,
            "avg_completion_length": 0.0,
            "issues": [f"Error reading file: {str(e)}"],
            "recommendations": []
        }

