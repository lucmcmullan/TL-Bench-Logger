let currentBench = null;

let inspectionData = {
    groundBond: null,
    insulation: null,
    weekly: null
};

const modal = document.getElementById("inspectionModal");
document.querySelectorAll(".bench").forEach(button => {
    button.addEventListener("click", () => {
        currentBench = button;

        inspectionData = { groundBond: null, insulation: null, weekly: null};

        document.getElementById("modalBenchTitle").innerText = button.innerText;
        document.getElementById("failureSection").style.display = "none";
        if (IS_FRIDAY) {
            document.getElementById("weeklySection").style.display = "block";
        }
        else {
            document.getElementById("weeklySection").style.display = "none";
        }

        modal.style.display = "block";
    });
});

function setResult(type, result) {
    inspectionData[type] = result;

    if (result === "FAIL") {
        document.getElementById("failureSection").style.display = "block";
    }
}

document.getElementById("gbPass").addEventListener("click", () => {
    setResult("groundBond", "PASS");
});

document.getElementById("gbFail").addEventListener("click", () => {
    setResult("groundBond", "FAIL");
});

document.getElementById("irPass").addEventListener("click", () => {
    setResult("insulation", "PASS");
});

document.getElementById("irFail").addEventListener("click", () => {
    setResult("insulation", "FAIL");
});

document.getElementById("weeklyPass").addEventListener("click", () => {
    setResult("weekly", "PASS");
});

document.getElementById("weeklyFail").addEventListener("click", () => {
    setResult("weekly", "FAIL");
});

document.getElementById("cancelInspection").addEventListener("click", () => {
    modal.style.display = "none";
});

document.getElementById("saveInspection").addEventListener("click", async () => {
    if (!inspectionData.groundBond) {
        alert("Select Ground Bond result");
        return;
    }

    if (!inspectionData.insulation) {
        alert("Select Insulation result");
        return;
    }

    if (IS_FRIDAY && !inspectionData.weekly) {
        alert("Select Weekly Check result");
        return;
    }

    const failed = inspectionData.groundBond === "FAIL" || inspectionData.insulation === "FAIL" || inspectionData.weekly === "FAIL";
    const failReason = document.getElementById("failReason").value;

    if (failed && !failReason) {
        const dropdown = document.getElementById("failReason")

        dropdown.style.border = "2px solid red"

        dropdown.focus()

        alert("You must select a failure reason before saving.")

        return
    }

    const response = await fetch(
        "/inspect",
        {
            method: "POST",
            headers: {
                "Content-Type":
                "application/json"
            },
            body: JSON.stringify({
                bench_id: currentBench.dataset.id,
                gb_result: inspectionData.groundBond,
                ir_result: inspectionData.insulation,
                weekly_result: inspectionData.weekly,
                fail_reason:document.getElementById("failReason").value,
                comments: document.getElementById("comments").value
            })
        }
    );

    const result = await response.json();

    currentBench.classList.remove("pending", "pass", "fail");
    currentBench.classList.add(result.overall === "PASS" ? "pass" : "fail");
    modal.style.display = "none";
});

async function refreshBenchStatuses() {
    try{
        const response = await fetch("/inspection-status")
        const data = await response.json()

        data.forEach(record => {
            const button = document.querySelector(`.bench[data-id="${record.bench_id}]`)

            if (!button) return

            button.classList.remove("pending", "pass", "fail")

            if (record.result === "PASS") {
                button.classList.add("pass")
            } else {
                button.classList.add("fail")
            }
        })
    } catch (err) {
        console.error("Status refresh failed", err)
    }
}

refreshBenchStatuses()

setInterval(() => {
    refreshBenchStatuses
}, 5000);