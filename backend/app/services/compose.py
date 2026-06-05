from app.models import Note
from app.schemas import ComposeOut, ComposeRequest
from app.services.llm import LLMClient

COMPOSE_SYSTEM = (
    "你是资深小红书内容创作者。请基于用户主题与可选参考，创作原创化的小红书笔记，"
    "禁止直接照搬参考原文。输出 JSON，字段："
    "titles(3个标题字符串数组), body(正文字符串，含适量emoji和换行), "
    "hashtags(话题标签字符串数组，不带#), imageSuggestions(配图建议字符串数组)。只输出 JSON。"
)


def _heuristic_compose(req: ComposeRequest) -> ComposeOut:
    topic = req.topic
    return ComposeOut(
        titles=[
            f"{topic}｜新手必看的 6 个避坑点（附清单）",
            f"研究了一周{topic}，这 3 点最值得抄",
            f"{topic}保姆级教程，看完直接上手",
        ],
        body=(
            f"最近好多姐妹问我{topic}到底怎么入门，今天一次性说清楚！\n\n"
            "✅ 第一，别盲目跟风，先想清楚自己的需求。\n"
            "✅ 第二，选品看核心指标，别为包装买单。\n"
            "✅ 第三，照着清单一步步来，少走弯路。\n\n"
            "整理成清单了，记得点收藏，有问题评论区见～"
        ),
        hashtags=[topic, "干货分享", "亲测有效", "保姆级教程"],
        imageSuggestions=["封面：大字标题 + 痛点关键词", "图2：要点清单卡片", "图3：前后对比图"],
    )


async def compose_note(req: ComposeRequest, ref: Note | None, llm: LLMClient) -> ComposeOut:
    if not llm.configured:
        return _heuristic_compose(req)

    ref_text = ""
    if ref:
        ref_text = f"\n参考笔记标题：{ref.title}\n参考笔记正文：{ref.content}\n"
    user = (
        f"主题/卖点：{req.topic}\n风格：{req.style}\n长度：{req.length}{ref_text}\n"
        "请创作原创笔记。"
    )
    try:
        data = await llm.chat_json(COMPOSE_SYSTEM, user)
        titles = [str(t) for t in data.get("titles", [])][:5]
        return ComposeOut(
            titles=titles or _heuristic_compose(req).titles,
            body=str(data.get("body", "")) or _heuristic_compose(req).body,
            hashtags=[str(h).lstrip("#") for h in data.get("hashtags", [])] or [req.topic],
            imageSuggestions=[str(s) for s in data.get("imageSuggestions", [])],
        )
    except Exception:  # noqa: BLE001
        return _heuristic_compose(req)
