---
title: 活动等
feature_text: |
  会议记录、报告活动和相关资料整理
feature_image: "https://raw.githubusercontent.com/recruitL/recruitL.github.io/main/document/picture/3a3101dd7047ff7f.jpg"
excerpt: "活动入口"
aside: true
---

这里整理学术会议、报告活动、资料链接和相关记录。

## 活动

<p class="activity-note">整理与学术活动有关的会议及报告信息，分享一些有用的网站和资料入口。</p>

## 活动万年历

<div class="activity-calendar" data-calendar>
  <div class="activity-calendar__toolbar">
    <button type="button" data-calendar-prev aria-label="上一月">上一月</button>
    <label>
      年份
      <input type="number" min="1900" max="9999" step="1" data-calendar-year>
    </label>
    <label>
      月份
      <select data-calendar-month>
        <option value="0">1 月</option>
        <option value="1">2 月</option>
        <option value="2">3 月</option>
        <option value="3">4 月</option>
        <option value="4">5 月</option>
        <option value="5">6 月</option>
        <option value="6">7 月</option>
        <option value="7">8 月</option>
        <option value="8">9 月</option>
        <option value="9">10 月</option>
        <option value="10">11 月</option>
        <option value="11">12 月</option>
      </select>
    </label>
    <button type="button" data-calendar-today>今天</button>
    <button type="button" data-calendar-next aria-label="下一月">下一月</button>
  </div>
  <div class="activity-calendar__header">
    <strong data-calendar-title></strong>
    <span>有活动的日期可点击并跳转到对应条目</span>
  </div>
  <table aria-label="活动万年历">
    <thead>
      <tr>
        <th>一</th>
        <th>二</th>
        <th>三</th>
        <th>四</th>
        <th>五</th>
        <th>六</th>
        <th>日</th>
      </tr>
    </thead>
    <tbody data-calendar-body></tbody>
  </table>
  <div class="activity-calendar__events" data-calendar-events></div>
</div>

<div class="timeline activity-list">
  <div
    class="timeline-item"
    id="conference-2024-gr"
    data-activity-start="2024-04-19"
    data-activity-end="2024-04-24"
    data-activity-title="2024 引力年会"
  >
    <span class="timeline-date">2024-04-19 至 2024-04-24</span>
    <span class="timeline-tag timeline-tag--activity">会议</span>
    <p><strong>2024 引力年会</strong>，中国物理学会引力与相对论天体物理分会学术年会暨第六届伽利略-徐光启国际会议，湖南衡阳。</p>
    <p><a href="/2024/04/19/annual/">查看会议记录</a> / <a href="http://meeting2024.usc.edu.cn/Meeting/conferences/gr24/home_1.php">会议官网</a></p>
  </div>
</div>

<p class="activity-more">更多会议记录会按时间线倒序追加。</p>

## 网站分享

<ol class="activity-links">
  <li><a href="https://www.ligo.org/">LIGO</a>：引力波观测与科普资料入口。</li>
  <li><a href="https://inspirehep.net/authors/2761677?ui-citation-summary=true">INSPIRE-HEP</a>：高能物理与引力相关文献、作者和引用信息。</li>
  <li><a href="https://arxiv.org/">arXiv</a>：论文预印本检索和订阅。</li>
</ol>

## 归档方式

后续活动记录按年份维护，优先保留日期、地点、主题、个人角色和资料链接。首页只展示近期动态，活动页负责长期归档。

<script>
(() => {
  const root = document.querySelector("[data-calendar]");
  if (!root) return;

  const title = root.querySelector("[data-calendar-title]");
  const body = root.querySelector("[data-calendar-body]");
  const yearInput = root.querySelector("[data-calendar-year]");
  const monthSelect = root.querySelector("[data-calendar-month]");
  const eventLinks = root.querySelector("[data-calendar-events]");
  const today = new Date();
  let viewYear = today.getFullYear();
  let viewMonth = today.getMonth();

  const escapeHtml = value => String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
  const pad = value => String(value).padStart(2, "0");
  const keyOf = date => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  const parseDate = value => {
    const [year, month, day] = value.split("-").map(Number);
    return new Date(year, month - 1, day);
  };

  const activityEvents = Array.from(document.querySelectorAll("[data-activity-start]"))
    .map(item => {
      const heading = item.querySelector("strong");
      return {
        start: item.dataset.activityStart,
        end: item.dataset.activityEnd || item.dataset.activityStart,
        title: item.dataset.activityTitle || (heading ? heading.textContent.trim() : "活动"),
        anchor: item.id
      };
    })
    .filter(event => event.start && event.anchor);

  const eventsByDate = new Map();
  activityEvents.forEach(event => {
    const start = parseDate(event.start);
    const end = parseDate(event.end || event.start);
    for (let date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
      const key = keyOf(date);
      const list = eventsByDate.get(key) || [];
      list.push(event);
      eventsByDate.set(key, list);
    }
  });

  const renderEventLinks = () => {
    eventLinks.innerHTML = activityEvents.map(event => {
      const endText = event.end && event.end !== event.start ? ` 至 ${event.end}` : "";
      return `<a href="#${event.anchor}">${event.start}${endText}：${escapeHtml(event.title)}</a>`;
    }).join("");
  };

  const renderCalendar = () => {
    const firstDay = new Date(viewYear, viewMonth, 1);
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const leadingBlankDays = (firstDay.getDay() + 6) % 7;
    const todayKey = keyOf(today);
    let day = 1;
    let html = "";

    title.textContent = `${viewYear} 年 ${viewMonth + 1} 月`;
    yearInput.value = viewYear;
    monthSelect.value = viewMonth;

    for (let row = 0; row < 6; row += 1) {
      html += "<tr>";
      for (let column = 0; column < 7; column += 1) {
        const cellIndex = row * 7 + column;
        if (cellIndex < leadingBlankDays || day > daysInMonth) {
          html += '<td class="activity-calendar__blank"></td>';
          continue;
        }

        const date = new Date(viewYear, viewMonth, day);
        const dateKey = keyOf(date);
        const dateEvents = eventsByDate.get(dateKey) || [];
        const classes = [];
        if (dateKey === todayKey) classes.push("activity-calendar__today");
        if (dateEvents.length > 0) classes.push("activity-calendar__has-event");
        const classAttr = classes.length ? ` class="${classes.join(" ")}"` : "";

        if (dateEvents.length > 0) {
          const labels = escapeHtml(dateEvents.map(event => event.title).join(" / "));
          html += `<td${classAttr}><a href="#${dateEvents[0].anchor}" title="${labels}">${day}</a></td>`;
        } else {
          html += `<td${classAttr}>${day}</td>`;
        }
        day += 1;
      }
      html += "</tr>";
      if (day > daysInMonth) break;
    }

    body.innerHTML = html;
  };

  root.querySelector("[data-calendar-prev]").addEventListener("click", () => {
    viewMonth -= 1;
    if (viewMonth < 0) {
      viewMonth = 11;
      viewYear -= 1;
    }
    renderCalendar();
  });

  root.querySelector("[data-calendar-next]").addEventListener("click", () => {
    viewMonth += 1;
    if (viewMonth > 11) {
      viewMonth = 0;
      viewYear += 1;
    }
    renderCalendar();
  });

  root.querySelector("[data-calendar-today]").addEventListener("click", () => {
    viewYear = today.getFullYear();
    viewMonth = today.getMonth();
    renderCalendar();
  });

  yearInput.addEventListener("change", () => {
    const nextYear = Number(yearInput.value);
    if (Number.isInteger(nextYear) && nextYear >= 1900 && nextYear <= 9999) {
      viewYear = nextYear;
      renderCalendar();
    }
  });

  monthSelect.addEventListener("change", () => {
    viewMonth = Number(monthSelect.value);
    renderCalendar();
  });

  renderEventLinks();
  renderCalendar();
})();
</script>
