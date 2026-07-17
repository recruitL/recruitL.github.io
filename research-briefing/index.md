---
title: 研究每日简报
lang: zh-CN
permalink: /research-briefing/
excerpt: 每天 09:00 更新的研究简报，独立于论文日报。
---

<section class="briefing-intro">
  <p>这里发布围绕当前研究主线整理的每日简报：优先保留真正值得跟进的论文、软件更新与会议动态，并给出“为什么相关”和下一步动作。</p>
  <p><strong>与论文日报的区别：</strong><a href="{{ '/papers/' | relative_url }}">论文日报</a>是批量抓取与筛选清单；这里是进一步编辑后的 5–8 条研究简报，不复用同一归档。</p>
</section>

{% assign briefings = site.research_briefings | sort: "date" | reverse %}
{% if briefings and briefings.size > 0 %}
<ol class="briefing-archive">
  {% for briefing in briefings %}
  <li class="briefing-archive__item">
    <time datetime="{{ briefing.date | date_to_xmlschema }}">{{ briefing.date | date: "%Y-%m-%d" }}</time>
    <div>
      <h2><a href="{{ briefing.url | relative_url }}">{{ briefing.title }}</a></h2>
      {% if briefing.description %}<p>{{ briefing.description }}</p>{% endif %}
      {% if briefing.item_count %}<span>{{ briefing.item_count }} 条</span>{% endif %}
    </div>
  </li>
  {% endfor %}
</ol>
{% else %}
<p class="briefing-empty">简报尚未生成。自动任务会在每天 09:00（Asia/Shanghai）更新这里。</p>
{% endif %}
