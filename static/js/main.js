let currentBench = null;
const draftInspections = {};

const NO_WEEKLY = ["TB01", "TB72"];

const NO_GROUNDBOND = ["TB72"];

let inspectionData = {
  groundBond: null,
  insulation: null,
  weekly: null,
};

const modal = document.getElementById("inspectionModal");

function saveDraft() {
  if (!currentBench) return;

  draftInspections[currentBench.dataset.id] = {
    groundBond: inspectionData.groundBond,
    insulation: inspectionData.insulation,
    weekly: inspectionData.weekly,
    failReason: document.getElementById("failReason").value,
    comments: document.getElementById("comments").value,
  };
}

function closeModal() {
  modal.style.display = "none";
  delete draftInspections[currentBench?.dataset?.id];
  currentBench = null;
}

document.querySelectorAll(".bench").forEach((button) => {
  button.addEventListener("click", async () => {
    if (button.dataset.objectType !== "testbench") return;

    if (button.dataset.active === "false") {
      document.getElementById("modalBenchTitle").innerText =
        `${button.innerText}\n(DISABLED)`;
      document.getElementById("disabledBenchMessage").style.display = "block";
      document.getElementById("groundBondSection").style.display = "none";
      document.getElementById("insulationResistanceSection").style.display =
        "none";
      document.getElementById("weeklySection").style.display = "none";
      document.getElementById("failureSection").style.display = "none";
      document.getElementById("saveInspection").disabled = true;
      document.getElementById("resetInspection").disabled = true;
      document.getElementById("comments").disabled = true;
      modal.style.display = "block";
      return;
    }
    const response = await fetch("/lock-bench", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bench_id: button.dataset.id }),
    });

    const result = await response.json();

    if (!result.success) {
      alert(`Bench currently being edited by ${result.locked_by}`);
      return;
    }

    currentBench = button;

    const draft = draftInspections[button.dataset.id];

    inspectionData = draft
      ? {
          groundBond: draft.groundBond,
          insulation: draft.insulation,
          weekly: draft.weekly,
        }
      : {
          groundBond: null,
          insulation: null,
          weekly: null,
        };

    document.getElementById("failReason").value = draft?.failReason || "";
    document.getElementById("comments").value = draft?.comments || "";

    document.getElementById("failureSection").style.display = "none";

    [
      "gbPass",
      "gbFail",
      "irPass",
      "irFail",
      "weeklyPass",
      "weeklyFail",
    ].forEach((id) => {
      document
        .getElementById(id)
        .classList.remove("selected-pass", "selected-fail");
    });

    if (inspectionData.groundBond)
      setResult("groundBond", inspectionData.groundBond);
    if (inspectionData.insulation)
      setResult("insulation", inspectionData.insulation);
    if (inspectionData.weekly) setResult("weekly", inspectionData.weekly);

    document.getElementById("modalBenchTitle").innerText = button.innerText;

    const benchName = button.innerText.trim();

    const groundBondSection = document.getElementById("groundBondSection");
    const weeklySection = document.getElementById("weeklySection");

    groundBondSection.style.display = NO_GROUNDBOND.includes(benchName)
      ? "none"
      : "block";

    if (IS_FRIDAY && !NO_WEEKLY.includes(benchName)) {
      weeklySection.style.display = "block";
    } else {
      weeklySection.style.display = "none";
    }

    document.getElementById("disabledBenchMessage").style.display = "none";
    document.getElementById("saveInspection").disabled = false;
    document.getElementById("resetInspection").disabled = false;
    document.getElementById("comments").disabled = false;
    document.getElementById("groundBondSection").style.display =
      NO_GROUNDBOND.includes(benchName) ? "none" : "block";
    document.getElementById("insulationResistanceSection").style.display =
      "block";
    modal.style.display = "block";
  });
});

function setResult(type, result) {
  const benchName = currentBench?.innerText.trim() || "";

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

  const failed =
    (!NO_GROUNDBOND.includes(benchName) &&
      inspectionData.groundBond === "FAIL") ||
    inspectionData.insulation === "FAIL" ||
    (!NO_WEEKLY.includes(benchName) && inspectionData.weekly === "FAIL");

  document.getElementById("failureSection").style.display = failed
    ? "block"
    : "none";
}

document.getElementById("gbPass")?.addEventListener("click", () => {
  setResult("groundBond", "PASS");
});

document.getElementById("gbFail")?.addEventListener("click", () => {
  setResult("groundBond", "FAIL");
});

document.getElementById("irPass")?.addEventListener("click", () => {
  setResult("insulation", "PASS");
});

document.getElementById("irFail")?.addEventListener("click", () => {
  setResult("insulation", "FAIL");
});

document.getElementById("weeklyPass")?.addEventListener("click", () => {
  setResult("weekly", "PASS");
});

document.getElementById("weeklyFail")?.addEventListener("click", () => {
  setResult("weekly", "FAIL");
});

document
  .getElementById("cancelInspection")
  ?.addEventListener("click", async () => {
    if (currentBench) {
      await fetch("/unlock-bench", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bench_id: currentBench.dataset.id }),
      });
    }

    saveDraft();
    modal.style.display = "none";
    currentBench = null;
  });

document
  .getElementById("saveInspection")
  ?.addEventListener("click", async () => {
    if (
      !NO_GROUNDBOND.includes(currentBench.innerText.trim()) &&
      !inspectionData.groundBond
    ) {
      alert("Select Ground Bond result");
      return;
    }

    if (!inspectionData.insulation) {
      alert("Select Insulation result");
      return;
    }

    if (
      IS_FRIDAY &&
      !NO_WEEKLY.includes(currentBench.innerText.trim()) &&
      !inspectionData.weekly
    ) {
      alert("Select Weekly Check result");
      return;
    }
    const benchName = currentBench.innerText.trim();
    const failed =
      (!NO_GROUNDBOND.includes(benchName) &&
        inspectionData.groundBond === "FAIL") ||
      inspectionData.insulation === "FAIL" ||
      (!NO_WEEKLY.includes(benchName) && inspectionData.weekly === "FAIL");

    const failReason = document.getElementById("failReason").value;

    if (failed && !failReason) {
      const dropdown = document.getElementById("failReason");
      dropdown.style.border = "2px solid red";
      dropdown.focus();
      alert("You must select a failure reason before saving.");

      return;
    }

    const response = await fetch("/inspect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        bench_id: currentBench.dataset.id,
        gb_result: inspectionData.groundBond,
        ir_result: inspectionData.insulation,
        weekly_result: inspectionData.weekly,
        fail_reason: document.getElementById("failReason").value,
        comments: document.getElementById("comments").value,
      }),
    });

    const result = await response.json();

    currentBench.classList.remove("pending", "pass", "fail");
    currentBench.classList.add(result.overall === "PASS" ? "pass" : "fail");
    await refreshProgress();
    closeModal();
  });

document
  .getElementById("userManagementButton")
  ?.addEventListener("click", () => {
    window.location.href = "/admin/users";
  });

document.getElementById("logoutButton")?.addEventListener("click", async () => {
  await fetch("/logout", { method: "POST" });

  window.location.href = "/";
});

document
  .getElementById("historyButton")
  ?.addEventListener("click", async () => {
    window.location.href = "/history";
  });

document
  .getElementById("completeSession")
  ?.addEventListener("click", async () => {
    /*
    const comment = prompt("Optional session comment:", "");

    if (comment === null) return;
    */
    const response = await fetch("/complete-session", { method: "POST" });
    const result = await response.json();

    if (result.success) {
      alert("Session completed successfully.");
      window.location.href = "/menu";
    } else {
      alert(result.message);
    }
  });

document
  .getElementById("resetInspection")
  ?.addEventListener("click", async () => {
    if (!currentBench) return;

    await fetch("/reset-inspection", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bench_id: currentBench.dataset.id }),
    });

    currentBench.classList.remove("pass", "fail", "locked");

    currentBench.classList.add("pending");
    await refreshProgress();

    closeModal();
  });

async function refreshProgress() {
  const response = await fetch("/progress");
  const data = await response.json();

  document.getElementById("progressHeader").textContent =
    `Progress: ${data.completed}/${data.total} (${data.percent}%)`;
  document.getElementById("progressFill").style.width = `${data.percent}%`;
}
async function sendHeartbeat() {
  await fetch("/heartbeat", { method: "POST" });
}

sendHeartbeat();

setInterval(sendHeartbeat, 30000);
