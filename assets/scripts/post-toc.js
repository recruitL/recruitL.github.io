(() => {
  const article = document.querySelector(".article--post");
  const tocContainers = Array.from(document.querySelectorAll("[data-post-toc]"));

  if (!article || !tocContainers.length) {
    return;
  }

  const headings = Array.from(article.querySelectorAll("h2, h3")).filter(heading => {
    return !heading.closest("[data-post-toc]") && heading.textContent.trim();
  });
  const minItems = Math.min(
    ...tocContainers.map(container => Number(container.dataset.postTocMin) || 4)
  );

  if (headings.length < minItems) {
    return;
  }

  const usedIds = new Set(Array.from(document.querySelectorAll("[id]")).map(node => node.id));
  const slugify = (text, index) => {
    const slug = text
      .trim()
      .toLowerCase()
      .normalize("NFKD")
      .replace(/[^\p{L}\p{N}\s-]/gu, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-|-$/g, "");

    return slug || `section-${index + 1}`;
  };

  const ensureId = (heading, index) => {
    if (heading.id) {
      return heading.id;
    }

    const base = slugify(heading.textContent, index);
    let id = base;
    let suffix = 2;
    while (usedIds.has(id)) {
      id = `${base}-${suffix}`;
      suffix += 1;
    }
    heading.id = id;
    usedIds.add(id);
    return id;
  };

  const entries = headings.map((heading, index) => ({
    id: ensureId(heading, index),
    level: Number(heading.tagName.replace("H", "")),
    text: heading.textContent.trim()
  }));

  tocContainers.forEach(container => {
    const list = container.querySelector("[data-post-toc-list]");
    if (!list) return;

    list.innerHTML = "";
    entries.forEach(entry => {
      const item = document.createElement("li");
      item.className = `post-toc__item post-toc__item--level-${entry.level}`;

      const link = document.createElement("a");
      link.className = "post-toc__link";
      link.href = `#${encodeURIComponent(entry.id)}`;
      link.textContent = entry.text;
      link.dataset.postTocLink = entry.id;

      item.append(link);
      list.append(item);
    });

    container.hidden = false;
  });

  document.documentElement.classList.add("has-post-toc");
  if (tocContainers.some(container => container.classList.contains("post-toc--aside"))) {
    document.documentElement.classList.add("has-post-toc-aside");
  }

  if (!("IntersectionObserver" in window)) {
    return;
  }

  const setActive = id => {
    document.querySelectorAll("[data-post-toc-link]").forEach(link => {
      link.classList.toggle("is-active", link.dataset.postTocLink === id);
    });
  };

  const visibleHeadings = new Map();
  const observer = new IntersectionObserver(observedEntries => {
    observedEntries.forEach(entry => {
      if (entry.isIntersecting) {
        visibleHeadings.set(entry.target.id, entry.boundingClientRect.top);
      } else {
        visibleHeadings.delete(entry.target.id);
      }
    });

    const firstVisible = Array.from(visibleHeadings.entries())
      .sort((a, b) => a[1] - b[1])[0];
    if (firstVisible) {
      setActive(firstVisible[0]);
    }
  }, {
    rootMargin: "0px 0px -70% 0px",
    threshold: 0
  });

  headings.forEach(heading => observer.observe(heading));
})();
