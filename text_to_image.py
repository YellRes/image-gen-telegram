"""
Telegram Image Gen - Text to Image using Minimax API
"""

import os
import requests
import base64
import json
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Configuration
load_dotenv()
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID", "")

# API endpoints
MINIMAX_API_URL = "https://api.minimax.chat/v1/image_generation"


def _extract_image_data(response_data: dict) -> tuple[str, str]:
    """Extract image base64/url from Minimax response."""
    try:
        data = response_data.get("data")

        # Old format: data is list with {"base64": "..."}
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0] if isinstance(data[0], dict) else {}
            image_base64 = first_item.get("base64", "")
            image_url = first_item.get("url", "")
            if image_base64 or image_url:
                return image_base64, image_url

        # New format: data is dict with {"image_urls": ["https://..."]}
        if isinstance(data, dict):
            image_urls = data.get("image_urls", [])
            if isinstance(image_urls, list) and len(image_urls) > 0:
                first_url = image_urls[0]
                if isinstance(first_url, str) and first_url:
                    return "", first_url

        raise Exception(f"Image data not found in response: {json.dumps(response_data)[:500]}")
    except Exception as e:
        raise Exception(f"Failed to parse image response: {json.dumps(response_data)[:500]}. Error: {str(e)}")


def text_to_image(prompt: str, output_path: str = None, **kwargs) -> str:
    """
    Generate image from text using Minimax API
    
    Args:
        prompt: Text description of the image to generate
        output_path: Path to save the generated image (optional)
        **kwargs: Additional parameters
    
    Returns:
        Path to the generated image or base64 encoded image data
    """
    if not MINIMAX_API_KEY:
        raise Exception("MINIMAX_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    # Get model, default to a Minimax image model
    model = kwargs.get("model", "image-01")
    
    # Build payload for Minimax
    payload = {
        "model": model,
        "prompt": prompt,
        "num_images": kwargs.get("num_images", 1),
    }
    
    # Optional parameters
    if "aspect_ratio" in kwargs:
        payload["aspect_ratio"] = kwargs["aspect_ratio"]
    if "image_size" in kwargs:
        payload["image_size"] = kwargs["image_size"]
    if "style" in kwargs:
        payload["style"] = kwargs["style"]

    response = requests.post(
        MINIMAX_API_URL,
        headers=headers,
        json=payload,
        timeout=kwargs.get("timeout", 180),
    )
    
    if not response.ok:
        raise Exception(f"Minimax API Error {response.status_code}: {response.text}")

    result = response.json()
    
    # Check for API errors in response
    if "base_resp" in result and result["base_resp"].get("status_code") != 0:
        raise Exception(f"Minimax API Error: {result['base_resp'].get('status_msg', 'Unknown error')}")
    
    image_base64, image_url = _extract_image_data(result)

    if output_path:
        if image_base64:
            # Add padding if necessary
            image_base64 += "=" * ((4 - len(image_base64) % 4) % 4)
            image_bytes = base64.b64decode(image_base64)
        elif image_url:
            image_resp = requests.get(image_url, timeout=kwargs.get("timeout", 180))
            if not image_resp.ok:
                raise Exception(f"Image download failed {image_resp.status_code}: {image_resp.text[:300]}")
            image_bytes = image_resp.content
        else:
            raise Exception("No base64 data or image URL returned from Minimax")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return output_path

    # Keep backward compatibility: prefer returning base64 when no output path provided.
    return image_base64 or image_url


def text_to_image_sync(prompt: str, timeout: int = 120) -> str:
    """
    Backward-compatible wrapper.
    """
    return text_to_image(prompt=prompt, timeout=timeout)


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Text to Image using Minimax")
    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument("-o", "--output", help="Output file path", default="output.jpeg")
    parser.add_argument("--model", default="image-01", help="Minimax image model")
    parser.add_argument("--api-key", help="Minimax API key (or set MINIMAX_API_KEY env)")
    
    args = parser.parse_args()
    
    # Override env vars if provided
    if args.api_key:
        MINIMAX_API_KEY = args.api_key
    
    print(f"Generating image for: {args.prompt}")
    
    try:
        output_path = text_to_image(
            prompt=args.prompt,
            output_path=args.output,
            model=args.model,
        )
        print(f"✅ Image saved to: {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
