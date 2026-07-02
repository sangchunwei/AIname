# AIName 1.0.4 更新报告

更新日期：2026-07-02

## 一句话版本提示

AIName 1.0.4 在 1.0.3 的开放平台、App 版本检测、社区互动、专家订单和 RAG 队列基础上，新增支付宝沙箱 H5 支付、统一支付交易记录、支付结果页、Docker/Nginx 部署配置，并将 VIP、专家服务和钱包充值从本地模拟支付升级为可联调的沙箱支付链路。

## 版本价值

1.0.3 已经完成平台化能力雏形，包括 B 端开放 API、App 更新检测和更完整的用户互动链路。1.0.4 进一步补齐商业闭环中的支付基础设施：

- 面向 C 端用户：VIP 购买、专家服务付款和钱包充值可以进入支付宝沙箱 H5 收银台，前端可查看支付结果并刷新交易状态。
- 面向后端业务：新增统一支付交易表，沉淀外部支付订单号、业务类型、金额、支付宝交易号、通知内容和支付时间。
- 面向部署联调：补充 Dockerfile、docker-compose 和 Nginx 反向代理示例，便于把后端、MySQL、PostgreSQL、Redis 和 Nginx 放进同一部署链路。

## 相比 1.0.3 的主要更新

### 1. 支付宝沙箱 H5 支付

- 新增支付宝沙箱签名服务，支持 RSA2 签名、支付宝公钥验签、H5 收银台 URL 构建和交易查询。
- 新增统一支付路由 `/payments`。
- VIP 订单支持创建支付宝沙箱支付链接。
- 专家订单支持创建支付宝沙箱支付链接，并保留待付款超时校验。
- 钱包充值支持创建支付宝沙箱支付链接，支付确认后自动写入钱包余额流水。
- 新增支付宝异步通知 `/payments/alipay/notify`。
- 新增支付宝同步回跳 `/payments/alipay/return`，回跳到前端支付结果页。
- 新增支付状态查询、同步支付宝交易状态和本地开发确认接口。

### 2. 统一支付交易表

- 新增 `payment_transaction` 模型，用于记录外部交易和内部业务订单的映射。
- 通过 `business_type + business_order_id` 唯一约束，避免同一业务订单重复创建多笔本地交易。
- 记录 `out_trade_no`、`provider`、业务类型、业务订单 ID、金额、主题、状态、支付宝交易号、原始通知和支付时间。
- 新增 Alembic 迁移 `b8f4c2d91a7e_add_payment_transaction.py`。

### 3. 前端支付体验

- VIP 购买支持选择“支付宝沙箱支付”或“余额支付”。
- 专家精批下单支持选择“支付宝沙箱支付”或“余额支付”。
- 钱包充值从“本地模拟充值”调整为“支付宝沙箱充值”。
- 新增支付结果页 `/pages/payment-result/payment-result`，可按 `out_trade_no` 查询和同步支付状态。
- 支付成功后按业务类型回到钱包或用户中心。
- H5 API 地址改为按当前访问主机动态拼接 `:8000`，减少局域网 IP 写死带来的联调成本。

### 4. 模拟支付收敛

- VIP、专家订单和充值的旧模拟支付接口返回 410，提示使用支付宝沙箱支付或余额支付。
- `AINAME_MOCK_PAYMENT_ENABLED` 仅用于本地开发确认支付结果，生产环境必须关闭。
- 钱包提现方式收敛为支付宝账号，微信和银行卡提现选项暂不开放。

### 5. Docker 与 Nginx 部署配置

- 新增 `Dockerfile`，用于构建 FastAPI 后端镜像。
- 新增 `docker-compose.yml`，包含后端、MySQL、PostgreSQL、Redis 和 Nginx 服务示例。
- 新增 `nginx.conf`，将 80 端口请求反向代理到后端 `web:8000`。
- `.env.example` 补充支付宝沙箱配置项。

## 数据与配置变化

### 新增数据库迁移

1.0.4 新增一条迁移：

- `b8f4c2d91a7e`：新增 `payment_transaction` 表及交易号、业务类型、业务订单、状态、支付宝交易号等索引。

当前最新 Alembic 版本：

```text
b8f4c2d91a7e
```

升级命令：

```powershell
D:\Anaconda3\envs\fastapi-env\python.exe -m pip install -r requirements.txt
D:\Anaconda3\envs\fastapi-env\python.exe -m alembic upgrade head
D:\Anaconda3\envs\fastapi-env\python.exe run.py
```

### 新增/建议配置项

```env
AINAME_APP_UPDATE_ENABLED=true
AINAME_APP_LATEST_VERSION_NAME=1.0.4
AINAME_APP_LATEST_VERSION_CODE=104
AINAME_APP_MIN_VERSION_CODE=0
AINAME_APP_UPDATE_URL=
AINAME_APP_RELEASE_NOTES=AIName 1.0.4 新增支付宝沙箱支付、支付结果页、Docker/Nginx 部署配置和支付链路优化。

AINAME_ALIPAY_APP_ID=
AINAME_ALIPAY_PRIVATE_KEY=
AINAME_ALIPAY_PUBLIC_KEY=
AINAME_ALIPAY_NOTIFY_URL=http://127.0.0.1:8000/payments/alipay/notify
AINAME_ALIPAY_RETURN_URL=http://127.0.0.1:8000/payments/alipay/return
```

> 注意：`ainame/manifest.json`、`ainame/utils/app-version.js`、`.env.example` 和后端默认版本配置已同步到 `1.0.4/104`。

## 当前限制

- 支付宝能力当前面向沙箱联调，不代表已经具备正式收单资质。
- 支付宝异步通知本地调试时通常需要公网回调地址或内网穿透；本地可使用开发确认接口辅助联调。
- 提现和佣金仍是本地账本与后台审核流程，不具备真实代付能力。
- Docker Compose 示例仍需要按部署环境补齐 `.env`、RabbitMQ、Ollama、HTTPS 和域名配置。
- App 更新下载地址需要部署 APK 包后配置，当前为空时只会提示未配置下载地址。

## 建议测试范围

- 支付：VIP 支付、专家支付、钱包充值、支付结果页刷新、支付宝同步查询、本地开发确认。
- 钱包：充值入账、余额支付、提现申请、资金流水和奖励次数展示。
- 专家服务：创建订单、支付宝支付、余额支付、待付款超时、取消订单和报告交付。
- VIP：创建订单、支付宝支付、余额支付、订阅开通、分销佣金生成。
- 数据库：执行 Alembic 到 `b8f4c2d91a7e` 后确认 `payment_transaction` 表存在。
- 部署：`docker compose config` 是否能正确解析，Nginx 是否能代理到 `web:8000`。

## 提交建议

```text
feat: add alipay sandbox payment flow and docker deployment config
```
