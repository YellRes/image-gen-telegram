## Context

当前 `text_to_image.py` 直接调用 OpenRouter 的 `/api/v1/chat/completions` 接口，响应是同步的，图片数据通过 base64 或 URL 形式返回。SoCheap.AI 的 Media API 采用完全不同的模式：异步任务队列，需要先创建任务再轮询状态，最终从 `result.outputs` 读取图片 URL。两者 API 风格差异较大，需要清晰的抽象边界。

## Goals / Non-Goals

**Goals:**
- 接入 SoCheap.AI，实现完整的异步图片生成流程（创建任务 → 轮询 → 下载）
- 通过 `IMAGE_PROVIDER` 环境变量选择 provider，默认 `openrouter` 保持向后兼容
- 新 provider 复用现有的 `output_path`、prompt 等接口，上层调用方无感知

**Non-Goals:**
- 不引入复杂的 OOP 抽象（Provider 基类/接口），保持代码简洁
- 不支持运行时动态切换 provider（进程启动时确定即可）
- 不同步支持 SoCheap.AI 的视频生成能力

## Decisions

### 决策 1：函数级别的 provider 分支，而非类抽象

**选择**：在 `text_to_image.py` 中新增 `_text_to_image_socheap()` 私有函数，`text_to_image()` 根据 `IMAGE_PROVIDER` 环境变量分发调用，不引入 Provider 类。

**理由**：项目目前只有两个 provider，引入基类/接口属于过度设计。函数分支更直观，代码量更少，日后若 provider 增多再重构为类也不复杂。

**备选**：抽象 `BaseProvider` 类 → 否决，当前不值得增加复杂度。

---

### 决策 2：轮询逻辑内置在 `_text_to_image_socheap()` 中

**选择**：轮询间隔 2 秒，最多等待 `timeout` 秒（默认 120 秒）。使用同步 `requests` 库轮询，与现有 OpenRouter 调用保持一致。

**理由**：现有代码已是同步模式，保持一致性。Telegram bot 的图片生成调用已在线程池中运行，不会阻塞事件循环。

---

### 决策 3：图片以 URL 形式下载后保存本地

**选择**：SoCheap.AI 返回的是图片 URL（`result.outputs[0]`），需要额外 GET 请求下载图片并写入 `output_path`。

**理由**：现有接口约定 `text_to_image()` 返回本地文件路径，下游（Telegram 发送、Douyin 上传）均依赖本地文件，保持此约定无需改动下游。

## Risks / Trade-offs

- **轮询超时**：SoCheap.AI 生成时间不确定，若超过 `timeout` 则抛出异常。→ 缓解：默认 timeout 设为 120 秒，并在日志中打印已等待时间。
- **轮询失败无重试**：网络抖动可能导致单次 GET 轮询失败误判任务失败。→ 缓解：仅在 HTTP 非 2xx 且连续 3 次失败时才抛出异常。
- **图片 URL 时效性**：SoCheap.AI 生成的图片 URL 可能有过期时间。→ 缓解：拿到 URL 后立即下载，不缓存 URL。
