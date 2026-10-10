/* Show progress without interrupting the first saved-form navigation. */
(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    var link = event.target.closest("a.al-session-form-title");
    if (!link || event.defaultPrevented || event.button !== 0 ||
        event.ctrlKey || event.metaKey || event.shiftKey || event.altKey ||
        link.hasAttribute("download") || (link.target && link.target !== "_self")) {
      return;
    }
    if (link.classList.contains("al-session-loading")) {
      event.preventDefault();
      event.stopImmediatePropagation();
      return;
    }

    link.classList.add("al-session-loading");
    link.setAttribute("aria-disabled", "true");
    link.setAttribute("aria-busy", "true");
    var status = document.createElement("span");
    status.className = "al-session-loading-status";
    status.setAttribute("role", "status");
    var spinner = document.createElement("i");
    spinner.className = "fa-solid fa-spinner fa-spin";
    spinner.setAttribute("aria-hidden", "true");
    status.appendChild(spinner);
    status.appendChild(document.createTextNode(" " +
      (link.dataset.loadingMessage || "Loading…")));
    link.insertAdjacentElement("afterend", status);
  });

  // Back/forward cache can restore the page exactly as it was while loading.
  window.addEventListener("pageshow", function () {
    document.querySelectorAll("a.al-session-loading").forEach(function (link) {
      link.classList.remove("al-session-loading");
      link.removeAttribute("aria-disabled");
      link.removeAttribute("aria-busy");
      var status = link.nextElementSibling;
      if (status && status.classList.contains("al-session-loading-status")) {
        status.remove();
      }
    });
  });
}());
