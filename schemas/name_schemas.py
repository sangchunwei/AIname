from pydantic import BaseModel, Field, model_validator
from typing import Annotated, List, Literal


#名字类
class NameSchema(BaseModel):
    name: Annotated[str, Field(..., description="The name of the person")]
    reference: Annotated[str, Field(..., description="The name of the person from where")]
    moral: Annotated[str, Field(..., description="寓意")]
    domain: str = Field(..., description="为该品牌设计的纯小写 .com 域名，例如:astar.com")
    domain_status: str = Field(default="正在查询...", description="域名的注册状态")
#  我们给大模型一个要求，让他起名字，一次性起多个名字。所以结构如下
class NameResultSchema(BaseModel):
    names:List[NameSchema]

CategoryLiteral= Literal["人名","企业名","宠物名"]
class NameIn(BaseModel):
    category: Annotated[CategoryLiteral, Field(..., description="命名的分类")]
    surname:Annotated[str,Field("",description="The surname of the name")]
    gender:Annotated[Literal["不限","男","女"],Field("",description="The gender of the name")]
    length:Annotated[str,Field("",description="The length of the name")]
    other:Annotated[str|None,Field("",description="The other person")]
    exclude:Annotated[list[str],Field([],description="The exclude person")]

    @model_validator(mode="after")#接收所有参数后
    def validate(self):
        if self.category == "人名" and not self.surname:
            raise ValueError("给人起名字时必须指定姓氏")
        #因为用户调用NameIn必定期望返回的是对象
        return self


class NameOut(BaseModel):
    names:List[NameSchema]

class NameSchemaWithThreadOut(BaseModel):
    thread_id: str
    names: List[NameSchema]

class FeedbackIn(BaseModel):
    thread_id:str=Field(...,description="前端回传的会话ID")
    category:Literal["人名", "企业名", "宠物名"]=Field(...,description="路由依据")
    feedback:str=Field(...,description="用户的修改意见,如:换成带水字旁的字")

