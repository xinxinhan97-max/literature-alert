"""
AI 文献分析模块
- 期刊影响因子匹配
- 多模型兼容的 AI 分析（OpenAI 兼容格式）
  支持: DeepSeek / OpenAI / 智谱 / 通义千问 / Ollama / 等
- 支持多语言输出（中文 / 英文 / 双语）
- 大批论文自动分批，单批失败不影响其他
"""
import json
import os
import re
import urllib.request
import urllib.error
from difflib import SequenceMatcher

# ============================================================
# 期刊 IF 匹配
# ============================================================

_IF_LOOKUP: dict | None = None


def _load_if_lookup() -> dict:
    global _IF_LOOKUP
    if _IF_LOOKUP is not None:
        return _IF_LOOKUP

    json_path = os.path.join(os.path.dirname(__file__), "journal_if.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            _IF_LOOKUP = json.load(f)
    else:
        _IF_LOOKUP = {}
    return _IF_LOOKUP


def _normalize(s: str) -> str:
    s = re.sub(r"[^a-z0-9\s]", "", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def match_journal_if(journal_name: str) -> dict:
    if not journal_name:
        return {}

    lookup = _load_if_lookup()
    norm_input = _normalize(journal_name)

    if norm_input in lookup:
        return lookup[norm_input]

    best_score = 0
    best_match = None
    for key, val in lookup.items():
        score = SequenceMatcher(None, norm_input, key).ratio()
        if score > best_score:
            best_score = score
            best_match = val

    if best_score >= 0.85 and best_match:
        return best_match

    return {}


# ============================================================
# 系统提示词（由 directions + language 动态生成）
# ============================================================

def build_system_prompt(directions: list[dict], language: str = "zh") -> str:
    """根据用户的研究方向和语言偏好动态生成分析提示词"""
    if not directions:
        directions_text_zh = "  （请先在 strategies.json 中配置研究方向）"
        directions_text_en = "  (Please configure research directions in strategies.json)"
        match_hint = ""
    else:
        lines_zh = []
        lines_en = []
        for d in directions:
            en = d.get("en_name", "")
            suffix = f"（{en}）" if en else ""
            lines_zh.append(f"  {d['id']}) {d['name']}{suffix}")
            lines_en.append(f"  {d['id']}) {d['name']}{suffix}")
        directions_text_zh = "\n".join(lines_zh)
        directions_text_en = "\n".join(lines_en)
        match_hint = ", ".join(str(d["id"]) for d in directions)

    if language == "en":
        return f"""You are a scientific literature analysis assistant. I will give you a batch of paper information (title, abstract, journal, impact factor). Analyze each paper and return JSON.

For each paper, extract:
- score: 1-5 stars, rating relevance to our research group. Criteria:
  ⭐5 = Directly on-topic (same materials/methods/system), must-read
  ⭐4 = Highly relevant, minor differences in materials or methods, worth reading
  ⭐3 = Same broad field, methods/ideas are transferable, some distance from specific topic
  ⭐2 = Same discipline but different subfield, limited reference value
  ⭐1 = Irrelevant or completely unrelated
  Our directions:
{directions_text_en}
- match: which direction(s) this matches ({match_hint}), can be multiple
- innovation: one-sentence highlight of novelty (method/material/mechanism)
- methods: main experimental/computational methods
- metrics: key performance metrics (FE, current density, selectivity, yield, etc. Say "not provided" if absent)
- takeaway: what our group can learn (1-2 sentences, say "limited reference value" if not much)
- abstract_en: a faithful English summary of the abstract (do not abbreviate or omit information)

Return ONLY valid JSON array, no extra text:
[{{"idx": 0, "score": 4, "match": [1, 2], "innovation": "...", "methods": "...", "metrics": "...", "takeaway": "...", "abstract_en": "..."}}, ...]"""

    elif language == "bilingual":
        return f"""你是一个科研文献分析助手。用户会给你一批论文信息（标题、摘要、期刊、影响因子），请逐篇分析并返回 JSON。

对每篇论文，提取以下信息：
- score: 1-5 星，评定与本课题组的相关程度。评分标准：
  ⭐5 = 直接命中研究方向（材料/方法/体系高度相关），必读
  ⭐4 = 与方向高度相关但材料或方法略有差异，值得读
  ⭐3 = 同一大类领域，方法或思路可参考，与具体课题有距离
  ⭐2 = 同一学科但不同子领域，参考价值有限
  ⭐1 = 不相关或完全不搭边
  课题组方向为：
{directions_text_zh}
- match: 匹配哪个方向 ({match_hint})，可多个
- innovation: 一句话提炼创新点（方法/材料/机理上的新意）
- methods: 主要实验/计算方法
- metrics: 关键性能指标（FE、电流密度、选择性、产率等，如摘要未提供则说"未提供"）
- takeaway: 值得本课题组借鉴之处（1-2句话，如果没什么借鉴价值就说"参考价值有限"）
- abstract_cn: 将论文摘要**逐句忠实翻译**为中文。不要概括、不要缩写、不要省略任何信息。逐句对应原文
- abstract_en: the original English abstract or a faithful English version of the abstract

严格按以下 JSON 格式返回，不要加任何额外文字：
[{{"idx": 0, "score": 4, "match": [1, 2], "innovation": "...", "methods": "...", "metrics": "...", "takeaway": "...", "abstract_cn": "...", "abstract_en": "..."}}, ...]"""

    else:  # zh (default)
        return f"""你是一个科研文献分析助手。用户会给你一批论文信息（标题、摘要、期刊、影响因子），请逐篇分析并返回 JSON。

对每篇论文，提取以下信息：
- score: 1-5 星，评定与本课题组的相关程度。评分标准：
  ⭐5 = 直接命中研究方向（材料/方法/体系高度相关），必读
  ⭐4 = 与方向高度相关但材料或方法略有差异，值得读
  ⭐3 = 同一大类领域，方法或思路可参考，与具体课题有距离
  ⭐2 = 同一学科但不同子领域，参考价值有限
  ⭐1 = 不相关或完全不搭边
  课题组方向为：
{directions_text_zh}
- match: 匹配哪个方向 ({match_hint})，可多个
- innovation: 一句话提炼创新点（方法/材料/机理上的新意）
- methods: 主要实验/计算方法
- metrics: 关键性能指标（FE、电流密度、选择性、产率等，如摘要未提供则说"未提供"）
- takeaway: 值得本课题组借鉴之处（1-2句话，如果没什么借鉴价值就说"参考价值有限"）
- abstract_cn: 将论文摘要**逐句忠实翻译**为中文。不要概括、不要缩写、不要省略任何信息。逐句对应原文

严格按以下 JSON 格式返回，不要加任何额外文字：
[{{"idx": 0, "score": 4, "match": [1, 2], "innovation": "...", "methods": "...", "metrics": "...", "takeaway": "...", "abstract_cn": "..."}}, ...]"""


# ============================================================
# AI API 调用（OpenAI 兼容格式）
# ============================================================

# 每批分析的论文数（避免单次调用太长超时）
BATCH_SIZE = 8


def _call_ai_api(
    papers_batch: list[dict],
    api_key: str,
    directions: list[dict],
    base_url: str,
    model: str,
    language: str,
) -> list[dict]:
    """调用 AI API 分析一批论文"""
    system_prompt = build_system_prompt(directions, language)

    user_text = "请分析以下论文：\n\n" if language != "en" else "Please analyze the following papers:\n\n"
    for p in papers_batch:
        jinfo = ""
        if p.get("journal"):
            jinfo = f" [{p.get('journal', '')}, IF={p.get('if_val', '?')}, {p.get('q', '')}]"
        user_text += f"--- Paper {p['idx']}{jinfo} ---\n"
        user_text += f"Title: {p['title']}\n"
        abstract = p.get("abstract", "") or "(no abstract)"
        user_text += f"Abstract: {abstract}\n\n"

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.3,
        "max_tokens": 32768,
    }).encode("utf-8")

    api_url = f"{base_url.rstrip('/')}/chat/completions"
    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else str(e)
        print(f"[AI] API HTTP {e.code}: {body[:300]}")
        raise
    except Exception as e:
        print(f"[AI] 调用失败: {e}")
        raise

    content = data["choices"][0]["message"]["content"]
    content = re.sub(r"^```(json)?\s*", "", content.strip())
    content = re.sub(r"\s*```$", "", content)

    try:
        results = json.loads(content)
        for r in results:
            r.setdefault("score", "?")
            r.setdefault("match", [])
            r.setdefault("innovation", "")
            r.setdefault("methods", "")
            r.setdefault("metrics", "")
            r.setdefault("takeaway", "")
            r.setdefault("abstract_cn", "")
            r.setdefault("abstract_en", "")
        return results
    except json.JSONDecodeError:
        print(f"[AI] JSON 解析失败, 原始输出: {content[:500]}")
        raise


def analyze_papers(
    papers: list[dict],
    api_key: str,
    directions: list[dict] | None = None,
    base_url: str = "https://api.deepseek.com/v1",
    model: str = "deepseek-chat",
    language: str = "zh",
) -> list[dict]:
    """
    调用 AI API 批量分析论文（OpenAI 兼容协议）
    papers: [{idx, title, abstract, journal, if_val, q}, ...]
    directions: 用户研究方向列表 [{id, name, name_short, en_name}, ...]
    language: "zh" / "en" / "bilingual"
    大批论文自动分批，单批失败不影响其他批次
    """
    if not api_key or "YOUR" in api_key:
        return _mock_analysis(papers)

    directions = directions or []

    # 分批处理
    all_results = []
    total_batches = (len(papers) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(papers), BATCH_SIZE):
        batch = papers[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1

        if total_batches > 1:
            print(f"  [AI] 批次 {batch_num}/{total_batches} ({len(batch)} 篇)...")

        try:
            results = _call_ai_api(batch, api_key, directions, base_url, model, language)
            all_results.extend(results)
        except Exception:
            print(f"  [AI] 批次 {batch_num} 失败，回退到占位分析")
            all_results.extend(_mock_analysis(batch))

    return all_results


def _mock_analysis(papers: list[dict]) -> list[dict]:
    """API 不可用时的回退分析"""
    return [
        {
            "idx": p["idx"],
            "score": "?",
            "match": [],
            "innovation": "（AI 分析未启用，请填写 config.json 中的 ai.api_key）",
            "methods": "",
            "metrics": "",
            "takeaway": "",
            "abstract_cn": "",
            "abstract_en": "",
        }
        for p in papers
    ]
