"""
Telegram Image Gen - Text to Image using OpenRouter API
"""

import os
import time
import requests
import base64
import json
import re
from pathlib import Path
from typing import Optional, Iterable, Dict, Any

from dotenv import load_dotenv

# Configuration
load_dotenv()
OPEN_ROUTER_KEY = os.getenv("OPEN_ROUTER_KEY", "")
SOCHEAP_API_KEY = os.getenv("SOCHEAP_API_KEY", "")
SOCHEAP_BASE_URL = os.getenv("SOCHEAP_BASE_URL", "https://socheap.ai")

_SUPPORTED_PROVIDERS = ("openrouter", "socheap")
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "openrouter")
if IMAGE_PROVIDER not in _SUPPORTED_PROVIDERS:
    raise ValueError(
        f"IMAGE_PROVIDER='{IMAGE_PROVIDER}' 不受支持，可选值：{_SUPPORTED_PROVIDERS}"
    )
if IMAGE_PROVIDER == "socheap" and not SOCHEAP_API_KEY:
    raise ValueError("IMAGE_PROVIDER=socheap 需要设置 SOCHEAP_API_KEY 环境变量")

# API endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_IMAGE_MODEL = "google/gemini-3.1-flash-image-preview"
DEFAULT_SOCHEAP_IMAGE_MODEL = "gpt-image-2"

try:
    from douyin_image_publish import publish_images_to_douyin, is_douyin_publish_enabled
except Exception:
    publish_images_to_douyin = None
    is_douyin_publish_enabled = None


def _extract_data_url_base64(text: str) -> str:
    """Extract base64 payload from a data URL in text."""
    if not text:
        return ""

    match = re.search(r"data:image/[a-zA-Z0-9.+-]+;base64,([A-Za-z0-9+/=]+)", text)
    return match.group(1) if match else ""


def _extract_first_http_url(text: str) -> str:
    """Extract first HTTP URL from text."""
    if not text:
        return ""

    match = re.search(r"https?://[^\s)>\]\"']+", text)
    return match.group(0) if match else ""


def _extract_openrouter_image_data(response_data: dict) -> tuple[str, str]:
    """Extract image base64/url from OpenRouter response payload."""
    try:
        choices = response_data.get("choices", [])
        if not choices or not isinstance(choices, list):
            raise Exception("No choices found")

        first_choice = choices[0] if isinstance(choices[0], dict) else {}
        message = first_choice.get("message", {}) if isinstance(first_choice, dict) else {}
        if not isinstance(message, dict):
            message = {}

        # Some providers return images in message.images.
        images = message.get("images", [])
        if isinstance(images, list) and images:
            first_image = images[0] if isinstance(images[0], dict) else {}
            image_url = first_image.get("image_url", "")
            if isinstance(image_url, dict):
                image_url = image_url.get("url", "")
            image_base64 = first_image.get("b64_json", "")
            if image_base64 or image_url:
                return image_base64, image_url

        content = message.get("content")
        content_items = content if isinstance(content, list) else [content]

        for item in content_items:
            if isinstance(item, dict):
                image_url_value = item.get("image_url")
                if isinstance(image_url_value, dict):
                    image_url_value = image_url_value.get("url", "")
                if isinstance(image_url_value, str) and image_url_value:
                    if image_url_value.startswith("data:image/"):
                        return _extract_data_url_base64(image_url_value), ""
                    return "", image_url_value

                b64_json = item.get("b64_json", "")
                if isinstance(b64_json, str) and b64_json:
                    return b64_json, ""

                text = item.get("text", "")
                if isinstance(text, str) and text:
                    data_base64 = _extract_data_url_base64(text)
                    if data_base64:
                        return data_base64, ""
                    http_url = _extract_first_http_url(text)
                    if http_url:
                        return "", http_url
            elif isinstance(item, str) and item:
                data_base64 = _extract_data_url_base64(item)
                if data_base64:
                    return data_base64, ""
                http_url = _extract_first_http_url(item)
                if http_url:
                    return "", http_url

        raise Exception(f"Image data not found in OpenRouter response: {json.dumps(response_data)[:500]}")
    except Exception as e:
        raise Exception(f"Failed to parse OpenRouter image response: {json.dumps(response_data)[:500]}. Error: {str(e)}")


def _poll_socheap_job(job_id: str, headers: dict, timeout: int) -> str:
    """轮询 SoCheap.AI 任务直到完成，返回图片 URL。"""
    poll_url = f"{SOCHEAP_BASE_URL}/media/image/generations/{job_id}"
    elapsed = 0
    consecutive_errors = 0

    while elapsed < timeout:
        time.sleep(2)
        elapsed += 2

        try:
            resp = requests.get(poll_url, headers=headers, timeout=30)
        except requests.RequestException:
            consecutive_errors += 1
            if consecutive_errors >= 3:
                raise Exception(f"SoCheap.AI 轮询连续 3 次网络错误，job_id={job_id}")
            continue

        if not resp.ok:
            consecutive_errors += 1
            if consecutive_errors >= 3:
                raise Exception(
                    f"SoCheap.AI 轮询 HTTP {resp.status_code} 连续 3 次失败，job_id={job_id}"
                )
            continue

        consecutive_errors = 0
        data = resp.json().get("data", {})

        if data.get("status") == "completed":
            outputs = data.get("result", {}).get("outputs", [])
            if not outputs:
                raise Exception(f"SoCheap.AI job {job_id} 已完成但 outputs 为空")
            return outputs[0]

    raise Exception(f"SoCheap.AI job {job_id} 超时（已等待 {elapsed}s）")


def _text_to_image_socheap(prompt: str, output_path: str = None, **kwargs) -> str:
    """通过 SoCheap.AI 异步 API 生成图片。"""
    headers = {
        "Authorization": f"Bearer {SOCHEAP_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": kwargs.get("model", DEFAULT_SOCHEAP_IMAGE_MODEL),
        "prompt": prompt,
        "resolution": kwargs.get("resolution", "1K"),
        "aspect_ratio": kwargs.get("aspect_ratio", "9:16"),
    }

    # 创建任务
    resp = requests.post(
        f"{SOCHEAP_BASE_URL}/media/image/generations",
        headers=headers,
        json=payload,
        timeout=kwargs.get("timeout", 60),
    )
    if not resp.ok:
        raise Exception(f"SoCheap.AI API 错误 {resp.status_code}: {resp.text[:500]}")

    result = resp.json()
    if result.get("code") != 0:
        raise Exception(f"SoCheap.AI 错误: {result.get('message', 'Unknown error')}")

    job_id = result["data"]["id"]

    # 轮询直到完成
    image_url = _poll_socheap_job(job_id, headers, timeout=kwargs.get("timeout", 120))

    # 下载图片
    img_resp = requests.get(image_url, timeout=60)
    if not img_resp.ok:
        raise Exception(
            f"SoCheap.AI 图片下载失败 {img_resp.status_code}: {image_url}"
        )

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_resp.content)
        return output_path

    return image_url


def _text_to_image_openrouter(prompt: str, output_path: str = None, **kwargs) -> str:
    """通过 OpenRouter API 生成图片。"""
    if not OPEN_ROUTER_KEY:
        raise Exception("OPEN_ROUTER_KEY is not set")

    headers = {
        "Authorization": f"Bearer {OPEN_ROUTER_KEY}",
        "Content-Type": "application/json",
    }

    http_referer = kwargs.get("http_referer") or os.getenv("OPEN_ROUTER_HTTP_REFERER", "")
    x_title = kwargs.get("x_openrouter_title") or os.getenv("OPEN_ROUTER_TITLE", "")
    if http_referer:
        headers["HTTP-Referer"] = http_referer
    if x_title:
        headers["X-OpenRouter-Title"] = x_title

    model = kwargs.get("model", DEFAULT_OPENROUTER_IMAGE_MODEL)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ],
            }
        ],
        "stream": False,
    }

    if "temperature" in kwargs:
        payload["temperature"] = kwargs["temperature"]
    if "max_tokens" in kwargs:
        payload["max_tokens"] = kwargs["max_tokens"]

    response = requests.post(
        OPENROUTER_API_URL,
        headers=headers,
        json=payload,
        timeout=kwargs.get("timeout", 180),
    )
    
    if not response.ok:
        raise Exception(f"OpenRouter API Error {response.status_code}: {response.text}")

    result = response.json()

    if "error" in result:
        error_msg = result["error"].get("message", "Unknown error") if isinstance(result["error"], dict) else str(result["error"])
        raise Exception(f"OpenRouter API Error: {error_msg}")

    image_base64, image_url = _extract_openrouter_image_data(result)

    if output_path:
        if image_base64:
            # Add padding if necessary
            image_base64 += "=" * ((4 - len(image_base64) % 4) % 4)
            image_bytes = base64.b64decode(image_base64)
        elif image_url:
            if image_url.startswith("data:image/"):
                image_base64 = _extract_data_url_base64(image_url)
                if not image_base64:
                    raise Exception("Invalid data URL image payload")
                image_base64 += "=" * ((4 - len(image_base64) % 4) % 4)
                image_bytes = base64.b64decode(image_base64)
            else:
                image_resp = requests.get(image_url, timeout=kwargs.get("timeout", 180))
                if not image_resp.ok:
                    raise Exception(f"Image download failed {image_resp.status_code}: {image_resp.text[:300]}")
                image_bytes = image_resp.content
        else:
            raise Exception("No base64 data or image URL returned from OpenRouter")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return output_path

    # Keep backward compatibility: prefer returning base64 when no output path provided.
    return image_base64 or image_url


def text_to_image(prompt: str, output_path: str = None, **kwargs) -> str:
    """根据 IMAGE_PROVIDER 环境变量分发到对应的图片生成 provider。"""
    if IMAGE_PROVIDER == "socheap":
        return _text_to_image_socheap(prompt, output_path, **kwargs)
    return _text_to_image_openrouter(prompt, output_path, **kwargs)


def text_to_image_sync(prompt: str, timeout: int = 120) -> str:
    """
    Backward-compatible wrapper.
    """
    return text_to_image(prompt=prompt, timeout=timeout)


async def generate_and_publish_to_douyin(
    prompt: str,
    output_path: Optional[str] = None,
    image_paths: Optional[Iterable[str]] = None,
    publish_enabled: Optional[bool] = None,
    title: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
    account_file: Optional[str] = None,
    handle_login: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    Generate image first, then optionally publish to Douyin image post.
    """
    files = [str(Path(p)) for p in (image_paths or []) if p and Path(p).exists()]
    if not files:
        if not output_path:
            raise ValueError("Either output_path or image_paths must be provided")
        generated_path = text_to_image(prompt=prompt, output_path=output_path, **kwargs)
        files = [generated_path]

    result = {
        "image_paths": files,
        "publish_attempted": False,
        "publish_status": "skipped",
        "publish_error": "",
    }

    if publish_enabled is None:
        if is_douyin_publish_enabled is None:
            publish_enabled = False
        else:
            publish_enabled = is_douyin_publish_enabled()

    if not publish_enabled:
        return result

    if publish_images_to_douyin is None:
        result["publish_status"] = "failed"
        result["publish_error"] = "douyin_image_publish import failed"
        return result

    result["publish_attempted"] = True
    try:
        await publish_images_to_douyin(
            title=title or prompt,
            image_paths=files,
            tags=tags,
            account_file=account_file,
            handle_login=handle_login,
        )
        result["publish_status"] = "success"
    except Exception as exc:
        result["publish_status"] = "failed"
        result["publish_error"] = str(exc)
    return result


# CLI interface
if __name__ == "__main__":
    import argparse
    from prompt_manager import prompt_builder, DEFAULT_QUALITY
    
    parser = argparse.ArgumentParser(description="Text to Image using OpenRouter")
    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument("-o", "--output", help="Output file path", default="output.jpeg")
    parser.add_argument("--model", default=None, help="Image model (provider-specific; defaults to provider's default)")
    parser.add_argument("--api-key", help="OpenRouter API key (or set OPEN_ROUTER_KEY env)")
    parser.add_argument("--raw-prompt", action="store_true", help="Use raw prompt without comic explain template")

    args = parser.parse_args()

    # Override env vars if provided
    if args.api_key:
        OPEN_ROUTER_KEY = args.api_key

    final_prompt = args.prompt if args.raw_prompt else prompt_builder.build(
        user_prompt=args.prompt,
        quality=DEFAULT_QUALITY,
        style="comic",
    )

    print(f"Generating image for: {args.prompt}")

    extra = {"model": args.model} if args.model else {}
    try:
        output_path = text_to_image(
            prompt=final_prompt,
            output_path=args.output,
            **extra,
        )
        print(f"[OK] Image saved to: {output_path}")
    except Exception as e:
        print(f"[ERROR] {e}")
