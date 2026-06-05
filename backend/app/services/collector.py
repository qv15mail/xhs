import asyncio
import json
import random
import uuid

from app.core.config import settings
from app.models import Note

_COVERS = ["#fde2e4", "#e2ece9", "#cddafd", "#fff1e6", "#dfe7fd", "#fde4cf"]
_AUTHORS = ["小羊不吃草", "护肤老中医", "城市漫游家", "穿搭研究所", "露营er阿may"]


class RateLimiter:
    """随机延时 + 并发上限，降低风控风险。"""

    def __init__(self, level: str = "conservative", concurrency: int = 1):
        self._sem = asyncio.Semaphore(max(1, concurrency))
        self._delay = (1.5, 3.5) if level == "conservative" else (0.6, 1.5)

    async def acquire(self):
        await self._sem.acquire()

    def release(self):
        self._sem.release()

    async def wait(self):
        await asyncio.sleep(random.uniform(*self._delay))


def _mock_note(i: int, task_id: str, topic: str) -> Note:
    likes = random.randint(800, 52000)
    titles = [
        f"{topic}｜新手必看的 5 个避坑点",
        f"我用一周时间研究了{topic}，结论是…",
        f"{topic}保姆级教程，看完直接抄作业",
        f"被低估的{topic}，第 3 点太香了",
        f"{topic}｜亲测有效，附清单",
    ]
    return Note(
        id=f"{task_id}-n{i}",
        task_id=task_id,
        note_id=f"{task_id}n{i}",
        title=titles[i % len(titles)],
        content=(
            f"最近很多姐妹问我{topic}怎么做，今天一次性讲清楚。\n\n"
            "首先，最容易踩的坑是盲目跟风。其次，选品要看成分/参数而不是包装。\n\n"
            "我整理了一份清单，照着做就行，记得收藏～"
        ),
        author=_AUTHORS[i % len(_AUTHORS)],
        likes=likes,
        collects=int(likes * 0.6),
        comments=int(likes * 0.08),
        shares=int(likes * 0.04),
        publish_time="",
        url=f"https://www.xiaohongshu.com/explore/{task_id}n{i}",
        cover=_COVERS[i % len(_COVERS)],
        images_json="[]",
        tags_json=json.dumps([topic, "干货分享", "亲测", "保姆级教程"][: random.randint(2, 4)], ensure_ascii=False),
    )


class Collector:
    """采集器：默认 mock；real 模式走 Playwright（需用户自有登录态）。"""

    def __init__(self, mode: str | None = None):
        self.mode = mode or settings.collect_mode

    async def collect(self, task_id: str, topic: str, total: int, limiter: RateLimiter, on_note):
        if self.mode == "real":
            async for note in self._collect_real(task_id, topic, total, limiter):
                await on_note(note)
        else:
            for i in range(total):
                await limiter.acquire()
                try:
                    await limiter.wait()
                    await on_note(_mock_note(i, task_id, topic))
                finally:
                    limiter.release()

    async def _collect_real(self, task_id: str, topic: str, total: int, limiter: RateLimiter):
        """
        真实采集路径（隔离实现）。

        说明：小红书官方 API 不对普通开发者开放，这里采用 Playwright 持久化上下文，
        复用用户「自有账号」登录态，并在浏览器内调用页面自带签名逻辑发起请求。
        为避免依赖未安装的浏览器导致整体不可用，此处在浏览器不可用时回退到 mock。
        """
        try:
            from playwright.async_api import async_playwright
        except Exception:  # noqa: BLE001
            for i in range(total):
                yield _mock_note(i, task_id, topic)
            return

        try:
            async with async_playwright() as p:
                context = await p.chromium.launch_persistent_context(
                    settings.user_data_dir, headless=True
                )
                page = await context.new_page()
                # 实际项目中：访问搜索页 -> 提取 note_id 列表 -> 逐条详情(浏览器内签名)
                # 此处保留结构骨架，详情解析依赖平台页面结构，需在 real 模式下完善。
                await page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded")
                count = 0
                while count < total:
                    await limiter.acquire()
                    try:
                        await limiter.wait()
                        yield _mock_note(count, task_id, topic)  # 占位：替换为真实解析结果
                        count += 1
                    finally:
                        limiter.release()
                await context.close()
        except Exception:  # noqa: BLE001
            for i in range(total):
                yield _mock_note(i, task_id, topic)


def new_task_id() -> str:
    return f"task-{uuid.uuid4().hex[:10]}"
