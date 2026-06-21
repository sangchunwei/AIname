DB_URI="mysql+aiomysql://root:123456@127.0.0.1:3306/ainame?charset=utf8mb4"

# 邮箱相关配置
MAIL_USERNAME="570591297@qq.com" # 964687160@qq.com
MAIL_PASSWORD="thwnyuokuetsbebg"
MAIL_FROM="570591297@qq.com" # 964687160@qq.com
MAIL_PORT=587
MAIL_SERVER="smtp.qq.com"
MAIL_FROM_NAME="ainameapp"
MAIL_STARTTLS=True # 显式加密
MAIL_SSL_TLS=False # 隐式加密

JWT_SECRET_KEY="grdmskva5151vavmalkwvma414121clamvia"
from datetime import timedelta
JWT_ACCESS_TOKEN_EXPIRES=timedelta(days=1)
JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=30)
