(function () {
  "use strict";

  const api = window.IntellAPI;
  const SESSION_KEY = "intell_session_v1";

  function showToast(message, type = "success") {
    const region = document.getElementById("toast-region");
    if (!region) return;
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    region.appendChild(toast);
    window.setTimeout(() => toast.remove(), 3200);
  }

  function setFeedback(form, message, type = "error") {
    form.querySelector(".form-feedback")?.remove();
    const feedback = document.createElement("p");
    feedback.className = `form-feedback${type === "success" ? " success" : ""}`;
    feedback.setAttribute("role", type === "error" ? "alert" : "status");
    feedback.textContent = message;
    form.prepend(feedback);
  }

  function normalizeEmail(value) {
    return value.trim().toLowerCase();
  }

  function validEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  function setLoading(form, loading, label) {
    const button = form.querySelector('.primary-button[type="submit"]');
    if (!button) return;
    if (!button.dataset.label) button.dataset.label = button.innerHTML;
    button.disabled = loading;
    if (loading) button.textContent = label;
    else button.innerHTML = button.dataset.label;
  }

  function saveSession(result) {
    const user = result.user;
    const session = {
      id: user._id || user.id,
      email: user.email,
      firstName: user.first_name,
      lastName: user.last_name,
      country: user.country,
      language: user.language,
      accessToken: result.access_token,
      expiresAt: Date.now() + result.expires_in * 1000,
    };
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  }

  function setupPasswordToggles() {
    document.querySelectorAll(".password-toggle").forEach((button) => {
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", () => {
        const input = button.closest(".password-input")?.querySelector("input");
        if (!input) return;
        const showing = input.type === "text";
        input.type = showing ? "password" : "text";
        button.setAttribute("aria-pressed", String(!showing));
        button.setAttribute("aria-label", showing ? "Show password" : "Hide password");
      });
    });
  }

  function setupLogin() {
    const form = document.getElementById("login-form");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const emailInput = form.elements.email;
      const passwordInput = form.elements.password;
      const email = normalizeEmail(emailInput.value);
      const valid = validEmail(email) && passwordInput.value.length >= 8;
      emailInput.setAttribute("aria-invalid", String(!validEmail(email)));
      passwordInput.setAttribute("aria-invalid", String(passwordInput.value.length < 8));
      if (!valid) {
        setFeedback(form, "Enter a valid email and a password of at least 8 characters.");
        return;
      }

      setLoading(form, true, "Signing in…");
      try {
        const result = await api.login({ email, password: passwordInput.value });
        saveSession(result);
        showToast("Signed in successfully.");
        window.setTimeout(() => window.location.assign("index.html"), 350);
      } catch (error) {
        setFeedback(form, error.message || "Unable to sign in.");
      } finally {
        setLoading(form, false);
      }
    });
  }

  function setupSignup() {
    const form = document.getElementById("signup-form");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const firstName = form.elements.first_name.value.trim();
      const lastName = form.elements.last_name.value.trim();
      const email = normalizeEmail(form.elements.email.value);
      const password = form.elements.password.value;
      const accepted = form.elements.terms.checked;
      if (!firstName || !lastName || !validEmail(email) || password.length < 8 || !accepted) {
        setFeedback(form, "Complete every field, use a valid email and accept the terms.");
        return;
      }

      setLoading(form, true, "Creating account…");
      try {
        const result = await api.register({
          first_name: firstName,
          last_name: lastName,
          email,
          password,
          country: "Malaysia",
          language: "English",
        });
        saveSession(result);
        showToast("Your account is ready.");
        window.setTimeout(() => window.location.assign("index.html"), 350);
      } catch (error) {
        setFeedback(form, error.message || "Unable to create the account.");
      } finally {
        setLoading(form, false);
      }
    });
  }

  function setupForgotPassword() {
    const form = document.getElementById("forgot-password-form");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const email = normalizeEmail(form.elements.email.value);
      if (!validEmail(email)) {
        setFeedback(form, "Enter a valid account email.");
        return;
      }
      setLoading(form, true, "Preparing reset…");
      try {
        const result = await api.forgotPassword(email);
        setFeedback(form, result.message, "success");
        form.reset();
      } catch (error) {
        setFeedback(form, error.message || "Unable to prepare the password reset.");
      } finally {
        setLoading(form, false);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (!api) {
      document.querySelector(".auth-form") &&
        setFeedback(document.querySelector(".auth-form"), "The API client failed to load.");
      return;
    }
    setupPasswordToggles();
    setupLogin();
    setupSignup();
    setupForgotPassword();
    document.querySelectorAll(".social-button").forEach((button) =>
      button.addEventListener("click", () =>
        showToast("OAuth provider credentials are not configured.", "error")
      )
    );
  });
})();
