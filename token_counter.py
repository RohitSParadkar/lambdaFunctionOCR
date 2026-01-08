from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
