(() => {
  const selector = ".typeset img:not(.no-lightbox)";
  const images = Array.from(document.querySelectorAll(selector)).filter(img => {
    return !img.closest("a, button, .image-lightbox");
  });

  if (!images.length) {
    return;
  }

  const lightbox = document.createElement("div");
  lightbox.className = "image-lightbox";
  lightbox.setAttribute("role", "dialog");
  lightbox.setAttribute("aria-modal", "true");
  lightbox.setAttribute("aria-hidden", "true");

  const closeButton = document.createElement("button");
  closeButton.className = "image-lightbox__close";
  closeButton.type = "button";
  closeButton.setAttribute("aria-label", "Close image preview");
  closeButton.textContent = "x";

  const preview = document.createElement("img");
  preview.className = "image-lightbox__image";
  preview.alt = "";

  const caption = document.createElement("p");
  caption.className = "image-lightbox__caption";

  lightbox.append(closeButton, preview, caption);
  document.body.append(lightbox);

  const open = img => {
    preview.src = img.currentSrc || img.src;
    preview.alt = img.alt || "";
    caption.textContent = img.alt || "";
    caption.hidden = !img.alt;
    lightbox.classList.add("is-open");
    lightbox.setAttribute("aria-hidden", "false");
    document.documentElement.classList.add("image-lightbox-open");
    closeButton.focus();
  };

  const close = () => {
    lightbox.classList.remove("is-open");
    lightbox.setAttribute("aria-hidden", "true");
    document.documentElement.classList.remove("image-lightbox-open");
    preview.removeAttribute("src");
  };

  images.forEach(img => {
    img.classList.add("image-lightbox__trigger");
    img.tabIndex = 0;
    img.setAttribute("role", "button");
    img.addEventListener("click", () => open(img));
    img.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        open(img);
      }
    });
  });

  closeButton.addEventListener("click", close);
  preview.addEventListener("click", close);
  lightbox.addEventListener("click", event => {
    if (event.target === lightbox) {
      close();
    }
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && lightbox.classList.contains("is-open")) {
      close();
    }
  });
})();
