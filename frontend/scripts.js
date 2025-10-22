const socket = io();

socket.on("connect", () => {
  console.log("Connected to server");
});

socket.on("server_message", (m) => {
  console.log("server:", m);
});

socket.on("rag_result", (data) => {
  // prepend to results
  const list = document.getElementById("results");
  const li = document.createElement("li");
  li.innerHTML = `<strong>${data.user}</strong> — <em>${data.llm_model || ""}</em><br/>
                  Q: ${data.question}<br/>
                  A: ${data.answer.slice(0, 600)}${data.answer.length>600 ? "..." : ""}`;
  list.prepend(li);
});

document.getElementById("askBtn").addEventListener("click", async () => {
  const user = document.getElementById("user").value || "web_user";
  const question = document.getElementById("question").value;
  if (!question) { alert("Please enter a question"); return; }
  const res = await fetch("/ask", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ user, question }) });
  const j = await res.json();
  if (j.status === "queued") {
    document.getElementById("question").value = "";
    alert("Question queued.");
  }
});

document.getElementById("refreshBtn").addEventListener("click", async () => {
  const res = await fetch("/recent");
  const data = await res.json();
  const out = document.getElementById("recent");
  out.innerHTML = "";
  data.forEach(d => {
    const el = document.createElement("div");
    el.innerHTML = `<strong>${d.user}</strong> — ${d.question}<br/><small>${(d.llm_model || "")} ${d.cache_hit? "(cache)": ""}</small><div style="margin-top:6px">${d.answer.slice(0,300)}${d.answer.length>300?"...":""}</div><hr/>`;
    out.appendChild(el);
  });
});
