import  redis
import settings

redis_client = redis.from_url(url=settings.REDIS_URL,decode_responses=True)

# #存入数据
# redis_client.set("username","admin")
# redis_client.set("password","123456")
# #获取数据
# username=redis_client.get("username")
# print(username)
# print(redis_client.exists("username"))
# print(redis_client.exists("dadad"))
# redis_client.delete("username")
# print(redis_client.exists("username"))

#存入redis验证码
#set 可设置时间,到时自动删除  等效于setex
redis_client.set("mail","3456",300)

#判断是否有效
data=redis_client.get("mail")
if data:
    print(f"验证码{data}有效")

