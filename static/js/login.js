document.getElementById("initials")?.addEventListener("blur", async () => {
    const initials = document.getElementById("initials").value.trim().toUpperCase();

    if (!initials) return;
    
    const response = await fetch(`/check-user/${initials}`);
    const data = await response.json();

    if (data.must_change_password) {
        document.getElementById("loginSection").style.display = "none";
        document.getElementById("passwordChangeSection").style.display = "block";
        document.getElementById("changeInitials").value = initials;
    }
});