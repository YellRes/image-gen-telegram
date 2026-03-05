## 2026-03-05 social-auto-upload 启动记录

- 用户请求：启动 `social-auto-upload` 项目。
- 已执行：`python sau_backend.py`，后端成功运行于 `http://127.0.0.1:5409`。
- 前端首次启动失败：`vite` 未找到。
- 已修复：在 `social-auto-upload/sau_frontend` 执行 `npm install`。
- 已执行：`npm run dev -- --host 0.0.0.0`，前端成功运行于 `http://localhost:5173/`。
- 当前状态：前后端均在后台运行。
