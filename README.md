# Literature Alert · 文献快报

一个每天自动搜论文、AI 读摘要、生成网页报告的小工具。

A small tool that searches new papers daily, uses AI to read abstracts, and generates an interactive HTML report.

---

## 怎么用 · How to use

在 Claude Code 里输入：

In Claude Code, type:

```
/setup-literature
```

聊几句就搭好了。不用懂 Python。

A few lines of conversation and it's done. No Python knowledge needed.

手动安装 · Manual install：

```bash
git clone https://github.com/xinxinhan97-max/literature-alert.git
cd literature-alert/templates
# 改 strategies.json，填研究方向 · Edit strategies.json with your research topics
# 想用 AI 分析的话，config.json 里填 api key · Fill in api key in config.json for AI analysis
python literature_alert.py --dry-run   # 先试跑 · test run
python literature_alert.py             # 正式跑 · run
```

---

## 具体干什么 · What it does

- 从 OpenAlex 搜最近一周的新论文（arXiv 可选）
  Searches OpenAlex for recent papers (arXiv optional)
- AI 读每篇摘要，给 1-5 星打分，匹配到具体子方向
  AI reads abstracts, scores relevance (1-5), matches to sub-topics
- 摘要逐句翻译（中文 / 英文 / 双语），不概括不省略
  Sentence-by-sentence abstract translation (Chinese / English / bilingual)
- 提炼创新点、方法、关键指标、有没有参考价值
  Extracts innovations, methods, metrics, and takeaways
- 自动标期刊影响因子和 JCR 分区
  Journal impact factor and JCR quartile lookup
- 生成 HTML 网页，浏览器打开就能标记已读/跳过、写笔记，状态存浏览器里
  Interactive HTML page: mark read/skip, write notes (persisted in browser)
- 一键导出当天阅读记录为 Markdown
  One-click Markdown export of daily reading log
- 可选邮件推送
  Optional email digest
- 可选定时任务或开机自启
  Optional scheduled daily run or auto-start on boot

AI 模型用 DeepSeek 一个月大概两块钱。不用 AI 也行，纯检索。

With DeepSeek it costs about $0.3/month. Works without AI too — search only.

---

## 环境 · Requirements

Python 3.9+。零第三方依赖。 Zero dependencies.

---

## Sponsor · 支持

如果帮你省了时间，欢迎打赏。

If this saved you some time, buy me a coffee.

<div align="center">
  <table>
    <tr>
      <td align="center"><b>支付宝</b></td>
      <td align="center"><b>微信 · WeChat</b></td>
    </tr>
    <tr>
      <td><img src="支付宝收款码.jpg" width="200" alt="支付宝"></td>
      <td><img src="微信收款码.jpg" width="200" alt="微信"></td>
    </tr>
  </table>
</div>

## License

MIT
