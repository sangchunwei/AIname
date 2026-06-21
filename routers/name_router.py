from fastapi import APIRouter,Depends
from core.workflow import generate_naming
from schemas.name_schemas import NameOut, NameIn, FeedbackIn
from core.auth import AuthHandler
auth_handler = AuthHandler()
router = APIRouter(prefix="/names",tags=["names"])

#检查token令牌,如果过期或者不合法就拒绝
#user_id:int=Depends(auth_handler.auth_access_dependency)用户登录校验,如果没有登陆无法访问
@router.post("/get_names",response_model=NameOut)
async def get_names(names:NameIn,user_id:int=Depends(auth_handler.auth_access_dependency)) :
    #user_id用户创建表时用的,当时创的时候用id指定表明,现在查应该用相同的名字才可以
    result=await generate_naming(names,user_id)#返回模型的输出数据
    names_list = result.get("names") if result else []#防止返回None
    return NameOut(names=names_list)

from schemas.name_schemas import NameSchemaWithThreadOut
from core.workflow import generate_naming_v2
@router.post("/generate",response_model=NameSchemaWithThreadOut)
async def take_names_first_time(names:NameIn,user_id:int=Depends(auth_handler.auth_access_dependency)) :
    #user_id用户创建表时用的,当时创的时候用id指定表明,现在查应该用相同的名字才可以
    result=await generate_naming_v2(names,user_id)
    return NameSchemaWithThreadOut(thread_id=result["thread_id"],names=result["names"]["names"])

import traceback
from schemas.name_schemas import FeedbackIn
from core.workflow import feedback_names
@router.post("/feedback",response_model=NameSchemaWithThreadOut)
async def take_names_feedback(data:FeedbackIn,user_id:int=Depends(auth_handler.auth_access_dependency)) :
    """带有 Thread_ID 的多轮微调"""
    result = await feedback_names(data, user_id)
    return NameSchemaWithThreadOut(thread_id=result["thread_id"],
                             names=result["data"].get("names", []))