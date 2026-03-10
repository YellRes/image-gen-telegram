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
        "prefix": "",
    }
}

DEFAULT_QUALITY = "medium"
DEFAULT_STYLE = "comic"  # 设为默认，因为你想用来跑纳瓦尔宝典

# 固定模板：把任意输入文本转成中文漫画讲解提示词。
COMIC_EXPLAIN_ZH_TEMPLATE = (
    "请根据下面这段内容，创作一张“漫画讲解图”。\n"
    "要求：\n"
    "1) 画面为单张漫画信息图风格，分成4个连贯小分镜（2x2布局）。\n"
    "2) 主题是“用漫画解释概念”，人物动作和场景要直观表达核心含义。\n"
    "3) 画面中允许出现文字时，所有文字必须是简体中文。\n"
    "4) 文案要短句、易懂，适合初学者阅读。\n"
    "5) 风格：清晰线稿、明快配色、干净构图、信息层次明确。\n"
    "6) 不要英文，不要乱码，不要难辨识小字。\n"
    "待解释文本：{user_text}"
)

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

    def build_comic_explain_prompt(self, user_text: str) -> str:
        """
        Build a fixed Chinese comic explanation prompt.
        """
        return COMIC_EXPLAIN_ZH_TEMPLATE.format(user_text=user_text.strip())

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
        
        # comic 风格使用固定中文漫画讲解模板，保证输出稳定。
        if style == "comic":
            final_prompt = f"{self.build_comic_explain_prompt(user_prompt)}, {suffix}"
        elif prefix:
            final_prompt = f"{prefix}{user_prompt}, {suffix}"
        else:
            final_prompt = f"{user_prompt}, {suffix}"
        
        return final_prompt

# Provide a singleton instance
prompt_builder = PromptBuilder()
