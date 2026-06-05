from pydantic import BaseModel, Field


class CreateTaskRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=100)
    total: int = Field(default=30, ge=5, le=200)
    sort: str = "comprehensive"
    includeComments: bool = False


class TaskOut(BaseModel):
    id: str
    topic: str
    total: int
    progress: int
    status: str
    sort: str
    includeComments: bool
    error: str | None = None
    createdAt: str


class NoteOut(BaseModel):
    id: str
    taskId: str
    title: str
    content: str
    author: str
    likes: int
    collects: int
    comments: int
    shares: int
    publishTime: str
    url: str
    cover: str
    tags: list[str]


class KeywordOut(BaseModel):
    word: str
    count: int


class RankingOut(BaseModel):
    noteId: str
    title: str
    author: str
    score: int
    likes: int
    reasons: list[str]


class BreakdownRequest(BaseModel):
    noteId: str


class BreakdownOut(BaseModel):
    noteId: str
    titleFormula: str
    hook: str
    skeleton: list[str]
    tagStrategy: str


class ComposeRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=100)
    refNoteId: str | None = None
    style: str = "种草"
    length: str = "中等"


class ComposeOut(BaseModel):
    titles: list[str]
    body: str
    hashtags: list[str]
    imageSuggestions: list[str]


class LLMSettings(BaseModel):
    baseUrl: str = "https://api.openai.com/v1"
    apiKey: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.8


class CollectSettings(BaseModel):
    defaultCount: int = 30
    rateLevel: str = "conservative"
    concurrency: int = 1
    includeComments: bool = False


class SettingsOut(BaseModel):
    llm: LLMSettings
    collect: CollectSettings


class AuthStatusOut(BaseModel):
    loggedIn: bool


class QRCodeOut(BaseModel):
    qrcode: str
    note: str


class TestLLMOut(BaseModel):
    ok: bool
    message: str
