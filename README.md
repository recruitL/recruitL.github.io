# [recruitL](https://recruitl.github.io/)

## Paper Watch

`scripts/paper_watch.py` 会按 `config/paper_watch.json` 抓取 arXiv、期刊 RSS 和 Crossref 元数据，生成 `/papers/` 下的论文日报。

本地手动生成：

```bash
python3 scripts/paper_watch.py --no-ai
```

启用 AI 分析需要设置 `OPENAI_API_KEY`，邮件提醒需要在 GitHub Secrets 中设置 `SMTP_HOST`、`SMTP_USER`、`SMTP_PASSWORD` 和 `PAPER_WATCH_EMAIL_TO`。
