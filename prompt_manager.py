"""
Prompt Manager Module
Handles the assembly and management of prompts for image generation.
"""

QUALITY_PRESETS = {
    "low": {
        "label": "低质量(更快)",
        "aspect_ratio": "1:1",
        "image_size": "1K",
        "prompt_suffix": "simple composition, fewer details",
    },
    "medium": {
        "label": "中等质量(1080p)",
        "aspect_ratio": "16:9",
        "image_size": "2K",
        "prompt_suffix": "clean composition, natural lighting, 1080p resolution",
    },
    "high": {
        "label": "高质量(1080p)",
        "aspect_ratio": "16:9",
        "image_size": "2K",
        "prompt_suffix": "highly detailed, sharp focus, cinematic lighting, 1080p high resolution",
    },
}

STYLE_PRESETS = {
    "default": {
        "label": "默认风格",
        "prefix": "",
    },
    "comic": {
        "label": "美式独立漫画 (适合哲理)",
        "prefix": "A single comic book panel, graphic novel style, clean linework, flat vibrant colors, metaphorical and philosophical concept. conceptual illustration of: ",
    }
}

DEFAULT_QUALITY = "medium"
DEFAULT_STYLE = "comic"  # 设为默认，因为你想用来跑纳瓦尔宝典

class PromptBuilder:
    """
    Builder class for constructing image generation prompts based on user input,
    quality settings, and optional style presets.
    """
    
    def __init__(self):
        self.presets = QUALITY_PRESETS
        self.styles = STYLE_PRESETS

    def get_preset(self, quality_level: str) -> dict:
        """
        Get the preset parameters for a specific quality level.
        Falls back to DEFAULT_QUALITY if the requested level is not found.
        """
        return self.presets.get(quality_level, self.presets[DEFAULT_QUALITY])

    def get_style(self, style_level: str) -> dict:
        """
        Get the preset parameters for a specific style level.
        Falls back to DEFAULT_STYLE if the requested level is not found.
        """
        return self.styles.get(style_level, self.styles[DEFAULT_STYLE])

    def build(self, user_prompt: str, quality: str = DEFAULT_QUALITY, style: str = DEFAULT_STYLE) -> str:
        """
        Build the final prompt to be sent to the API.
        
        Args:
            user_prompt: The initial prompt provided by the user.
            quality: The desired quality level (low, medium, high).
            style: The desired style preset.
            
        Returns:
            The assembled prompt string.
        """
        preset = self.get_preset(quality)
        suffix = preset["prompt_suffix"]
        
        style_preset = self.get_style(style)
        prefix = style_preset["prefix"]
        
        # Assemble logic: style prefix + user prompt + quality suffix
        if prefix:
            final_prompt = f"{prefix}{user_prompt}, {suffix}"
        else:
            final_prompt = f"{user_prompt}, {suffix}"
        
        return final_prompt

# Provide a singleton instance
prompt_builder = PromptBuilder()
