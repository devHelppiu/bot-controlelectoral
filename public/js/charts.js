/**
 * Módulo de gráficos — Chart.js
 */

const COLORS = [
    "#4F46E5", "#7C3AED", "#EC4899", "#F59E0B", "#10B981",
    "#06B6D4", "#EF4444", "#8B5CF6", "#F97316", "#14B8A6",
    "#6366F1", "#D946EF", "#84CC16", "#0EA5E9", "#E11D48",
];

let chartCandidatos = null;
let chartConsulta = null;
let chartCamara = null;
let chartMunicipios = null;
let chartPuestos = null;

function crearChartConsulta(labels, data) {
    const ctx = document.getElementById("chart-consulta").getContext("2d");
    if (chartConsulta) chartConsulta.destroy();

    chartConsulta = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Votos",
                data: data,
                backgroundColor: COLORS.slice(0, labels.length),
                borderRadius: 6,
                borderSkipped: false,
            }],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { stepSize: 1, font: { size: 12 } },
                    grid: { color: "rgba(0,0,0,0.05)" },
                },
                y: {
                    ticks: { font: { size: 11 } },
                    grid: { display: false },
                },
            },
        },
    });
}

function crearChartCandidatos(labels, data) {
    const ctx = document.getElementById("chart-candidatos").getContext("2d");
    if (chartCandidatos) chartCandidatos.destroy();

    chartCandidatos = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Votos",
                data: data,
                backgroundColor: COLORS.slice(0, labels.length),
                borderRadius: 6,
                borderSkipped: false,
            }],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { stepSize: 1, font: { size: 12 } },
                    grid: { color: "rgba(0,0,0,0.05)" },
                },
                y: {
                    ticks: { font: { size: 11 } },
                    grid: { display: false },
                },
            },
        },
    });
}

function crearChartCamara(labels, data) {
    const ctx = document.getElementById("chart-camara").getContext("2d");
    if (chartCamara) chartCamara.destroy();

    chartCamara = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Votos",
                data: data,
                backgroundColor: COLORS.slice(0, labels.length),
                borderRadius: 6,
                borderSkipped: false,
            }],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { stepSize: 1, font: { size: 12 } },
                    grid: { color: "rgba(0,0,0,0.05)" },
                },
                y: {
                    ticks: { font: { size: 11 } },
                    grid: { display: false },
                },
            },
        },
    });
}

function crearChartMunicipios(labels, data) {
    const ctx = document.getElementById("chart-municipios").getContext("2d");
    if (chartMunicipios) chartMunicipios.destroy();

    chartMunicipios = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: COLORS.slice(0, labels.length),
                borderWidth: 2,
                borderColor: "#fff",
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { font: { size: 11 }, padding: 12 },
                },
            },
        },
    });
}

function crearChartPuestos(labels, data) {
    const ctx = document.getElementById("chart-puestos").getContext("2d");
    if (chartPuestos) chartPuestos.destroy();

    chartPuestos = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Registros",
                data: data,
                backgroundColor: "#4F46E5",
                borderRadius: 4,
                borderSkipped: false,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: "y",
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { stepSize: 1, font: { size: 12 } },
                    grid: { color: "rgba(0,0,0,0.05)" },
                },
                y: {
                    ticks: { font: { size: 11 } },
                    grid: { display: false },
                },
            },
        },
    });
}
