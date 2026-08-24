---
title: recruitL个人主页
layout: home
lang: zh-CN
lang_pair: /en/
excerpt: ""
---

<header class="research-home__intro">
  <p class="research-home__kicker">Theoretical physics · Scientific computing</p>
  <h1>探索引力，以计算抵达。</h1>
  <p class="research-home__lead">这里是 recruitL 的开放研究入口：沿着问题、方法和代码，记录对引力与相对论天体物理的持续探索。</p>
  <p class="research-home__summary">主要关注引力、相对论天体物理、数值计算和论文复现。网站既面向同行与读者，也作为一份持续生长、可检索、可复现的个人研究地图。</p>
</header>

{% assign research_topics = site.data.research_topics.topics | sort: "order" %}
{% if research_topics and research_topics.size > 0 %}
<section class="research-home__section" id="research-map" aria-labelledby="home-research-title">
  <header class="research-home__section-heading">
    <p>01 / Current research</p>
    <div>
      <h2 id="home-research-title">研究坐标</h2>
      <p>从问题域进入当前积累；每个专题连接方法、文献、代码与下一步。</p>
    </div>
  </header>
  <ol class="research-home__research-list">
  {% for topic in research_topics %}
    <li>
      <a href="{{ '/research/' | append: topic.slug | append: '/' | relative_url }}">
        <span class="research-home__index">{{ forloop.index | prepend: '0' | slice: -2, 2 }}</span>
        <span class="research-home__item-copy"><strong>{{ topic.short_title | default: topic.title }}</strong><span>{{ topic.summary }}</span></span>
        <span class="research-home__arrow" aria-hidden="true">↗</span>
      </a>
    </li>
  {% endfor %}
  </ol>
</section>
{% endif %}

<section class="research-home__section" id="home-updates" aria-labelledby="home-updates-title">
  <header class="research-home__section-heading">
    <p>02 / Recent updates</p>
    <div>
      <h2 id="home-updates-title">近期动态</h2>
      <p>站点内容与研究工具的最近变化。</p>
    </div>
  </header>
  <div class="research-home__updates">
    <article>
      <div><span>近期</span><span>代码库</span></div>
      <p><a href="/AIRobort/">AIRobort</a> App 设计仓库已加入代码库页面，集中整理应用设计、界面与交互相关内容。</p>
    </article>
    <article>
      <div><span>近期</span><span>代码库</span></div>
      <p><a href="/code/">py-sc</a> 已补全至第十三章“数值优化”，覆盖单变量搜索、无导数优化、梯度/Newton、拟 Newton 和启发式算法。</p>
    </article>
  </div>
</section>

<section class="research-home__section" aria-labelledby="home-content-title">
  <header class="research-home__section-heading">
    <p>03 / Content</p>
    <div>
      <h2 id="home-content-title">内容入口</h2>
      <p>按实现、阅读与活动进入持续维护的成果。</p>
    </div>
  </header>
  <nav aria-label="内容入口">
    <ul class="research-home__content-list">
      <li><a href="/code/"><strong>代码库</strong><span>数值计算、论文复现和个人研究工具。</span><i aria-hidden="true">↗</i></a></li>
      <li><a href="/papers/"><strong>论文日报</strong><span>围绕当前研究兴趣的筛选、评述与追踪。</span><i aria-hidden="true">↗</i></a></li>
      <li><a href="/research-briefing/"><strong>研究简报</strong><span>面向当前研究方向的周期性线索与观察。</span><i aria-hidden="true">↗</i></a></li>
      <li><a href="/blog/"><strong>博客</strong><span>论文阅读、学习记录与技术笔记。</span><i aria-hidden="true">↗</i></a></li>
      <li><a href="/activities/"><strong>活动</strong><span>学术会议、报告和相关资料记录。</span><i aria-hidden="true">↗</i></a></li>
    </ul>
  </nav>
</section>

<section class="research-home__section research-home__calendar" aria-labelledby="home-calendar-title">
  <header class="research-home__section-heading">
    <p>04 / Schedule</p>
    <div>
      <h2 id="home-calendar-title">活动万年历</h2>
      <p>已有活动记录的时间索引。</p>
    </div>
  </header>
  {% include activity-calendar.html activity_path="/activities/" %}
</section>
