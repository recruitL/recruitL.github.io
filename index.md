---
title: recruitL个人主页
layout: home
lang: zh-CN
lang_pair: /en/
feature_image: "/document/picture/1300_400.jpg"
excerpt: ""
---

<section class="home-hero">
  <div class="home-hero__copy">
    <p class="home-kicker">Theoretical physics · Scientific computing</p>
    <h1>探索引力、计算与开放研究</h1>
    <p class="home-lead">这里是 recruitL 的个人网站，用于整理科研学习、代码实现、活动记录和博客。</p>
    <p>主要关注引力、相对论天体物理、数值计算和论文复现。这个网站既是对外的研究入口，也是持续生长的个人知识索引。</p>
  </div>
  <aside class="home-hero__aside" aria-label="学术主页">
    <span class="home-aside__label">Academic profiles</span>
    <div class="profile-links">
  <a href="https://github.com/recruitL">{% include icon.html id="github" title="GitHub" color="#181717" %}<span>GitHub</span></a>
  <a href="mailto:shenglong@ucas.ac.cn">{% include icon.html id="email" title="Email" color="#d44638" %}<span>Email</span></a>
  <a href="https://inspirehep.net/authors/2761677?ui-citation-summary=true">{% include icon.html id="inspire" title="INSPIRE-HEP" color="#00e5ff" %}<span>INSPIRE-HEP</span></a>
  <a href="https://scholar.google.com/citations?user=zDxt9_kAAAAJ&hl=zh-TW&authuser=1">{% include icon.html id="google-scholar" title="Google Scholar" color="#4285f4" %}<span>Google Scholar</span></a>
  <a href="https://orcid.org/0009-0009-0163-2724">{% include icon.html id="orcid" title="ORCID" color="#a6ce39" %}<span>ORCID</span></a>
    </div>
    <p class="home-aside__note">研究记录优先保持可检索、可复现，并尽可能链接到代码与原始资料。</p>
  </aside>
</section>

<section class="home-section home-section--index">
<header class="home-section__heading">
  <span>01 / Index</span>
  <h2>从这里开始</h2>
  <p>按研究、实现、阅读与活动进入网站，不必沿时间线逐页翻找。</p>
</header>

<div class="home-entry-grid">
  <a class="home-entry home-entry--research" href="/blog/#research-tree-title">
    <span class="home-entry__number">01</span><strong>研究专题</strong>
    <span>围绕引力、QNM、EOB、LISA 等方向组织的知识入口。</span>
  </a>
  <a class="home-entry home-entry--code" href="/code/">
    <span class="home-entry__number">02</span><strong>代码库</strong>
    <span>数值计算、数据处理、论文复现和个人工具。</span>
  </a>
  <a class="home-entry home-entry--papers" href="/papers/">
    <span class="home-entry__number">03</span><strong>论文日报</strong>
    <span>面向当前研究兴趣的论文筛选、评述与追踪。</span>
  </a>
  <a class="home-entry home-entry--activity" href="/activities/">
    <span class="home-entry__number">04</span><strong>活动等</strong>
    <span>学术会议、报告活动、资料链接和相关记录。</span>
  </a>
  <a class="home-entry home-entry--note" href="/blog/">
    <span class="home-entry__number">05</span><strong>博客</strong>
    <span>论文阅读、学习记录、技术笔记和阶段总结。</span>
  </a>
</div>
</section>

{% assign research_topics = site.data.research_topics.topics | sort: "order" %}
{% if research_topics and research_topics.size > 0 %}
<section class="home-section home-section--research">
<header class="home-section__heading">
  <span>02 / Research map</span>
  <h2>研究坐标</h2>
  <p>从问题域进入当前积累；每个专题连接方法、文献、代码与下一步。</p>
</header>
<div class="home-research-grid">
{% for topic in research_topics %}
  <a class="home-research-item" href="{{ '/research/' | append: topic.slug | append: '/' | relative_url }}">
    <span>{{ forloop.index | prepend: '0' | slice: -2, 2 }}</span>
    <div><strong>{{ topic.title }}</strong><p>{{ topic.summary }}</p></div>
    <i aria-hidden="true">↗</i>
  </a>
{% endfor %}
</div>
</section>
{% endif %}

<section class="home-section home-section--calendar">
<header class="home-section__heading">
  <span>03 / Calendar</span>
  <h2>活动万年历</h2>
</header>
{% include activity-calendar.html activity_path="/activities/" %}
</section>

<section class="home-section home-section--updates">
<header class="home-section__heading">
  <span>04 / Log</span>
  <h2>近期动态</h2>
</header>
<div class="timeline">
  <div class="timeline-item">
    <span class="timeline-date">近期</span>
    <span class="timeline-tag timeline-tag--code">代码库</span>
    <p><a href="/AIRobort/">AIRobort</a> App 设计仓库已加入代码库页面，集中整理应用设计、界面与交互相关内容。</p>
  </div>
  <div class="timeline-item">
    <span class="timeline-date">近期</span>
    <span class="timeline-tag timeline-tag--code">代码库</span>
    <p><a href="/code/">py-sc</a> 已补全至第十三章“数值优化”，覆盖单变量搜索、无导数优化、梯度/Newton、拟 Newton 和启发式算法。</p>
  </div>
</div>
</section>
