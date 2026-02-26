"""
Telegram Image Gen - Text to Image using Minimax API
"""

import os
import requests
import base64
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Configuration
load_dotenv()
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID", "")

# API endpoints
MINIMAX_IMAGE_API_URL = "https://api.minimaxi.com/v1/image_generation"


def _aspect_ratio_from_size(width: Optional[int], height: Optional[int]) -> str:
    """Convert width/height to the nearest supported aspect ratio string."""
    if not width or not height:
        return "1:1"

    target = width / height
    candidates = {
        "1:1": 1.0,
        "16:9": 16 / 9,
        "9:16": 9 / 16,
        "4:3": 4 / 3,
        "3:4": 3 / 4,
    }
    return min(candidates, key=lambda ratio: abs(candidates[ratio] - target))


def _extract_image_base64(result: dict) -> str:
    """Extract first base64 image from different response shapes."""
    data = result.get("data")
    if isinstance(data, dict):
        image_base64 = data.get("image_base64", [])
        if image_base64:
            return image_base64[0]

    # Fallback for legacy response formats
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            if first.get("b64_json"):
                return first["b64_json"]
            if first.get("image_base64"):
                return first["image_base64"]

    raise Exception(f"Failed to parse image response: {result}")


def text_to_image(prompt: str, output_path: str = None, **kwargs) -> str:
    """
    Generate image from text using Minimax API
    
    Args:
        prompt: Text description of the image to generate
        output_path: Path to save the generated image (optional)
        **kwargs: Additional parameters like width, height, steps, etc.
    
    Returns:
        Path to the generated image or base64 encoded image data
    """
    if not MINIMAX_API_KEY:
        raise Exception("MINIMAX_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    aspect_ratio = kwargs.get("aspect_ratio")
    if not aspect_ratio:
        aspect_ratio = _aspect_ratio_from_size(kwargs.get("width"), kwargs.get("height"))

    payload = {
        "model": kwargs.get("model", "image-01"),
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "response_format": "base64",
    }

    # Optional subject reference for image-to-image/character consistency use cases.
    if kwargs.get("subject_reference"):
        payload["subject_reference"] = kwargs["subject_reference"]

    response = requests.post(
        MINIMAX_IMAGE_API_URL,
        headers=headers,
        json=payload,
        timeout=kwargs.get("timeout", 120),
    )
    response.raise_for_status()

    result = response.json()
    image_data = _extract_image_base64(result)

    if output_path:
        image_bytes = base64.b64decode(image_data)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return output_path

    return image_data


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
    parser.add_argument("--width", type=int, default=1024, help="Image width")
    parser.add_argument("--height", type=int, default=1024, help="Image height")
    parser.add_argument("--aspect-ratio", help="Aspect ratio (e.g. 1:1, 16:9, 9:16)")
    parser.add_argument("--model", default="image-01", help="Minimax image model")
    parser.add_argument("--api-key", help="Minimax API key (or set MINIMAX_API_KEY env)")
    
    args = parser.parse_args()
    
    # Override env vars if provided
    if args.api_key:
        MINIMAX_API_KEY = args.api_key
    if args.group_id:
        MINIMAX_GROUP_ID = args.group_id
    
    print(f"Generating image for: {args.prompt}")
    
    try:
        output_path = text_to_image(
            prompt=args.prompt,
            output_path=args.output,
            width=args.width,
            height=args.height,
            aspect_ratio=args.aspect_ratio,
            model=args.model,
        )
        print(f"✅ Image saved to: {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
