## ADDED Requirements

### Requirement: 创建图片生成任务
系统 SHALL 通过 POST `{SOCHEAP_BASE_URL}/media/image/generations` 创建图片生成任务，请求体包含 `model`、`prompt`、`resolution`、`aspect_ratio` 字段，并携带 `Authorization: Bearer {SOCHEAP_API_KEY}` 请求头。

#### Scenario: 任务创建成功
- **WHEN** 调用 SoCheap.AI 创建图片任务且 API 返回 `code=0`
- **THEN** 系统从响应 `data.id` 中提取任务 ID 并进入轮询阶段

#### Scenario: 任务创建失败
- **WHEN** API 返回非 2xx HTTP 状态码或 `code != 0`
- **THEN** 系统抛出包含错误信息的异常，终止生成流程

---

### Requirement: 轮询任务状态直至完成
系统 SHALL 每隔 2 秒 GET `{SOCHEAP_BASE_URL}/media/image/generations/{id}` 轮询任务状态，直到 `data.status == "completed"` 或超过 timeout 时长。

#### Scenario: 任务正常完成
- **WHEN** 轮询响应中 `data.status == "completed"`
- **THEN** 系统从 `data.result.outputs[0]` 读取图片 URL，进入下载阶段

#### Scenario: 任务超时
- **WHEN** 累计等待时间超过 `timeout` 秒仍未完成
- **THEN** 系统抛出超时异常，终止生成流程

#### Scenario: 轮询网络错误重试
- **WHEN** 单次 GET 轮询返回非 2xx 状态码
- **THEN** 系统记录错误并继续重试，连续 3 次失败后抛出异常

---

### Requirement: 下载图片并保存到本地路径
系统 SHALL 对 `result.outputs[0]` 的 URL 发起 GET 请求，将图片二进制内容写入 `output_path` 指定的本地文件。

#### Scenario: 图片下载成功
- **WHEN** 图片 URL 可访问且响应为图片二进制内容
- **THEN** 系统将内容写入 `output_path`，函数返回该路径字符串

#### Scenario: 图片 URL 不可访问
- **WHEN** 下载请求返回非 2xx 状态码
- **THEN** 系统抛出包含 URL 和状态码的异常
