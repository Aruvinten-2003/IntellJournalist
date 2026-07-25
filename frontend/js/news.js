(function () {
  "use strict";

  const app = window.IntellApp;
  const api = window.IntellAPI;
  if (!app || !api) return;

  let articles = [];
  let bookmarks = new Set(app.readJSON(app.KEYS.bookmarks, []));
  let activeFilter = "all";

  function signedIn() {
    return Boolean(app.getSession()?.accessToken);
  }

  function saveLocalBookmarks() {
    app.writeJSON(app.KEYS.bookmarks, [...bookmarks]);
  }

  function relativeTime(value) {
    const timestamp = new Date(value).getTime();
    if (!Number.isFinite(timestamp)) return "Recently";
    const minutes = Math.round((timestamp - Date.now()) / 60_000);
    const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
    if (Math.abs(minutes) < 60) return formatter.format(minutes, "minute");
    const hours = Math.round(minutes / 60);
    if (Math.abs(hours) < 24) return formatter.format(hours, "hour");
    return formatter.format(Math.round(hours / 24), "day");
  }

  function categoryClass(category) {
    return {
      technology: "violet-tag",
      climate: "green-tag",
      business: "amber-tag",
    }[category] || "";
  }

  function createArt(category, index) {
    const art = document.createElement("div");
    if (category === "climate") {
      art.className = "card-art art-climate";
      const sun = document.createElement("span");
      sun.className = "sun";
      const horizon = document.createElement("span");
      horizon.className = "horizon";
      art.append(sun, horizon);
      return art;
    }
    if (category === "business") {
      art.className = "card-art art-business";
      const bars = document.createElement("div");
      bars.className = "bars";
      for (let count = 0; count < 5; count += 1) bars.appendChild(document.createElement("i"));
      const trend = document.createElement("span");
      trend.className = "trend";
      trend.textContent = "↗";
      art.append(bars, trend);
      return art;
    }
    art.className = "card-art art-tech";
    const number = document.createElement("span");
    number.textContent = String(index + 1).padStart(2, "0");
    art.appendChild(number);
    for (let count = 0; count < 3; count += 1) art.appendChild(document.createElement("i"));
    return art;
  }

  function createArticleCard(article, index) {
    const card = document.createElement("article");
    card.className = "story-card";
    card.dataset.storyId = article.id;
    card.dataset.category = article.category;
    card.dataset.country = article.country;
    card.dataset.articleUrl = article.url;
    card.tabIndex = 0;
    card.setAttribute("role", "link");
    card.setAttribute("aria-label", `Read ${article.title}`);

    const body = document.createElement("div");
    body.className = "card-body";
    const kicker = document.createElement("div");
    kicker.className = "story-kicker";
    const tag = document.createElement("span");
    tag.className = `category-tag ${categoryClass(article.category)}`.trim();
    tag.textContent = article.category.toUpperCase();
    const time = document.createElement("time");
    time.dateTime = article.published_at;
    time.textContent = relativeTime(article.published_at);
    kicker.append(tag, time);

    const title = document.createElement("h3");
    title.textContent = article.title;
    const excerpt = document.createElement("p");
    excerpt.textContent = article.excerpt;

    const footer = document.createElement("footer");
    const publisherIcon = document.createElement("span");
    publisherIcon.className = "publisher-icon";
    publisherIcon.textContent = article.publisher.slice(0, 1).toUpperCase();
    const publisher = document.createElement("strong");
    publisher.textContent = article.publisher;
    const bookmarkButton = document.createElement("button");
    bookmarkButton.type = "button";
    bookmarkButton.dataset.action = "bookmark";
    bookmarkButton.setAttribute("aria-label", "Bookmark story");
    bookmarkButton.setAttribute("aria-pressed", "false");
    bookmarkButton.innerHTML =
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4h12v16l-6-4-6 4z"/></svg>';
    footer.append(publisherIcon, publisher, bookmarkButton);
    body.append(kicker, title, excerpt, footer);
    card.append(createArt(article.category, index), body);
    return card;
  }

  function renderArticles() {
    const grid = document.querySelector(".story-grid");
    if (!grid) return;
    grid.replaceChildren(...articles.map(createArticleCard));
    renderBookmarkState();
    filterStories(activeFilter);
  }

  function renderBookmarkState() {
    document.querySelectorAll(".story-card").forEach((card) => {
      const saved = bookmarks.has(card.dataset.storyId);
      card.classList.toggle("bookmarked", saved);
      const button = card.querySelector('[data-action="bookmark"]');
      button?.setAttribute("aria-pressed", String(saved));
      button?.setAttribute("aria-label", saved ? "Remove bookmark" : "Bookmark story");
    });
    const count = document.querySelector(".nav-item .count");
    if (count) count.textContent = String(bookmarks.size);
  }

  function filterStories(filter) {
    let visible = 0;
    document.querySelectorAll(".story-card").forEach((card) => {
      const matches =
        filter === "all" ||
        (filter === "bookmarks" && bookmarks.has(card.dataset.storyId)) ||
        card.dataset.category === filter ||
        card.dataset.country === filter;
      card.hidden = !matches;
      if (matches) visible += 1;
    });

    const grid = document.querySelector(".story-grid");
    grid?.querySelector(".empty-state")?.remove();
    if (!visible && grid) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      const title = document.createElement("strong");
      title.textContent =
        filter === "bookmarks" ? "No saved stories yet" : "No stories match this filter";
      empty.append(
        title,
        document.createTextNode(
          filter === "bookmarks"
            ? "Use the bookmark icon on any story to save it here."
            : "Choose another category to continue reading."
        )
      );
      grid.appendChild(empty);
    }
  }

  function setActiveFilter(filter) {
    activeFilter = filter;
    document.querySelectorAll(".filter[data-filter]").forEach((button) => {
      const active = button.dataset.filter === filter;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    filterStories(filter);
  }

  async function toggleBookmark(card) {
    const id = card?.dataset.storyId;
    if (!id) return;
    const saved = bookmarks.has(id);
    try {
      if (signedIn()) {
        if (saved) await api.removeBookmark(id);
        else await api.saveBookmark(id);
      }
      if (saved) bookmarks.delete(id);
      else bookmarks.add(id);
      if (!signedIn()) saveLocalBookmarks();
      renderBookmarkState();
      if (activeFilter === "bookmarks") filterStories("bookmarks");
      app.showToast(saved ? "Bookmark removed." : "Story saved to bookmarks.");
    } catch (error) {
      app.showToast(error.message || "Unable to update the bookmark.", "error");
    }
  }

  function updateLeadStory() {
    const lead = articles[0];
    if (!lead) return;
    const container = document.querySelector(".lead-story");
    const heading = container?.querySelector(".lead-copy h3");
    const copy = container?.querySelector(".lead-copy > p");
    const time = container?.querySelector(".story-kicker time");
    const tag = container?.querySelector(".category-tag");
    const openButton = container?.querySelector(".round-button");
    if (heading) heading.textContent = lead.title;
    if (copy) copy.textContent = lead.excerpt;
    if (time) {
      time.dateTime = lead.published_at;
      time.textContent = relativeTime(lead.published_at);
    }
    if (tag) tag.textContent = lead.category.toUpperCase();
    if (openButton) openButton.dataset.articleUrl = lead.url;

    const sources = new Set(articles.map((article) => article.publisher));
    const stats = document.querySelectorAll(".brief-meta strong");
    if (stats[0]) stats[0].textContent = String(sources.size);
    if (stats[1]) stats[1].textContent = String(articles.length);
  }

  async function loadNews() {
    try {
      articles = await api.articles({ limit: 50 });
      renderArticles();
      updateLeadStory();
    } catch (error) {
      app.showToast(error.message || "Unable to load current stories.", "error");
      renderBookmarkState();
    }
  }

  async function loadBookmarks() {
    if (!signedIn()) {
      renderBookmarkState();
      return;
    }
    try {
      const savedArticles = await api.bookmarks();
      if (!signedIn()) return;
      bookmarks = new Set(savedArticles.map((article) => article.id));
      renderBookmarkState();
    } catch (error) {
      app.showToast(error.message || "Unable to load bookmarks.", "error");
    }
  }

  function storyContext(query) {
    const words = query.toLowerCase().split(/\W+/).filter((word) => word.length > 3);
    const matches = articles.filter((article) => {
      const text = `${article.title} ${article.excerpt} ${article.category} ${article.country}`.toLowerCase();
      return words.some((word) => text.includes(word));
    });
    const selected = (matches.length ? matches : articles).slice(0, 3);
    if (!selected.length) {
      return { text: "Current reporting is unavailable while the API reconnects.", sources: [] };
    }
    return {
      text: selected.map((article) => `${article.title}: ${article.excerpt}`).join(" "),
      sources: selected.map((article, index) => ({
        label: `[${index + 1}] ${article.publisher}`,
        title: article.title,
        url: article.url,
      })),
    };
  }

  window.IntellNews = {
    storyContext,
    setActiveFilter,
    getArticles: () => articles.slice(),
  };

  document.addEventListener("DOMContentLoaded", async () => {
    const grid = document.querySelector(".story-grid");
    grid?.addEventListener("click", (event) => {
      const bookmarkButton = event.target.closest('[data-action="bookmark"]');
      const card = event.target.closest(".story-card");
      if (bookmarkButton) {
        event.preventDefault();
        event.stopPropagation();
        toggleBookmark(card);
      } else if (card?.dataset.articleUrl) {
        window.open(card.dataset.articleUrl, "_blank", "noopener,noreferrer");
      }
    });
    grid?.addEventListener("keydown", (event) => {
      const card = event.target.closest(".story-card");
      if (card && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        window.open(card.dataset.articleUrl, "_blank", "noopener,noreferrer");
      }
    });

    document.querySelectorAll(".filter[data-filter]").forEach((button) =>
      button.addEventListener("click", () => setActiveFilter(button.dataset.filter))
    );
    document.querySelector('[data-action="show-bookmarks"]')?.addEventListener("click", (event) => {
      event.preventDefault();
      setActiveFilter("bookmarks");
      document.querySelector(".latest-section")?.scrollIntoView({ behavior: "smooth" });
    });
    document.querySelector(".filter-icon")?.addEventListener("click", () =>
      app.showToast("Use the category filters or ask the assistant for a specific topic.")
    );
    document.querySelector(".round-button")?.addEventListener("click", (event) => {
      const url = event.currentTarget.dataset.articleUrl;
      if (url) window.open(url, "_blank", "noopener,noreferrer");
    });
    document.querySelector(".text-button")?.addEventListener("click", () =>
      document.querySelector(".latest-section")?.scrollIntoView({ behavior: "smooth" })
    );
    window.addEventListener("intell:new-briefing", async () => {
      setActiveFilter("all");
      await loadNews();
    });
    window.addEventListener("intell:session-changed", () => {
      bookmarks = new Set(app.readJSON(app.KEYS.bookmarks, []));
      renderBookmarkState();
      filterStories(activeFilter);
    });

    await loadNews();
    await loadBookmarks();
  });
})();
