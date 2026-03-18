const BASE_URL = "https://acceso-universitario-api-production.up.railway.app";
let historyData = [];
let filteredData = [];

// ════════════════════════════════════════════
//  CARGAR HISTORIAL
// ════════════════════════════════════════════

async function cargarHistorial() {
    try {
        const res = await fetch(`${BASE_URL}/history`);
        const data = await res.json();

        historyData = data;
        filteredData = [...data];

        renderTable(data);

    } catch (err) {
        console.error("Error al cargar historial:", err);
        document.getElementById("historyBody").innerHTML =
            `<tr><td colspan="6" class="text-center text-danger">No se pudo conectar al servidor</td></tr>`;
    }
}

// ════════════════════════════════════════════
//  RENDERIZAR TABLA
// ════════════════════════════════════════════

function renderTable(data) {
    const tbody = document.getElementById("historyBody");
    if (!tbody) return;

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">Sin resultados</td></tr>`;
        return;
    }

    tbody.innerHTML = data.map(row => `
        <tr>
            <td>${row.nombre ?? "—"}</td>
            <td>${row.control ?? "—"}</td>
            <td>${row.carrera ?? "—"}</td>
            <td>
                <span class="badge ${row.tipo === 'entrada' ? 'bg-success' : 'bg-primary'}">
                    ${row.tipo ?? "—"}
                </span>
            </td>
            <td>${row.fecha ?? "—"}</td>
            <td>${row.hora ?? "—"}</td>
        </tr>
    `).join("");
}

// ════════════════════════════════════════════
//  FILTROS
// ════════════════════════════════════════════

function applyFilters() {
    const date = document.getElementById("filterDate")?.value ?? "";
    const tipo = document.getElementById("filterType")?.value ?? "";
    const carrera = document.getElementById("filterCareer")?.value.toLowerCase() ?? "";

    filteredData = historyData.filter(row => {
        if (date && row.fecha !== date) return false;
        if (tipo && row.tipo !== tipo) return false;
        if (carrera && !row.carrera?.toLowerCase().includes(carrera)) return false;
        return true;
    });

    renderTable(filteredData);
}

// ════════════════════════════════════════════
//  EXPORTAR A EXCEL
// ════════════════════════════════════════════

function downloadExcel() {
    if (filteredData.length === 0) {
        alert("No hay datos para exportar.");
        return;
    }

    // Mapear a columnas legibles
    const exportData = filteredData.map(row => ({
        "Nombre": row.nombre ?? "",
        "Matrícula": row.control ?? "",
        "Carrera": row.carrera ?? "",
        "Tipo": row.tipo ?? "",
        "Fecha": row.fecha ?? "",
        "Hora": row.hora ?? ""
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Historial");
    XLSX.writeFile(workbook, "historial_accesos.xlsx");
}

// ════════════════════════════════════════════
//  INICIO
// ════════════════════════════════════════════
cargarHistorial();
