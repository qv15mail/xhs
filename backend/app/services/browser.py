import asyncio

# 持久化登录态目录同一时刻只能被一个 Chromium 持久化上下文占用，
# 登录（扫码）与采集共享同一把锁，避免「user data dir in use」冲突。
browser_lock = asyncio.Lock()
