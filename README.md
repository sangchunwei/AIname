# AIName

AIName 是一个基于 AI 的多端智能起名应用。前端使用 uni-app 和 Vue 3，可构建为浏览器 H5 页面及 Android App；后端使用 FastAPI，提供账号系统、智能起名、多轮反馈、企业知识库和管理员用户管理功能。

## 主要功能

- 邮箱验证码注册与 JWT 登录
- 人名、企业名、宠物名生成
- LangGraph 多轮会话记忆
- TXT/PDF 企业知识库与 Chroma 向量检索
- 企业 `.com` 域名状态查询
- 管理员隐藏入口
- 普通用户搜索、冻结、解冻、重置密码和软删除
- H5 与 Android 多端支持

## 技术架构

- 前端：uni-app、Vue 3
- API：FastAPI、Uvicorn
- 用户数据库：MySQL、SQLAlchemy、Alembic
- 会话记忆：PostgreSQL、LangGraph Checkpoint
- 验证码缓存：Redis
- AI 模型：DeepSeek
- 向量检索：Chroma、Ollama `nomic-embed-text`

## 目录结构

```text
AIName/
├── ainame/                 uni-app 前端
├── routers/                FastAPI 路由
├── schemas/                请求与响应数据模型
├── models/                 SQLAlchemy 数据模型
├── repository/             数据访问层
├── core/                   鉴权、AI 工作流与 RAG
├── settings/               统一配置入口
├── alembictable/           MySQL 数据库迁移
├── main.py                 FastAPI 应用入口
├── run.py                  Windows 后端启动入口
├── create_admin.py         管理员创建脚本
├── init_pg_memory.py       LangGraph 记忆表初始化
├── requirements.txt        Python 依赖
└── .env.example            配置模板
```

## 环境要求

- Python 3.11 或更高版本
- MySQL 8
- PostgreSQL
- Redis
- Ollama
- HBuilderX（运行或构建 uni-app）

## 后端安装

在项目根目录创建并激活虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 配置

复制配置模板：

```powershell
Copy-Item .env.example .env
```

打开 `.env`，填写真实配置：

```env
AINAME_MYSQL_DB_URI=mysql+aiomysql://用户名:密码@127.0.0.1:3306/ainame?charset=utf8mb4
AINAME_POSTGRES_CHECKPOINT_DB_URI=postgresql://用户名:密码@127.0.0.1:5432/ainame
AINAME_REDIS_URL=redis://127.0.0.1:6379/0

AINAME_DEEPSEEK_API_KEY=你的DeepSeek密钥
AINAME_DEEPSEEK_MODEL=deepseek-chat

AINAME_MAIL_USERNAME=你的QQ邮箱
AINAME_MAIL_PASSWORD=你的QQ邮箱SMTP授权码
AINAME_MAIL_FROM=你的QQ邮箱

AINAME_JWT_SECRET_KEY=至少64字符的随机密钥
```

生成 JWT 密钥：

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

`.env` 包含敏感信息，已通过 `.gitignore` 排除，禁止提交、分享或打包到前端。

## 初始化数据库

请先分别创建 MySQL 和 PostgreSQL 的 `ainame` 数据库，然后执行 MySQL 迁移：

```powershell
alembic upgrade head
```

初始化 LangGraph 的 PostgreSQL 会话记忆表：

```powershell
python init_pg_memory.py
```

确保 Redis 已在 `.env` 配置的地址运行。

安装并启动 Ollama，然后准备向量模型：

```powershell
ollama pull nomic-embed-text
```

## 创建管理员

管理员账号不会硬编码在源码中。创建或提升管理员前，在当前 PowerShell 窗口设置：

```powershell
$env:ADMIN_EMAIL="admin@example.com"
$env:ADMIN_PASSWORD="替换为管理员强密码"
$env:ADMIN_USERNAME="系统管理员"
python create_admin.py
```

管理员创建完成后，可以关闭当前 PowerShell。管理员密码会以哈希形式保存在 MySQL 中。

## 启动后端

Windows 环境建议使用：

```powershell
python run.py
```

默认地址：

- API：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`

## 运行前端

1. 使用 HBuilderX 打开 `ainame` 目录。
2. 检查 `ainame/http/http.js` 中的 `BASE_URL`。
3. 运行到 Chrome 测试 H5，或运行到 Android 真机。

只在本机浏览器测试时，可以使用：

```text
http://127.0.0.1:8000
```

Android 手机测试时不能使用 `127.0.0.1`，需要填写后端电脑的局域网 IPv4 地址，并确保手机与电脑处于同一网络。

## 管理员入口

在普通用户登录页面的“AI 智能起名”标题上，于 4 秒内连续点击 7 次，即可进入管理员登录页面。

隐藏入口只是交互设计，实际管理员权限始终由后端校验。

## Git 提交注意事项

提交前执行：

```powershell
git status
git check-ignore .env
```

必须确认 `.env`、数据库、上传文件、向量库、IDE 配置、构建产物和 APK 没有进入提交列表。APK 建议通过 GitHub Releases 等发布渠道分发。

## 安全提醒

- 不要在源码、README、接口测试文件或截图中填写真实密钥。
- 已经暴露过的 DeepSeek Key、邮箱授权码及数据库密码应在对应服务中作废并重新生成。
- 正式部署必须使用 HTTPS，并限制 FastAPI CORS 来源。
- 管理员账号应使用独立邮箱和高强度密码。
