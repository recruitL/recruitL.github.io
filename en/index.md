---
title: recruitL Home
layout: home
lang: en
lang_pair: /
feature_image: "/document/picture/1300_400.jpg"
excerpt: ""
---

<section class="home-hero">
  <div class="home-hero__copy">
    <p class="home-kicker">Theoretical physics · Scientific computing</p>
    <h1>Exploring gravitation through computation</h1>
    <p class="home-lead">This is recruitL's personal website for organizing research notes, code implementations, academic activities, and blog posts.</p>
    <p>My current interests include gravitation, relativistic astrophysics, numerical computation, and reproducing methods from papers. New updates are maintained primarily in Chinese, while this English home page provides a concise entry point.</p>
  </div>
  <aside class="home-hero__aside" aria-label="Academic profiles">
    <span class="home-aside__label">Academic profiles</span>
    <div class="profile-links">
  <a href="https://github.com/recruitL">{% include icon.html id="github" title="GitHub" color="#181717" %}<span>GitHub</span></a>
  <a href="mailto:shenglong@ucas.ac.cn">{% include icon.html id="email" title="Email" color="#d44638" %}<span>Email</span></a>
  <a href="https://inspirehep.net/authors/2761677?ui-citation-summary=true">{% include icon.html id="inspire" title="INSPIRE-HEP" color="#00e5ff" %}<span>INSPIRE-HEP</span></a>
  <a href="https://scholar.google.com/citations?user=zDxt9_kAAAAJ&hl=zh-TW&authuser=1">{% include icon.html id="google-scholar" title="Google Scholar" color="#4285f4" %}<span>Google Scholar</span></a>
  <a href="https://orcid.org/0009-0009-0163-2724">{% include icon.html id="orcid" title="ORCID" color="#a6ce39" %}<span>ORCID</span></a>
    </div>
    <p class="home-aside__note">Research records are kept searchable and reproducible, with links to code and primary material whenever possible.</p>
  </aside>
</section>

<section class="home-section home-section--index">
<header class="home-section__heading">
  <span>01 / Index</span>
  <h2>Start here</h2>
  <p>Enter through research, implementation, reading, or activities rather than browsing one long chronology.</p>
</header>

<div class="home-entry-grid">
  <a class="home-entry home-entry--research" href="/en/blog/#research-tree-title">
    <span class="home-entry__number">01</span><strong>Research</strong>
    <span>Knowledge paths across gravitation, QNMs, EOB, LISA, and related topics.</span>
  </a>
  <a class="home-entry home-entry--code" href="/en/code/">
    <span class="home-entry__number">02</span><strong>Code</strong>
    <span>Numerical computation, data processing, paper reproduction, and personal tools.</span>
  </a>
  <a class="home-entry home-entry--papers" href="/papers/">
    <span class="home-entry__number">03</span><strong>Paper Watch</strong>
    <span>Daily paper filtering, review, and tracking around current research interests.</span>
  </a>
  <a class="home-entry home-entry--activity" href="/en/activities/">
    <span class="home-entry__number">04</span><strong>Activities</strong>
    <span>Academic conferences, invited talks, useful links, and activity records.</span>
  </a>
  <a class="home-entry home-entry--note" href="/en/blog/">
    <span class="home-entry__number">05</span><strong>Blog</strong>
    <span>Paper reading notes, study logs, technical notes, and periodic summaries.</span>
  </a>
</div>
</section>

{% assign research_topics = site.data.research_topics.topics | sort: "order" %}
{% if research_topics and research_topics.size > 0 %}
<section class="home-section home-section--research">
<header class="home-section__heading">
  <span>02 / Research map</span>
  <h2>Research coordinates</h2>
  <p>Enter through a problem area; each topic connects methods, literature, code, and next steps.</p>
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
<header class="home-section__heading"><span>03 / Calendar</span><h2>Activity calendar</h2></header>
{% include activity-calendar.html lang="en" activity_path="/en/activities/" %}
</section>

<section class="home-section home-section--updates">
<header class="home-section__heading"><span>04 / Log</span><h2>Recent updates</h2></header>
<div class="timeline">
  <div class="timeline-item">
    <span class="timeline-date">Recent</span>
    <span class="timeline-tag timeline-tag--code">Code</span>
    <p><a href="/en/AIRobort/">AIRobort</a> has been added as an app design repository for application design, interface, and interaction materials.</p>
  </div>
  <div class="timeline-item">
    <span class="timeline-date">Recent</span>
    <span class="timeline-tag timeline-tag--code">Code</span>
    <p><a href="/en/code/">py-sc</a> now reaches chapter 13, numerical optimization, covering one-dimensional search, derivative-free optimization, gradient/Newton methods, quasi-Newton methods, and heuristic algorithms.</p>
  </div>
  <div class="timeline-item">
    <span class="timeline-date">2026-06</span>
    <span class="timeline-tag timeline-tag--activity">Activities</span>
    <p><a href="/en/activities/">Activities</a> now include conferences, talks, and a calendar-linked activity timeline.</p>
  </div>
</div>
</section>
