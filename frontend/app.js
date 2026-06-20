const uploadForm = document.querySelector("#uploadForm");
const fileInput = document.querySelector("#fileInput");
const askForm = document.querySelector("#askForm");
const questionInput = document.querySelector("#questionInput");
const documentsEl = document.querySelector("#documents");
const messagesEl = document.querySelector("#messages");
const clearButton = document.querySelector("#clearButton");

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return entities[char];
  });
}

function addMessage(role, html) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.innerHTML = html;
  messagesEl.appendChild(message);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return message;
}

async function loadDocuments() {
  const response = await fetch("/api/documents");
  const data = await response.json();
  const documents = data.documents || [];

  if (!documents.length) {
    documentsEl.innerHTML = `<p class="subtle">No documents uploaded yet.</p>`;
    return;
  }

  documentsEl.innerHTML = documents
    .map(
      (doc) => `
        <div class="doc">
          <strong>${escapeHtml(doc.name)}</strong>
          <span>${doc.chunk_count} chunks indexed</span>
        </div>
      `,
    )
    .join("");
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = fileInput.files[0];
  if (!file) return;

  const button = uploadForm.querySelector("button");
  button.disabled = true;
  button.textContent = "Uploading...";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Upload failed");

    addMessage(
      "assistant",
      `<strong>Indexed ${escapeHtml(data.document.name)}</strong><p>${data.document.chunk_count} chunks are ready for questions.</p>`,
    );
    fileInput.value = "";
    await loadDocuments();
  } catch (error) {
    addMessage("assistant", `<strong>Upload failed</strong><p>${escapeHtml(error.message)}</p>`);
  } finally {
    button.disabled = false;
    button.textContent = "Upload";
  }
});

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  addMessage("user", escapeHtml(question));
  questionInput.value = "";

  const pending = addMessage("assistant", "<strong>Thinking...</strong>");

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: 4 }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Question failed");

    const sources = (data.sources || [])
      .map(
        (source, index) => `
          <div class="source">
            <div class="source-title">
              <span>Source ${index + 1}: ${escapeHtml(source.doc_name)} #${source.chunk_index}</span>
              <span>${source.score}</span>
            </div>
            <p>${escapeHtml(source.text.slice(0, 420))}${source.text.length > 420 ? "..." : ""}</p>
          </div>
        `,
      )
      .join("");

    pending.innerHTML = `
      <strong>Answer</strong>
      <p>${escapeHtml(data.answer).replace(/\n/g, "<br />")}</p>
      ${sources ? `<div class="sources">${sources}</div>` : ""}
    `;
  } catch (error) {
    pending.innerHTML = `<strong>Ask failed</strong><p>${escapeHtml(error.message)}</p>`;
  }
});

clearButton.addEventListener("click", async () => {
  await fetch("/api/documents", { method: "DELETE" });
  await loadDocuments();
  addMessage("assistant", "<strong>Cleared.</strong><p>The local document index is empty.</p>");
});

loadDocuments();
