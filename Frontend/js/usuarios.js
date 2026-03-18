const BASE_URL = "https://acceso-universitario-api-production.up.railway.app";

// Almacén global para poder filtrar sin volver a pedir al servidor
let _datos = { estudiantes: [], docentes: [], administrativos: [], empleados: [] };

async function apiFetch(url, opciones = {}) {
    try {
        const res = await fetch(`${BASE_URL}${url}`, opciones);
        return await res.json();
    } catch (err) {
        console.error(`Error en ${url}:`, err);
        alert("No se pudo conectar al servidor.");
        return null;
    }
}

function badgeEstado(estado) {
    const activo = estado === "Activo" || estado == 1;
    return `<span class="badge ${activo ? "bg-success" : "bg-danger"}">${activo ? "Activo" : "Inactivo"}</span>`;
}

function setTexto(id, valor) {
    const el = document.getElementById(id);
    if (el) el.textContent = valor ?? "—";
}

async function cargarDatos() {
    const [est, doc, admin, emp] = await Promise.all([
        apiFetch("/estudiantes"),
        apiFetch("/docentes"),
        apiFetch("/administrativos"),
        apiFetch("/empleados")
    ]);

    if (est) { _datos.estudiantes = est; llenarEstudiantes(est); }
    if (doc) { _datos.docentes = doc; llenarDocentes(doc); }
    if (admin) { _datos.administrativos = admin; llenarAdministrativos(admin); }
    if (emp) { _datos.empleados = emp; llenarEmpleados(emp); }

    // Actualizar contadores
    setTexto("statEstudiantes", est?.length ?? "—");
    setTexto("statDocentes", doc?.length ?? "—");
    setTexto("statAdmin", admin?.length ?? "—");
    setTexto("statEmpleados", emp?.length ?? "—");
}


function llenarEstudiantes(data) {
    const tabla = document.getElementById("tablaEstudiantes");
    if (!tabla) return;
    tabla.innerHTML = data.map(est => `
        <tr>
            <td>${est.control}</td>
            <td>${est.nombre}</td>
            <td>${est.carrera}</td>
            <td>${est.semestre}</td>
            <td>${badgeEstado(est.estado)}</td>
            <td>
                <button class="btn btn-primary btn-sm"
                    onclick="editarEstudiante('${est.control}','${est.semestre}','${est.estado}')">
                    Editar
                </button>
                <button class="btn btn-danger btn-sm"
                    onclick="eliminar('estudiantes','${est.control}')">
                    Eliminar
                </button>
            </td>
        </tr>
    `).join("");
}

function llenarDocentes(data) {
    const tabla = document.getElementById("tablaDocentes");
    if (!tabla) return;
    tabla.innerHTML = data.map(doc => `
        <tr>
            <td>${doc.id}</td>
            <td>${doc.nombre}</td>
            <td>${doc.departamento}</td>
            <td>${badgeEstado(doc.estado)}</td>
            <td>
                <button class="btn btn-primary btn-sm"
                    onclick="editarPersonal('docentes','${doc.id}','${doc.estado}')">
                    Editar
                </button>
                <button class="btn btn-danger btn-sm"
                    onclick="eliminar('docentes','${doc.id}')">
                    Eliminar
                </button>
            </td>
        </tr>
    `).join("");
}

function llenarAdministrativos(data) {
    const tabla = document.getElementById("tablaAdministrativos");
    if (!tabla) return;
    tabla.innerHTML = data.map(admin => `
        <tr>
            <td>${admin.id}</td>
            <td>${admin.nombre}</td>
            <td>${admin.area}</td>
            <td>${badgeEstado(admin.estado)}</td>
            <td>
                <button class="btn btn-primary btn-sm"
                    onclick="editarPersonal('administrativos','${admin.id}','${admin.estado}')">
                    Editar
                </button>
                <button class="btn btn-danger btn-sm"
                    onclick="eliminar('administrativos','${admin.id}')">
                    Eliminar
                </button>
            </td>
        </tr>
    `).join("");
}

function llenarEmpleados(data) {
    const tabla = document.getElementById("tablaEmpleados");
    if (!tabla) return;
    tabla.innerHTML = data.map(emp => `
        <tr>
            <td>${emp.id}</td>
            <td>${emp.nombre}</td>
            <td>${emp.puesto}</td>
            <td>${badgeEstado(emp.estado)}</td>
            <td>
                <button class="btn btn-primary btn-sm"
                    onclick="editarEmpleado('${emp.id}','${emp.puesto}','${emp.estado}')">
                    Editar
                </button>
                <button class="btn btn-danger btn-sm"
                    onclick="eliminar('empleados','${emp.id}')">
                    Eliminar
                </button>
            </td>
        </tr>
    `).join("");
}

function filtrarTablas() {
    const texto = document.getElementById("busqueda")?.value.toLowerCase() ?? "";
    const filtro = document.getElementById("filtroPor")?.value ?? "";

    const secciones = ["estudiantes", "docentes", "administrativos", "empleados"];

    secciones.forEach(sec => {
        const seccion = document.getElementById(`seccion${capitalizar(sec)}`);
        if (!seccion) return;

        // Mostrar u ocultar sección completa según filtro de tipo
        if (filtro && filtro !== sec) {
            seccion.style.display = "none";
            return;
        }
        seccion.style.display = "";

        // Filtrar filas por texto
        if (!texto) {
            // Sin texto → recargar original
            const fn = {
                estudiantes: llenarEstudiantes, docentes: llenarDocentes,
                administrativos: llenarAdministrativos, empleados: llenarEmpleados
            };
            fn[sec](_datos[sec]);
            return;
        }

        const filtrados = _datos[sec].filter(item => {
            const valores = Object.values(item).join(" ").toLowerCase();
            return valores.includes(texto);
        });

        const fn = {
            estudiantes: llenarEstudiantes, docentes: llenarDocentes,
            administrativos: llenarAdministrativos, empleados: llenarEmpleados
        };
        fn[sec](filtrados);
    });
}

function capitalizar(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}


async function eliminar(entidad, id) {
    if (!confirm("¿Eliminar este registro?")) return;

    const data = await apiFetch(`/${entidad}/${id}`, { method: "DELETE" });
    if (!data) return;

    alert(data.mensaje || data.error);
    cargarDatos();
}


async function editarEstudiante(control, semestreActual, estadoActual) {
    const semestre = prompt("Nuevo semestre:", semestreActual);
    if (semestre === null) return;

    const estadoInput = prompt("Estado (1 = Activo, 0 = Inactivo):", estadoActual === "Activo" ? "1" : "0");
    if (estadoInput === null) return;

    const data = await apiFetch(`/estudiantes/${control}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ semestre, estado: estadoInput })
    });

    if (!data) return;
    alert(data.mensaje || data.error);
    cargarDatos();
}


async function editarPersonal(entidad, id, estadoActual) {
    const estadoInput = prompt("Estado (1 = Activo, 0 = Inactivo):", estadoActual === "Activo" ? "1" : "0");
    if (estadoInput === null) return;

    const data = await apiFetch(`/${entidad}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estado: estadoInput })
    });

    if (!data) return;
    alert(data.mensaje || data.error);
    cargarDatos();
}


async function editarEmpleado(id, puestoActual, estadoActual) {
    const puesto = prompt("Nuevo puesto:", puestoActual);
    if (puesto === null) return;

    const estadoInput = prompt("Estado (1 = Activo, 0 = Inactivo):", estadoActual === "Activo" ? "1" : "0");
    if (estadoInput === null) return;

    const data = await apiFetch(`/empleados/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ puesto, estado: estadoInput })
    });

    if (!data) return;
    alert(data.mensaje || data.error);
    cargarDatos();
}

async function registrarEstudiante() {
    const campos = ["nombre", "apellido_p", "apellido_m", "control", "carrera", "semestre"];
    const body = {};

    for (const campo of campos) {
        const el = document.getElementById(campo);
        if (!el || !el.value.trim()) {
            alert(`El campo "${campo}" es requerido.`);
            return;
        }
        body[campo] = el.value.trim();
    }

    const data = await apiFetch("/estudiantes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    if (!data) return;
    alert(data.mensaje || data.error);

    // Cerrar modal y recargar
    bootstrap.Modal.getInstance(document.getElementById("modalRegistrar"))?.hide();
    cargarDatos();
}

cargarDatos();

async function cargarAreas() {
    const data = await apiFetch("/areas");
    if (!data) return;

    ["doc_id_area", "adm_id_area"].forEach(id => {
        const select = document.getElementById(id);
        if (!select) return;
        select.innerHTML = `<option value="">-- Sin área asignada --</option>`;
        data.forEach(a => {
            select.innerHTML += `<option value="${a.id_area}">${a.nombre_area}</option>`;
        });
    });
}


async function registrarDocente() {
    const body = {
        nombre: document.getElementById("doc_nombre")?.value.trim(),
        apellido_p: document.getElementById("doc_apellido_p")?.value.trim(),
        apellido_m: document.getElementById("doc_apellido_m")?.value.trim() || "",
        control: document.getElementById("doc_control")?.value.trim(),
        area: document.getElementById("doc_area")?.value.trim() || "",
    };

    if (!body.nombre || !body.apellido_p || !body.control) {
        alert("Nombre, apellido paterno y número de control son requeridos.");
        return;
    }

    const data = await apiFetch("/docentes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    if (!data) return;
    alert(data.mensaje || data.error);

    if (data.mensaje) {
        bootstrap.Modal.getInstance(document.getElementById("modalDocente"))?.hide();
        document.getElementById("doc_nombre").value = "";
        document.getElementById("doc_apellido_p").value = "";
        document.getElementById("doc_apellido_m").value = "";
        document.getElementById("doc_control").value = "";
        cargarDatos();
    }
}

async function registrarAdmin() {
    const body = {
        nombre: document.getElementById("adm_nombre")?.value.trim(),
        apellido_p: document.getElementById("adm_apellido_p")?.value.trim(),
        apellido_m: document.getElementById("adm_apellido_m")?.value.trim() || "",
        control: document.getElementById("adm_control")?.value.trim(),
        area: document.getElementById("adm_area")?.value.trim() || ""
    };

    if (!body.nombre || !body.apellido_p || !body.control) {
        alert("Nombre, apellido paterno y número de control son requeridos.");
        return;
    }

    const data = await apiFetch("/administrativos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    if (!data) return;
    alert(data.mensaje || data.error);

    if (data.mensaje) {
        bootstrap.Modal.getInstance(document.getElementById("modalAdmin"))?.hide();
        document.getElementById("adm_nombre").value = "";
        document.getElementById("adm_apellido_p").value = "";
        document.getElementById("adm_apellido_m").value = "";
        document.getElementById("adm_control").value = "";
        cargarDatos();
    }
}

async function registrarEmpleado() {
    const body = {
        nombre: document.getElementById("emp_nombre")?.value.trim(),
        apellido_p: document.getElementById("emp_apellido_p")?.value.trim(),
        apellido_m: document.getElementById("emp_apellido_m")?.value.trim() || "",
        control: document.getElementById("emp_control")?.value.trim(),
        puesto: document.getElementById("emp_puesto")?.value.trim()
    };

    if (!body.nombre || !body.apellido_p || !body.control || !body.puesto) {
        alert("Todos los campos excepto apellido materno son requeridos.");
        return;
    }

    const data = await apiFetch("/empleados", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    if (!data) return;
    alert(data.mensaje || data.error);

    if (data.mensaje) {
        bootstrap.Modal.getInstance(document.getElementById("modalEmpleado"))?.hide();
        document.getElementById("emp_nombre").value = "";
        document.getElementById("emp_apellido_p").value = "";
        document.getElementById("emp_apellido_m").value = "";
        document.getElementById("emp_control").value = "";
        document.getElementById("emp_puesto").value = "";
        cargarDatos();
    }
}

cargarAreas();
