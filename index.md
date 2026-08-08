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
    <div class="home-hero__meta" aria-hidden="true">
      <span>Research atlas</span>
      <span>recruitL / 2026</span>
    </div>
    <p class="home-kicker">Theoretical physics · Scientific computing</p>
    <h1>探索引力，<br>以计算抵达。</h1>
    <p class="home-lead">这里是 recruitL 的开放研究入口：沿着问题、方法和代码，记录对引力与相对论天体物理的持续探索。</p>
    <p class="home-intro">主要关注引力、相对论天体物理、数值计算和论文复现。网站既面向同行与读者，也作为一份持续生长、可检索、可复现的个人研究地图。</p>
    <div class="home-hero__actions">
      <a class="atlas-button" href="#research-map">浏览研究坐标 <span aria-hidden="true">↓</span></a>
      <a class="atlas-button atlas-button--ghost" href="/papers/">进入论文日报 <span aria-hidden="true">↗</span></a>
    </div>
  </div>

  <aside class="home-hero__aside" aria-label="Research atlas visual">
    <figure class="home-visual">
      <img src="{{ page.feature_image | relative_url }}" alt="">
      <svg class="home-visual__orbit" viewBox="0 0 520 520" aria-hidden="true">
        <ellipse cx="260" cy="260" rx="194" ry="92"></ellipse>
        <ellipse cx="260" cy="260" rx="194" ry="92" transform="rotate(58 260 260)"></ellipse>
        <path d="M74 318C150 112 366 88 448 250"></path>
        <circle cx="373" cy="139" r="7"></circle>
        <circle cx="128" cy="334" r="4"></circle>
      </svg>
      <figcaption><span>Field notes 01</span><span>Gravitation / Computation</span></figcaption>
    </figure>
  </aside>

  <div class="home-hero__profiles">
    <span class="home-aside__label">Academic profiles</span>
    <div class="profile-links">
      <a href="https://github.com/recruitL">{% include icon.html id="github" title="GitHub" %}<span>GitHub</span></a>
      <a href="mailto:shenglong@ucas.ac.cn">{% include icon.html id="email" title="Email" %}<span>Email</span></a>
      <a href="https://inspirehep.net/authors/2761677?ui-citation-summary=true">{% include icon.html id="inspire" title="INSPIRE-HEP" %}<span>INSPIRE-HEP</span></a>
      <a href="https://scholar.google.com/citations?user=zDxt9_kAAAAJ&hl=zh-TW&authuser=1">{% include icon.html id="google-scholar" title="Google Scholar" %}<span>Google Scholar</span></a>
      <a href="https://orcid.org/0009-0009-0163-2724">{% include icon.html id="orcid" title="ORCID" %}<span>ORCID</span></a>
    </div>
  </div>
</section>

<section class="home-section home-section--index">
  <header class="home-section__heading">
    <span>01 / Index</span>
    <div>
      <h2>从这里开始</h2>
      <p>按研究、实现、阅读与活动进入网站；每个入口都对应一类持续维护的成果。</p>
    </div>
  </header>

  <div class="home-entry-grid">
    <a class="home-entry home-entry--research" href="#research-map">
      <span class="home-entry__number">01</span><strong>研究专题</strong>
      <span>引力、QNM、EOB、LISA 等方向的知识入口。</span><i aria-hidden="true">↗</i>
    </a>
    <a class="home-entry home-entry--code" href="/code/">
      <span class="home-entry__number">02</span><strong>代码库</strong>
      <span>数值计算、论文复现和个人研究工具。</span><i aria-hidden="true">↗</i>
    </a>
    <a class="home-entry home-entry--papers" href="/papers/">
      <span class="home-entry__number">03</span><strong>论文日报</strong>
      <span>围绕当前研究兴趣的筛选、评述与追踪。</span><i aria-hidden="true">↗</i>
    </a>
    <a class="home-entry home-entry--activity" href="/activities/">
      <span class="home-entry__number">04</span><strong>活动</strong>
      <span>学术会议、报告和相关资料记录。</span><i aria-hidden="true">↗</i>
    </a>
    <a class="home-entry home-entry--note" href="/blog/">
      <span class="home-entry__number">05</span><strong>博客</strong>
      <span>论文阅读、学习记录与技术笔记。</span><i aria-hidden="true">↗</i>
    </a>
  </div>
</section>

{% assign research_topics = site.data.research_topics.topics | sort: "order" %}
{% if research_topics and research_topics.size > 0 %}
<section class="home-section home-section--research" id="research-map">
  <header class="home-section__heading">
    <span>02 / Research map</span>
    <div>
      <h2>研究坐标</h2>
      <p>从问题域进入当前积累；每个专题连接方法、文献、代码与下一步。</p>
    </div>
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

<section class="home-section home-section--current">
  <header class="home-section__heading">
    <span>03 / Current</span>
    <div>
      <h2>当前坐标</h2>
      <p>近期活动与站点更新并列呈现，构成这份研究地图的时间维度。</p>
    </div>
  </header>

  <div class="home-current-grid">
    <section class="home-current-panel" aria-labelledby="home-calendar-title">
      <header class="home-current-panel__heading">
        <span>Schedule</span><h3 id="home-calendar-title">活动万年历</h3>
      </header>
      {% include activity-calendar.html activity_path="/activities/" %}
    </section>

    <section class="home-current-panel" aria-labelledby="home-updates-title">
      <header class="home-current-panel__heading">
        <span>Log</span><h3 id="home-updates-title">近期动态</h3>
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
  </div>
</section>
