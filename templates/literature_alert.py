#!/usr/bin/env python3
"""
每日文献推送脚本 v3（通用版）
检索策略从 strategies.json 读取，AI 分析从 config.json 读取。
支持任意研究方向、任意推送节奏、任意 OpenAI 兼容的 AI 模型。

使用:
  python literature_alert.py                # 检索 + 分析 + 保存 HTML
  python literature_alert.py --dry-run      # 仅生成预览
  python literature_alert.py --no-ai        # 跳过 AI 分析
  python literature_alert.py --force-day 2  # 强制按某天检索（0=Mon）
"""

import sys
import json
import os
import re
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import ssl
import hashlib
import pickle
import time
import webbrowser

from ai_analyzer import match_journal_if, analyze_papers

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ============================================================
# 路径
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
STRATEGIES_PATH = os.path.join(SCRIPT_DIR, "strategies.json")
CACHE_PATH = os.path.join(SCRIPT_DIR, "sent_cache.pkl")

# ============================================================
# 默认配置（config.json 不存在时自动生成）
# ============================================================

DEFAULT_CONFIG = {
    "email": {
        "smtp_server": "smtp.qq.com",
        "smtp_port": 465,
        "sender": "YOUR_EMAIL@qq.com",
        "password": "YOUR_SMTP_AUTH_CODE",
        "receiver": "YOUR_EMAIL@qq.com"
    },
    "search": {
        "max_results_per_query": 15,
        "lookback_days": 7,
        "arxiv_timeout": 60,
        "use_semantic_scholar": False
    },
    "ai": {
        "enabled": True,
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "api_key": "YOUR_API_KEY"
    }
}


# ============================================================
# 工具函数
# ============================================================

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 已创建默认配置文件: {CONFIG_PATH}")
        print("[INFO] 请编辑后填入邮箱信息 + AI API Key，再运行")
        return DEFAULT_CONFIG


def load_strategies() -> dict:
    if not os.path.exists(STRATEGIES_PATH):
        print(f"[ERROR] 策略文件不存在: {STRATEGIES_PATH}")
        print("[ERROR] 请先运行 setup-literature 技能生成")
        sys.exit(1)
    with open(STRATEGIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# API 检索
# ============================================================

def search_arxiv(query: str, max_results: int = 10, lookback_days: int = 7, timeout: int = 60) -> list[dict]:
    base_url = "https://export.arxiv.org/api/query"
    params = {"search_query": query, "sortBy": "submittedDate", "sortOrder": "descending", "max_results": max_results}
    url = base_url + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LiteratureAlert/3.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                xml_data = resp.read().decode("utf-8")
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                print(f"[WARN] arXiv API 失败: {e}")
                return []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"[WARN] arXiv XML 解析失败: {e}")
        return []
    papers = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    for entry in root.findall("atom:entry", ns):
        published = entry.find("atom:published", ns)
        pub_date = published.text.strip()[:10] if published is not None else "?"
        try:
            if datetime.fromisoformat(pub_date).replace(tzinfo=timezone.utc) < cutoff_date:
                continue
        except (ValueError, AttributeError):
            pass
        title = entry.find("atom:title", ns)
        title = title.text.strip().replace("\n", " ") if title is not None else "No title"
        abstract = entry.find("atom:summary", ns)
        abstract = abstract.text.strip().replace("\n", " ") if abstract is not None else ""
        url_tag = entry.find("atom:id", ns)
        paper_url = url_tag.text.strip() if url_tag is not None else ""
        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.find("atom:name", ns)
            if name is not None:
                authors.append(name.text.strip())
        papers.append({
            "title": title, "authors": ", ".join(authors[:6]) + (", ..." if len(authors) > 6 else ""),
            "abstract": abstract, "url": paper_url, "date": pub_date, "source": "arXiv",
        })
    return papers


def search_openalex(query: str, max_results: int = 15, lookback_days: int = 7) -> list[dict]:
    from_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    params = {"search": query, "sort": "publication_date:desc", "per-page": max_results,
              "filter": f"from_publication_date:{from_date}"}
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LiteratureAlert/3.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
            else:
                print(f"[WARN] OpenAlex API 失败: {e}")
                return []
    papers = []
    for item in data.get("results", []):
        title = item.get("title", "No title")
        authors_list = []
        for authorship in item.get("authorships", [])[:6]:
            auth = authorship.get("author", {})
            name = auth.get("display_name", "")
            if name:
                authors_list.append(name)
        authors = ", ".join(authors_list)
        if len(item.get("authorships", [])) > 6:
            authors += ", ..."
        abstract = ""
        if item.get("abstract"):
            abstract = item["abstract"]
        elif item.get("abstract_inverted_index"):
            idx_map = item["abstract_inverted_index"]
            if isinstance(idx_map, dict) and idx_map:
                max_pos = max(p for positions in idx_map.values() for p in positions)
                words = [""] * (max_pos + 1)
                for word, positions in idx_map.items():
                    for p in positions:
                        words[p] = word
                abstract = " ".join(words)
        doi = item.get("doi", "")
        paper_url = f"https://doi.org/{doi}" if doi else (
            item.get("primary_location", {}).get("landing_page_url", "") or item.get("id", ""))
        pub_date = item.get("publication_date", "?")
        source = item.get("primary_location", {}).get("source", {})
        journal = source.get("display_name", "") if source else ""
        papers.append({
            "title": title, "authors": authors, "abstract": abstract,
            "url": paper_url, "date": pub_date, "source": "OpenAlex",
            "journal": journal, "doi": doi, "type": item.get("type", ""),
        })
    return papers


# ============================================================
# 缓存
# ============================================================

def load_sent_cache() -> set[str]:
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    return set()


def save_sent_cache(cache: set[str]):
    if len(cache) > 2000:
        cache = set(list(cache)[-2000:])
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(cache, f)


def deduplicate_papers(papers: list[dict], sent_cache: set[str]) -> list[dict]:
    new_papers = []
    for p in papers:
        url = p.get("url", "")
        if not url:
            continue
        h = hashlib.md5(url.encode()).hexdigest()
        if h not in sent_cache:
            p["_hash"] = h
            new_papers.append(p)
    return new_papers


# ============================================================
# HTML 生成
# ============================================================

def _render_paper_card(p: dict, match_map: dict, interactive: bool = False) -> str:
    hid = p.get("_hash", "")[:12]
    jname = p.get("journal", "")
    if_val = p.get("if_val", "?")
    if_q = p.get("if_q", "")
    jinfo = ""
    if jname:
        if_str = f"IF={if_val}" if if_val and if_val != "?" else ""
        q_str = f"· {if_q}" if if_q else ""
        jinfo = f'<span class="badge" style="background:#e3f2fd;color:#1565c0;">{jname}</span>'
        if if_str:
            jinfo += f'<span class="badge" style="background:#f3e5f5;color:#7b1fa2;">{if_str}</span>'
        if q_str:
            jinfo += f'<span class="badge" style="background:#e8f5e9;color:#2e7d32;">{q_str}</span>'

    ai = p.get("ai", {})
    ai_html = ""
    if ai:
        star = "⭐" * (ai.get("score", 0) if isinstance(ai.get("score"), int) else 0) or ai.get("score", "?")
        match_tags = " ".join(
            f'<span class="badge" style="background:#ff9800;color:#fff;">🎯 {match_map.get(m, str(m))}</span>'
            for m in ai.get("match", []) if m in match_map
        )
        ai_html = '<div class="ai-box">'
        ai_html += f'<div class="ai-row"><b>评分：</b>{star} {match_tags}</div>'
        for key, icon, label in [("innovation", "💡", "创新点"), ("methods", "🔬", "方法"),
                                    ("metrics", "📊", "指标"), ("takeaway", "💭", "可借鉴")]:
            val = ai.get(key, "")
            if val:
                ai_html += f'<div class="ai-row"><b>{icon} {label}：</b>{val}</div>'
        cn = ai.get("abstract_cn", "")
        if cn:
            ai_html += f'<div class="ai-row" style="margin-top:6px;padding-top:6px;border-top:1px dashed #ddd;"><b>📝 中文摘要：</b>{cn}</div>'
        ai_html += '</div>'

    int_html = ""
    if interactive:
        int_html = f"""
  <div class="int-row" data-pid="{hid}">
    <button class="st-btn st-unread active" onclick="setStatus('{hid}','unread')">📌 未读</button>
    <button class="st-btn st-read" onclick="setStatus('{hid}','read')">✅ 已读</button>
    <button class="st-btn st-skip" onclick="setStatus('{hid}','skip')">⏭️ 不读</button>
    <button class="note-btn" onclick="toggleNote('{hid}')">📝 笔记</button>
    <div class="note-area" id="note-{hid}" style="display:none">
      <textarea placeholder="写笔记..." onchange="saveNote('{hid}',this.value)"></textarea>
    </div>
  </div>"""

    return f"""<div class="paper" id="paper-{hid}">
  <div class="title"><a href="{p['url']}">{p['title']}</a><span class="badge">{p['source']}</span>{jinfo}</div>
  <div class="meta">{p['date']} · {p['authors']}</div>
  {ai_html}
  {int_html}
</div>"""


def build_html(papers_by_layer, strategy, match_map=None, interactive=True) -> str:
    if match_map is None:
        match_map = {}
    today_str = datetime.now().strftime("%Y年%m月%d日")
    weekday_cn = ["一", "二", "三", "四", "五", "六", "日"][datetime.now().weekday()]
    topic = strategy.get("topic", "文献推送")
    total = sum(len(ps) for _, ps in papers_by_layer)
    has_arxiv = any(p["source"] == "arXiv" for _, ps in papers_by_layer for p in ps)
    source_note = "OpenAlex + arXiv" if has_arxiv else "OpenAlex"

    extra_css = extra_js = ""
    if interactive:
        extra_css = """
  .int-row { margin-top: 10px; padding-top: 8px; border-top: 1px solid #f0f0f0; display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
  .st-btn { font-size: 11px; padding: 3px 10px; border-radius: 12px; border: 1px solid #ddd; cursor: pointer; background: #fff; color: #777; transition: all 0.15s; }
  .st-btn:hover { opacity: 0.8; }
  .st-btn.active { border-color: #1976d2; background: #e3f2fd; color: #1565c0; font-weight: 600; }
  .st-read.active { border-color: #388e3c; background: #e8f5e9; color: #2e7d32; font-weight: 600; }
  .st-skip.active { border-color: #c62828; background: #ffebee; color: #c62828; font-weight: 600; }
  .note-btn { font-size: 11px; padding: 3px 10px; border-radius: 12px; border: 1px dashed #ccc; cursor: pointer; background: #fafafa; color: #888; margin-left: 4px; }
  .note-area { width: 100%; margin-top: 6px; }
  .note-area textarea { width: 100%; height: 48px; font-size: 12px; border: 1px solid #e0e0e0; border-radius: 4px; padding: 6px 8px; font-family: 'Microsoft YaHei', sans-serif; resize: vertical; }
  .toolbar { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; }
  .toolbar button { font-size: 12px; padding: 6px 16px; border-radius: 6px; border: 1px solid #2980b9; background: #2980b9; color: #fff; cursor: pointer; }
  .toolbar .stats { font-size: 12px; color: #888; margin-left: 12px; }
  .paper.read { border-left: 3px solid #388e3c; }
  .paper.skip { border-left: 3px solid #c62828; opacity: 0.55; }
  .paper.unread { border-left: 3px solid #1976d2; }
"""
        extra_js = """<script>
const TODAY = document.querySelector('.header .sub')?.textContent?.match(/[0-9]{4}年[0-9]{2}月[0-9]{2}日/)?.[0] || '';
function getStore(k){ try{return JSON.parse(localStorage.getItem('lit_'+k));}catch(e){return null;} }
function setStore(k,v){ localStorage.setItem('lit_'+k,JSON.stringify(v)); }
function setStatus(h,st){ setStore(h,{status:st,note:getStore(h)?.note||''});renderPaper(h);updateStats(); }
function toggleNote(h){ var e=document.getElementById('note-'+h); e.style.display=e.style.display==='none'?'block':'none'; var t=e.querySelector('textarea'); var s=getStore(h); if(s&&s.note)t.value=s.note; t.focus(); }
function saveNote(h,n){ var s=getStore(h)||{status:'unread'}; s.note=n; setStore(h,s); }
function renderPaper(h){ var s=getStore(h)||{status:'unread',note:''}; var p=document.getElementById('paper-'+h); if(!p)return; p.className='paper '+s.status; var r=p.querySelector('.int-row'); if(!r)return; r.querySelectorAll('.st-btn').forEach(function(b){b.classList.remove('active')}); var ab=null; if(s.status==='read')ab=r.querySelector('.st-read'); else if(s.status==='skip')ab=r.querySelector('.st-skip'); else ab=r.querySelector('.st-unread'); if(ab)ab.classList.add('active'); var na=document.getElementById('note-'+h); if(na&&s.note){na.querySelector('textarea').value=s.note;} }
function updateStats(){ var u=0,r=0,s=0; document.querySelectorAll('.paper').forEach(function(p){var c=p.className;if(c.indexOf('read')>=0)r++;else if(c.indexOf('skip')>=0)s++;else u++;}); var e=document.getElementById('stats'); if(e)e.textContent='未读:'+u+' | 已读:'+r+' | 不读:'+s; }
function exportLog(){ var md='# 文献阅读日志 · '+TODAY+'\\n\\n'; var sec={read:'## ✅ 已读\\n',skip:'## ❌ 不读\\n',unread:'## 📌 未读\\n'}; var data={}; ['read','skip','unread'].forEach(function(k){data[k]='';}); document.querySelectorAll('.paper').forEach(function(p){var h=(p.id||'').replace('paper-','');var sv=getStore(h)||{status:'unread',note:''};var t=(p.querySelector('.title a')||{}).textContent||'';var m=(p.querySelector('.meta')||{}).textContent||'';var e='- **'+t+'**';var jt=p.querySelector('.title');if(jt){var im=jt.textContent.match(/IF=([\\d.]+)/);if(im)e+=' ['+im[1]+']';} e+='\\n  '+m.split('·')[0].trim(); if(sv.note)e+='\\n  > 📝 '+sv.note; e+='\\n\\n'; var st=sv.status||'unread'; if(data[st]!==undefined)data[st]+=e;}); for(var k in sec){if(data[k])md+=sec[k]+data[k];} var b=new Blob([md],{type:'text/markdown;charset=utf-8'});var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='reading_log_'+(TODAY||'export')+'.md';a.click();}
document.addEventListener('DOMContentLoaded',function(){document.querySelectorAll('.paper').forEach(function(p){var h=(p.id||'').replace('paper-','');if(h)renderPaper(h);});updateStats();});
</script>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, 'Microsoft YaHei', sans-serif; max-width: 760px; margin: 0 auto; padding: 20px; background: #fafafa; }}
  .header {{ background: linear-gradient(135deg, #1a5276, #2980b9); color: white; padding: 24px 28px; border-radius: 12px; margin-bottom: 22px; }}
  .header h1 {{ margin: 0 0 6px 0; font-size: 21px; }}
  .header .sub {{ opacity: 0.85; font-size: 13px; }}
  .header .topic {{ font-size: 16px; font-weight: bold; margin-top: 10px; }}
  .layer {{ margin-bottom: 20px; }}
  .layer-label {{ font-size: 13px; color: #666; margin-bottom: 8px; padding: 5px 12px; background: #e8f0fe; border-left: 4px solid #2980b9; border-radius: 3px; font-weight: 600; }}
  .paper {{ background: white; padding: 14px 18px; margin-bottom: 8px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border-left: 3px solid transparent; }}
  .paper .title {{ font-size: 15px; font-weight: 600; margin-bottom: 4px; line-height: 1.4; }}
  .paper .title a {{ color: #1a5276; text-decoration: none; }}
  .paper .title a:hover {{ text-decoration: underline; }}
  .paper .meta {{ font-size: 12px; color: #999; margin-bottom: 6px; }}
  .paper .badge {{ display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 3px; background: #eee; color: #777; margin-left: 6px; vertical-align: middle; }}
  .footer {{ font-size: 11px; color: #ccc; text-align: center; margin-top: 30px; padding: 16px; border-top: 1px solid #eee; }}
  .no-paper {{ text-align: center; color: #aaa; padding: 32px; font-size: 14px; }}
  .ai-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 14px; margin-top: 10px; }}
  .ai-row {{ font-size: 13px; color: #333; line-height: 1.7; }}
  .ai-row b {{ color: #1a5276; }}
  {extra_css}
</style></head><body>

<div class="header">
  <h1>📚 前沿文献推送</h1>
  <div class="sub">{today_str} · 星期{weekday_cn}</div>
  <div class="topic">🔬 {topic}</div>
  <div class="sub" style="margin-top:4px;">{strategy.get('subtitle', '')}</div>
</div>
"""

    if interactive:
        html += """<div class="toolbar">
  <button onclick="exportLog()">📥 导出日志</button>
  <span class="stats" id="stats"></span>
</div>
"""

    if total == 0:
        html += '<div class="no-paper">😴 今日暂无新文献匹配</div>\n'

    for layer_label, papers in papers_by_layer:
        html += f'<div class="layer"><div class="layer-label">{layer_label} · {len(papers)} 篇</div>\n'
        if not papers:
            html += '<div class="no-paper" style="padding:12px;font-size:13px;">— 无新文献 —</div>\n'
        for p in papers:
            html += _render_paper_card(p, match_map, interactive=interactive)
        html += "</div>\n"

    html += f"""<div class="footer">
    每日自动推送 · 共 {total} 篇 · 数据源: {source_note} · {datetime.now().strftime('%H:%M')}<br>
    <small>Literature Alert v3 · OpenAlex + AI · 无 LLM Token 消耗</small>
</div>
{extra_js}
</body></html>"""
    return html


# ============================================================
# 邮件发送
# ============================================================

def send_email(config: dict, html_body: str, topic: str):
    email_cfg = config["email"]
    msg = MIMEMultipart("mixed")
    today_str = datetime.now().strftime("%m/%d")
    msg["Subject"] = f"📚 [{today_str}] {topic} · 前沿文献推送"
    msg["From"] = email_cfg["sender"]
    msg["To"] = email_cfg["receiver"]
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        use_ssl = email_cfg["smtp_port"] == 465 or "qq.com" in email_cfg["smtp_server"]
        if use_ssl:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(email_cfg["smtp_server"], email_cfg["smtp_port"],
                                  timeout=30, context=ctx) as server:
                server.login(email_cfg["sender"], email_cfg["password"])
                server.sendmail(email_cfg["sender"], email_cfg["receiver"], msg.as_string())
        else:
            with smtplib.SMTP(email_cfg["smtp_server"], email_cfg["smtp_port"], timeout=30) as server:
                server.starttls()
                server.login(email_cfg["sender"], email_cfg["password"])
                server.sendmail(email_cfg["sender"], email_cfg["receiver"], msg.as_string())
        print("[OK] 邮件发送成功")
    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERROR] 邮箱登录被拒 (535): 授权码错误或SMTP服务未开启")
        print(f"  详细信息: {e}")
    except smtplib.SMTPServerDisconnected as e:
        print(f"[ERROR] 邮件服务器断开连接: 登录频率过高被临时封禁，等待更长时间后再试")
        print(f"  详细信息: {e}")
    except Exception as e:
        print(f"[ERROR] 邮件发送失败: {e}")


# ============================================================
# 主流程
# ============================================================

def main():
    dry_run = "--dry-run" in sys.argv
    no_ai = "--no-ai" in sys.argv

    force_day = None
    for i, arg in enumerate(sys.argv):
        if arg == "--force-day" and i + 1 < len(sys.argv):
            force_day = int(sys.argv[i + 1])

    config = load_config()
    search_cfg = config.get("search", {})

    if not dry_run:
        email_ok = "YOUR" not in config.get("email", {}).get("sender", "YOUR")
        if not email_ok:
            print("[INFO] 邮件未配置，仅保存本地 HTML")

    strategies = load_strategies()
    workdays = strategies.get("workdays", [0, 1, 2, 3, 4])
    directions = strategies.get("directions", [])
    s_days = strategies.get("days", {})

    weekday = force_day if force_day is not None else datetime.now().weekday()
    if weekday not in workdays:
        wd_names = ["一", "二", "三", "四", "五", "六", "日"]
        print(f"[SKIP] 今天（周{wd_names[weekday]}）不在推送日内 (推送日: {[wd_names[d] for d in workdays]})")
        # 仍然生成空 HTML
        html = build_html([], {}, interactive=True)
        out_dir = os.path.dirname(os.path.abspath(__file__))
        today_tag = datetime.now().strftime("%m%d")
        html_path = os.path.join(out_dir, f"literature_{today_tag}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        return

    day_key = str(weekday)
    strategy = s_days.get(day_key)
    if strategy is None:
        print(f"[SKIP] 星期 {weekday} 无策略配置")
        sys.exit(0)

    print(f"[INFO] 今日主题: {strategy.get('topic', '未知')}")
    print(f"[INFO] 策略: {strategy.get('subtitle', '')}")

    # match_map: direction id → short name
    match_map = {d["id"]: d.get("name_short", d["name"]) for d in directions}

    # 检索
    sent_cache = load_sent_cache()
    papers_by_layer = []

    for layer in strategy.get("layers", []):
        label = layer.get("label", "检索")
        openalex_q = layer.get("openalex", "")
        arxiv_q = layer.get("arxiv", "")
        print(f"[SEARCH] {label} ...")

        openalex_papers = []
        if openalex_q:
            openalex_papers = search_openalex(openalex_q,
                max_results=search_cfg.get("max_results_per_query", 15),
                lookback_days=search_cfg.get("lookback_days", 7))

        arxiv_papers = []
        if arxiv_q:
            arxiv_papers = search_arxiv(arxiv_q,
                max_results=search_cfg.get("max_results_per_query", 15),
                lookback_days=search_cfg.get("lookback_days", 7),
                timeout=search_cfg.get("arxiv_timeout", 60))

        seen_urls = set()
        merged = []
        for p in openalex_papers + arxiv_papers:
            url = p.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(p)

        new_papers = deduplicate_papers(merged, sent_cache)
        print(f"  OpenAlex:{len(openalex_papers)} arXiv:{len(arxiv_papers)} → 新:{len(new_papers)}")
        papers_by_layer.append((label, new_papers))

    # IF 匹配 + 缺失摘要回退
    all_new_papers = []
    for _, papers in papers_by_layer:
        all_new_papers.extend(papers)

    for p in all_new_papers:
        if not p.get("abstract"):
            doi = p.get("doi", "")
            if not doi:
                m = re.search(r'doi\.org/(10\.[^/\s]+/[^/\s]+)', p.get("url", ""))
                if m:
                    doi = m.group(1)
            if doi:
                try:
                    cr_url = f"https://api.crossref.org/works/{doi}"
                    req = urllib.request.Request(cr_url, headers={"User-Agent": "LiteratureAlert/3.0"})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        cr_data = json.loads(resp.read().decode("utf-8"))
                    cr_abs = cr_data.get("message", {}).get("abstract", "")
                    if cr_abs:
                        cr_abs = re.sub(r'<[^>]+>', '', cr_abs)
                        cr_abs = re.sub(r'\s+', ' ', cr_abs).strip()
                        if cr_abs:
                            p["abstract"] = cr_abs
                            print(f"  [CrossRef] 补获摘要: {p.get('title','')[:50]}...")
                except Exception:
                    pass

        jname = p.get("journal", "")
        if jname:
            info = match_journal_if(jname)
            p["if_val"] = info.get("if", "?")
            p["if_q"] = info.get("q", "")
        else:
            p["if_val"] = "?"
            p["if_q"] = ""

    # AI 分析
    ai_cfg = config.get("ai", {})
    ai_enabled = ai_cfg.get("enabled", True) and not no_ai
    ai_key = ai_cfg.get("api_key", "")
    ai_base = ai_cfg.get("base_url", "https://api.deepseek.com/v1")
    ai_model = ai_cfg.get("model", "deepseek-chat")

    if all_new_papers and ai_enabled and not dry_run and ai_key and "YOUR" not in ai_key:
        print(f"\n[AI] 准备分析 {len(all_new_papers)} 篇论文 ({ai_model}) ...")
        for_input = []
        for i, p in enumerate(all_new_papers):
            for_input.append({
                "idx": i, "title": p.get("title", ""),
                "abstract": p.get("abstract", ""),
                "journal": p.get("journal", ""),
                "if_val": p.get("if_val", "?"), "q": p.get("if_q", ""),
            })
        analyses = analyze_papers(for_input, ai_key,
                                   directions=directions,
                                   base_url=ai_base, model=ai_model)
        for a in analyses:
            idx = a.get("idx", -1)
            if 0 <= idx < len(all_new_papers):
                all_new_papers[idx]["ai"] = a
        print(f"[AI] 分析完成: {len(analyses)} 篇")

        # 按评分排序
        def _score(p):
            ai = p.get("ai", {})
            s = ai.get("score", 0)
            return s if isinstance(s, (int, float)) else 0
        all_new_papers.sort(key=_score, reverse=True)

    sorted_papers = [("📊 按相关度排序", all_new_papers)] if all_new_papers else papers_by_layer

    html_local = build_html(sorted_papers, strategy, match_map=match_map, interactive=True)
    html_email = build_html(sorted_papers, strategy, match_map=match_map, interactive=False)

    # 缓存
    for _, papers in papers_by_layer:
        for p in papers:
            sent_cache.add(p["_hash"])
    save_sent_cache(sent_cache)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    today_tag = datetime.now().strftime("%m%d")
    html_path = os.path.join(out_dir, f"literature_{today_tag}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_local)

    if dry_run:
        print(f"[DRY-RUN] 预览: {html_path}")
    else:
        if email_ok:
            send_email(config, html_email, strategy.get("topic", "文献推送"))
        print(f"[HTML] {html_path}")
        try:
            webbrowser.open(f"file:///{html_path.replace(chr(92), '/')}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
