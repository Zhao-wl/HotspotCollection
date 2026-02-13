"""
F005：使用 LangExtract + 硅基流动 API 对文本/文章进行关键词提取。
LLM 与 API Key 通过配置或环境变量设置，不硬编码密钥。
"""
import textwrap
from typing import List

try:
    import langextract as lx
except ImportError:
    lx = None  # 未安装 langextract 时仅跳过提取，不阻塞启动

from app.config import settings


def _get_prompt_and_examples():
    """返回 LangExtract 的提示与示例（仅在 lx 可用时使用）。"""
    prompt = textwrap.dedent("""\
从给定文本中提取 3～10 个关键词或短语，用于文章分类与聚合。
要求：仅输出原文中出现或紧密相关的词，不要解释；每个关键词单独一条；使用简体中文。""")
    examples = [
        lx.data.ExampleData(
            text="人工智能与机器学习正在改变各行各业，深度学习在图像识别领域应用广泛。",
            extractions=[
                lx.data.Extraction(extraction_class="keyword", extraction_text="人工智能", attributes={}),
                lx.data.Extraction(extraction_class="keyword", extraction_text="机器学习", attributes={}),
                lx.data.Extraction(extraction_class="keyword", extraction_text="深度学习", attributes={}),
                lx.data.Extraction(extraction_class="keyword", extraction_text="图像识别", attributes={}),
            ],
        ),
    ]
    return prompt, examples


def extract_keywords(text: str) -> List[str]:
    """
    对指定文本使用 LangExtract + 硅基流动 LLM 提取关键词。
    若未配置 API Key、未安装 langextract 或调用失败，返回空列表。
    """
    if not text or not text.strip():
        return []
    if lx is None:
        return []
    if not settings.siliconflow_api_key:
        return []

    try:
        # 直接实例化 OpenAI 兼容 model，绕过 resolve_provider，确保走硅基流动 API
        try:
            from langextract.providers.openai import OpenAILanguageModel
        except ImportError:
            return []  # 需 pip install "langextract[openai]"
        prompt, examples = _get_prompt_and_examples()
        language_model = OpenAILanguageModel(
            model_id=settings.siliconflow_model,
            api_key=settings.siliconflow_api_key,
            base_url=settings.siliconflow_base_url,
        )
        result = lx.extract(
            text_or_documents=text.strip(),
            prompt_description=prompt,
            examples=examples,
            model=language_model,
            fence_output=True,
            use_schema_constraints=False,
        )
    except Exception:
        return []

    # 单文档时 result 为 AnnotatedDocument，多文档时为 list
    if hasattr(result, "extractions"):
        docs = [result]
    else:
        docs = result if isinstance(result, list) else [result]

    keywords: List[str] = []
    seen: set = set()
    for doc in docs:
        for ext in getattr(doc, "extractions", []):
            cls_ = getattr(ext, "extraction_class", None)
            txt = getattr(ext, "extraction_text", None)
            if cls_ == "keyword" and txt and isinstance(txt, str):
                t = txt.strip()
                if t and t.lower() not in seen:
                    seen.add(t.lower())
                    keywords.append(t)
    return keywords
