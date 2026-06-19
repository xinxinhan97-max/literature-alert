# Literature Alert

每天早上扫一眼自己领域的新论文——这事我手工做了两年，烦了，于是写了这个。

在 Claude Code 里聊几句，告诉它你研究什么，它就帮你搭好一套自动化系统：每天去 OpenAlex 搜最新论文，AI 逐篇读摘要、打分、匹配子方向、翻译摘要、提炼创新点，最后生成一个浏览器能打开的 HTML 报告。你点点鼠标就能标记已读/不读、随手写笔记、导出一份 Markdown 日志。

不需要懂 Python，不需要服务器，甚至不需要装任何第三方包。

---

## 怎么用

### Claude Code 一键部署

```
/setup-literature
```

跟着对话走就行。AI 模型选 DeepSeek 的话，一个月大概两块钱。

### 手动安装

```bash
git clone https://github.com/xinxinhan97-max/literature-alert.git
cd literature-alert/templates
# 编辑 strategies.json，写上你的研究方向
# 编辑 config.json，填 API Key（要用 AI 分析的话）
python literature_alert.py --dry-run   # 先试跑看看
python literature_alert.py             # 正式运行
```

---

## 具体功能

- **双源检索** — 同时搜 OpenAlex（2.5 亿篇论文）和 arXiv，合并去重
- **AI 打分** — 每篇论文 1-5 星，匹配到你的具体子方向
- **摘要翻译** — 把英文摘要逐句翻成中文（或英文/双语，你选），不概括、不省略
- **提炼关键信息** — 创新点、实验方法、性能指标、对你课题的借鉴价值
- **期刊分级** — 自动匹配影响因子和 JCR 分区（10,200+ 期刊）
- **浏览器交互** — 打开 HTML 就能标记已读/跳过/写笔记，状态存本地浏览器
- **一键导出** — 把当天的阅读记录导出为 Markdown 日志
- **邮件推送**（可选）— 用 QQ 邮箱 SMTP 把报告发到邮箱
- **定时 + 开机自启** — Windows 定时任务到点就跑，开机自启当兜底

---

## 支持的 AI 模型

| 模型 | 月费（估） |
|------|-----------|
| DeepSeek（推荐） | ~¥2 |
| OpenAI GPT-4o-mini | ~¥5 |
| 智谱 GLM-4-Flash | ~¥3 |
| 通义千问 Qwen-Plus | ~¥3 |
| 本地 Ollama | 免费 |
| 其他 OpenAI 兼容 API | 自己试 |

也可以完全不用 AI——纯检索，跳过分析和翻译。

---

## 环境要求

Python 3.9+。零第三方依赖，换了电脑拷过去就能跑。

---

## English

I spent two years manually searching for new papers every morning. Got tired of it and built this.

Describe your research area to Claude Code, and it sets up a daily pipeline for you: searches OpenAlex (and optionally arXiv) for the latest papers, then an AI reads each abstract, scores relevance to your sub-topics, translates the abstract, and extracts innovations, methods, and takeaways. Results open as an interactive HTML page in your browser — mark papers read or skip, jot notes, export a reading log.

### Features

- **Dual-source search** — OpenAlex (250M papers) + arXiv, merged and deduplicated
- **AI scoring** — 1-5 star relevance rating, matched to your specific sub-directions
- **Abstract translation** — faithful sentence-by-sentence translation (Chinese / English / bilingual)
- **Key extraction** — innovation, methods, performance metrics, practical takeaways
- **Journal metrics** — impact factor and JCR quartile lookup (10,200+ journals)
- **Interactive HTML** — read/skip/note buttons, state persisted in browser localStorage
- **One-click export** — Markdown reading log for the day
- **Email digest** (optional) — SMTP delivery to your inbox
- **Scheduled + auto-start** — Windows Task Scheduler for timed runs, startup shortcut as fallback

### Setup

```
/setup-literature
```

Or manually:

```bash
git clone https://github.com/xinxinhan97-max/literature-alert.git
cd literature-alert/templates
python literature_alert.py --dry-run
```

### AI Models

DeepSeek (recommended, ~$0.3/month), OpenAI, Zhipu GLM, Qwen, local Ollama, or any OpenAI-compatible API. Skip AI entirely if you only want search results.

### Requirements

Python 3.9+. Zero pip dependencies. Works on any machine.

---

## Sponsor

省了你的时间的话，请我喝杯咖啡。

<div align="center">
  <table>
    <tr>
      <td align="center"><b>支付宝</b></td>
      <td align="center"><b>微信</b></td>
    </tr>
    <tr>
      <td><img src="支付宝收款码.jpg" width="200" alt="支付宝"></td>
      <td><img src="微信收款码.jpg" width="200" alt="微信"></td>
    </tr>
  </table>
</div>

## License

MIT
