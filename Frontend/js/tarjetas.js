const BASE_URL = "https://acceso-universitario-api-production.up.railway.app";
let _tarjetas = [];
let _pollingTimer = null;

async function apiFetch(url, opts = {}) {
    try {
        const res = await fetch(`${BASE_URL}${url}`, opts);
        return await res.json();
    } catch (err) {
        console.error(`Error en ${url}:`, err);
        return null;
    }
}

function toast(msg, tipo = "info") {
    const c = document.getElementById("toastContainer");
    if (!c) return;
    const icons = { success: "✅", error: "❌", info: "ℹ️" };
    const div = document.createElement("div");
    div.className = `toast-msg ${tipo}`;
    div.innerHTML = `<span>${icons[tipo] || "ℹ️"}</span> ${msg}`;
    c.appendChild(div);
    setTimeout(() => div.remove(), 4000);
}

async function cargarTarjetas() {
    const data = await apiFetch("/tarjetas");
    if (!data) return;

    _tarjetas = data;

    const activas = data.filter(t => t.estado === "Activa").length;
    const sinTarj = data.filter(t => t.estado === "Sin tarjeta").length;

    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    set("totalTarjetas", data.length);
    set("tarjetasActivas", activas);
    set("tarjetasInactivas", sinTarj);

    renderTarjetas(data);
}

function renderTarjetas(data) {
    const tabla = document.getElementById("tablaTarjetas");
    if (!tabla) return;

    if (data.length === 0) {
        tabla.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4">Sin resultados</td></tr>`;
        return;
    }

    tabla.innerHTML = data.map(t => {
        const estadoClass = t.estado === "Activa" ? "badge-activa"
            : t.estado === "Inactiva" ? "badge-inactiva"
                : "badge-sin";

        return `
        <tr>
            <td>${t.control}</td>
            <td><strong>${t.nombre}</strong></td>
            <td><span class="badge badge-tipo">${t.tipo}</span></td>
            <td>${t.carrera}</td>
            <td>${t.semestre}</td>
            <td><span class="badge ${estadoClass}">${t.estado}</span></td>
            <td style="color:var(--clr-muted);font-size:.82rem">${t.fecha}</td>
            <td>
                <button class="action-btn"
                    onclick='abrirRegistroDirecto(${JSON.stringify({ control: t.control, nombre: t.nombre })})'>
                    Asignar tarjeta
                </button>
            </td>
        </tr>`;
    }).join("");
}

function filtrarTarjetas() {
    const texto = document.getElementById("busquedaTarjeta")?.value.toLowerCase() ?? "";
    const tipo = document.getElementById("filtroTipo")?.value ?? "";
    const estado = document.getElementById("filtroEstado")?.value ?? "";

    const filtradas = _tarjetas.filter(t => {
        const ok1 = !texto || `${t.control} ${t.nombre}`.toLowerCase().includes(texto);
        const ok2 = !tipo || t.tipo === tipo;
        const ok3 = !estado || t.estado === estado;
        return ok1 && ok2 && ok3;
    });

    renderTarjetas(filtradas);
}

async function abrirModalRegistro() {
    mostrarPaso("seleccion");

    // Cargar usuarios sin tarjeta
    const sel = document.getElementById("selectUsuarioRegistro");
    sel.innerHTML = `<option value="">— Cargando... —</option>`;

    const usuarios = await apiFetch("/tarjetas/usuarios-sin-tarjeta");

    if (!usuarios || usuarios.length === 0) {
        sel.innerHTML = `<option value="">— Todos los usuarios tienen tarjeta asignada —</option>`;
    } else {
        sel.innerHTML = `<option value="">— Selecciona un usuario —</option>` +
            usuarios.map(u =>
                `<option value="${u.id_usuario}" data-nombre="${u.nombre_completo}" data-control="${u.numero_control}" data-tipo="${u.tipo}">
                    ${u.nombre_completo} (${u.numero_control}) — ${u.tipo}
                 </option>`
            ).join("");
    }

    sel.onchange = () => {
        const opt = sel.selectedOptions[0];
        const info = document.getElementById("infoUsuarioSeleccionado");
        if (opt && opt.value) {
            info.innerHTML = `<span style="color:var(--clr-accent)">✓</span> ${opt.dataset.nombre} · ${opt.dataset.control} · ${opt.dataset.tipo}`;
        } else {
            info.innerHTML = "";
        }
    };

    const modal = new bootstrap.Modal(document.getElementById("modalRegistro"));
    modal.show();
}

async function abrirRegistroDirecto(usuario) {
    await abrirModalRegistro();
    const sel = document.getElementById("selectUsuarioRegistro");

    await new Promise(r => setTimeout(r, 600));

    for (const opt of sel.options) {
        if (opt.dataset.control === usuario.control) {
            opt.selected = true;
            sel.dispatchEvent(new Event("change"));
            break;
        }
    }
}

async function iniciarModoRegistro() {
    const sel = document.getElementById("selectUsuarioRegistro");
    const id_usuario = sel?.value;

    if (!id_usuario) {
        toast("Selecciona un usuario primero.", "error");
        return;
    }

    const res = await apiFetch("/tarjetas/modo-registro", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ activo: true, id_usuario: parseInt(id_usuario) })
    });

    if (!res || res.error) {
        toast(res?.error || "Error al activar modo registro.", "error");
        return;
    }


    mostrarPaso("esperando");
    document.getElementById("bannerRegistro").style.display = "block";

    toast("Modo registro activo. Acerca la tarjeta al lector.", "info");

    iniciarPollingRegistro();
}

async function cancelarModoRegistro() {
    detenerPolling();

    await apiFetch("/tarjetas/modo-registro", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ activo: false })
    });

    document.getElementById("bannerRegistro").style.display = "none";

    mostrarPaso("seleccion");
    bootstrap.Modal.getInstance(document.getElementById("modalRegistro"))?.hide();

    toast("Modo registro cancelado.", "info");
}
function iniciarPollingRegistro() {
    detenerPolling();
    _pollingTimer = setInterval(async () => {
        const estado = await apiFetch("/tarjetas/modo-registro");
        if (!estado) return;

        if (!estado.activo) {
            detenerPolling();
            document.getElementById("bannerRegistro").style.display = "none";
            mostrarExito("Tarjeta registrada exitosamente.");
            cargarTarjetas();
        }
    }, 1500);
}

function detenerPolling() {
    if (_pollingTimer) {
        clearInterval(_pollingTimer);
        _pollingTimer = null;
    }
}

function mostrarPaso(paso) {
    document.getElementById("pasoSeleccion").style.display = paso === "seleccion" ? "block" : "none";
    document.getElementById("pasoEsperando").style.display = paso === "esperando" ? "block" : "none";
    document.getElementById("pasoExito").style.display = paso === "exito" ? "block" : "none";

    const footer = document.getElementById("footerRegistro");
    if (paso === "esperando") {
        footer.innerHTML = `<button type="button" class="btn btn-danger" onclick="cancelarModoRegistro()">✕ Cancelar</button>`;
    } else if (paso === "exito") {
        footer.innerHTML = `<button type="button" class="btn btn-success" data-bs-dismiss="modal">Cerrar</button>`;
    } else {
        footer.innerHTML = `
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
            <button type="button" class="btn-register" onclick="iniciarModoRegistro()">📡 Activar Modo Registro</button>`;
    }
}

function mostrarExito(msg) {
    document.getElementById("msgExitoRegistro").textContent = msg;
    mostrarPaso("exito");
    toast(msg, "success");
}

cargarTarjetas();