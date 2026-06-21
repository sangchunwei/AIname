"""
项目启动入口（Windows 兼容）
在 uvicorn 创建事件循环之前设置 SelectorEventLoop 策略，
PostgreSQL的psycopg v3的异步模式要求 SelectorEventLoop
解决 psycopg 异步模式与 Windows 默认 ProactorEventLoop 的冲突。
"""
'''
执行逻辑:
1.set_event_loop_policy(SelectorEventLoopPolicy)
       └─ 此时还没有任何事件循环存在，只是设了"未来建循环时用什么策略"
2.import uvicorn
3.uvicorn.run('main:app')
       └─ uvicorn 内部要创建一个事件循环
            └─ 读取当前的 policy → 发现是 SelectorEventLoopPolicy
            └─ 创建 SelectorEventLoop
uvicorn main:app 这个 CLI 命令本身就比 main.py 更早启动了进程和事件循环，main.py 里的代码已经来不及影响它了
'''
"""
此外,使用热加载启动uvicorn服务器会启动一个监视进程（reloader）来监控文件变化,它在某种程度上“绕过”了 ProactorEventLoop 的兼容性问题，所以反
而能正常启动。但是仅仅是绕过了,没有实质性解决问题
"""
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

import uvicorn

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)