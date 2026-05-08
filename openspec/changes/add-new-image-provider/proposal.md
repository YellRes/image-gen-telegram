## Why

当前图片生成硬编码使用 OpenRouter 单一 provider，缺乏灵活性且存在单点依赖风险。现在需要接入 SoCheap.AI 作为新的图片生成 provider，以支持更多模型选择和更低成本。

## What Changes

- 新增 SoCheap.AI 图片生成 provider，支持异步任务轮询模式
- 引入 provider 抽象层，通过环境变量选择使用 OpenRouter 还是 SoCheap.AI
- 新增 SoCheap.AI 专用环境变量配置（`SOCHEAP_API_KEY`、`SOCHEAP_BASE_URL`、`IMAGE_PROVIDER`）
- 更新 `.env.example` 说明新增配置项

## Capabilities

### New Capabilities

- `socheap-image-provider`：SoCheap.AI 图片生成能力，包含异步任务创建、状态轮询、结果提取完整流程
- `provider-selection`：通过环境变量 `IMAGE_PROVIDER` 在运行时选择图片生成 provider（`openrouter` 或 `socheap`）

### Modified Capabilities

（无现有规格文件，无需修改）

## Impact

- **文件**：`text_to_image.py`（主要改动）、`.env.example`
- **新增依赖**：无（使用已有的 `requests` 库）
- **配置**：新增 3 个环境变量，旧配置完全向后兼容
- **行为**：默认 provider 保持 `openrouter`，不影响现有用户
