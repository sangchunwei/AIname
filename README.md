# AIName

AIName 是一个面向 H5 与 Android 的 AI 智能起名和品牌冷启动平台。前端使用 uni-app、Vue 3，后端使用 FastAPI，并整合 DeepSeek、LangGraph、RAG、品牌视觉、VIP、社区投票、真人专家精批、钱包分销与 B 端开放平台能力。

> 当前文档版本：`1.0.3`（2026-06-23）。本版本在 `1.0.2` 的品牌视觉、用户/VIP、社区、专家、钱包与分销基础上，继续补齐 B 端开放 API、App 启动页与版本更新检测、社区回复互动、专家订单处理体验、RAG 后台队列和图像接口错误提示。

## 主要功能

### 智能起名

- 人名、企业名和宠物名生成。
- LangGraph 多轮反馈与 PostgreSQL 会话记忆。
- 企业 TXT/PDF 私有知识库：Chroma + Ollama `nomic-embed-text` 语义检索。
- 企业 `.com` 域名状态查询。
- Ollama 代理隔离和 RAG 故障自动降级，避免知识库异常阻断核心起名请求。

### 品牌视觉工作台

- 从企业候选名字创建品牌项目。
- DeepSeek 生成品牌定位、视觉关键词和 Slogan。
- Logo 概念图与名片排版任务。
- Redis 异步视觉任务队列。
- 品牌素材保存与预览。
- 支持 `mock` 本地 SVG 提供器、DashScope 真实图像生成和 OpenAI-compatible 图像接口。
- DashScope 使用官方异步任务接口创建、轮询并下载真实图片结果。
- 1.0.3 优化了正式图像接口调用失败时的错误信息，便于排查 HTTP 状态码、请求异常、非 JSON 返回和空图片结果。

当前默认使用 `mock` 提供器生成本地 SVG 概念图，用于免费测试业务流程；如需真实生成，请在 `.env` 中配置 DashScope。

### 用户中心与 VIP

- 展示用户资料、头像、账号类型、VIP 状态、到期时间和每周额度。
- 昵称、个人简介和密码独立修改。
- 修改密码后所有旧 Token 立即失效。
- 免费用户与 VIP 每周起名、视觉生成额度。
- 月度和年度 VIP 套餐。
- VIP 专家服务折扣。
- 管理员赠送 VIP。

### 个人头像

- 普通用户和专家可在“修改个人资料”中从相册或相机选择头像。
- 支持 JPEG、PNG、WebP，原文件最大 5 MB。
- 服务端校验真实图片内容、纠正 EXIF 方向，并居中裁剪为 512×512 JPEG。
- 内置熊猫、猫咪、兔兔、小熊、狐狸和小鸡 6 个固定卡通头像。
- 可恢复昵称首字默认头像。
- 上传头像保存到 `generated/avatars/`，该目录已被 Git 忽略，不会进入提交。

### 灵感社区

- 发布讨论、点赞和评论。
- 将 AI 候选名字发布为社区投票。
- 防止同一用户对同一投票重复计票。
- 支持修改投票选项。
- 1.0.3 新增评论回复、楼中楼展示、评论点赞、评论预览、展开/收起回复等互动能力。

### 真人专家精批

- 管理员认证国学命名、品牌咨询等专家。
- 专家发布服务并管理订单。
- 用户购买专家精批服务。
- AI 生成专家内部初稿。
- 专家人工审核、修改并交付正式报告。
- 用户在个人中心查看最终报告。
- 1.0.3 优化专家工作台，支持订单状态筛选、订单详情页、客户信息展示、金额展示、AI 初稿生成和报告交付状态反馈。
- 1.0.3 新增专家订单待支付超时与取消逻辑，避免长期占用未支付订单。

AI 初稿不会直接作为专家报告交付，最终报告必须经过专家人工确认。

### 增长、钱包与分销

- 本地模拟现金余额、充值、提现申请和管理员审核。
- 使用钱包余额购买 VIP 和专家精批服务。
- 专家交付报告后获得净收入，平台自动扣除服务费。
- 邀请码、邀请链接和专属二维码。
- 邀请好友注册后双方获得高级 AI 推演次数。
- 孕婴店、工商代办等渠道可申请分销合伙人。
- 被邀请客户购买服务后生成合伙人待结算佣金。
- 管理员审核合伙人、提现申请和佣金结算。
- 1.0.3 在钱包中心补充了冻结余额、待结算余额和奖励次数流水展示。

当前全部资金操作仅为本地账本模拟，不会连接微信、支付宝或银行卡，也不会发生真实资金转移。

### B 端开放平台

1.0.3 新增面向开发者/合作方的开放平台雏形：

- 用户可在个人中心进入“B 端开放平台”。
- 创建开发者应用。
- 创建、重命名、启用、停用和删除 API 密钥。
- API 密钥只展示一次完整明文，后续仅展示前缀和尾号。
- 应用拥有演示调用额度，可本地模拟充值额度。
- 查看调用统计、成功/失败次数、扣费次数、剩余额度和调用日志。
- 开放命名 API 支持游戏 NPC、小说角色、小说地名等场景演示。

开放接口示例：

```text
POST /open/v1/names/game-npc
POST /open/v1/names/novel-character
POST /open/v1/names/novel-place
```

调用时可使用：

```http
Authorization: Bearer ak_test_xxx
```

或：

```http
x-api-key: ak_test_xxx
```

### App 启动页与版本更新

- 1.0.3 新增 Android App 启动页，使用本地启动封面图，默认 3 秒倒计时并支持跳过。
- H5 环境会自动跳过启动页，直接进入登录页、首页或管理员页。
- 新增账号设置页中的“版本更新”入口。
- 后端新增 `/app/version`，可返回最新版本号、是否有更新、是否强制更新、下载地址和更新说明。
- Android 端检测到 APK 更新地址时，可下载并触发安装；其他环境会尝试打开下载地址或复制链接。

### RAG 知识库后台队列

- 1.0.3 将知识库文件上传后的向量化处理改为 RabbitMQ 队列任务。
- 上传接口先保存文件并投递任务，避免用户请求长时间等待。
- 新增独立 `rag_worker.py` 消费者，用于后台处理文档解析和入库。

RabbitMQ 连接已通过 `.env` 配置化，后端上传接口和 `rag_worker.py` 会统一读取 `AINAME_RABBITMQ_URL` 与 `AINAME_RABBITMQ_RAG_QUEUE`。

### 管理员端

- 普通登录页隐藏管理员入口。
- 用户搜索、冻结、解冻和软删除。
- 管理员重置用户密码。
- 赠送 VIP 和认证专家。
- 管理员可审核增长、钱包、合伙人、提现和佣金相关业务。

## 技术架构

- 前端：uni-app、Vue 3。
- API：FastAPI、Uvicorn。
- 用户与业务数据：MySQL、SQLAlchemy、Alembic。
- 会话记忆：PostgreSQL、LangGraph Checkpoint。
- 缓存与视觉任务队列：Redis。
- RAG 后台队列：RabbitMQ。
- 大语言模型：DeepSeek。
- RAG：Chroma、Ollama `nomic-embed-text`。
- 视觉素材：Mock SVG / DashScope / 可配置兼容图像 API。
- 模拟钱包：整数分账本、幂等流水、冻结与待结算余额。
- 开放平台：开发者应用、API Key 哈希存储、调用额度、调用日志。

## 目录结构

```text
AIName/
├── ainame/                 uni-app 前端
├── routers/                FastAPI 路由
├── schemas/                请求和响应模型
├── models/                 SQLAlchemy 数据模型
├── repository/             数据访问层
├── core/                   鉴权、AI、RAG、VIP、视觉、钱包和开放平台服务
├── settings/               统一配置入口
├── alembictable/           MySQL 数据库迁移
├── static/default-avatars/ 固定默认头像
├── generated/              本地生成素材和上传头像，不提交 Git
├── main.py                 FastAPI 应用入口
├── run.py                  Windows 后端启动入口
├── rag_worker.py           RAG 文档解析后台消费者
├── create_admin.py         管理员创建脚本
├── init_pg_memory.py       LangGraph 记忆表初始化
├── requirements.txt        Python 依赖
├── CHANGELOG.md            版本更新记录
└── .env.example            安全配置模板
```

## 环境要求

- Python 3.11 或更高版本。
- MySQL 8。
- PostgreSQL。
- Redis。
- RabbitMQ（1.0.3 RAG 后台队列需要）。
- Ollama。
- HBuilderX。

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
AINAME_RABBITMQ_URL=amqp://用户名:密码@127.0.0.1:5672/
AINAME_RABBITMQ_RAG_QUEUE=rag_document_queue
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

# 真实图像生成示例；本地免费联调可继续使用 AINAME_IMAGE_PROVIDER=mock。
AINAME_IMAGE_PROVIDER=dashscope
AINAME_IMAGE_API_URL=https://dashscope.aliyuncs.com/api/v1
AINAME_IMAGE_API_KEY=你的DashScope API Key
AINAME_IMAGE_MODEL=wanx2.1-t2i-turbo
AINAME_IMAGE_SIZE=1024x1024
AINAME_IMAGE_API_TIMEOUT=180

AINAME_APP_UPDATE_ENABLED=true
AINAME_APP_LATEST_VERSION_NAME=1.0.3
AINAME_APP_LATEST_VERSION_CODE=103
AINAME_APP_MIN_VERSION_CODE=0
AINAME_APP_UPDATE_URL=
AINAME_APP_RELEASE_NOTES=AIName 1.0.3 新增开放平台、版本检测、启动页和社区/专家体验优化。
```

生成 JWT 密钥：

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

`.env` 包含真实密钥，已被 `.gitignore` 排除，禁止提交或分享。

> 注意：`ainame/manifest.json`、`ainame/utils/app-version.js`、`.env.example` 和后端默认版本配置已同步为 `1.0.3/103`。

## 初始化数据库

先创建 MySQL 和 PostgreSQL 的 `ainame` 数据库，然后执行：

```powershell
D:\Anaconda3\envs\fastapi-env\python.exe -m alembic upgrade head
D:\Anaconda3\envs\fastapi-env\python.exe init_pg_memory.py
```

当前 Alembic 最新版本：

```text
a41c8e72b905
```

1.0.3 新增迁移：

- `f2b6c9a1d034`：B 端开放平台开发者应用、API 密钥和调用日志。
- `a41c8e72b905`：社区评论回复和评论点赞。

安装 Ollama 向量模型：

```powershell
ollama pull nomic-embed-text
```

## 启动

启动后端：

```powershell
D:\Anaconda3\envs\fastapi-env\python.exe run.py
```

- API：`http://127.0.0.1:8000`
- Swagger：`http://127.0.0.1:8000/docs`

启动 RAG Worker（如需测试知识库异步入库）：

```powershell
D:\Anaconda3\envs\fastapi-env\python.exe rag_worker.py
```

在 HBuilderX 中打开 `ainame` 目录，检查 `ainame/http/http.js` 的 `BASE_URL` 后运行到 Chrome 或 Android。

## 创建管理员

```powershell
$env:ADMIN_EMAIL="admin@example.com"
$env:ADMIN_PASSWORD="替换为管理员强密码"
$env:ADMIN_USERNAME="系统管理员"
D:\Anaconda3\envs\fastapi-env\python.exe create_admin.py
```

管理员入口：在普通用户登录页面标题上，于 4 秒内连续点击 7 次。

## 测试品牌视觉与支付

默认视觉模式：

```env
AINAME_IMAGE_PROVIDER=mock
```

该模式生成本地 SVG，仅用于测试，不调用收费图片 API。

需要生成真实 Logo 时改为：

```env
AINAME_IMAGE_PROVIDER=dashscope
AINAME_IMAGE_API_URL=https://dashscope.aliyuncs.com/api/v1
AINAME_IMAGE_API_KEY=你的DashScope API Key
AINAME_IMAGE_MODEL=wanx2.1-t2i-turbo
AINAME_IMAGE_SIZE=1024x1024
```

如果旧配置仍写着 `https://dashscope.aliyuncs.com/compatible-mode/v1/images/generations`，后端会自动归一化到 DashScope 官方异步任务地址；但新配置建议直接使用 `/api/v1`。

需要测试 VIP 或专家订单付款时，可在本地临时设置：

```env
AINAME_MOCK_PAYMENT_ENABLED=true
```

生产环境必须恢复为：

```env
AINAME_MOCK_PAYMENT_ENABLED=false
```

## 测试开放平台

1. 使用普通用户登录。
2. 进入个人中心，点击“B 端开放平台”。
3. 创建应用。
4. 创建 API 密钥，并保存首次展示的完整密钥。
5. 使用 Swagger 或 HTTP 工具调用 `/open/v1/names/game-npc`。
6. 在请求头加入 `Authorization: Bearer ak_test_xxx` 或 `x-api-key: ak_test_xxx`。
7. 返回开放平台页面查看额度扣减和调用日志。

## 安全提醒

- 不要在源码、README、测试请求或截图中填写真实密钥。
- 已暴露过的密钥必须在对应平台作废并重新生成。
- 正式部署必须使用 HTTPS，并限制 CORS 来源。
- 模拟支付不得在生产环境启用。
- 当前钱包、充值、提现和佣金均为本地测试功能，不具备真实支付资质或代付能力。
- AI 视觉结果仅作为概念方案，商用前需要确认字体、图片和商标权利。
- 开放平台 API Key 只应展示一次完整明文，数据库只保存哈希值和部分标识。
- RabbitMQ 连接已从代码硬编码迁移到 `.env`，正式部署前应在 `AINAME_RABBITMQ_URL` 中使用专用账号密码。
