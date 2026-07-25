(function () {
  "use strict";

  const SESSION_KEY = "intell_session_v1";
  const staticDevPorts = new Set(["3000", "8000"]);
  const inferredOrigin = staticDevPorts.has(window.location.port)
    ? `${window.location.protocol}//${window.location.hostname}:5500`
    : window.location.origin;
  const API_BASE = window.INTELL_API_BASE || `${inferredOrigin}/api`;

  function getSession() {
    try {
      return JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
    } catch (_error) {
      return null;
    }
  }

  function getToken() {
    return getSession()?.accessToken || null;
  }

  async function request(path, options = {}) {
    const headers = new Headers(options.headers || {});
    if (options.body !== undefined && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    const token = options.auth === false ? null : getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);

    let response;
    try {
      response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
        body:
          options.body === undefined || options.body instanceof FormData
            ? options.body
            : JSON.stringify(options.body),
      });
    } catch (_error) {
      throw new Error("Cannot reach the API. Start the FastAPI server and try again.");
    }

    if (response.status === 204) return null;
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
      ? await response.json()
      : { detail: await response.text() };
    if (!response.ok) {
      const detail = Array.isArray(payload.detail)
        ? payload.detail.map((item) => item.msg).join(" ")
        : payload.detail;
      throw new Error(detail || `Request failed (${response.status})`);
    }
    return payload;
  }

  function queryString(params) {
    const query = new URLSearchParams();
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        query.set(key, String(value));
      }
    });
    const encoded = query.toString();
    return encoded ? `?${encoded}` : "";
  }

  window.IntellAPI = {
    API_BASE,
    request,
    health: () => request("/health", { auth: false }),
    register: (payload) =>
      request("/auth/register", { method: "POST", body: payload, auth: false }),
    login: (payload) =>
      request("/auth/login", { method: "POST", body: payload, auth: false }),
    logout: () => request("/auth/logout", { method: "POST" }),
    forgotPassword: (email) =>
      request("/auth/forgot-password", {
        method: "POST",
        body: { email },
        auth: false,
      }),
    profile: () => request("/auth/me"),
    articles: (params) =>
      request(`/news/articles${queryString(params)}`, { auth: false }),
    bookmarks: () => request("/news/bookmarks"),
    saveBookmark: (articleId) =>
      request(`/news/bookmarks/${encodeURIComponent(articleId)}`, { method: "POST" }),
    removeBookmark: (articleId) =>
      request(`/news/bookmarks/${encodeURIComponent(articleId)}`, { method: "DELETE" }),
    ask: (question, scope = "all", conversationId = null) =>
      request("/chat/ask", {
        method: "POST",
        body: {
          question,
          scope,
          conversation_id: conversationId,
        },
      }),
  };
})();
