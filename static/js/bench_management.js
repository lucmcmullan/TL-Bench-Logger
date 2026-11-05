const editor = document.getElementById("layout-editor");
const preview = document.getElementById("drop-preview");
const editModal = document.getElementById("benchEditModal");
const cellInput = document.getElementById("editBenchCell");
const cellPrefix = document.getElementById("cellPrefix");

const GRID_SIZE = 40;
const SESSION_ACTIVE = document.body.dataset.sessionActive === "true";

let draggedBench = null;
let selectedBench = null;
let dragOffsetX = 0;
let dragOffsetY = 0;

let resizingBench = null;
let resizeDirection = null;

function stopResize() {
    console.log("STOP RESIZE");
    if (!resizingBench)
        return;

    saveBench(
        resizingBench.dataset.id,
        {
            x: parseInt(resizingBench.dataset.x),
            y: parseInt(resizingBench.dataset.y),
            width: parseInt(resizingBench.dataset.width),
            height: parseInt(resizingBench.dataset.height)
        }
    );

    resizingBench = null;
    resizeDirection = null;
}

function updateCellPrefix() {
    const value = cellInput.value.trim();
    
    if (value === "") {
        cellPrefix.style.display = "inline";
        return;
    }

    if (/^\d/.test(value)) {
        cellPrefix.style.display = "inline";
    } else {
        cellPrefix.style.display = "none";
    }
}

document.getElementById("saveBenchEdit").addEventListener("click", () => {
    const benchId = document.getElementById("editBenchId").value;

    saveBench(benchId,
        {
            name: document.getElementById("editBenchName").value,
            cell: document.getElementById("editBenchCell").value,
            active: document.getElementById("editBenchActive").checked
        }
    ).then(data => {
        if (data.success) {
            location.reload()
        }
    })

});

document.getElementById("deleteBenchEdit").addEventListener("click", () => {
        if (!selectedBench)
            return;

        const benchName = selectedBench.dataset.name || selectedBench.querySelector(".bench-title").textContent;

        fetch(
            "/admin/benches/delete",
            { method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ bench_id: selectedBench.dataset.id })
            }
        )
        .then(response => response.json()).then(data => {
            if (data.success) {
                selectedBench.remove();
                editModal.style.display = "none";
            } else {
                alert("Delete failed.");
            }
        })
        .catch(error => {
            console.error(error);
            alert("Delete failed.", error);

        });

    }
);

document.getElementById("cancelBenchEdit").addEventListener("click", () => {
    editModal.style.display ="none";
});

document.getElementById("addBenchBtn").addEventListener("click", () => {
        fetch("/admin/benches/create",
            { method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name: "00", cell: "", x: 0, y: 0, width: 3, height: 2, active: true})
            }
        )
        .then(response => response.json()).then(data => {
            if (data.success) {
                location.reload();
            }
        });
    }
);


document.querySelectorAll(".layout-bench").forEach(bench => {
    bench.addEventListener("mousedown", e => {
        if (SESSION_ACTIVE) return
        const rect = bench.getBoundingClientRect();
        dragOffsetX = e.clientX - rect.left;
        dragOffsetY = e.clientY - rect.top;
    });

    bench.addEventListener("dragstart", () => {
        draggedBench = bench;
    });

    bench.addEventListener("click", () => {
        console.log(`Bench ${bench.dataset.id} X=${bench.dataset.x} Y=${bench.dataset.y}`);
        }
    );

    bench.addEventListener("dragend", () => {
            preview.style.display = "none";
        }
    );

    bench.addEventListener("contextmenu", e => {
        if (SESSION_ACTIVE) {
            e.preventDefault();
            alert("Layout editing is disabled while a session is active.");
            return;
        }

        e.preventDefault();
        selectedBench = bench;

        document.getElementById("editBenchId").value = bench.dataset.id;
        document.getElementById("editBenchName").value = bench.dataset.name || "";
        document.getElementById("editBenchCell").value = bench.dataset.cell || ""; 
        updateCellPrefix();
        document.getElementById("editBenchActive").checked = bench.dataset.active === "true";
        editModal.style.display = "block";
    });
});


editor.addEventListener("dragover", event => {
        event.preventDefault();
        if (!draggedBench)
            return;

        preview.style.display = "block";

        const rect = editor.getBoundingClientRect();
        const gridX = Math.max(0, Math.round((event.clientX - rect.left - dragOffsetX) / GRID_SIZE));
        const gridY = Math.max(0, Math.round((event.clientY - rect.top - dragOffsetY) / GRID_SIZE));
        const width = parseInt(draggedBench.dataset.width) || 2;
        const height = parseInt(draggedBench.dataset.height) || 1;

        preview.style.display = "block";
        preview.style.left = `${gridX * GRID_SIZE}px`;
        preview.style.top = `${gridY * GRID_SIZE}px`;
        preview.style.width = `${width * GRID_SIZE}px`;
        preview.style.height = `${height * GRID_SIZE}px`;
    }
);

editor.addEventListener("drop", event => {
    event.preventDefault();

    if (!draggedBench)
        return;

    const rect = editor.getBoundingClientRect();
    const gridX = Math.max(0, Math.round((event.clientX - rect.left - dragOffsetX) / GRID_SIZE));
    const gridY = Math.max(0, Math.round((event.clientY - rect.top - dragOffsetY) / GRID_SIZE));

    draggedBench.style.left = `${gridX * GRID_SIZE}px`;
    draggedBench.style.top = `${gridY * GRID_SIZE}px`;

    draggedBench.dataset.x = gridX;
    draggedBench.dataset.y = gridY;

    saveBench(draggedBench.dataset.id, { x: gridX, y: gridY });
    preview.style.display = "none";
});


cellInput.addEventListener("input", updateCellPrefix)
function saveBench(benchId, data) {
    return fetch(
        "/admin/benches/update", 
        { method: "POST", headers: 
            { "Content-Type": "application/json" },
            body: JSON.stringify({bench_id: benchId, ...data })
        }
    ).then(response => response.json()).then(data => {
        console.log("Bench updated:",data);
    })
}

document.querySelectorAll(".resize-handle").forEach(handle => {
    handle.addEventListener("mousedown", e => {
        resizingBench = handle.closest(".layout-bench");
        resizeStartWidth = parseInt(resizingBench.dataset.width) || 2;
        resizeStartHeight = parseInt(resizingBench.dataset.height) || 1;
        resizeStartX = parseInt(resizingBench.dataset.x) || 0;
        resizeStartY = parseInt(resizingBench.dataset.y) || 0;

        resizeStartMouseX = e.clientX;
        resizeStartMouseY = e.clientY;
        
        e.preventDefault()
        e.stopPropagation();

        if (handle.classList.contains("resize-right")) {
            resizeDirection = "right";
        }

        if (handle.classList.contains("resize-left")) {
            resizeDirection = "left";
        }

        if (handle.classList.contains("resize-top")) {
            resizeDirection = "top";
        }

        if (handle.classList.contains("resize-bottom")) {
            resizeDirection = "bottom";
        }

    });

});

document.addEventListener("mousemove", e => {
        if (!resizingBench || !resizeDirection) {
            return;
        }

        let width = parseInt(resizingBench.dataset.width) || 2;
        let height = parseInt(resizingBench.dataset.height) || 1;
        let x = parseInt(resizingBench.dataset.x) || 0;
        let y = parseInt(resizingBench.dataset.y) || 0;

        if (resizeDirection === "right") {
            const deltaX = Math.round((e.clientX - resizeStartMouseX) / GRID_SIZE);
            width = resizeStartWidth + deltaX;
        }

        if (resizeDirection === "bottom") {
            const deltaY = Math.round((e.clientY - resizeStartMouseY) / GRID_SIZE);
            height = resizeStartHeight + deltaY;
        }

        if (resizeDirection === "left") {
            const deltaX = Math.round((e.clientX - resizeStartMouseX) / GRID_SIZE);
            x = resizeStartX + deltaX;
            width = resizeStartWidth - deltaX;
        }

        if (resizeDirection === "top") {
            const deltaY = Math.round((e.clientY - resizeStartMouseY) / GRID_SIZE);
            y = resizeStartY + deltaY;
            height = resizeStartHeight - deltaY;
        }

        width = Math.max(1, width);
        height = Math.max(1, height);

        resizingBench.dataset.x = x;
        resizingBench.dataset.y = y;

        resizingBench.dataset.width = width;
        resizingBench.dataset.height = height;
        resizingBench.style.left = `${x * GRID_SIZE}px`;
        resizingBench.style.top = `${y * GRID_SIZE}px`;
        resizingBench.style.width = `${width * GRID_SIZE}px`;
        resizingBench.style.height =`${height * GRID_SIZE}px`;
    }
);

document.addEventListener("mouseup",stopResize);
document.addEventListener("mouseleave", stopResize);
window.addEventListener("blur", stopResize);

updateCellPrefix();