let currentBench = null;

const NO_WEEKLY = [
    "TB01",
    "TB72"
]

const NO_GROUNDBOND = [
    "TB72"
]

let inspectionData = {
    groundBond: null,
    insulation: null,
    weekly: null
};

const modal = document.getElementById("inspectionModal");
document.querySelectorAll(".bench").forEach(button => {
    button.addEventListener("click", async () => {
        const response = await fetch(
            "/lock-bench",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ bench_id: button.dataset.id })
            }
        );

        const result = await response.json();

        if (!result.success) {
            alert(`Bench currently being edited by ${result.locked_by}`);
            return;
        }

        currentBench = button;

        inspectionData = { groundBond: null, insulation: null, weekly: null};

        document.getElementById("failReason").value = "";
        document.getElementById("comments").value = "";

        document.getElementById("failureSection").style.display = "none";

        ["gbPass", "gbFail", "irPass", "irFail", "weeklyPass", "weeklyFail"].forEach(id => {
            document.getElementById(id).classList.remove("selected-pass", "selected-fail");
        });

        document.getElementById("modalBenchTitle").innerText = button.innerText;
        
        const benchName = button.innerText.trim()
        
        const groundBondSection = document.getElementById("groundBondSection")
        const weeklySection = document.getElementById("weeklySection")

        groundBondSection.style.display = NO_GROUNDBOND.includes(benchName) ? "none" : "block"
        weeklySection.style.display = NO_WEEKLY.includes(benchName) ? "none" : "block"

        if (IS_FRIDAY) {
            document.getElementById("weeklySection").style.display = "block";
        } else {
            document.getElementById("weeklySection").style.display = "none";
        }

        modal.style.display = "block";
    });
});

function setResult(type, result) {

    inspectionData[type] = result;

    let passButton;
    let failButton;

    if (type === "groundBond") {
        passButton = document.getElementById("gbPass");
        failButton = document.getElementById("gbFail");
    } else if (type === "insulation") {
        passButton = document.getElementById("irPass");
        failButton = document.getElementById("irFail");
    } else if (type === "weekly") {
        passButton = document.getElementById("weeklyPass");
        failButton = document.getElementById("weeklyFail");
    }

    passButton.classList.remove("selected-pass", "selected-fail");

    failButton.classList.remove("selected-pass", "selected-fail");

    if (result === "PASS") {
        passButton.classList.add("selected-pass");
    } else {
        failButton.classList.add("selected-fail");
    }

    const failed = inspectionData.groundBond === "FAIL" || inspectionData.insulation === "FAIL" || inspectionData.weekly === "FAIL";

    document.getElementById("failureSection").style.display = failed ? "block" : "none";
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

document.getElementById("cancelInspection").addEventListener("click", async () => {
    if (currentBench) {

        await fetch(
            "/unlock-bench",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({bench_id: currentBench.dataset.id})
            }
        );
    }

    modal.style.display = "none";
    currentBench = null
});

document.getElementById("saveInspection").addEventListener("click", async () => {
    if (!NO_GROUNDBOND.includes(currentBench.innerText.trim()) && !inspectionData.groundBond) {
        alert("Select Ground Bond result");
        return;
    }

    if (!inspectionData.insulation) {
        alert("Select Insulation result");
        return;
    }

    if (IS_FRIDAY && !NO_WEEKLY.includes(currentBench.innerText.trim()) && !inspectionData.weekly) {
        alert("Select Weekly Check result");
        return;
    }
    const benchName = currentBench.innerText.trim()
    const failed =(!NO_GROUNDBOND.includes(benchName) && inspectionData.groundBond === "FAIL") || inspectionData.insulation === "FAIL" ||
    (!NO_WEEKLY.includes(benchName) && inspectionData.weekly === "FAIL");

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

    currentBench = null
});

/*
async function refreshBenchStatuses() {
    try{
        const response = await fetch("/inspection-status")
        const data = await response.json()

        data.forEach(record => {
            const button = document.querySelector(`.bench[data-id="${record.bench_id}"]`)

            if (!button) return

            button.classList.remove("pending", "pass", "fail")

            if (record.result === "PASS") {
                button.classList.add("pass")
            } else if (record.result === "FAIL") {
                button.classList.add("fail")
            } else {
                button.classList.add("pending")
            }
        })
    } catch (err) {
        console.error("Status refresh failed", err)
    }
}



async function refreshLocks() {

    const response =
        await fetch("/lock-status");

    const locks =
        await response.json();

    document.querySelectorAll(".bench")
        .forEach(button => {

            button.classList.remove(
                "locked"
            );

        });

    locks.forEach(lock => {

        const button =
            document.querySelector(
                `.bench[data-id="${lock.bench_id}"]`
            );

        if (button) {

            button.classList.add(
                "locked"
            );

        }

    });

}
*/

async function sendHeartbeat() {
    await fetch("/heartbeat", { method: "POST" });
}

sendHeartbeat()

setInterval(sendHeartbeat, 30000);

