import asyncio
import json
import random
import re
import uuid
import urllib.parse

from app.core.config import settings
from app.models import Note

# 小红书正文末尾常见的话题标记，如「#露营[话题]#」，清洗为「#露营」。
_TOPIC_TAG_RE = re.compile(r"#([^#\[\]]+?)\[话题\]#")


def _clean_content(text: str) -> str:
    if not text:
        return ""
    text = _TOPIC_TAG_RE.sub(r"#\1", text)
    return re.sub(r"[ \t]+", " ", text).strip()

_COVERS = ["#fde2e4", "#e2ece9", "#cddafd", "#fff1e6", "#dfe7fd", "#fde4cf"]
_AUTHORS = ["小羊不吃草", "护肤老中医", "城市漫游家", "穿搭研究所", "露营er阿may"]


def _to_int(value) -> int:
    """解析互动数：支持纯数字、字符串、以及「1.2万」「3亿」等中文计数。"""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip().replace(",", "").replace("+", "")
    if not s:
        return 0
    try:
        if s.endswith("万"):
            return int(float(s[:-1]) * 10000)
        if s.endswith("亿"):
            return int(float(s[:-1]) * 100000000)
        return int(float(s))
    except ValueError:
        return 0


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

    # 详情页抽取脚本：优先 window.__INITIAL_STATE__.note.noteDetailMap，DOM 兜底。
    _NOTE_DETAIL_SCRIPT = r"""
        (noteId) => {
            const result = {
                noteId: noteId, title: '', author: '', content: '',
                likes: '', collects: '', comments: '', shares: '',
                publishTime: '', cover: '', tags: [], images: []
            };
            const text = (el) => el ? el.textContent.trim() : '';

            // 1) 结构化数据：__INITIAL_STATE__.note.noteDetailMap
            try {
                const s = window.__INITIAL_STATE__ || window.__INITIAL_SSR_STATE__;
                const map = s && s.note && s.note.noteDetailMap;
                if (map) {
                    let entry = map[noteId];
                    if (!entry) {
                        const k = Object.keys(map).find(x => x !== 'undefined' && map[x] && map[x].note);
                        if (k) entry = map[k];
                    }
                    const n = entry && entry.note;
                    if (n) {
                        result.title = n.title || '';
                        result.content = n.desc || n.content || '';
                        result.author = (n.user || {}).nickname || (n.user || {}).nickName || '';
                        const ii = n.interactInfo || {};
                        result.likes = ii.likedCount != null ? ii.likedCount : '';
                        result.collects = ii.collectedCount != null ? ii.collectedCount : '';
                        result.comments = ii.commentCount != null ? ii.commentCount : '';
                        result.shares = ii.shareCount != null ? ii.shareCount : '';
                        if (n.time) result.publishTime = String(n.time);
                        if (Array.isArray(n.tagList)) {
                            n.tagList.forEach(t => { if (t && t.name) result.tags.push(t.name); });
                        }
                        const imgs = n.imageList || n.imagesList || [];
                        if (Array.isArray(imgs)) {
                            imgs.forEach(im => {
                                const u = im && (im.urlDefault || im.url || (im.infoList && im.infoList[0] && im.infoList[0].url));
                                if (u) result.images.push(u);
                            });
                        }
                        if (result.images.length) result.cover = result.images[0];
                    }
                }
            } catch (e) { /* ignore */ }

            // 2) DOM 兜底
            if (!result.title) result.title = text(document.querySelector('#detail-title, .note-content .title, h1'));
            if (!result.content) result.content = text(document.querySelector('#detail-desc, .note-text, .desc'));
            if (!result.author) result.author = text(document.querySelector('.author-wrapper .username, .username, .author-name'));

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

        小红书笔记详情页需要 `xsec_token` 才能访问（缺失会重定向到 404）。
        因此先从「搜索结果页」（主题驱动）或「推荐页」收集 (note_id, xsec_token, source)，
        再带 token 逐条访问详情页，从 `window.__INITIAL_STATE__` 提取结构化数据。
        """
        try:
            from playwright.async_api import async_playwright
        except Exception:  # noqa: BLE001
            for i in range(total):
                yield _mock_note(i, task_id, topic)
            return

        user_data_dir = settings.user_data_dir

        try:
            from app.services.browser import browser_lock

            async with browser_lock, async_playwright() as p:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=False,
                    viewport={"width": 1280, "height": 800},
                )
                page = context.pages[0] if context.pages else await context.new_page()

                # 主题驱动：优先搜索页；不足再用推荐页补充
                items = await self._collect_search_items(page, topic, total)
                print(f"[Collector] 搜索页「{topic}」提取到 {len(items)} 个笔记")
                if len(items) < total:
                    feed_items = await self._collect_feed_items(page, total - len(items))
                    print(f"[Collector] 推荐页补充 {len(feed_items)} 个笔记")
                    items.extend(feed_items)

                # 去重
                seen: set[str] = set()
                uniq: list[dict] = []
                for it in items:
                    if it["id"] and it["id"] not in seen:
                        seen.add(it["id"])
                        uniq.append(it)

                count = 0
                for it in uniq[:total]:
                    await limiter.acquire()
                    try:
                        await limiter.wait()
                        note = await self._fetch_note_detail(page, task_id, it)
                        if note:
                            title = note.title
                            yield note
                            count += 1
                            print(f"[Collector] 已采集 {count}/{total}: {title}")
                        else:
                            print(f"[Collector] 跳过 {it['id']}（无法获取详情）")
                    except Exception as e:  # noqa: BLE001
                        print(f"[Collector] 采集 {it['id']} 失败: {e}")
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

    # 从搜索结果页 DOM 提取 (id, token, source)：搜索页 a[href] 自带 xsec_token。
    _SEARCH_ITEMS_SCRIPT = r"""
        () => {
            const out = [];
            const seen = new Set();
            document.querySelectorAll('a[href*="/search_result/"], a[href*="/explore/"]').forEach(a => {
                const href = a.getAttribute('href') || '';
                const m = href.match(/(?:search_result|explore)\/([a-f0-9]+)/);
                if (!m || !m[1] || seen.has(m[1])) return;
                let token = '', source = '';
                try {
                    const qs = new URLSearchParams(href.split('?')[1] || '');
                    token = qs.get('xsec_token') || '';
                    source = qs.get('xsec_source') || '';
                } catch (e) { /* ignore */ }
                if (!token) return;
                seen.add(m[1]);
                out.push({ id: m[1], token, source: source || 'pc_search' });
            });
            return out;
        }
    """

    async def _collect_search_items(self, page, topic: str, total: int) -> list[dict]:
        search_url = (
            "https://www.xiaohongshu.com/search_result?"
            f"keyword={urllib.parse.quote(topic)}&source=web_search_result_notes"
        )
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:  # noqa: BLE001
            print(f"[Collector] 搜索页打开失败: {e}")
            return []
        await page.wait_for_timeout(5000)

        items: list[dict] = []
        seen: set[str] = set()

        async def harvest():
            for it in await page.evaluate(self._SEARCH_ITEMS_SCRIPT):
                if it["id"] not in seen:
                    seen.add(it["id"])
                    items.append(it)

        await harvest()
        for _ in range(8):
            if len(items) >= total:
                break
            await page.evaluate("window.scrollBy(0, window.innerHeight * 1.5)")
            await page.wait_for_timeout(2500)
            await harvest()
        return items

    async def _collect_feed_items(self, page, total: int) -> list[dict]:
        try:
            await page.goto(
                "https://www.xiaohongshu.com/explore", wait_until="domcontentloaded", timeout=20000
            )
        except Exception as e:  # noqa: BLE001
            print(f"[Collector] 推荐页打开失败: {e}")
            return []
        await page.wait_for_timeout(4000)

        # 推荐页 token 在 __INITIAL_STATE__.feed.feeds 中，DOM href 不带 token。
        script = r"""
            () => {
                const out = [];
                try {
                    const s = window.__INITIAL_STATE__;
                    let fd = s && s.feed && s.feed.feeds;
                    if (fd && fd._value !== undefined) fd = fd._value;
                    if (Array.isArray(fd)) {
                        fd.forEach(n => {
                            if (n && n.id && n.xsecToken) {
                                out.push({ id: n.id, token: n.xsecToken, source: 'pc_feed' });
                            }
                        });
                    }
                } catch (e) { /* ignore */ }
                return out;
            }
        """
        items: list[dict] = []
        seen: set[str] = set()

        async def harvest():
            for it in await page.evaluate(script):
                if it["id"] not in seen:
                    seen.add(it["id"])
                    items.append(it)

        await harvest()
        for _ in range(6):
            if len(items) >= total:
                break
            await page.evaluate("window.scrollBy(0, window.innerHeight * 1.5)")
            await page.wait_for_timeout(2500)
            await harvest()
        return items

    async def _fetch_note_detail(self, page, task_id: str, item: dict) -> Note | None:
        """带 xsec_token 访问笔记详情页，从 __INITIAL_STATE__ 提取结构化数据。"""
        note_id = item["id"]
        token = item.get("token", "")
        source = item.get("source") or "pc_feed"
        url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={token}&xsec_source={source}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2500)

            data = await page.evaluate(self._NOTE_DETAIL_SCRIPT, note_id)

            if not data.get("title") and not data.get("author") and not data.get("content"):
                print(f"[Collector] 未获取到笔记 {note_id} 的数据，回退占位")
                return self._fallback_note(task_id, note_id, note_id)

            return Note(
                id=f"{task_id}-{note_id}",
                task_id=task_id,
                note_id=note_id,
                title=data.get("title") or f"小红书笔记 {note_id}",
                content=_clean_content(data.get("content")) or "",
                author=data.get("author") or "小红书用户",
                likes=_to_int(data.get("likes")),
                collects=_to_int(data.get("collects")),
                comments=_to_int(data.get("comments")),
                shares=_to_int(data.get("shares")),
                publish_time=data.get("publishTime") or "",
                url=f"https://www.xiaohongshu.com/explore/{note_id}",
                cover=data.get("cover") or random.choice(_COVERS),
                images_json=json.dumps(data.get("images", []), ensure_ascii=False),
                tags_json=json.dumps(data.get("tags", []), ensure_ascii=False),
            )

        except Exception as e:  # noqa: BLE001
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
