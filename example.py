"""
Example usage for text_to_image module
"""

from text_to_image import text_to_image

# Set your API key and group ID
import os
os.environ["MINIMAX_API_KEY"] = "your-api-key"
os.environ["MINIMAX_GROUP_ID"] = "your-group-id"

# Basic usage
result = text_to_image(
    prompt="A beautiful sunset over the ocean, orange and pink sky",
    output_path="examples/sunset.png",
    width=1024,
    height=1024
)
print(f"Image saved to: {result}")

# Another example
result2 = text_to_image(
    prompt="Cute cat sitting on a windowsill, looking outside, rainy day",
    output_path="examples/cat.png",
    width=512,
    height=512,
    steps=20
)
print(f"Image saved to: {result2}")
