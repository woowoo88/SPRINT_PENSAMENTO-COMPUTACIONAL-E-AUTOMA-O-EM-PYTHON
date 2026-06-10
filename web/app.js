let state = {};

const numberValue = id => Number(document.getElementById(id).value);
const brl = value => value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

async function loadDefaults() {
  state = await fetch("/api/default").then(response => response.json());
  ["contract_kw", "building_kw", "solar_kw", "bess_kw", "hour", "duration_hours"].forEach(id => {
    document.getElementById(id).value = state[id];
  });
  runSimulation();
}

async function runSimulation() {
  ["contract_kw", "building_kw", "solar_kw", "bess_kw", "hour", "duration_hours"].forEach(id => {
    state[id] = numberValue(id);
  });
  const response = await fetch("/api/simulate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state)
  });
  const result = await response.json();
  render(result);
}

function render(result) {
  const s = result.summary;
  const metrics = [
    ["Disponível para recarga", `${s.available_for_charging_kw} kW`],
    ["Potência solicitada", `${s.requested_kw} kW`],
    ["Potência alocada", `${s.allocated_kw} kW`],
    ["Sobrecarga evitada", `${s.avoided_overload_kw} kW`],
    ["Receita estimada", brl(s.estimated_revenue_brl)]
  ];
  document.getElementById("metrics").innerHTML = metrics
    .map(([label, value]) => `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");

  document.getElementById("alerts").innerHTML = result.alerts
    .map(alert => `<div class="alert ${alert.level}">${alert.message}</div>`)
    .join("");

  document.getElementById("allocations").innerHTML = result.allocations.map(item => `
    <tr>
      <td><strong>${item.charger_id}</strong></td>
      <td title="${item.normalized_protocol}">${item.protocol_received}</td>
      <td><span class="tag">${item.priority}</span></td>
      <td>${item.requested_kw} kW</td>
      <td><strong>${item.allocated_kw} kW</strong></td>
      <td class="${item.status.includes("limitado") ? "limited" : ""}">${item.status}</td>
    </tr>`).join("");

  const max = Math.max(...result.forecast.map(item => item.predicted_kw), 1);
  document.getElementById("forecast").innerHTML = result.forecast.map(item => `
    <div class="bar" style="height:${Math.max(4, item.predicted_kw / max * 100)}%"
      data-label="${String(item.hour).padStart(2, "0")}h · ${item.predicted_kw} kW"></div>
  `).join("");
}

document.getElementById("simulate").addEventListener("click", runSimulation);
loadDefaults();
