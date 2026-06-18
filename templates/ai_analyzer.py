"""
AI 文献分析模块
- 期刊影响因子匹配
- 多模型兼容的 AI 分析（OpenAI 兼容格式）
  支持: DeepSeek / OpenAI / 智谱 / 通义千问 / Ollama / 等
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
# 系统提示词（由 directions 动态生成）
# ============================================================

def build_system_prompt(directions: list[dict]) -> str:
    """根据用户的研究方向动态生成分析提示词"""
    if not directions:
        directions_text = "  （请先在 strategies.json 中配置研究方向）"
        match_hint = ""
    else:
        lines = []
        for d in directions:
            en = d.get("en_name", "")
            suffix = f"（{en}）" if en else ""
            lines.append(f"  {d['id']}) {d['name']}{suffix}")
        directions_text = "\n".join(lines)
        match_hint = ", ".join(str(d["id"]) for d in directions)

    return f"""你是一个科研文献分析助手。用户会给你一批论文信息（标题、摘要、期刊、影响因子），请逐篇分析并返回 JSON。

对每篇论文，提取以下信息：
- score: 1-5 星，评定与本课题组的相关程度。课题组方向为：
{directions_text}
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

def analyze_papers(
    papers: list[dict],
    api_key: str,
    directions: list[dict] | None = None,
    base_url: str = "https://api.deepseek.com/v1",
    model: str = "deepseek-chat",
) -> list[dict]:
    """
    调用 AI API 批量分析论文（OpenAI 兼容协议）
    papers: [{idx, title, abstract, journal, if_val, q}, ...]
    directions: 用户研究方向列表 [{id, name, name_short, en_name}, ...]
    """
    if not api_key or "YOUR" in api_key:
        return _mock_analysis(papers)

    system_prompt = build_system_prompt(directions or [])

    # 构建用户消息
    user_text = "请分析以下论文：\n\n"
    for p in papers:
        jinfo = f" [{p.get('journal', '')}, IF={p.get('if_val', '?')}, {p.get('q', '')}]" if p.get("journal") else ""
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else str(e)
        print(f"[AI] API HTTP {e.code}: {body[:300]}")
        return _mock_analysis(papers)
    except Exception as e:
        print(f"[AI] 调用失败: {e}")
        return _mock_analysis(papers)

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
        return results
    except json.JSONDecodeError:
        print(f"[AI] JSON 解析失败, 原始输出: {content[:500]}")
        return _mock_analysis(papers)


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
        }
        for p in papers
    ]
