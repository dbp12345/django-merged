let deferredPrompt = null;

function isIos() {
  return /iphone|ipad|ipod/i.test(window.navigator.userAgent);
}

function isAndroid() {
  return /android/i.test(window.navigator.userAgent);
}

function isStandalone() {
  return window.matchMedia("(display-mode: standalone)").matches
    || window.navigator.standalone === true;
}

function updateInstallHelp() {
  const helpEls = document.querySelectorAll("[data-install-help]");
  const titleEls = document.querySelectorAll("[data-install-title]");
  const subtextEls = document.querySelectorAll("[data-install-subtext]");
  const installButtons = document.querySelectorAll("#install-app-button, #install-app-button-summary");
  const hasPrompt = Boolean(deferredPrompt);

  function setCopy(title, help, subtext) {
    titleEls.forEach((el) => {
      el.textContent = title;
    });
    helpEls.forEach((el) => {
      el.textContent = help;
      el.hidden = false;
    });
    subtextEls.forEach((el) => {
      el.textContent = subtext;
    });
  }

  if (isStandalone()) {
    setCopy("App installed", "This app is already installed on this device.", "Open it from your home screen like a normal app.");
    installButtons.forEach((button) => {
      button.hidden = true;
      button.disabled = true;
    });
    return;
  }

  if (isIos()) {
    setCopy(
      "Install on iPhone",
      'In Safari, tap Share and then "Add to Home Screen".',
      "Safari installs this app manually instead of showing an install popup."
    );
    installButtons.forEach((button) => {
      button.hidden = true;
      button.disabled = true;
    });
    return;
  }

  if (hasPrompt) {
    setCopy(
      "Install this app",
      "Your browser is ready. Use the Install button now.",
      "This adds the app to your home screen or app launcher."
    );
    installButtons.forEach((button) => {
      button.hidden = false;
      button.disabled = false;
    });
    return;
  }

  if (isAndroid()) {
    setCopy(
      "Install on Android",
      "If the Install button is not showing yet, open the browser menu and choose Install app or Add to Home screen.",
      "Chrome sometimes waits for a little browsing activity before showing the install prompt."
    );
  } else {
    setCopy(
      "Install on this device",
      "Use your browser menu or address-bar install icon if available.",
      "Desktop Chrome and some mobile browsers do not always show the prompt immediately."
    );
  }

  installButtons.forEach((button) => {
    button.hidden = true;
    button.disabled = !hasPrompt;
  });
}

function updateNetworkStatus() {
  const online = navigator.onLine;
  const statusEls = document.querySelectorAll("#network-status, #network-status-summary");
  statusEls.forEach((statusEl) => {
    statusEl.textContent = online ? "Online" : "Offline";
    statusEl.classList.toggle("offline", !online);
  });
}

function setInstallButtonsVisible(visible) {
  const buttons = document.querySelectorAll("#install-app-button, #install-app-button-summary");
  buttons.forEach((button) => {
    button.hidden = !visible;
  });
}

function syncDrawer(open) {
  const drawer = document.getElementById("app-drawer");
  const toggle = document.getElementById("menu-toggle");
  if (!drawer || !toggle) return;

  drawer.hidden = !open;
  toggle.setAttribute("aria-expanded", open ? "true" : "false");
  document.body.classList.toggle("drawer-open", open);
}

window.addEventListener("online", updateNetworkStatus);
window.addEventListener("offline", updateNetworkStatus);
window.addEventListener("load", updateNetworkStatus);
window.addEventListener("load", () => syncDrawer(false));
window.addEventListener("load", updateInstallHelp);

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredPrompt = event;
  setInstallButtonsVisible(true);
  updateInstallHelp();
});

window.addEventListener("appinstalled", () => {
  deferredPrompt = null;
  setInstallButtonsVisible(false);
  updateInstallHelp();
});

document.addEventListener("click", async (event) => {
  const drawerToggle = event.target.closest("#menu-toggle");
  if (drawerToggle) {
    syncDrawer(true);
    return;
  }

  const drawerClose = event.target.closest("#menu-close");
  if (drawerClose) {
    syncDrawer(false);
    return;
  }

  const button = event.target.closest("#install-app-button, #install-app-button-summary");
  if (!button || !deferredPrompt) return;

  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  setInstallButtonsVisible(false);
  updateInstallHelp();
});
