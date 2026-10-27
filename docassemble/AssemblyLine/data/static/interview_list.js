/* Show progress without interrupting the first saved-form navigation. */
(function () {
  "use strict";

  function resetLink(link) {
    window.clearTimeout(link.alSessionLoadingTimer);
    delete link.alSessionLoadingTimer;
    link.classList.remove("al-session-loading");
    link.removeAttribute("aria-disabled");
    link.removeAttribute("aria-busy");
    if (link.alSessionLoadingDialog) {
      link.alSessionLoadingDialog.close();
      link.alSessionLoadingDialog.remove();
      delete link.alSessionLoadingDialog;
    }
  }

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
    var dialog = document.createElement("dialog");
    dialog.className = "al-session-loading-dialog";
    dialog.setAttribute("aria-label", link.dataset.loadingMessage || "Loading…");
    var status = document.createElement("div");
    status.className = "al-session-loading-status";
    status.setAttribute("role", "status");
    var spinner = document.createElement("i");
    spinner.className = "fa-solid fa-spinner fa-spin";
    spinner.setAttribute("aria-hidden", "true");
    status.appendChild(spinner);
    status.appendChild(document.createTextNode(" " +
      (link.dataset.loadingMessage || "Loading…")));
    dialog.appendChild(status);
    document.body.appendChild(dialog);
    link.alSessionLoadingDialog = dialog;
    dialog.addEventListener("cancel", function () { resetLink(link); });
    dialog.showModal();
    // Stop/Escape or a cancelled navigation may leave this document in place
    // without another pageshow event. Allow retrying after the initial wait.
    link.alSessionLoadingTimer = window.setTimeout(function () {
      resetLink(link);
    }, 15000);
  });

  // Back/forward cache can restore the page exactly as it was while loading.
  window.addEventListener("pageshow", function () {
    document.querySelectorAll("a.al-session-loading").forEach(function (link) {
      resetLink(link);
    });
  });
}());
