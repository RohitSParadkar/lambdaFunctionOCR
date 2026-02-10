from google import genai
import os
from aws_secret_extractor import get_secret
import json

from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv("MODEL_NAME")
key = get_secret()
GEMINI_API_KEY = json.loads(key)["GEMINI_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)


def gemini_token_and_generate(prompt: str, model: str = MODEL_NAME) -> dict:
    """
    Counts Gemini tokens and generates content for a given prompt.

    Returns:
        {
            "prompt": str,
            "token_count": int,
            "response_text": str,
            "usage_metadata": dict
        }
    """
    # Count tokens
    token_response = client.models.count_tokens(
        model=model,
        contents=prompt
    )

    token_count = token_response.total_tokens

    # Generate content
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )

    return {
        "prompt": prompt,
        "token_count": token_count,
        "usage_metadata": {
            "prompt_token_count": response.usage_metadata.prompt_token_count,
            "output_token_count": response.usage_metadata.candidates_token_count,
            "total_token_count": response.usage_metadata.total_token_count
        }
    }

def estimate_tokens(text: str) -> int:
    """
    Lightweight token estimation for pre-checks.
    Used ONLY to decide whether chunking is required.

    Rule of thumb:
    1 token ≈ 4 characters (Gemini-safe approximation)
    """
    if not text:
        return 0

    return max(1, len(text) // 4)