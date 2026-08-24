---
title: recruitL Home
layout: home
lang: en
lang_pair: /
excerpt: ""
---

<header class="research-home__intro">
  <p class="research-home__kicker">Theoretical physics · Scientific computing</p>
  <h1>Tracing gravity through computation.</h1>
  <p class="research-home__lead">This is recruitL's open research atlas: a place to follow questions, methods, and code across gravitation and relativistic astrophysics.</p>
  <p class="research-home__summary">My current interests include gravitation, relativistic astrophysics, numerical computation, and reproducing methods from papers. The site serves both as a public research entry point and a searchable, reproducible record of work in progress.</p>
</header>

{% assign research_topics = site.data.research_topics.topics | sort: "order" %}
{% if research_topics and research_topics.size > 0 %}
<section class="research-home__section" id="research-map" aria-labelledby="home-research-title">
  <header class="research-home__section-heading">
    <p>01 / Current research</p>
    <div>
      <h2 id="home-research-title">Research coordinates</h2>
      <p>Enter through a problem area; each topic connects methods, literature, code, and next steps.</p>
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
      <h2 id="home-updates-title">Recent updates</h2>
      <p>Recent changes to site content and research tools.</p>
    </div>
  </header>
  <div class="research-home__updates">
    <article>
      <div><span>Recent</span><span>Code</span></div>
      <p><a href="/en/AIRobort/">AIRobort</a> has been added as an app design repository for application design, interface, and interaction materials.</p>
    </article>
    <article>
      <div><span>Recent</span><span>Code</span></div>
      <p><a href="/en/code/">py-sc</a> now reaches chapter 13, numerical optimization, from one-dimensional search to quasi-Newton and heuristic methods.</p>
    </article>
  </div>
</section>

<section class="research-home__section" aria-labelledby="home-content-title">
  <header class="research-home__section-heading">
    <p>03 / Content</p>
    <div>
      <h2 id="home-content-title">Explore the site</h2>
      <p>Enter through implementation, reading, or activities.</p>
    </div>
  </header>
  <nav aria-label="Site content">
    <ul class="research-home__content-list">
      <li><a href="/en/code/"><strong>Code</strong><span>Numerical computation, paper reproduction, and research tools.</span><i aria-hidden="true">↗</i></a></li>
      <li><a href="/papers/"><strong>Paper Watch</strong><span>Daily filtering, review, and tracking around current interests.</span><i aria-hidden="true">↗</i></a></li>
      <li><a href="/research-briefing/"><strong>Research Briefing</strong><span>Periodic signals and observations for current research directions.</span><i aria-hidden="true">↗</i></a></li>
      <li><a href="/en/blog/"><strong>Blog</strong><span>Paper reading, study logs, and technical notes.</span><i aria-hidden="true">↗</i></a></li>
      <li><a href="/en/activities/"><strong>Activities</strong><span>Academic conferences, talks, and related records.</span><i aria-hidden="true">↗</i></a></li>
    </ul>
  </nav>
</section>

<section class="research-home__section research-home__calendar" aria-labelledby="home-calendar-title">
  <header class="research-home__section-heading">
    <p>04 / Schedule</p>
    <div>
      <h2 id="home-calendar-title">Activity calendar</h2>
      <p>A time index of existing activity records.</p>
    </div>
  </header>
  {% include activity-calendar.html lang="en" activity_path="/en/activities/" %}
</section>
