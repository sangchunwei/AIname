# AIName

AIName 是一个面向 H5 与 Android 的 AI 智能起名和品牌冷启动平台。前端使用 uni-app、Vue 3，后端使用 FastAPI，并整合 DeepSeek、LangGraph、RAG、品牌视觉、VIP、社区投票和真人专家精批能力。

> 当前版本：`1.0.2`（2026-06-22）。本版本从企业起名后的 AIGC 品牌视觉扩展开始，新增用户与 VIP 中心、社区投票、真人专家、模拟钱包与分销增长体系，并完善管理员、账号安全和头像能力。

## 主要功能

### 智能起名

- 人名、企业名和宠物名生成
- LangGraph 多轮反馈与 PostgreSQL 会话记忆
- 企业 TXT/PDF 私有知识库
- Chroma + Ollama `nomic-embed-text` 语义检索
- 企业 `.com` 域名状态查询
- Ollama 代理隔离和 RAG 故障自动降级

### 品牌视觉工作台

- 从企业候选名字创建品牌项目
- DeepSeek 生成品牌定位、视觉关键词和 Slogan
- Logo 概念图与名片排版任务
- Redis 异步视觉任务队列
- 品牌素材保存与预览

当前默认使用 `mock` 提供器生成本地 SVG 概念图，用于免费测试业务流程；尚未接入正式图片生成 API。

### 用户中心与 VIP

- 用户资料、VIP 状态和到期时间展示
- 昵称、个人简介和密码独立修改页面
- 修改密码后所有旧 Token 立即失效
- 免费用户与 VIP 每日起名、视觉生成额度
- 月度和年度 VIP 套餐
- VIP 专家服务九折
- 管理员赠送 VIP

### 灵感社区

- 发布讨论、点赞和评论
- 将 AI 候选名字发布为社区投票
- 防止同一用户对同一投票重复计票
- 支持修改投票选项

### 真人专家精批

- 管理员认证国学命名、品牌咨询等专家
- 专家发布服务并管理订单
- 用户购买专家精批服务
- AI 生成专家内部初稿
- 专家人工审核、修改并交付正式报告
- 用户在个人中心查看最终报告

AI 初稿不会直接作为专家报告交付，最终报告必须经过专家人工确认。

### 增长、钱包与分销

- 本地模拟现金余额、充值、提现申请和管理员审核
- 使用钱包余额购买 VIP 和专家精批服务
- 专家交付报告后获得净收入，平台自动扣除服务费
- 邀请码、邀请链接和专属二维码
- 邀请好友注册后双方获得高级 AI 推演次数
- 孕婴店、工商代办等渠道申请分销合伙人
- 被邀请客户购买服务后生成合伙人待结算佣金
- 管理员审核合伙人、提现申请和佣金结算

当前全部资金操作仅为本地账本模拟，不会连接微信、支付宝或银行，也不会发生真实资金转移。

### 管理员端

- 普通登录页隐藏管理员入口
- 用户搜索、冻结、解冻和软删除
- 管理员重置用户密码
- 赠送 VIP 和认证专家

## 技术架构

- 前端：uni-app、Vue 3
- API：FastAPI、Uvicorn
- 用户与业务数据：MySQL、SQLAlchemy、Alembic
- 会话记忆：PostgreSQL、LangGraph Checkpoint
- 缓存与任务队列：Redis
- 大语言模型：DeepSeek
- RAG：Chroma、Ollama `nomic-embed-text`
- 视觉素材：Mock SVG / 可配置兼容图像 API
- 模拟钱包：整数分账本、幂等流水、冻结与待结算余额

## 目录结构

```text
AIName/
├── ainame/                 uni-app 前端
├── routers/                FastAPI 路由
├── schemas/                请求和响应模型
├── models/                 SQLAlchemy 数据模型
├── repository/             数据访问层
├── core/                   鉴权、AI、RAG、VIP 和任务服务
├── settings/               统一配置入口
├── alembictable/           MySQL 数据库迁移
├── generated/              本地视觉素材，不提交 Git
├── main.py                 FastAPI 应用入口
├── run.py                  Windows 后端启动入口
├── create_admin.py         管理员创建脚本
├── init_pg_memory.py       LangGraph 记忆表初始化
├── requirements.txt        Python 依赖
├── CHANGELOG.md            版本更新记录
└── .env.example            安全配置模板
```

## 环境要求

- Python 3.11 或更高版本
- MySQL 8
- PostgreSQL
- Redis
- Ollama
- HBuilderX

## 安装依赖

```powershell
cd D:\all_codes\AIName
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

如果使用现有 Conda 环境：

```powershell
D:\Anaconda3\envs\fastapi-env\python.exe -m pip install -r requirements.txt
```

## 配置

复制模板：

```powershell
Copy-Item .env.example .env
```

至少需要配置：

```env
AINAME_MYSQL_DB_URI=mysql+aiomysql://用户名:密码@127.0.0.1:3306/ainame?charset=utf8mb4
AINAME_POSTGRES_CHECKPOINT_DB_URI=postgresql://用户名:密码@127.0.0.1:5432/ainame
AINAME_REDIS_URL=redis://127.0.0.1:6379/0
AINAME_OLLAMA_BASE_URL=http://127.0.0.1:11434
AINAME_OLLAMA_EMBED_MODEL=nomic-embed-text

AINAME_DEEPSEEK_API_KEY=你的DeepSeek密钥
AINAME_DEEPSEEK_MODEL=deepseek-chat

AINAME_MAIL_USERNAME=你的QQ邮箱
AINAME_MAIL_PASSWORD=你的QQ邮箱SMTP授权码
AINAME_MAIL_FROM=你的QQ邮箱

AINAME_JWT_SECRET_KEY=至少64字符的随机密钥
AINAME_IMAGE_PROVIDER=mock
AINAME_MOCK_PAYMENT_ENABLED=false
AINAME_EXPERT_PLATFORM_FEE_BPS=1000
AINAME_DEFAULT_PARTNER_COMMISSION_BPS=1000
AINAME_PUBLIC_H5_URL=http://127.0.0.1:8080
```

生成 JWT 密钥：

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

`.env` 包含真实密钥，已被 `.gitignore` 排除，禁止提交或分享。

## 初始化数据库

先创建 MySQL 和 PostgreSQL 的 `ainame` 数据库，然后执行：

```powershell
D:\Anaconda3\envs\fastapi-env\python.exe -m alembic upgrade head
D:\Anaconda3\envs\fastapi-env\python.exe init_pg_memory.py
```

当前 Alembic 最新版本：

```text
e9a4c72d8f10
```

安装 Ollama 向量模型：

```powershell
ollama pull nomic-embed-text
```

## 创建管理员

```powershell
$env:ADMIN_EMAIL="admin@example.com"
$env:ADMIN_PASSWORD="替换为管理员强密码"
$env:ADMIN_USERNAME="系统管理员"
D:\Anaconda3\envs\fastapi-env\python.exe create_admin.py
```

管理员入口：在普通用户登录页面标题上，于 4 秒内连续点击 7 次。

## 启动

```powershell
D:\Anaconda3\envs\fastapi-env\python.exe run.py
```

- API：`http://127.0.0.1:8000`
- Swagger：`http://127.0.0.1:8000/docs`

在 HBuilderX 中打开 `ainame` 目录，检查 `ainame/http/http.js` 的 `BASE_URL` 后运行到 Chrome 或 Android。

## 测试品牌视觉与支付

默认视觉模式：

```env
AINAME_IMAGE_PROVIDER=mock
```

该模式生成本地 SVG，仅用于测试，不调用收费图片 API。

需要测试 VIP 或专家订单付款时，可在本地临时设置：

```env
AINAME_MOCK_PAYMENT_ENABLED=true
```

生产环境必须恢复为：

```env
AINAME_MOCK_PAYMENT_ENABLED=false
```

## 自定义头像

- 普通用户和专家可在“修改个人资料”中从相册或相机选择头像，也可恢复昵称首字默认头像。
- 内置熊猫、猫咪、兔兔、小熊、狐狸和小鸡 6 个固定卡通头像，可直接选择并跨端显示。
- 支持 JPEG、PNG、WebP，原文件最大 5 MB；服务端会校验真实图片内容、纠正 EXIF 方向并居中裁剪为 512×512 JPEG。
- 头像保存在 `generated/avatars/`，该目录已被 Git 忽略，不会进入版本提交；当前功能复用现有 `user_profile.avatar_url`，无需执行 Alembic 迁移。

## 安全提醒

- 不要在源码、README、测试请求或截图中填写真实密钥。
- 已暴露过的密钥必须在对应平台作废并重新生成。
- 正式部署必须使用 HTTPS，并限制 CORS 来源。
- 模拟支付不得在生产环境启用。
- 当前钱包、充值、提现和佣金均为本地测试功能，不具备真实支付资质或代付能力。
- AI 视觉结果仅作为概念方案，商用前需要确认字体、图片和商标权利。
