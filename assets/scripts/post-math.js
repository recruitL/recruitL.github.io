// Local MathJax 3.2.2, Apache-2.0: assets/vendor/mathjax-3.2.2/LICENSE.
// SVG output includes its glyphs, so equation rendering needs no remote fonts.
window.MathJax = {
  tex: {
    inlineMath: [["$", "$"], ["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"], ["$$", "$$"]]
  },
  svg: { fontCache: "global" },
  options: { enableMenu: false }
};
