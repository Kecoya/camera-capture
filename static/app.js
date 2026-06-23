/* 摄像头抓拍工具 · Web 看板前端逻辑（原生 JS，无框架） */

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

let galleryPage = 1;
let currentLightbox = null; // {type, name}
let configLoaded = false;   // 配置表单是否已载入，避免来回切 Tab 时覆盖未保存的编辑

/* ----------------------------- 通用工具 ----------------------------- */

function toast(msg, ms = 2500) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.add("hidden"), ms);
}

/** HTML 转义：所有插入 innerHTML 的动态值都先过它，防注入。 */
function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

/** 读取数字输入：空或非数字则抛错（由调用方捕获提示）。 */
function readNum(input, label) {
  const raw = (input.value || "").trim();
  if (raw === "") throw new Error(`${label} 不能为空`);
  const v = Number(raw);
  if (Number.isNaN(v)) throw new Error(`${label} 不是有效数字`);
  return v;
}

async function api(url, opts = {}) {
  const init = { ...opts };
  // 仅在有请求体时声明 JSON，避免 GET 等无 body 请求带无谓的 Content-Type
  if (init.body && typeof init.body !== "string") {
    init.body = JSON.stringify(init.body);
    init.headers = { "Content-Type": "application/json", ...(init.headers || {}) };
  }
  const res = await fetch(url, init);
  let data = null;
  try { data = await res.json(); } catch (e) { /* 无 JSON 体 */ }
  if (!res.ok) {
    const err = (data && data.error) || `请求失败 (${res.status})`;
    throw new Error(err);
  }
  return data;
}

function fmtBytes(n) {
  if (n == null) return "-";
  const u = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(i ? 1 : 0)} ${u[i]}`;
}

/* ----------------------------- Tab 切换 ----------------------------- */

$$(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    $$(".tab-btn").forEach(b => b.classList.toggle("active", b === btn));
    const id = btn.dataset.tab;
    $$(".tab-panel").forEach(p => p.classList.toggle("active", p.id === `tab-${id}`));
    // 配置仅首次切入时载入，保留用户未保存的编辑
    if (id === "config" && !configLoaded) loadConfig();
    if (id === "gallery") loadGallery(galleryPage);
    if (id === "gif") loadGifs();
    if (id === "startup") loadStartup();
  });
});

/* ----------------------------- 状态轮询 ----------------------------- */

let pollFailures = 0;
const pollTimer = setInterval(pollStatus, 5000);

async function pollStatus() {
  try {
    const s = await api("/api/status");
    pollFailures = 0;
    const rangeTxt = s.in_range && s.current_range
      ? `${esc(s.current_range.start)}-${esc(s.current_range.end)}`
      : "空闲";
    // last_capture 为服务端格式化的时间字符串，其余均为数值/布尔，安全
    $("#statusBar").innerHTML =
      `<span class="dot ${s.is_running ? "on" : "off"}"></span>` +
      `抓拍：<b>${s.is_running ? "运行中" : "已停止"}</b> · ` +
      `摄像头 #${s.camera_id} · ` +
      `当前：<b>${rangeTxt}</b> · ` +
      `临时 ${s.counts.temp} / 永久 ${s.counts.permanent} / GIF ${s.counts.gif} · ` +
      `最近抓拍 ${esc(s.last_capture || "无")} · ` +
      `开机启动：<b>${s.startup_enabled ? "已启用" : "已禁用"}</b>`;
    $("#startupStatus").textContent = s.startup_enabled ? "已启用" : "已禁用";
  } catch (e) {
    pollFailures++;
    $("#statusBar").textContent = `状态获取失败：${e.message}`;
    // 连续失败（如服务已退出）后停止轮询，避免无限刷屏
    if (pollFailures >= 5) clearInterval(pollTimer);
  }
}

/* ----------------------------- 实时预览 ----------------------------- */

$("#btnPreviewStart").addEventListener("click", () => {
  $("#preview").src = "/video_feed?t=" + Date.now();
  $("#preview").style.display = "";
  $("#previewPlaceholder").style.display = "none";
  $("#previewState").textContent = "预览中…";
});

$("#btnPreviewStop").addEventListener("click", () => {
  $("#preview").src = "";
  $("#preview").style.display = "none";
  $("#previewPlaceholder").style.display = "";
  $("#previewState").textContent = "已停止";
});

/* ----------------------------- 配置 ----------------------------- */

async function loadConfig() {
  try {
    const cfg = await api("/api/config");
    const f = $("#configForm");
    f.camera_id.value = cfg.camera_id ?? 0;
    f.temporary_dir.value = cfg.temporary_dir ?? "";
    f.permanent_dir.value = cfg.permanent_dir ?? "";
    f.gif_dir.value = cfg.gif_dir ?? "";
    f.max_temp_captures.value = cfg.max_temp_captures ?? 1000;
    f.gif_fps.value = cfg.gif_fps ?? 24;
    f.gif_duration.value = cfg.gif_duration ?? 2.0;
    f.enable_timestamp.checked = !!cfg.enable_timestamp;
    f.timestamp_scale.value = cfg.timestamp_scale ?? 1.0;
    f.timestamp_thickness.value = cfg.timestamp_thickness ?? 2;
    const color = cfg.timestamp_color || [0, 0, 255];
    f.ts_b.value = color[0]; f.ts_g.value = color[1]; f.ts_r.value = color[2];
    f.auto_cleanup.checked = !!cfg.auto_cleanup;
    f.cleanup_days.value = cfg.cleanup_days ?? 7;

    renderRanges(cfg.time_ranges || []);
    renderFixed(cfg.fixed_times || []);
    configLoaded = true;
  } catch (e) {
    toast("加载配置失败：" + e.message);
  }
}

function rangeRow(r = { start: "", end: "", interval: 30 }) {
  const tr = document.createElement("tr");
  tr.innerHTML =
    `<td><input type="text" class="hhmm" value="${esc(r.start)}" placeholder="09:00"></td>` +
    `<td><input type="text" class="hhmm" value="${esc(r.end)}" placeholder="12:00"></td>` +
    `<td><input type="number" class="interval" value="${esc(r.interval)}" min="1"></td>` +
    `<td><button type="button" class="btn small danger">删除</button></td>`;
  tr.querySelector("button").addEventListener("click", () => tr.remove());
  return tr;
}

function fixedRow(f = { time: "", description: "" }) {
  const tr = document.createElement("tr");
  tr.innerHTML =
    `<td><input type="text" class="hhmm" value="${esc(f.time)}" placeholder="08:00"></td>` +
    `<td><input type="text" class="desc" value="${esc(f.description || "")}"></td>` +
    `<td><button type="button" class="btn small danger">删除</button></td>`;
  tr.querySelector("button").addEventListener("click", () => tr.remove());
  return tr;
}

function renderRanges(ranges) {
  const tb = $("#timeRangesTable tbody");
  tb.innerHTML = "";
  ranges.forEach(r => tb.appendChild(rangeRow(r)));
}
function renderFixed(fixed) {
  const tb = $("#fixedTimesTable tbody");
  tb.innerHTML = "";
  fixed.forEach(f => tb.appendChild(fixedRow(f)));
}

$("#btnAddRange").addEventListener("click", () => $("#timeRangesTable tbody").appendChild(rangeRow()));
$("#btnAddFixed").addEventListener("click", () => $("#fixedTimesTable tbody").appendChild(fixedRow()));

$("#configForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.target;
  $("#configMsg").textContent = "保存中…";
  try {
    const body = {
      camera_id: readNum(f.camera_id, "摄像头ID"),
      temporary_dir: f.temporary_dir.value.trim(),
      permanent_dir: f.permanent_dir.value.trim(),
      gif_dir: f.gif_dir.value.trim(),
      max_temp_captures: readNum(f.max_temp_captures, "最大临时照片数"),
      gif_fps: readNum(f.gif_fps, "GIF帧率"),
      gif_duration: readNum(f.gif_duration, "GIF时长"),
      enable_timestamp: f.enable_timestamp.checked,
      timestamp_scale: readNum(f.timestamp_scale, "时间戳大小"),
      timestamp_thickness: readNum(f.timestamp_thickness, "时间戳粗细"),
      timestamp_color: [
        parseInt(f.ts_b.value, 10) || 0,
        parseInt(f.ts_g.value, 10) || 0,
        parseInt(f.ts_r.value, 10) || 0,
      ],
      auto_cleanup: f.auto_cleanup.checked,
      cleanup_days: readNum(f.cleanup_days, "清理天数"),
      time_ranges: $$("#timeRangesTable tbody tr").map(tr => ({
        start: tr.querySelector(".hhmm").value.trim(),
        end: tr.querySelectorAll(".hhmm")[1].value.trim(),
        interval: readNum(tr.querySelector(".interval"), "间隔"),
      })),
      fixed_times: $$("#fixedTimesTable tbody tr").map(tr => ({
        time: tr.querySelector(".hhmm").value.trim(),
        description: tr.querySelector(".desc").value.trim(),
      })),
    };
    const r = await api("/api/config", { method: "POST", body });
    $("#configMsg").textContent = r.restarted ? "已保存，并按新配置重启抓拍" : "已保存";
    toast("配置已保存");
    pollStatus();
  } catch (e) {
    $("#configMsg").textContent = "保存失败：" + e.message;
    toast("保存失败：" + e.message);
  }
});

/* ----------------------------- 控制 ----------------------------- */

$("#btnManual").addEventListener("click", async () => {
  $("#controlMsg").textContent = "抓拍中…";
  try {
    // 失败时 api() 会抛出（其中已含服务端 error 文案），成功才有 r.path
    const r = await api("/api/capture/manual", { method: "POST" });
    $("#controlMsg").textContent = `已抓拍：${r.path}`;
    toast("已抓拍一张");
    pollStatus();
  } catch (e) { $("#controlMsg").textContent = "失败：" + e.message; }
});

$("#btnCaptureStart").addEventListener("click", async () => {
  try { await api("/api/capture/start", { method: "POST" }); toast("已启动抓拍"); pollStatus(); }
  catch (e) { toast("启动失败：" + e.message); }
});

$("#btnCaptureStop").addEventListener("click", async () => {
  try { await api("/api/capture/stop", { method: "POST" }); toast("已停止抓拍"); pollStatus(); }
  catch (e) { toast("停止失败：" + e.message); }
});

/* ----------------------------- 图片画廊 ----------------------------- */

$("#galleryType").addEventListener("change", () => loadGallery(1));
$("#btnGalleryRefresh").addEventListener("click", () => loadGallery(galleryPage));

async function loadGallery(page = 1) {
  galleryPage = page;
  const type = $("#galleryType").value;
  try {
    const r = await api(`/api/images?type=${encodeURIComponent(type)}&page=${page}&size=24`);
    const grid = $("#galleryGrid");
    grid.innerHTML = "";
    if (r.items.length === 0) {
      grid.innerHTML = '<p class="hint">暂无图片</p>';
    }
    r.items.forEach(it => {
      const encName = encodeURIComponent(it.name);
      const card = document.createElement("div");
      card.className = "thumb-card";
      card.innerHTML =
        `<img src="/api/thumbnail/${encodeURIComponent(type)}/${encName}" loading="lazy" alt="${esc(it.name)}">` +
        `<div class="thumb-meta">${esc(it.mtime)}<br>${esc(fmtBytes(it.size))}</div>`;
      card.addEventListener("click", () => openLightbox(type, it.name));
      grid.appendChild(card);
    });
    const totalPages = r.total_pages || (r.total ? 1 : 0);
    $("#galleryInfo").textContent = `共 ${r.total} 张 · 第 ${r.page}/${totalPages || 1} 页`;

    const pager = $("#galleryPager");
    pager.innerHTML = "";
    const mk = (label, target, disabled) => {
      const b = document.createElement("button");
      b.className = "btn small";
      b.textContent = label;
      b.disabled = disabled;
      b.addEventListener("click", () => loadGallery(target));
      pager.appendChild(b);
    };
    mk("上一页", page - 1, page <= 1);
    mk("下一页", page + 1, page >= totalPages);
  } catch (e) {
    $("#galleryInfo").textContent = "加载失败：" + e.message;
  }
}

/* ----------------------------- GIF ----------------------------- */

$("#btnGifRefresh").addEventListener("click", loadGifs);

async function loadGifs() {
  try {
    const r = await api("/api/gifs");
    const grid = $("#gifGrid");
    grid.innerHTML = "";
    if (r.items.length === 0) grid.innerHTML = '<p class="hint">暂无 GIF</p>';
    r.items.forEach(it => {
      const encName = encodeURIComponent(it.name);
      const card = document.createElement("div");
      card.className = "thumb-card";
      card.innerHTML =
        `<img src="/gif/${encName}" alt="${esc(it.name)}">` +
        `<div class="thumb-meta">${esc(it.mtime)}<br>${esc(fmtBytes(it.size))}</div>`;
      card.addEventListener("click", () => openLightbox("gif", it.name));
      grid.appendChild(card);
    });
    $("#gifInfo").textContent = `共 ${r.total} 个 GIF`;
  } catch (e) { $("#gifInfo").textContent = "加载失败：" + e.message; }
}

/* ----------------------------- 灯箱 ----------------------------- */

function openLightbox(type, name) {
  currentLightbox = { type, name };
  const encName = encodeURIComponent(name);
  const src = type === "gif"
    ? `/gif/${encName}`
    : `/image/${encodeURIComponent(type)}/${encName}`;
  $("#lightboxImg").src = src;
  $("#lightboxDownload").href = src;
  $("#lightboxDownload").setAttribute("download", name);
  $("#lightbox").classList.remove("hidden");
}

$("#lightboxClose").addEventListener("click", () => $("#lightbox").classList.add("hidden"));
$("#lightbox").addEventListener("click", (e) => {
  if (e.target.id === "lightbox") $("#lightbox").classList.add("hidden");
});

$("#lightboxDelete").addEventListener("click", async () => {
  if (!currentLightbox) return;
  if (!confirm(`确认删除 ${currentLightbox.name}？`)) return;
  try {
    await api("/api/image/delete", { method: "POST", body: currentLightbox });
    toast("已删除");
    $("#lightbox").classList.add("hidden");
    const activeTab = $(".tab-btn.active").dataset.tab;
    if (activeTab === "gallery") loadGallery(galleryPage);
    if (activeTab === "gif") loadGifs();
    pollStatus();
  } catch (e) { toast("删除失败：" + e.message); }
});

/* ----------------------------- 启动设置 ----------------------------- */

async function loadStartup() {
  try {
    const r = await api("/api/startup");
    $("#startupStatus").textContent = r.enabled ? "已启用" : "已禁用";
  } catch (e) { $("#startupStatus").textContent = "查询失败"; }
}

$("#btnStartupEnable").addEventListener("click", async () => {
  try { const r = await api("/api/startup", { method: "POST", body: { enable: true } });
    $("#startupMsg").textContent = r.ok ? "已启用开机启动" : ("失败：" + (r.error || ""));
    pollStatus(); } catch (e) { $("#startupMsg").textContent = "失败：" + e.message; }
});

$("#btnStartupDisable").addEventListener("click", async () => {
  try { const r = await api("/api/startup", { method: "POST", body: { enable: false } });
    $("#startupMsg").textContent = r.ok ? "已禁用开机启动" : ("失败：" + (r.error || ""));
    pollStatus(); } catch (e) { $("#startupMsg").textContent = "失败：" + e.message; }
});

$("#btnShortcut").addEventListener("click", async () => {
  try { const r = await api("/api/desktop-shortcut", { method: "POST" });
    $("#startupMsg").textContent = r.ok ? `桌面快捷方式已创建：${r.path}` : ("失败：" + (r.error || ""));
    toast(r.ok ? "快捷方式已创建" : "创建失败"); } catch (e) { $("#startupMsg").textContent = "失败：" + e.message; }
});

/* ----------------------------- 退出服务 ----------------------------- */

$("#btnShutdown").addEventListener("click", async () => {
  if (!confirm("确认退出抓拍服务？将停止抓拍并关闭 Web 服务。")) return;
  clearInterval(pollTimer); // 服务即将退出，停止轮询避免刷屏
  try { await api("/api/shutdown", { method: "POST" }); toast("服务即将退出…"); }
  catch (e) { toast("退出请求已发送"); }
});

/* ----------------------------- 初始化 ----------------------------- */
pollStatus();
