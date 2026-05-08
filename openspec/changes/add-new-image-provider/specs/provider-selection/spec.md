## ADDED Requirements

### Requirement: 通过环境变量选择图片生成 Provider
系统 SHALL 在进程启动时读取 `IMAGE_PROVIDER` 环境变量，支持 `openrouter`（默认）和 `socheap` 两个值，并将 `text_to_image()` 的实际调用分发到对应的 provider 实现。

#### Scenario: 使用默认 provider（openrouter）
- **WHEN** `IMAGE_PROVIDER` 环境变量未设置或值为 `openrouter`
- **THEN** `text_to_image()` 调用原有 OpenRouter 实现，行为与接入前完全一致

#### Scenario: 切换到 SoCheap provider
- **WHEN** `IMAGE_PROVIDER=socheap` 且 `SOCHEAP_API_KEY` 已设置
- **THEN** `text_to_image()` 调用 `_text_to_image_socheap()` 实现

#### Scenario: SoCheap API Key 缺失
- **WHEN** `IMAGE_PROVIDER=socheap` 但 `SOCHEAP_API_KEY` 环境变量未设置
- **THEN** 系统在启动时或首次调用时抛出明确错误，提示用户配置 `SOCHEAP_API_KEY`

#### Scenario: 无效的 provider 值
- **WHEN** `IMAGE_PROVIDER` 设置为 `openrouter` 和 `socheap` 以外的值
- **THEN** 系统抛出明确错误，列出支持的 provider 名称
