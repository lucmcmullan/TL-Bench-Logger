const modal = document.getElementById("historyModal");

document.querySelectorAll(".bench").forEach(bench => {
        bench.addEventListener("click", () => {
            const data = JSON.parse(bench.dataset.inspection || "{}");

            document.getElementById("historyBenchTitle").textContent = bench.innerText;
            document.getElementById("historyGb").textContent = data.gb_result || "N/A";
            document.getElementById("historyIr").textContent = data.ir_result || "N/A";
            document.getElementById("historyWeekly").textContent = data.weekly_result || "N/A";
            document.getElementById("historyOverall").textContent = data.overall_result || "UNTESTED";
            document.getElementById("historyReason").textContent = data.fail_reason || "-";
            document.getElementById("historyComments").textContent = data.comments || "-";

            modal.style.display = "block";
    });
});

document.getElementById("backToHistory").addEventListener("click", () => {
    window.location.href = "/history";
});

document.getElementById("closeHistoryModal").addEventListener("click", () => {
    modal.style.display = "none";
});

document.getElementById("deleteSessionButton")?.addEventListener("click", () => {
    document.getElementById("deleteSessionModal").style.display = "block";
    }
);

document.getElementById("cancelDeleteSession").addEventListener("click", () => {
    document.getElementById("deleteSessionModal").style.display = "none";
    }
);

document.getElementById("deleteConfirmation").addEventListener("input",() => {
    document.getElementById("confirmDeleteSession").disabled = document.getElementById("deleteConfirmation").value !== "DELETE";
    }
);

document.getElementById("confirmDeleteSession").addEventListener("click", async () => {
        const response = await fetch(window.location.pathname + "/delete", { method: "POST" });
        const result = await response.json();

        if (result.success) {
            window.location.replace("/history")
        }
    }
);