(function () {
  "use strict";

  const app = window.IntellApp;
  const api = window.IntellAPI;
  const CONVERSATION_KEY = "intell_conversation_id_v1";
  if (!app || !api) return;

  function createMessage(role, text, sources = []) {
    const message = document.createElement("div");
    message.className = `chat-message ${role}`;
    if (role === "assistant") {
      const heading = document.createElement("strong");
      heading.textContent = "Intell Assistant";
      message.appendChild(heading);
    }
    const copy = document.createElement("span");
    copy.textContent = text;
    message.appendChild(copy);
    if (sources.length) {
      const sourceRow = document.createElement("div");
      sourceRow.className = "message-sources";
      sources.forEach((source, index) => {
        const link = document.createElement("a");
        const reference =
          typeof source === "string"
            ? { label: source, title: source, url: "" }
            : source;
        link.textContent = reference.label || `[${index + 1}] ${reference.title}`;
        link.title = reference.title || "Open source";
        link.href = reference.url || "#";
        if (reference.url) {
          link.target = "_blank";
          link.rel = "noopener noreferrer";
        } else {
          link.addEventListener("click", (event) => event.preventDefault());
        }
        sourceRow.appendChild(link);
      });
      message.appendChild(sourceRow);
    }
    return message;
  }

  function saveHistory(history) {
    app.writeJSON(app.KEYS.chat, history.slice(-20));
  }

  function addTyping(transcript) {
    const typing = document.createElement("div");
    typing.className = "chat-message assistant";
    typing.innerHTML =
      '<span class="typing-indicator" aria-label="Assistant is preparing an answer"><i></i><i></i><i></i></span>';
    transcript.appendChild(typing);
    transcript.scrollTop = transcript.scrollHeight;
    return typing;
  }

  function currentScope() {
    return (
      document.querySelector("#scope-button .scope-label")?.textContent?.trim().toLowerCase() ||
      "all"
    );
  }

  function updateSuggestions(suggestions) {
    if (!suggestions?.length) return;
    const buttons = document.querySelectorAll("[data-prompt]");
    suggestions.slice(0, buttons.length).forEach((suggestion, index) => {
      buttons[index].textContent = suggestion;
      buttons[index].dataset.prompt = suggestion;
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("news-question");
    const transcript = document.getElementById("chat-transcript");
    const submit = form?.querySelector('[type="submit"]');
    if (!form || !input || !transcript) return;

    let history = app.readJSON(app.KEYS.chat, []);
    let conversationId = localStorage.getItem(CONVERSATION_KEY);
    history.forEach((entry) =>
      transcript.appendChild(createMessage(entry.role, entry.text, entry.sources || []))
    );
    transcript.hidden = history.length === 0;

    async function ask(question) {
      const cleaned = question.trim();
      if (!cleaned) {
        app.showToast("Type a question first.", "error");
        input.focus();
        return;
      }

      transcript.hidden = false;
      transcript.appendChild(createMessage("user", cleaned));
      history.push({ role: "user", text: cleaned });
      saveHistory(history);
      input.value = "";
      input.disabled = true;
      if (submit) submit.disabled = true;
      const typing = addTyping(transcript);

      let result;
      try {
        result = await api.ask(cleaned, currentScope(), conversationId);
        if (result.conversation_id) {
          conversationId = result.conversation_id;
          localStorage.setItem(CONVERSATION_KEY, conversationId);
        }
      } catch (error) {
        app.showToast(error.message || "The assistant is unavailable.", "error");
        result =
          window.IntellNews?.storyContext(cleaned) || {
            text: "The assistant could not reach the API. Start the backend and try again.",
            sources: [],
          };
        result = {
          answer: result.answer || result.text,
          sources: result.sources || [],
          suggestions: [],
        };
      } finally {
        typing.remove();
        input.disabled = false;
        if (submit) submit.disabled = false;
      }

      transcript.appendChild(createMessage("assistant", result.answer, result.sources));
      history.push({
        role: "assistant",
        text: result.answer,
        sources: result.sources,
      });
      saveHistory(history);
      updateSuggestions(result.suggestions);
      transcript.scrollTop = transcript.scrollHeight;
      input.focus();
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      ask(input.value);
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });
    document.querySelectorAll("[data-prompt]").forEach((button) =>
      button.addEventListener("click", () => ask(button.dataset.prompt))
    );
    window.addEventListener("intell:new-briefing", () => {
      history = [];
      conversationId = null;
      saveHistory(history);
      localStorage.removeItem(CONVERSATION_KEY);
      transcript.replaceChildren();
      transcript.hidden = true;
      input.focus();
    });
  });
})();
