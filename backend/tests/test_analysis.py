import json

from app.models import Note
from app.services.analysis import build_ranking, extract_keywords, heuristic_breakdown


def _note(i: int, likes: int, title: str, content: str, tags: list[str]) -> Note:
    return Note(
        id=f"t-n{i}",
        task_id="t",
        title=title,
        content=content,
        author="作者",
        likes=likes,
        collects=likes // 2,
        comments=likes // 10,
        shares=likes // 20,
        tags_json=json.dumps(tags, ensure_ascii=False),
    )


def test_extract_keywords_filters_stopwords():
    notes = [
        _note(1, 100, "护肤教程分享", "护肤教程 护肤 干货 干货 干货", ["护肤"]),
        _note(2, 200, "护肤避坑", "护肤 避坑 避坑", ["护肤"]),
    ]
    kws = extract_keywords(notes, top_k=10)
    words = [k.word for k in kws]
    assert "护肤" in words
    assert "的" not in words
    top = kws[0]
    assert top.count >= 1


def test_build_ranking_sorted_desc():
    notes = [
        _note(1, 100, "标题1", "内容", ["a"]),
        _note(2, 5000, "标题2 含数字3", "最近很多人问我", ["a", "b", "c"]),
        _note(3, 800, "标题3", "内容", ["a"]),
    ]
    ranking = build_ranking(notes, top_k=3)
    assert ranking[0].likes == 5000
    assert ranking[0].score >= ranking[1].score >= ranking[2].score
    assert "数字标题" in ranking[0].reasons


def test_heuristic_breakdown_schema():
    n = _note(1, 100, "5 个避坑点", "最近很多人问我", ["a", "b", "c"])
    bd = heuristic_breakdown(n)
    assert bd.noteId == n.id
    assert isinstance(bd.skeleton, list) and len(bd.skeleton) > 0
    assert bd.titleFormula
