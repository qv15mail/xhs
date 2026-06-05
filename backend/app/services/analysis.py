import re
from collections import Counter

import jieba

from app.models import Note
from app.schemas import BreakdownOut, KeywordOut, RankingOut
from app.services.llm import LLMClient

STOPWORDS = {
    "的", "了", "和", "是", "我", "你", "他", "她", "也", "都", "就", "在", "有",
    "这", "那", "一个", "我们", "你们", "以及", "可以", "什么", "怎么", "一下",
    "今天", "大家", "很多", "还有", "一起", "因为", "所以", "但是", "如果",
    "记得", "一定", "真的", "这个", "那个", "不是", "没有", "自己", "时候",
}

TOKEN_RE = re.compile(r"[\u4e00-\u9fa5A-Za-z]{2,}")


def extract_keywords(notes: list[Note], top_k: int = 20) -> list[KeywordOut]:
    counter: Counter[str] = Counter()
    for n in notes:
        text = f"{n.title} {n.content}"
        for token in jieba.cut(text):
            token = token.strip()
            if not TOKEN_RE.fullmatch(token) or token in STOPWORDS:
                continue
            counter[token] += 1
    return [KeywordOut(word=w, count=c) for w, c in counter.most_common(top_k)]


def _engagement_score(n: Note) -> int:
    return round((n.likes + n.collects * 1.5 + n.comments * 2 + n.shares * 2) / 100)


def _reasons(n: Note) -> list[str]:
    reasons: list[str] = []
    reasons.append("数字标题" if re.search(r"\d", n.title) else "悬念标题")
    if any(k in n.content[:30] for k in ("最近", "很多人", "姐妹", "你是不是")):
        reasons.append("痛点开头")
    import json

    tags = json.loads(n.tags_json or "[]")
    reasons.append("标签密集" if len(tags) >= 3 else "强干货")
    return reasons


def build_ranking(notes: list[Note], top_k: int = 10) -> list[RankingOut]:
    ranked = sorted(notes, key=_engagement_score, reverse=True)[:top_k]
    return [
        RankingOut(
            noteId=n.id,
            title=n.title,
            author=n.author,
            score=_engagement_score(n),
            likes=n.likes,
            reasons=_reasons(n),
        )
        for n in ranked
    ]


def heuristic_breakdown(n: Note) -> BreakdownOut:
    has_num = bool(re.search(r"\d", n.title))
    return BreakdownOut(
        noteId=n.id,
        titleFormula=(
            "数字 + 痛点 + 利益承诺" if has_num else "悬念/反差 + 利益承诺"
        ),
        hook="开头用共鸣式提问或反常识结论留住读者。",
        skeleton=["共鸣开场", "核心结论", "分点干货", "清单/对比", "收藏引导 + 互动"],
        tagStrategy="主话题 1 个 + 泛流量标签 2-3 个，控制在 4 个内。",
    )


BREAKDOWN_SYSTEM = (
    "你是小红书爆款拆解专家。请分析给定笔记，输出 JSON，字段："
    "titleFormula(标题公式), hook(开头钩子), skeleton(正文骨架字符串数组), "
    "tagStrategy(标签策略)。只输出 JSON。"
)


async def llm_breakdown(n: Note, llm: LLMClient) -> BreakdownOut:
    if not llm.configured:
        return heuristic_breakdown(n)
    try:
        data = await llm.chat_json(
            BREAKDOWN_SYSTEM,
            f"标题：{n.title}\n正文：{n.content}",
        )
        return BreakdownOut(
            noteId=n.id,
            titleFormula=str(data.get("titleFormula", "")),
            hook=str(data.get("hook", "")),
            skeleton=[str(s) for s in data.get("skeleton", [])] or ["共鸣开场", "核心结论", "干货", "引导"],
            tagStrategy=str(data.get("tagStrategy", "")),
        )
    except Exception:  # noqa: BLE001
        return heuristic_breakdown(n)
