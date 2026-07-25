(function () {
  "use strict";

  const KEYS = {
    session: "intell_session_v1",
    bookmarks: "intell_bookmarks_v1",
    chat: "intell_chat_v1",
  };

  function readJSON(key, fallback) {
    try {
      const value = localStorage.getItem(key);
      return value ? JSON.parse(value) : fallback;
    } catch (_error) {
      return fallback;
    }
  }

  function writeJSON(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  function showToast(message, type = "success") {
    const region = document.getElementById("toast-region");
    if (!region) return;
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    region.appendChild(toast);
    window.setTimeout(() => toast.remove(), 3200);
  }

  function getSession() {
    const session = readJSON(KEYS.session, null);
    if (session?.expiresAt && session.expiresAt <= Date.now()) {
      localStorage.removeItem(KEYS.session);
      return null;
    }
    return session;
  }

  function updateProfile() {
    const session = getSession();
    const card = document.getElementById("profile-trigger");
    if (!card) return;
    const name = card.querySelector("strong");
    const detail = card.querySelector("small");
    const avatar = card.querySelector(".avatar");
    const loginAction = document.querySelector('[data-profile-action="login"]');
    const logoutAction = document.querySelector('[data-profile-action="logout"]');
    const welcomeHeading = document.querySelector(".welcome h1");

    if (session) {
      const fullName = `${session.firstName || ""} ${session.lastName || ""}`.trim() || session.email;
      if (name) name.textContent = fullName;
      if (detail) detail.textContent = session.email;
      if (avatar) avatar.textContent = `${session.firstName?.[0] || "U"}${session.lastName?.[0] || ""}`.toUpperCase();
      if (welcomeHeading) welcomeHeading.textContent = `Good morning, ${session.firstName || "reader"}.`;
      if (loginAction) loginAction.hidden = true;
      if (logoutAction) logoutAction.hidden = false;
    } else {
      if (name) name.textContent = "Guest reader";
      if (detail) detail.textContent = "Sign in to personalise";
      if (avatar) avatar.textContent = "G";
      if (welcomeHeading) welcomeHeading.textContent = "Good morning.";
      if (loginAction) loginAction.hidden = false;
      if (logoutAction) logoutAction.hidden = true;
    }
  }

  function setupProfileMenu() {
    const trigger = document.getElementById("profile-trigger");
    const menu = document.getElementById("profile-menu");
    if (!trigger || !menu) return;

    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      const opening = menu.hidden;
      menu.hidden = !opening;
      trigger.setAttribute("aria-expanded", String(opening));
    });

    document.addEventListener("click", (event) => {
      if (!menu.hidden && !menu.contains(event.target) && !trigger.contains(event.target)) {
        menu.hidden = true;
        trigger.setAttribute("aria-expanded", "false");
      }
    });

    menu.querySelector('[data-profile-action="logout"]')?.addEventListener("click", async () => {
      try {
        if (getSession()?.accessToken) await window.IntellAPI?.logout();
      } catch (_error) {
        // Clearing the local token still completes logout if the server is offline.
      } finally {
        localStorage.removeItem(KEYS.session);
        menu.hidden = true;
        trigger.setAttribute("aria-expanded", "false");
        updateProfile();
        window.dispatchEvent(
          new CustomEvent("intell:session-changed", {
            detail: { authenticated: false },
          })
        );
        showToast("You have been signed out.");
      }
    });
  }

  function setupNavigation() {
    const navToggle = document.getElementById("nav-toggle");
    document.querySelectorAll(".main-nav .nav-item").forEach((link) => {
      link.addEventListener("click", () => {
        document.querySelectorAll(".main-nav .nav-item").forEach((item) => item.classList.remove("active"));
        link.classList.add("active");
        if (navToggle) navToggle.checked = false;
      });
    });

    document.querySelector('[data-action="new-briefing"]')?.addEventListener("click", () => {
      window.dispatchEvent(new CustomEvent("intell:new-briefing"));
      if (navToggle) navToggle.checked = false;
      document.getElementById("briefing")?.scrollIntoView({ behavior: "smooth" });
      showToast("A new briefing is ready.");
    });

    const liveButton = document.getElementById("live-coverage");
    liveButton?.addEventListener("click", () => {
      const enabled = liveButton.getAttribute("aria-pressed") !== "true";
      liveButton.setAttribute("aria-pressed", String(enabled));
      showToast(enabled ? "Live coverage enabled." : "Live coverage paused.");
    });

    document.getElementById("notifications-button")?.addEventListener("click", () => {
      showToast("You’re caught up. No new notifications.");
      document.querySelector(".notification-dot")?.remove();
    });

    const scopes = ["All news", "Malaysia", "World", "Technology"];
    const scopeButton = document.getElementById("scope-button");
    scopeButton?.addEventListener("click", () => {
      const label = scopeButton.querySelector(".scope-label");
      const current = scopes.indexOf(label?.textContent || scopes[0]);
      const next = scopes[(current + 1) % scopes.length];
      if (label) label.textContent = next;
      showToast(`Question scope: ${next}.`);
    });

    document.querySelectorAll('a[href^="#"]').forEach((link) => {
      link.addEventListener("click", (event) => {
        const target = link.getAttribute("href");
        if (target === "#" || !document.querySelector(target)) {
          event.preventDefault();
          showToast("This section will be connected to the backend later.");
        }
      });
    });
  }

  window.IntellApp = { KEYS, readJSON, writeJSON, showToast, getSession };

  document.addEventListener("DOMContentLoaded", () => {
    const date = document.getElementById("current-date");
    if (date) {
      const today = new Date();
      date.dateTime = today.toISOString().slice(0, 10);
      date.textContent = new Intl.DateTimeFormat("en-MY", {
        weekday: "long",
        day: "numeric",
        month: "long",
      }).format(today);
    }
    updateProfile();
    setupProfileMenu();
    setupNavigation();
  });
})();
