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
    <div class="home-hero__meta" aria-hidden="true">
      <span>Research atlas</span>
      <span>recruitL / 2026</span>
    </div>
    <p class="home-kicker">Theoretical physics · Scientific computing</p>
    <h1>Tracing gravity<br>through computation.</h1>
    <p class="home-lead">This is recruitL's open research atlas: a place to follow questions, methods, and code across gravitation and relativistic astrophysics.</p>
    <p class="home-intro">My current interests include gravitation, relativistic astrophysics, numerical computation, and reproducing methods from papers. The site serves both as a public research entry point and a searchable, reproducible record of work in progress.</p>
    <div class="home-hero__actions">
      <a class="atlas-button" href="#research-map">Explore research <span aria-hidden="true">↓</span></a>
      <a class="atlas-button atlas-button--ghost" href="/papers/">Open Paper Watch <span aria-hidden="true">↗</span></a>
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
      <h2>Start here</h2>
      <p>Enter through research, implementation, reading, or activities; each path leads to a body of work that keeps evolving.</p>
    </div>
  </header>

  <div class="home-entry-grid">
    <a class="home-entry home-entry--research" href="#research-map">
      <span class="home-entry__number">01</span><strong>Research</strong>
      <span>Knowledge paths across gravitation, QNMs, EOB, and LISA.</span><i aria-hidden="true">↗</i>
    </a>
    <a class="home-entry home-entry--code" href="/en/code/">
      <span class="home-entry__number">02</span><strong>Code</strong>
      <span>Numerical computation, paper reproduction, and research tools.</span><i aria-hidden="true">↗</i>
    </a>
    <a class="home-entry home-entry--papers" href="/papers/">
      <span class="home-entry__number">03</span><strong>Paper Watch</strong>
      <span>Daily filtering, review, and tracking around current interests.</span><i aria-hidden="true">↗</i>
    </a>
    <a class="home-entry home-entry--activity" href="/en/activities/">
      <span class="home-entry__number">04</span><strong>Activities</strong>
      <span>Academic conferences, talks, and related records.</span><i aria-hidden="true">↗</i>
    </a>
    <a class="home-entry home-entry--note" href="/en/blog/">
      <span class="home-entry__number">05</span><strong>Blog</strong>
      <span>Paper reading, study logs, and technical notes.</span><i aria-hidden="true">↗</i>
    </a>
  </div>
</section>

{% assign research_topics = site.data.research_topics.topics | sort: "order" %}
{% if research_topics and research_topics.size > 0 %}
<section class="home-section home-section--research" id="research-map">
  <header class="home-section__heading">
    <span>02 / Research map</span>
    <div>
      <h2>Research coordinates</h2>
      <p>Enter through a problem area; each topic connects methods, literature, code, and next steps.</p>
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
      <h2>Current coordinates</h2>
      <p>Upcoming activities and recent site updates form the time axis of this research atlas.</p>
    </div>
  </header>

  <div class="home-current-grid">
    <section class="home-current-panel" aria-labelledby="home-calendar-title">
      <header class="home-current-panel__heading">
        <span>Schedule</span><h3 id="home-calendar-title">Activity calendar</h3>
      </header>
      {% include activity-calendar.html lang="en" activity_path="/en/activities/" %}
    </section>

    <section class="home-current-panel" aria-labelledby="home-updates-title">
      <header class="home-current-panel__heading">
        <span>Log</span><h3 id="home-updates-title">Recent updates</h3>
      </header>
      <div class="timeline">
        <div class="timeline-item">
          <span class="timeline-date">Recent</span>
          <span class="timeline-tag timeline-tag--code">Code</span>
          <p><a href="/en/AIRobort/">AIRobort</a> has been added as an app design repository for application design, interface, and interaction materials.</p>
        </div>
        <div class="timeline-item">
          <span class="timeline-date">Recent</span>
          <span class="timeline-tag timeline-tag--code">Code</span>
          <p><a href="/en/code/">py-sc</a> now reaches chapter 13, numerical optimization, from one-dimensional search to quasi-Newton and heuristic methods.</p>
        </div>
      </div>
    </section>
  </div>
</section>
