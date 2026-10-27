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

document.getElementById("closeHistoryModal").addEventListener("click", () => {
    modal.style.display = "none";
});