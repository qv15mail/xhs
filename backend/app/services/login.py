import asyncio
import json
import os
import time

from app.core.config import settings
from app.services.browser import browser_lock

_QR_SELECTOR = "img.qrcode-img"


class LoginManager:
    """正式扫码登录：Playwright 持久化上下文打开小红书登录页，
    捕获官方二维码图片返回前端，后台轮询登录结果并落库登录态。"""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._playwright = None
        self._context = None
        self._page = None
        self._poll_task: asyncio.Task | None = None
        self._logged_in = self._has_persisted_state()
        self._status = "idle"  # idle / waiting / scanned / success / expired / error
        self._error: str | None = None
        self._started_at = 0.0

    # ---- 持久化登录态 ----
    @property
    def _state_path(self) -> str:
        return os.path.join(settings.user_data_dir, "storage_state.json")

    def _has_persisted_state(self) -> bool:
        """启动时根据已保存的 cookies 判断登录态（存在非空 web_session）。"""
        path = os.path.join(settings.user_data_dir, "cookies.json")
        if not os.path.exists(path):
            return False
        try:
            with open(path, encoding="utf-8") as f:
                cookies = json.load(f)
            return any(c.get("name") == "web_session" and c.get("value") for c in cookies)
        except Exception:  # noqa: BLE001
            return False

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    def status(self) -> str:
        return self._status

    @property
    def error(self) -> str | None:
        return self._error

    async def _is_logged_in(self) -> bool:
        """权威登录判定：持久化上下文中存在非空的 web_session cookie。"""
        if self._context is None:
            return False
        try:
            for c in await self._context.cookies():
                if c.get("name") == "web_session" and c.get("value"):
                    return True
        except Exception:  # noqa: BLE001
            pass
        return False

    async def _cleanup(self):
        for closer in (self._context, self._playwright):
            try:
                if closer is self._context and closer is not None:
                    await closer.close()
                elif closer is self._playwright and closer is not None:
                    await closer.stop()
            except Exception:  # noqa: BLE001
                pass
        self._context = None
        self._page = None
        self._playwright = None

    async def start_qrcode(self) -> dict:
        """打开登录页并返回二维码（data URL）。已登录则直接返回状态。"""
        async with self._lock:
            # 结束上一轮未完成的会话
            if self._poll_task and not self._poll_task.done():
                self._poll_task.cancel()
            await self._cleanup()

            try:
                from playwright.async_api import async_playwright
            except Exception as e:  # noqa: BLE001
                self._status = "error"
                self._error = f"Playwright 不可用: {e}"
                return {"qrcode": "", "note": self._error, "loggedIn": self._logged_in}

            await browser_lock.acquire()
            try:
                self._playwright = await async_playwright().start()
                self._context = await self._playwright.chromium.launch_persistent_context(
                    settings.user_data_dir,
                    headless=False,
                    viewport={"width": 1280, "height": 900},
                )
                self._page = (
                    self._context.pages[0]
                    if self._context.pages
                    else await self._context.new_page()
                )
                await self._page.goto(
                    "https://www.xiaohongshu.com", wait_until="domcontentloaded", timeout=30000
                )
                await self._page.wait_for_timeout(3000)

                # 已登录：保存登录态后直接返回
                if await self._is_logged_in():
                    await self._persist_state()
                    self._logged_in = True
                    self._status = "success"
                    await self._cleanup()
                    browser_lock.release()
                    return {"qrcode": "", "note": "当前已是登录状态", "loggedIn": True}

                # 未登录：尝试点出登录弹窗并抓取二维码
                qr = await self._grab_qrcode()
                if not qr:
                    self._status = "error"
                    self._error = "未能获取二维码，请重试"
                    await self._cleanup()
                    browser_lock.release()
                    return {"qrcode": "", "note": self._error, "loggedIn": False}

                self._status = "waiting"
                self._error = None
                self._started_at = time.time()
                # 后台轮询登录结果（轮询内释放 browser_lock）
                self._poll_task = asyncio.create_task(self._poll_login())
                return {
                    "qrcode": qr,
                    "note": "请使用小红书 App 扫描二维码登录",
                    "loggedIn": False,
                }
            except Exception as e:  # noqa: BLE001
                self._status = "error"
                self._error = str(e)
                await self._cleanup()
                if browser_lock.locked():
                    browser_lock.release()
                return {"qrcode": "", "note": f"打开登录页失败: {e}", "loggedIn": False}

    async def _grab_qrcode(self) -> str:
        page = self._page
        # 登录弹窗通常自动出现；否则点击「登录」入口
        try:
            await page.wait_for_selector(_QR_SELECTOR, timeout=4000)
        except Exception:  # noqa: BLE001
            for txt in ["登录", "登 录", "立即登录"]:
                try:
                    el = await page.query_selector(f"text={txt}")
                    if el:
                        await el.click()
                        break
                except Exception:  # noqa: BLE001
                    continue
            try:
                await page.wait_for_selector(_QR_SELECTOR, timeout=6000)
            except Exception:  # noqa: BLE001
                return ""
        src = await page.evaluate(
            "() => { const e=document.querySelector('img.qrcode-img'); return e? e.src : ''; }"
        )
        return src or ""

    async def _poll_login(self):
        """后台轮询：检测扫码登录是否成功，成功则落库登录态。"""
        try:
            deadline = time.time() + 180  # 二维码有效期内轮询
            while time.time() < deadline:
                await asyncio.sleep(2)
                if self._context is None:
                    break
                if await self._is_logged_in():
                    await self._persist_state()
                    self._logged_in = True
                    self._status = "success"
                    return
            self._status = "expired"
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            self._status = "error"
            self._error = str(e)
        finally:
            await self._cleanup()
            if browser_lock.locked():
                browser_lock.release()

    async def _persist_state(self):
        """保存登录态：storage_state.json + cookies.json。"""
        try:
            os.makedirs(settings.user_data_dir, exist_ok=True)
            await self._context.storage_state(path=self._state_path)
            cookies = await self._context.cookies()
            with open(
                os.path.join(settings.user_data_dir, "cookies.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
        except Exception:  # noqa: BLE001
            pass

    async def logout(self) -> bool:
        """清除登录态：清空持久化上下文 cookie 并删除登录态文件。"""
        async with self._lock:
            if self._poll_task and not self._poll_task.done():
                self._poll_task.cancel()
            await self._cleanup()
            async with browser_lock:
                try:
                    from playwright.async_api import async_playwright

                    async with async_playwright() as p:
                        ctx = await p.chromium.launch_persistent_context(
                            settings.user_data_dir, headless=False
                        )
                        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
                        try:
                            await page.goto(
                                "https://www.xiaohongshu.com",
                                wait_until="domcontentloaded",
                                timeout=20000,
                            )
                            # 清除本地存储，避免 id_token 自动恢复登录态
                            await page.evaluate(
                                "() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }"
                            )
                        except Exception:  # noqa: BLE001
                            pass
                        await ctx.clear_cookies()
                        await ctx.close()
                except Exception:  # noqa: BLE001
                    pass
            for name in ("storage_state.json", "cookies.json"):
                path = os.path.join(settings.user_data_dir, name)
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            self._logged_in = False
            self._status = "idle"
            return False


login_manager = LoginManager()
