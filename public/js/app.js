/**
 * App principal del dashboard — Conecta con Firebase Realtime Database
 * y renderiza métricas, gráficos y tabla en tiempo real.
 */

const ITEMS_PER_PAGE = 20;
let allRegistros = [];
let allConversaciones = [];
let allData = [];
let filteredRegistros = [];
let currentPage = 1;

const ESTADO_LABELS = {
    ESPERANDO_CEDULA: "Esperando cédula",
    CONFIRMACION_DATOS: "Confirmando datos",
    PREGUNTA_CONSULTA: "Consulta presidencial",
    ESPERANDO_CANDIDATO_CONSULTA: "Esperando Consulta",
    CONFIRMANDO_CONSULTA: "Eligiendo Consulta",
    ESPERANDO_CANDIDATO_SENADO: "Esperando Senado",
    CONFIRMANDO_SENADO: "Eligiendo Senado",
    ESPERANDO_CANDIDATO_CAMARA: "Esperando Cámara",
    CONFIRMANDO_CAMARA: "Eligiendo Cámara",
    ESPERANDO_FOTO: "Esperando foto",
    completado: "Completado",
};

// ── Inicialización ────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    setupListeners();
    setupFilters();
});

function setupListeners() {
    // Listener en tiempo real para registros completados
    database.ref("registros").on("value", (snapshot) => {
        const data = snapshot.val();
        allRegistros = data ? Object.values(data).map((r) => ({ ...r, _source: "registro" })) : [];
        mergeData();
    });

    // Listener en tiempo real para conversaciones en progreso
    database.ref("conversaciones").on("value", (snapshot) => {
        const data = snapshot.val();
        allConversaciones = [];
        if (data) {
            Object.entries(data).forEach(([tel, conv]) => {
                const dv = conv.datos_votante || {};
                allConversaciones.push({
                    cedula: conv.cedula || dv.cedula || "",
                    nombre_completo: dv.nombre_completo || "",
                    candidato: conv.candidato || "",
                    municipio_votacion: dv.municipio_votacion || "",
                    puesto: dv.puesto || "",
                    mesa: dv.mesa || "",
                    estado: conv.estado || "",
                    fecha_registro: conv.ultima_actividad || 0,
                    telefono_whatsapp: tel,
                    _source: "conversacion",
                });
            });
        }
        mergeData();
    });
}

function mergeData() {
    allData = [...allRegistros, ...allConversaciones];
    applyFilters();
}

// ── Filtros ───────────────────────────────────────────────

function setupFilters() {
    document.getElementById("filtro-municipio").addEventListener("change", applyFilters);
    document.getElementById("filtro-candidato").addEventListener("change", applyFilters);
    document.getElementById("filtro-fecha-desde").addEventListener("change", applyFilters);
    document.getElementById("filtro-fecha-hasta").addEventListener("change", applyFilters);
    document.getElementById("btn-limpiar-filtros").addEventListener("click", clearFilters);
    document.getElementById("btn-prev").addEventListener("click", () => changePage(-1));
    document.getElementById("btn-next").addEventListener("click", () => changePage(1));
}

function clearFilters() {
    document.getElementById("filtro-municipio").value = "";
    document.getElementById("filtro-candidato").value = "";
    document.getElementById("filtro-fecha-desde").value = "";
    document.getElementById("filtro-fecha-hasta").value = "";
    applyFilters();
}

function applyFilters() {
    const municipio = document.getElementById("filtro-municipio").value;
    const candidato = document.getElementById("filtro-candidato").value;
    const desde = document.getElementById("filtro-fecha-desde").value;
    const hasta = document.getElementById("filtro-fecha-hasta").value;

    filteredRegistros = allData.filter((r) => {
        if (municipio && r.municipio_votacion !== municipio) return false;
        if (candidato && r.candidato_consulta !== candidato && r.candidato_senado !== candidato && r.candidato_camara !== candidato && r.candidato !== candidato) return false;
        if (desde) {
            const fechaReg = new Date(r.fecha_registro);
            if (fechaReg < new Date(desde)) return false;
        }
        if (hasta) {
            const fechaReg = new Date(r.fecha_registro);
            const hastaDate = new Date(hasta);
            hastaDate.setDate(hastaDate.getDate() + 1);
            if (fechaReg >= hastaDate) return false;
        }
        return true;
    });

    currentPage = 1;
    updateAll();
    populateFilterOptions();
}

function populateFilterOptions() {
    const municipioSelect = document.getElementById("filtro-municipio");
    const candidatoSelect = document.getElementById("filtro-candidato");

    const currentMunicipio = municipioSelect.value;
    const currentCandidato = candidatoSelect.value;

    // Municipios
    const municipios = [...new Set(allData.map((r) => r.municipio_votacion).filter(Boolean))].sort();
    municipioSelect.innerHTML = '<option value="">Todos</option>';
    municipios.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        if (m === currentMunicipio) opt.selected = true;
        municipioSelect.appendChild(opt);
    });

    // Candidatos (Consulta + Senado + Cámara)
    const candidatos = [...new Set([
        ...allData.map((r) => r.candidato_consulta).filter(Boolean),
        ...allData.map((r) => r.candidato_senado).filter(Boolean),
        ...allData.map((r) => r.candidato_camara).filter(Boolean),
        ...allData.map((r) => r.candidato).filter(Boolean),
    ])].sort();
    candidatoSelect.innerHTML = '<option value="">Todos</option>';
    candidatos.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = c;
        if (c === currentCandidato) opt.selected = true;
        candidatoSelect.appendChild(opt);
    });
}

// ── Actualización general ─────────────────────────────────

function updateAll() {
    updateMetrics();
    updateCharts();
    updateTable();
}

// ── Métricas ──────────────────────────────────────────────

function updateMetrics() {
    const completados = filteredRegistros.filter((r) => r._source === "registro");
    const enProgreso = filteredRegistros.filter((r) => r._source === "conversacion");
    const verificados = completados.filter((r) => r.ocr_verificado === true);
    const noVerificados = completados.filter((r) => r.ocr_verificado !== true);
    const total = filteredRegistros.length;

    // Municipio líder
    const municipioCounts = {};
    filteredRegistros.forEach((r) => {
        const m = r.municipio_votacion || "N/A";
        municipioCounts[m] = (municipioCounts[m] || 0) + 1;
    });
    const municipioLider = Object.entries(municipioCounts).sort((a, b) => b[1] - a[1])[0];

    document.getElementById("total-registros").textContent = total;
    document.getElementById("municipio-lider").textContent = municipioLider ? municipioLider[0] : "-";
    document.getElementById("total-verificados").textContent = verificados.length;
    document.getElementById("total-no-verificados").textContent = noVerificados.length;
    document.getElementById("en-progreso").textContent = enProgreso.length;
}

// ── Gráficos ──────────────────────────────────────────────

function updateCharts() {
    // Votos Consulta Presidencial
    const consultaCounts = {};
    filteredRegistros.forEach((r) => {
        const c = r.candidato_consulta || "";
        if (c) consultaCounts[c] = (consultaCounts[c] || 0) + 1;
    });
    const consultaSorted = Object.entries(consultaCounts).sort((a, b) => b[1] - a[1]);
    crearChartConsulta(
        consultaSorted.map((c) => c[0]),
        consultaSorted.map((c) => c[1])
    );

    // Votos por candidato - Senado
    const senadoCounts = {};
    filteredRegistros.forEach((r) => {
        const c = r.candidato_senado || r.candidato || "";
        if (c) senadoCounts[c] = (senadoCounts[c] || 0) + 1;
    });
    const senadoSorted = Object.entries(senadoCounts).sort((a, b) => b[1] - a[1]);
    crearChartCandidatos(
        senadoSorted.map((c) => c[0]),
        senadoSorted.map((c) => c[1])
    );

    // Votos por candidato - Cámara
    const camaraCounts = {};
    filteredRegistros.forEach((r) => {
        const c = r.candidato_camara || "";
        if (c) camaraCounts[c] = (camaraCounts[c] || 0) + 1;
    });
    const camaraSorted = Object.entries(camaraCounts).sort((a, b) => b[1] - a[1]);
    crearChartCamara(
        camaraSorted.map((c) => c[0]),
        camaraSorted.map((c) => c[1])
    );

    // Distribución por municipio
    const munCounts = {};
    filteredRegistros.forEach((r) => {
        const m = r.municipio_votacion || "N/A";
        munCounts[m] = (munCounts[m] || 0) + 1;
    });
    const munSorted = Object.entries(munCounts).sort((a, b) => b[1] - a[1]);
    crearChartMunicipios(
        munSorted.map((m) => m[0]),
        munSorted.map((m) => m[1])
    );

    // Top 10 puestos
    const puestoCounts = {};
    filteredRegistros.forEach((r) => {
        const p = r.puesto || "N/A";
        puestoCounts[p] = (puestoCounts[p] || 0) + 1;
    });
    const puestoSorted = Object.entries(puestoCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    crearChartPuestos(
        puestoSorted.map((p) => p[0]),
        puestoSorted.map((p) => p[1])
    );
}

// ── Tabla ─────────────────────────────────────────────────

function updateTable() {
    const tbody = document.getElementById("tabla-body");
    const sorted = [...filteredRegistros].sort(
        (a, b) => (b.fecha_registro || 0) - (a.fecha_registro || 0)
    );

    const totalPages = Math.max(1, Math.ceil(sorted.length / ITEMS_PER_PAGE));
    if (currentPage > totalPages) currentPage = totalPages;

    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const pageItems = sorted.slice(start, start + ITEMS_PER_PAGE);

    tbody.innerHTML = "";
    pageItems.forEach((r) => {
        const tr = document.createElement("tr");
        const fecha = r.fecha_registro ? new Date(r.fecha_registro).toLocaleString("es-CO") : "N/A";
        let estadoBadge;
        let verificacionBadge;
        if (r._source === "registro") {
            estadoBadge = '<span class="badge badge-success"><span class="material-symbols-outlined badge-icon">check_circle</span> Completado</span>';
            if (r.ocr_verificado === true) {
                verificacionBadge = '<span class="badge badge-verified"><span class="material-symbols-outlined badge-icon">verified</span> Verificado</span>';
            } else if (r.ocr_texto_extraido) {
                verificacionBadge = '<span class="badge badge-warning"><span class="material-symbols-outlined badge-icon">warning</span> No coincide</span>';
            } else {
                verificacionBadge = '<span class="badge badge-notext"><span class="material-symbols-outlined badge-icon">photo_camera</span> Solo foto</span>';
            }
        } else {
            const label = ESTADO_LABELS[r.estado] || r.estado || "En progreso";
            estadoBadge = `<span class="badge badge-progress"><span class="material-symbols-outlined badge-icon">hourglass_top</span> ${escapeHtml(label)}</span>`;
            verificacionBadge = '<span class="badge badge-pending"><span class="material-symbols-outlined badge-icon">pending</span> Pendiente</span>';
        }

        tr.innerHTML = `
            <td>${escapeHtml(String(r.cedula || ""))}</td>
            <td>${escapeHtml(r.nombre_completo || "")}</td>
            <td>${escapeHtml(r.candidato_consulta || "-")}</td>
            <td>${escapeHtml(r.candidato_senado || r.candidato || "-")}</td>
            <td>${escapeHtml(r.candidato_camara || "-")}</td>
            <td>${escapeHtml(r.municipio_votacion || "")}</td>
            <td>${escapeHtml(r.puesto || "")}</td>
            <td>${escapeHtml(String(r.mesa || ""))}</td>
            <td>${verificacionBadge}</td>
            <td>${estadoBadge}</td>
            <td>${escapeHtml(fecha)}</td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById("table-count").textContent = `${sorted.length} registros`;
    document.getElementById("page-info").textContent = `Página ${currentPage} de ${totalPages}`;
    document.getElementById("btn-prev").disabled = currentPage <= 1;
    document.getElementById("btn-next").disabled = currentPage >= totalPages;
}

function changePage(delta) {
    currentPage += delta;
    updateTable();
}

// ── Utilidades ────────────────────────────────────────────

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
