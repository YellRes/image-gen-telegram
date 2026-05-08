## 1. 环境变量与配置

- [x] 1.1 在 `.env.example` 中新增 `IMAGE_PROVIDER`、`SOCHEAP_API_KEY`、`SOCHEAP_BASE_URL` 三个配置项，并附注说明

## 2. SoCheap.AI Provider 实现

- [x] 2.1 在 `text_to_image.py` 中新增 `_text_to_image_socheap(prompt, output_path, **kwargs)` 函数，实现 POST 创建任务逻辑
- [x] 2.2 实现轮询函数：每 2 秒 GET 一次任务状态，`status == "completed"` 时返回图片 URL；超时抛异常；连续 3 次网络失败抛异常
- [x] 2.3 实现图片下载：GET 图片 URL，将二进制内容写入 `output_path`，返回路径字符串

## 3. Provider 选择分发

- [x] 3.1 在 `text_to_image.py` 顶部读取 `IMAGE_PROVIDER` 环境变量，校验合法值（`openrouter` / `socheap`），非法值启动时抛出明确错误
- [x] 3.2 修改 `text_to_image()` 函数：根据 `IMAGE_PROVIDER` 分发到 `_text_to_image_openrouter()`（原逻辑重命名）或 `_text_to_image_socheap()`
- [x] 3.3 校验：`IMAGE_PROVIDER=socheap` 时若 `SOCHEAP_API_KEY` 未设置，抛出明确错误提示

## 4. 测试验证

- [x] 4.1 手动设置 `IMAGE_PROVIDER=socheap` 并配置真实 `SOCHEAP_API_KEY`，运行一次图片生成，确认图片正常保存
- [x] 4.2 确认不设置 `IMAGE_PROVIDER`（默认 openrouter）时，原有功能不受影响
