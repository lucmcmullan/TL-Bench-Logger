const socket = io();

console.log("IO TYPE:", typeof io);

console.log("SOCKET CREATED");

socket.on("connect", () => {
  console.log("CONNECTED", socket.id);
});

socket.on("connect_error", (err) => {
  console.error("CONNECT ERROR", err);
});

socket.onAny((event, data) => {
  console.log("EVENT:", event, data);
});

socket.on("active_users_changed", (data) => {
  if (!document.getElementById("activeUsersList")) return;

  document.getElementById("activeUsersList").textContent =
    data.users.join(", ");
});

socket.on("bench_updated", (data) => {
  const button = document.querySelector(`.bench[data-id="${data.bench_id}"]`);

  if (!button) return;

  button.classList.remove("pending", "pass", "fail", "locked");
  button.classList.add(data.result === "PASS" ? "pass" : "fail");
});

socket.on("lock_changed", (data) => {
  const button = document.querySelector(`.bench[data-id="${data.bench_id}"]`);

  if (!button) return;

  if (data.locked) {
    button.classList.add("locked");
  } else {
    button.classList.remove("locked");
  }
});

socket.on("inspection_refresh", () => {
  window.location.reload();
});

socket.on("audit_log", (data) => {
  const textarea = document.getElementById("auditLog");

  if (!textarea) return;

  const entry = `${data.timestamp} - ${data.event_type} - ${data.user_initials} - ${data.message}`;
  textarea.value = entry + "\n" + textarea.value;
});

socket.on("bench_deleted", () => {
  location.reload();
});

socket.on("bench_created", () => {
  location.reload();
});

socket.on("bench_updated", () => {
  location.reload();
});

socket.on("session_deleted", () => {
  document.getElementById("sessionDeletedBanner").style.display = "block";
});
