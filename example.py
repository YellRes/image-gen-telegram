"""
Example usage for text_to_image module
"""

from text_to_image import text_to_image

# Set your OpenRouter API key
import os
os.environ["OPEN_ROUTER_KEY"] = "your-openrouter-api-key"

# Basic usage
result = text_to_image(
    prompt="A beautiful sunset over the ocean, orange and pink sky",
    output_path="examples/sunset.png",
    model="google/gemini-3-flash-preview"
)
print(f"Image saved to: {result}")

# Another example
result2 = text_to_image(
    prompt="Cute cat sitting on a windowsill, looking outside, rainy day",
    output_path="examples/cat.png",
    model="google/gemini-3-flash-preview"
)
print(f"Image saved to: {result2}")
