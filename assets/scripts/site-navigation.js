(() => {
  const root = document.documentElement;
  const sidebar = document.querySelector("[data-site-sidebar]");
  const stage = document.querySelector("[data-site-stage]");
  const openButton = document.querySelector("[data-sidebar-open]");
  const closeButton = document.querySelector("[data-sidebar-close]");
  const scrim = document.querySelector("[data-sidebar-scrim]");
  const media = window.matchMedia("(max-width: 959px)");

  if (!sidebar) return;

  const language = document.documentElement.lang.toLowerCase().startsWith("en") ? "en" : "zh";
  const storageKey = `recruitl.sidebar.sections.v1.${language}`;
  let lastFocused = null;

  const readStoredSections = () => {
    try {
      return JSON.parse(window.localStorage.getItem(storageKey)) || {};
    } catch (_) {
      return {};
    }
  };

  const writeStoredSections = state => {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(state));
    } catch (_) {
      // Navigation remains usable when storage is unavailable.
    }
  };

  const setSection = (section, expanded) => {
    const toggle = section.querySelector("[data-sidebar-toggle]");
    const items = toggle && document.getElementById(toggle.getAttribute("aria-controls"));
    if (!toggle || !items) return;
    toggle.setAttribute("aria-expanded", String(expanded));
    items.hidden = !expanded;
  };

  const storedSections = readStoredSections();
  sidebar.querySelectorAll("[data-sidebar-section]").forEach(section => {
    const id = section.dataset.sidebarSection;
    const expanded = section.classList.contains("has-current-page") || storedSections[id] !== false;
    setSection(section, expanded);
  });

  sidebar.querySelectorAll("[data-sidebar-toggle]").forEach(toggle => {
    toggle.addEventListener("click", () => {
      const section = toggle.closest("[data-sidebar-section]");
      const expanded = toggle.getAttribute("aria-expanded") !== "true";
      setSection(section, expanded);
      const nextState = readStoredSections();
      nextState[section.dataset.sidebarSection] = expanded;
      writeStoredSections(nextState);
    });
  });

  const focusableSelector = [
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    "[tabindex]:not([tabindex='-1'])"
  ].join(",");

  const setStageInert = inert => {
    if (!stage) return;
    if (inert) {
      stage.setAttribute("inert", "");
      stage.setAttribute("aria-hidden", "true");
    } else {
      stage.removeAttribute("inert");
      stage.removeAttribute("aria-hidden");
    }
  };

  const closeDrawer = ({ restoreFocus = true } = {}) => {
    root.classList.remove("sidebar-is-open");
    openButton?.setAttribute("aria-expanded", "false");
    sidebar.removeAttribute("role");
    sidebar.removeAttribute("aria-modal");
    scrim?.setAttribute("hidden", "");
    setStageInert(false);
    if (restoreFocus && lastFocused instanceof HTMLElement) lastFocused.focus();
  };

  const openDrawer = () => {
    if (!media.matches) return;
    lastFocused = document.activeElement;
    root.classList.add("sidebar-is-open");
    openButton?.setAttribute("aria-expanded", "true");
    sidebar.setAttribute("role", "dialog");
    sidebar.setAttribute("aria-modal", "true");
    scrim?.removeAttribute("hidden");
    setStageInert(true);
    closeButton?.focus();
  };

  openButton?.addEventListener("click", openDrawer);
  closeButton?.addEventListener("click", () => closeDrawer());
  scrim?.addEventListener("click", () => closeDrawer());

  sidebar.addEventListener("click", event => {
    if (media.matches && event.target.closest("a[href]")) closeDrawer({ restoreFocus: false });
  });

  document.addEventListener("keydown", event => {
    if (!root.classList.contains("sidebar-is-open")) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeDrawer();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = Array.from(sidebar.querySelectorAll(focusableSelector)).filter(element => !element.hidden && element.offsetParent !== null);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  const handleViewportChange = event => {
    if (!event.matches) closeDrawer({ restoreFocus: false });
  };

  if (typeof media.addEventListener === "function") media.addEventListener("change", handleViewportChange);
  else media.addListener(handleViewportChange);
})();
