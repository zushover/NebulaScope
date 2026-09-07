const $ = (id) => document.getElementById(id);
const HISTORY = 90;
const histories = { gpu: [], vram: [], throughput: [], kv: [], ttft: [], tpot: [] };
const colors = { cyan: "#45e8da", blue: "#5b8cff", violet: "#a073ff" };

function number(value, digits = 0) {
  return value == null || Number.isNaN(Number(value)) ? "—" : Number(value).toFixed(digits);
}
function integer(value) { return value == null ? "—" : Math.round(value).toLocaleString(); }
function setText(id, value) { $(id).textContent = value; }
function push(name, value) {
  histories[name].push(value == null ? null : Number(value));
  if (histories[name].length > HISTORY) histories[name].shift();
}

function updateDashboard(sample) {
  const gpu = sample.gpu || {};
  const inf = sample.inference || {};
  const evaluation = sample.evaluation || {};
  setText("gpuName", gpu.name || "GPU unavailable");
  setText("modelName", inf.model_name || "Not connected");
  setText("engineName", inf.engine_name || "—");
  setText("runStatus", (inf.status || "idle").replaceAll("_", " "));
  $("runStatus").parentElement.previousElementSibling.classList.toggle("active", inf.status === "running");

  setText("gpuUtil", number(gpu.utilization_pct));
  setText("vram", `${number(gpu.memory_used_gb, 1)} / ${number(gpu.memory_total_gb, 1)}`);
  setText("vramPct", `${number(gpu.memory_utilization_pct)}%`);
  setText("power", number(gpu.power_w));
  setText("temperature", number(gpu.temperature_c));
  setText("gpuClock", number(gpu.gpu_clock_mhz));
  setText("memoryClock", number(gpu.memory_clock_mhz));
  $("gpuUtilBar").style.width = `${Math.min(100, gpu.utilization_pct || 0)}%`;

  setText("throughput", number(inf.throughput_tps));
  setText("batchSize", number(inf.batch_size));
  setText("activeRequests", number(inf.active_requests));
  setText("kvCache", `${number(inf.kv_cache_used_gb, 1)} / ${number(inf.kv_cache_total_gb, 1)}`);
  setText("kvPct", `${number(inf.kv_cache_usage_pct)}%`);
  $("kvBar").style.width = `${Math.min(100, inf.kv_cache_usage_pct || 0)}%`;
  setText("ttft", number(inf.ttft_ms, 1));
  setText("tpot", number(inf.tpot_ms, 1));
  setText("inputTokens", integer(inf.input_tokens));
  setText("outputTokens", integer(inf.output_tokens));
  setText("prefill", number(inf.prefill_latency_ms, 1));
  setText("decode", number(inf.decode_latency_ms, 1));

  setText("chartGpuNow", `${number(gpu.utilization_pct)}%`);
  setText("chartVramNow", `${number(gpu.memory_utilization_pct)}%`);
  setText("chartThroughputNow", `${number(inf.throughput_tps)} tok/s`);
  setText("chartKvNow", `${number(inf.kv_cache_usage_pct)}%`);
  if (evaluation.score != null) {
    setText("evalBenchmark", evaluation.benchmark || "CUSTOM EVALUATION");
    setText("evalScore", `${number(evaluation.score * 100, 1)}%`);
    setText("evalMetric", `${evaluation.metric_name || "score"}${evaluation.samples ? ` · ${evaluation.samples} samples` : ""}`);
  }
  setText("lastUpdate", `UPDATED ${new Date(sample.timestamp).toLocaleTimeString()}`);

  push("gpu", gpu.utilization_pct); push("vram", gpu.memory_utilization_pct);
  push("throughput", inf.throughput_tps); push("kv", inf.kv_cache_usage_pct);
  push("ttft", inf.ttft_ms); push("tpot", inf.tpot_ms);
  drawAll();
}

function drawChart(canvasId, series, options = {}) {
  const canvas = $(canvasId);
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, rect.width * dpr); canvas.height = Math.max(1, rect.height * dpr);
  const ctx = canvas.getContext("2d"); ctx.scale(dpr, dpr);
  const w = rect.width, h = rect.height, pad = 6;
  ctx.clearRect(0, 0, w, h);
  ctx.strokeStyle = "rgba(130,157,191,.10)"; ctx.lineWidth = 1;
  for (let i = 1; i < 4; i++) { const y = (h / 4) * i; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
  const valid = series.flatMap((s) => s.values.filter((v) => v != null));
  let min = options.min ?? (valid.length ? Math.min(...valid) : 0);
  let max = options.max ?? (valid.length ? Math.max(...valid) : 100);
  if (max <= min) max = min + 1;
  const range = max - min;
  series.forEach((item) => {
    if (item.values.length < 2) return;
    ctx.beginPath(); ctx.strokeStyle = item.color; ctx.lineWidth = 1.6; ctx.lineJoin = "round"; ctx.lineCap = "round";
    let drawing = false;
    item.values.forEach((value, index) => {
      if (value == null) { drawing = false; return; }
      const x = pad + (index / Math.max(1, HISTORY - 1)) * (w - pad * 2);
      const y = h - pad - ((value - min) / range) * (h - pad * 2);
      if (!drawing) { ctx.moveTo(x, y); drawing = true; } else ctx.lineTo(x, y);
    });
    ctx.stroke();
  });
}
function drawAll() {
  drawChart("gpuChart", [{ values: histories.gpu, color: colors.cyan }], { min: 0, max: 100 });
  drawChart("vramChart", [{ values: histories.vram, color: colors.blue }], { min: 0, max: 100 });
  drawChart("throughputChart", [{ values: histories.throughput, color: colors.cyan }], { min: 0 });
  drawChart("kvChart", [{ values: histories.kv, color: colors.violet }], { min: 0, max: 100 });
  drawChart("latencyChart", [{ values: histories.ttft, color: colors.cyan }, { values: histories.tpot, color: colors.violet }], { min: 0 });
}

let reconnectTimer;
function connect() {
  clearTimeout(reconnectTimer);
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${location.host}/ws/metrics`);
  socket.addEventListener("open", () => { $("connectionDot").parentElement.className = "connection live"; setText("connectionText", "LIVE STREAM"); });
  socket.addEventListener("message", (event) => updateDashboard(JSON.parse(event.data)));
  socket.addEventListener("close", () => { $("connectionDot").parentElement.className = "connection offline"; setText("connectionText", "RECONNECTING"); reconnectTimer = setTimeout(connect, 1800); });
  socket.addEventListener("error", () => socket.close());
}
window.addEventListener("resize", drawAll);
connect();

