const BASE_URL = "https://acceso-universitario-api-production.up.railway.app";

async function apiFetch(url, opciones = {}) {
    try {
        const res = await fetch(`${BASE_URL}${url}`, opciones);
        return await res.json();
    } catch (err) {
        console.error(`Error en ${url}:`, err);
        return null;
    }
}

function setTexto(id, valor) {
    const el = document.getElementById(id);
    if (el) el.textContent = valor ?? "—";
}

async function cargarStats() {
    const data = await apiFetch("/dashboard/stats");
    if (!data) return;

    setTexto("accesos_hoy", data.accesos_hoy);
    setTexto("denegados_hoy", data.denegados_hoy);
    setTexto("statEstudiantes", data.estudiantes);
    setTexto("statDocentes", data.docentes);
}

async function cargarActividad() {
    const data = await apiFetch("/dashboard/actividad");
    if (!data) return;

    const tabla = document.getElementById("tablaActividad");
    if (!tabla) return;

    tabla.innerHTML = data.map(r => `
        <tr>
            <td>${r.nombre}</td>
            <td>${r.tipo}</td>
            <td>
                <span class="badge ${r.resultado === 'permitido' ? 'bg-success' : 'bg-danger'}">
                    ${r.resultado}
                </span>
            </td>
            <td>${r.fecha} ${r.hora}</td>
        </tr>
    `).join("");
}

async function cargarModoAcceso() {
    const data = await apiFetch("/access-mode");
    if (!data) return;

    const radios = document.querySelectorAll("input[name='modoAcceso']");
    radios.forEach(r => { r.checked = r.value === data.modo; });

    mostrarModoActual(data.modo);
}

async function activarRestriccion() {
    const radio = document.querySelector("input[name='modoAcceso']:checked");
    if (!radio) {
        alert("Selecciona un modo.");
        return;
    }

    const data = await apiFetch("/access-mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ modo: radio.value })
    });

    if (!data) return;
    alert(`✅ Modo actualizado: ${data.modo}`);
    mostrarModoActual(data.modo);
}

function mostrarModoActual(modo) {
    const badge = document.getElementById("modoActualBadge");
    if (!badge) return;

    const etiquetas = {
        "normal": { texto: "Normal", clase: "bg-success" },
        "bloquear_entradas": { texto: "Entradas bloqueadas", clase: "bg-warning text-dark" },
        "bloquear_salidas": { texto: "Salidas bloqueadas", clase: "bg-warning text-dark" },
        "bloqueo_total": { texto: "Bloqueo Total", clase: "bg-danger" }
    };

    const info = etiquetas[modo] || { texto: modo, clase: "bg-secondary" };
    badge.innerHTML = `<span class="badge ${info.clase}">Modo actual: ${info.texto}</span>`;
}


async function cargarCodigos() {
    const codigos = await apiFetch("/emergency/codigos");
    if (!codigos) return;

    const select = document.getElementById("selectCodigo");
    if (!select) return;

    select.innerHTML = `<option value="">-- Selecciona un código --</option>`;
    codigos.forEach(c => {
        select.innerHTML += `<option value="${c.id_codigo}">${c.codigo} - ${c.descripcion}</option>`;
    });
}

async function cargarEstadoEmergencia() {
    const data = await apiFetch("/emergency");
    if (!data) return;

    const banner = document.getElementById("bannerEmergencia");
    if (!banner) return;

    if (data.activo) {
        banner.style.display = "block";
        banner.textContent = `🚨 EMERGENCIA ACTIVA: ${data.codigo}`;
        banner.style.backgroundColor = data.color || "#dc3545";
    } else {
        banner.style.display = "none";
    }
}

async function activarEmergencia() {
    const select = document.getElementById("selectCodigo");
    const tipo = document.querySelector("input[name='tipoEmergencia']:checked");

    if (!select?.value) { alert("Selecciona un código de emergencia."); return; }
    if (!tipo) { alert("Selecciona el tipo de emergencia."); return; }

    const data = await apiFetch("/emergency", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_codigo: select.value, tipo: tipo.value })
    });

    if (!data) return;
    alert(data.mensaje || data.error);
    cargarEstadoEmergencia();


    bootstrap.Modal.getInstance(document.getElementById("modalEmergencia"))?.hide();
}

async function desactivarEmergencia() {
    if (!confirm("¿Desactivar la emergencia actual?")) return;

    const data = await apiFetch("/emergency", { method: "DELETE" });
    if (!data) return;

    alert(data.mensaje || data.error);
    cargarEstadoEmergencia();

    bootstrap.Modal.getInstance(document.getElementById("modalEmergencia"))?.hide();
}

cargarStats();
cargarActividad();
cargarModoAcceso();
cargarEstadoEmergencia();

// Refrescar actividad cada 30 segundos
setInterval(() => {
    cargarStats();
    cargarActividad();
    cargarEstadoEmergencia();
}, 30000);
