import asyncio
import json
import random
import uuid
import urllib.parse

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

    # 详情页 DOM 抽取脚本（含从 __INITIAL_STATE__ 兜底解析）。
    _NOTE_DETAIL_SCRIPT = r"""
        (noteId) => {
            const result = {
                noteId: noteId,
                title: '',
                author: '',
                likes: 0,
                collects: 0,
                comments: 0,
                shares: 0,
                publishTime: '',
                content: '',
                tags: []
            };

            const text = (el) => el ? el.textContent.trim() : '';

            const titleEl = document.querySelector('h1, .note-article__title, .note-container__title, .article-title');
            if (titleEl) result.title = text(titleEl);
            if (!result.title) {
                const exploreTitle = document.querySelector('.note-detail__title, .detail__title, .note-info__title');
                if (exploreTitle) result.title = text(exploreTitle);
            }

            const authorEl = document.querySelector('.author__name, .author-name, .user-name, .note-detail__author, .detail-author');
            if (authorEl) result.author = text(authorEl);

            const timeEl = document.querySelector('.publish-time, .time, [class*="time"]');
            if (timeEl) result.publishTime = text(timeEl);

            const contentEl = document.querySelector('.article-article .article-content, .note-article__content, .note-detail__content, .article-title + p, .markdown-body, .note-content');
            if (contentEl) result.content = text(contentEl);

            const tagEls = document.querySelectorAll('[class*="tag"], .search-result__tags, .note-detail__tag, .hashtag');
            tagEls.forEach(el => {
                const t = text(el);
                if (t && !t.includes('话题')) result.tags.push(t);
            });

            // 从 window.__INITIAL_STATE__ / __INITIAL_SSR_STATE__ 兜底提取结构化数据
            const findInState = (root) => {
                if (!root || typeof root !== 'object') return null;
                if (root.noteId === noteId || root.note_id === noteId) return root;
                for (const key of Object.keys(root)) {
                    if (key === '__N_SSP__' || key === '__N_SSG__') continue;
                    try {
                        const hit = findInState(root[key]);
                        if (hit) return hit;
                    } catch (e) { /* 忽略循环引用等异常 */ }
                }
                return null;
            };

            try {
                const initialState = window.__INITIAL_STATE__ || window.__INITIAL_SSR_STATE__;
                if (initialState) {
                    const noteData = findInState(initialState);
                    const note = noteData && (noteData.note || noteData.noteCard || noteData);
                    if (note) {
                        if (!result.title) result.title = note.title || '';
                        if (!result.author) {
                            const u = note.user || note.author || {};
                            result.author = u.nickname || u.nickName || u.nickname_or_id || result.author;
                        }
                        if (!result.content) result.content = note.content || note.desc || note.markdown_desc || '';
                        const ii = note.interactInfo || note.interact_info;
                        if (ii) {
                            result.likes = ii.liked_count || ii.likedCount || 0;
                            result.collects = ii.collected_count || ii.collectedCount || 0;
                            result.comments = ii.comment_count || ii.commentCount || 0;
                            result.shares = ii.share_count || ii.shareCount || 0;
                        }
                        if (Array.isArray(note.tagList)) {
                            note.tagList.forEach(t => { if (t && t.name) result.tags.push(t.name); });
                        } else if (Array.isArray(note.tags)) {
                            note.tags.forEach(t => {
                                const name = typeof t === 'string' ? t : (t && (t.name || t.noteName));
                                if (name) result.tags.push(name);
                            });
                        }
                    }
                }
            } catch (e) {
                console.warn('[Collector] 解析 __INITIAL_STATE__ 失败', e);
            }

            return result;
        }
    """

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
        真实采集路径：Playwright 持久化上下文。

        由于小红书搜索页有较强的反爬措施，采用更可靠的方式：
        1. 直接访问推荐页，收集笔记 URL
        2. 逐条访问详情页提取数据
        """
        try:
            from playwright.async_api import async_playwright
        except Exception:  # noqa: BLE001
            for i in range(total):
                yield _mock_note(i, task_id, topic)
            return

        user_data_dir = settings.user_data_dir
        state_path = f"{user_data_dir}/storage_state.json"

        try:
            async with async_playwright() as p:
                if not __import__("os").path.exists(state_path):
                    print(
                        f"[Collector] 未找到登录态文件 {state_path}，请先在浏览器中完成登录..."
                    )
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir, headless=False, viewport={"width": 1280, "height": 800}
                    )
                    page = context.pages[0] if context.pages else await context.new_page()
                    await page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded")
                    print(
                        "[Collector] 请在打开的浏览器中完成登录；登录完成后请按回车继续..."
                    )
                    await asyncio.to_thread(input)
                    await context.storage_state(path=state_path)
                    await context.close()
                    print(f"[Collector] 登录态已保存: {state_path}")

                # ===== 正式采集 =====
                context = await p.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=False,
                )
                page = await context.new_page()

                # 先访问首页加载登录态
                await page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)

                # 从首页提取 note_id
                note_ids = await self._extract_note_ids_from_page_async(page)
                print(f"[Collector] 首页提取到 {len(note_ids)} 个笔记")

                # 滚动加载更多
                for page_num in range(5):
                    if len(note_ids) >= total:
                        break
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(3000)
                    new_ids = await self._extract_note_ids_from_page_async(page)
                    added = [nid for nid in new_ids if nid not in note_ids]
                    note_ids.extend(added)
                    print(f"[Collector] 滚动 #{page_num + 1} 后共 {len(note_ids)} 个笔记")

                if not note_ids:
                    # 首页没拿到，尝试搜索页
                    print("[Collector] 首页未找到笔记，尝试搜索页...")
                    search_url = f"https://www.xiaohongshu.com/search_result?keyword={urllib.parse.quote(topic)}&source=web_search_result_notes"
                    await page.goto(search_url, wait_until="domcontentloaded")
                    await page.wait_for_timeout(5000)
                    note_ids = await self._extract_note_ids_from_page_async(page)
                    print(f"[Collector] 搜索页提取到 {len(note_ids)} 个笔记")

                # 如果还是不够，从推荐页的链接中获取更多
                for page_num in range(5):
                    if len(note_ids) >= total:
                        break
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(2000)
                    new_ids = await self._extract_note_ids_from_page_async(page)
                    added = [nid for nid in new_ids if nid not in note_ids]
                    note_ids.extend(added)
                    print(f"[Collector] 继续滚动 #{page_num + 1} 后共 {len(note_ids)} 个笔记")

                # 逐条访问详情页提取数据
                count = 0
                for note_id in note_ids[:total]:
                    await limiter.acquire()
                    try:
                        await limiter.wait()
                        note = await self._fetch_note_detail(page, task_id, note_id)
                        if note:
                            yield note
                            count += 1
                            print(f"[Collector] 已采集 {count}/{total}: {note.title}")
                        else:
                            print(f"[Collector] 跳过 {note_id}（无法获取详情）")
                    except Exception as e:
                        print(f"[Collector] 采集 {note_id} 失败: {e}")
                    finally:
                        limiter.release()

                print(f"[Collector] 采集完成: {count}/{total}")
                await context.close()

        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            print(f"[Collector] 采集异常: {e}")
            for i in range(total):
                yield _mock_note(i, task_id, topic)

    def _extract_note_ids_from_page(self, page) -> list[str]:
        """从当前页面提取所有 note_id（通过 JavaScript 执行）"""
        return page.evaluate("""
            () => {
                const allLinks = document.querySelectorAll('a');
                const ids = [];
                const seen = new Set();
                allLinks.forEach(a => {
                    const href = a.href;
                    // 匹配 search_result/{noteId} 或 explore/{noteId}
                    const searchMatch = href.match(/search_result\\/([a-f0-9]+)/);
                    const exploreMatch = href.match(/explore\\/([a-f0-9]+)/);
                    const match = searchMatch || exploreMatch;
                    if (match && match[1] && !seen.has(match[1])) {
                        seen.add(match[1]);
                        ids.push(match[1]);
                    }
                });
                return ids;
            }
        """)

    async def _extract_note_ids_from_page_async(self, page) -> list[str]:
        """异步版提取 note_id"""
        return await self._extract_note_ids_from_page(page)

    async def _fetch_note_detail(self, page, task_id: str, note_id: str) -> Note | None:
        """访问笔记详情页提取结构化数据"""
        url = f"https://www.xiaohongshu.com/explore/{note_id}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)  # 等待 JS 渲染

            # 从页面提取笔记数据
            data = await page.evaluate(self._NOTE_DETAIL_SCRIPT, note_id)

            if not data.get("title") and not data.get("author"):
                # 尝试了所有方式都没拿到数据，可能页面被风控
                print(f"[Collector] 未获取到笔记 {note_id} 的数据，回退到 mock")
                return self._fallback_note(task_id, note_id, note_id)

            return Note(
                id=f"{task_id}-{note_id}",
                task_id=task_id,
                note_id=note_id,
                title=data["title"] or f"小红书笔记 {note_id}",
                content=data["content"] or f"这是一篇关于 {data['title']} 的小红书笔记。",
                author=data["author"] or "小红书用户",
                likes=data["likes"],
                collects=data["collects"],
                comments=data["comments"],
                shares=data["shares"],
                publish_time=data["publishTime"],
                url=f"https://www.xiaohongshu.com/explore/{note_id}",
                cover=random.choice(_COVERS),
                images_json="[]",
                tags_json=json.dumps(data.get("tags", ["小红书"]), ensure_ascii=False),
            )

        except Exception as e:
            print(f"[Collector] 详情页请求失败 {note_id}: {e}")
            return self._fallback_note(task_id, note_id, note_id)

    def _fallback_note(self, task_id: str, note_id: str, _index: int) -> Note:
        """当无法获取真实数据时的回退方案"""
        return Note(
            id=f"{task_id}-{note_id}",
            task_id=task_id,
            note_id=note_id,
            title=f"小红书笔记 {note_id}",
            content="正在采集数据...",
            author="小红书用户",
            likes=0,
            collects=0,
            comments=0,
            shares=0,
            publish_time="",
            url=f"https://www.xiaohongshu.com/explore/{note_id}",
            cover=random.choice(_COVERS),
            images_json="[]",
            tags_json=json.dumps(["小红书"], ensure_ascii=False),
        )


def new_task_id() -> str:
    return f"task-{uuid.uuid4().hex[:10]}"
