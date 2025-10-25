const socket = io();


// ----------------- WebSocket Events -----------------
socket.on("connect", () => console.log("Connected to server"));


socket.on("server_message", (msg) => console.log("server:", msg));

socket.on("rag_result", (data) => {
  const list = document.getElementById("results");
  const li = document.createElement("li");
  const answerSnippet = data.answer ? data.answer.slice(0, 600) : "";
  li.innerHTML = `<strong>${data.user}</strong> — <em>${data.llm_model || ""}</em><br/>
                  Q: ${data.question}<br/>
                  A: ${answerSnippet}${data.answer && data.answer.length > 600 ? "..." : ""}`;
  list.prepend(li);
});

// ----------------- Populate PDF Dropdown Dynamically -----------------
async function loadPDFOptions() {
  try {
    const res = await fetch("/pdf_list");
    const pdfs = await res.json();
    const pdfSelect = document.getElementById("pdfSelect");
    pdfSelect.innerHTML = ""; // Clear existing options
    pdfs.forEach(pdf => {
      const option = document.createElement("option");
      option.value = pdf;
      option.textContent = pdf;
      pdfSelect.appendChild(option);
    });
  } catch (err) {
    console.error("Error loading PDF list:", err);
  }
}

// ----------------- DOM Actions -----------------
async function queueQuestion() {
  const user = document.getElementById("user").value || "web_user";
  const question = document.getElementById("question").value.trim();
  if (!question) return alert("Please enter a question");

  // Get selected PDFs
  const pdfSelect = document.getElementById("pdfSelect");
  const pdf_ids = Array.from(pdfSelect.selectedOptions).map(opt => opt.value);
  if (pdf_ids.length === 0) return alert("Please select at least one PDF");

  const payload = { user, question, pdf_ids };

  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === "queued") {
      document.getElementById("question").value = "";
      alert("Question queued.");
    }
  } catch (err) {
    console.error("Error sending question:", err);
  }
}

async function refreshRecent() {
  try {
    const res = await fetch("/recent");
    const data = await res.json();
    const out = document.getElementById("recent");
    out.innerHTML = "";
    data.forEach(d => {
      const el = document.createElement("div");
      const answerSnippet = d.answer ? d.answer.slice(0, 300) : "";
      el.innerHTML = `<strong>${d.user}</strong> — ${d.question}<br/>
                      <small>${d.llm_model || ""} ${d.cache_hit ? "(cache)" : ""}</small>
                      <div style="margin-top:6px">${answerSnippet}${d.answer && d.answer.length>300 ? "..." : ""}</div>
                      <hr/>`;
      out.appendChild(el);
    });
  } catch (err) {
    console.error("Error fetching recent queries:", err);
  }
}

// ----------------- Event Listeners -----------------
document.getElementById("askBtn").addEventListener("click", queueQuestion);
document.getElementById("refreshBtn").addEventListener("click", refreshRecent);

// ----------------- Initialize -----------------
loadPDFOptions(); // Populate PDF dropdown on page load
