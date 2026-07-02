from fastapi import FastAPI,Depends
from fastapi_mail import FastMail, MessageSchema, MessageType
from routers.auth_router import router as auth_router
from routers.name_router import router as name_router
from routers.rag_router import router as rag_router
from routers.admin_router import router as admin_router
from routers.brand_router import router as brand_router
from routers.membership_router import router as membership_router
from routers.community_router import router as community_router
from routers.expert_router import router as expert_router
from routers.growth_router import router as growth_router
from routers.open_platform_router import router as open_platform_router
from routers.open_api_router import router as open_api_router
from routers.app_version_router import router as app_version_router
from routers.payment_router import router as payment_router

from contextlib import asynccontextmanager
from core.workflow import init_workflow_graph, close_workflow_graph
from core.visual_worker import start_visual_worker, stop_visual_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动时，安全地初始化带记忆的工作流
    await init_workflow_graph()
    await start_visual_worker()
    yield
    # 服务停止时，清理数据库连接
    await stop_visual_worker()
    await close_workflow_graph()

app = FastAPI(lifespan=lifespan)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # 允许请求的源列表
    allow_credentials=True,    # 允许携带 Cookie/凭证
    allow_methods=["*"],       # 允许的请求方法（"GET", "POST", "PUT", "DELETE" 等，"*" 表示全部允许）
    allow_headers=["*"],       # 允许的请求头（"*" 表示全部允许）
)
app.include_router(auth_router)
app.include_router(name_router)
app.include_router(rag_router)
app.include_router(admin_router)
app.include_router(brand_router)
app.include_router(membership_router)
app.include_router(community_router)
app.include_router(expert_router)
app.include_router(growth_router)
app.include_router(open_platform_router)
app.include_router(open_api_router)
app.include_router(app_version_router)
app.include_router(payment_router)

from pathlib import Path
from fastapi.staticfiles import StaticFiles
import settings
Path(settings.GENERATED_ASSET_DIR).mkdir(parents=True, exist_ok=True)
app.mount(settings.PUBLIC_ASSET_PREFIX, StaticFiles(directory=settings.GENERATED_ASSET_DIR), name="generated")
app.mount(settings.DEFAULT_AVATAR_PREFIX, StaticFiles(directory=settings.DEFAULT_AVATAR_DIR), name="default-avatars")
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

from dependencies import get_mail
@app.get("/mail/test")
async def mail_test(email:str,mail:FastMail=Depends(get_mail)):
        #  1.准备邮件对象
        message = MessageSchema(
            subject="ainame验证码",
            recipients=[email],
            body=f"Hello {email}",  # 验证码是生产的
            subtype=MessageType.plain)

        await  mail.send_message(message)
        return {"message": "邮件发送成功！"}
