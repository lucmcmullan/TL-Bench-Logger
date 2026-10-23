const socket = io();

socket.on("connect", () => {
    console.log("CONNECTED", socket.id);
});

socket.onAny((event, data) => {
    console.log("EVENT RECEIVED:", event, data);
});

socket.on("active_users_changed", data =>{
    document.getElementById("activeUsersList").textContent = data.users.join(", ")
})

socket.on("bench_updated", data => {
    const button = document.querySelector(`.bench[data-id="${data.bench_id}"]`);

    if (!button) return;

    button.classList.remove("pending", "pass", "fail", "locked");

    button.classList.add(data.result === "PASS" ? "pass" : "fail");
});

socket.on("lock_changed", data => {
    const button = document.querySelector(`.bench[data-id="${data.bench_id}"]`);

    if (!button) return;

    if (data.locked) {

        button.classList.add("locked");

    } else {

        button.classList.remove("locked");
    }
});
