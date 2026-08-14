/* ============================================================
   YouTube Engagement Analytics Studio - Client Application Logic
   ============================================================ */

let currentChannelData = null;
let chartInstances = {};

const SUGGESTIONS = [
    { name: "MrBeast", handle: "@MrBeast", query: "@MrBeast" },
    { name: "Marques Brownlee", handle: "@mkbhd", query: "@mkbhd" },
    { name: "Veritasium", handle: "@veritasium", query: "@veritasium" },
    { name: "Fireship", handle: "@fireship", query: "@fireship" },
    { name: "TED", handle: "@TED", query: "@TED" },
    { name: "PewDiePie", handle: "@PewDiePie", query: "@PewDiePie" },
    { name: "Kurzgesagt", handle: "@kurzgesagt", query: "@kurzgesagt" },
    { name: "Linus Tech Tips", handle: "@LinusTechTips", query: "@LinusTechTips" }
];

document.addEventListener("DOMContentLoaded", () => {
    initParticles();
    loadSearchHistory();
    initCounters();
});

/* ------------------------------------------------------------
   THEME TOGGLE
   ------------------------------------------------------------ */
function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById("theme-icon");
    if (html.classList.contains("dark")) {
        html.classList.remove("dark");
        icon.classList.remove("fa-moon");
        icon.classList.add("fa-sun");
    } else {
        html.classList.add("dark");
        icon.classList.remove("fa-sun");
        icon.classList.add("fa-moon");
    }
}

/* ------------------------------------------------------------
   AUTOCOMPLETE ENGINE
   ------------------------------------------------------------ */
function handleAutocomplete(e) {
    const val = e.target.value.toLowerCase().trim();
    const dropdown = document.getElementById("autocomplete-dropdown");

    if (!val || val.length < 2) {
        dropdown.classList.add("hidden");
        return;
    }

    const matches = SUGGESTIONS.filter(s => s.name.toLowerCase().includes(val) || s.handle.toLowerCase().includes(val));
    if (!matches.length) {
        dropdown.classList.add("hidden");
        return;
    }

    dropdown.innerHTML = "";
    matches.forEach(m => {
        const item = document.createElement("div");
        item.className = "p-2.5 rounded-xl hover:bg-slate-800 cursor-pointer flex justify-between items-center transition";
        item.onclick = () => {
            document.getElementById("channel-input").value = m.query;
            dropdown.classList.add("hidden");
            executeAnalysis(m.query);
        };
        item.innerHTML = `
            <div class="flex items-center gap-2">
                <i class="fa-brands fa-youtube text-red-500"></i>
                <span class="font-bold text-white">${m.name}</span>
            </div>
            <span class="text-[11px] text-red-400 font-semibold">${m.handle}</span>
        `;
        dropdown.appendChild(item);
    });
    dropdown.classList.remove("hidden");
}

/* ------------------------------------------------------------
   ANIMATED HERO COUNTERS
   ------------------------------------------------------------ */
function initCounters() {
    const counters = document.querySelectorAll(".counter");
    counters.forEach(c => {
        const target = +c.getAttribute("data-target");
        let count = 0;
        const inc = Math.ceil(target / 40);

        function update() {
            count += inc;
            if (count > target) count = target;
            c.innerText = count.toLocaleString() + "+";
            if (count < target) requestAnimationFrame(update);
        }
        update();
    });
}

/* ------------------------------------------------------------
   PARTICLE CANVAS BACKGROUND
   ------------------------------------------------------------ */
function initParticles() {
    const canvas = document.getElementById("particle-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener("resize", () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const numParticles = 45;
    const particles = [];

    for (let i = 0; i < numParticles; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            radius: Math.random() * 2 + 1,
            color: i % 3 === 0 ? "rgba(239, 68, 68, " : (i % 3 === 1 ? "rgba(245, 158, 11, " : "rgba(99, 102, 241, "),
            alpha: Math.random() * 0.4 + 0.1,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4
        });
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);
        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0) p.x = width;
            if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            if (p.y > height) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = p.color + p.alpha + ")";
            ctx.fill();
        });
        requestAnimationFrame(animate);
    }

    animate();
}

/* ------------------------------------------------------------
   SEARCH & API INTEGRATION
   ------------------------------------------------------------ */
async function handleSearch(e) {
    if (e) e.preventDefault();
    const dropdown = document.getElementById("autocomplete-dropdown");
    if (dropdown) dropdown.classList.add("hidden");

    const query = document.getElementById("channel-input").value.trim();
    if (!query) return;

    executeAnalysis(query);
}

function quickSearch(query) {
    document.getElementById("channel-input").value = query;
    executeAnalysis(query);
}

async function executeAnalysis(query) {
    showLoading(true);

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query })
        });

        const res = await response.json();

        if (!response.ok || res.error) {
            alert("Analysis Error: " + (res.error || "Could not fetch channel. Check the search term."));
            showLoading(false);
            return;
        }

        currentChannelData = res.data;
        saveSearchHistory(res.data.channel_info.title, query);
        renderDashboard(res.data);

    } catch (err) {
        console.error("API error:", err);
        alert("Failed to connect to YouTube Analytics Server. Check python backend.");
    } finally {
        showLoading(false);
    }
}

function showLoading(isLoading) {
    const welcome = document.getElementById("welcome-state");
    const spinner = document.getElementById("loading-spinner");
    const content = document.getElementById("analytics-content");
    const submitBtn = document.getElementById("search-submit-btn");

    if (isLoading) {
        welcome.classList.add("hidden");
        content.classList.add("hidden");
        spinner.classList.remove("hidden");
        submitBtn.disabled = true;
        submitBtn.classList.add("opacity-50");
    } else {
        spinner.classList.add("hidden");
        submitBtn.disabled = false;
        submitBtn.classList.remove("opacity-50");
    }
}

/* ------------------------------------------------------------
   DASHBOARD RENDERER
   ------------------------------------------------------------ */
function renderDashboard(data) {
    const content = document.getElementById("analytics-content");
    content.classList.remove("hidden");

    const info = data.channel_info;
    const scores = data.scores;
    const metrics = data.metrics_summary;
    const ai = data.ai_recommendations;

    document.getElementById("channel-avatar").src = info.avatar_url;
    document.getElementById("channel-title").innerText = info.title;
    document.getElementById("channel-handle").innerText = info.handle;
    document.getElementById("channel-country").innerText = info.country;
    document.getElementById("channel-created").innerText = info.published_at ? info.published_at.substring(0, 10) : "N/A";
    document.getElementById("channel-yt-link").href = `https://www.youtube.com/${info.handle}`;

    if (info.banner_url) {
        document.getElementById("channel-banner-bg").style.backgroundImage = `url('${info.banner_url}')`;
    }

    document.getElementById("score-overall").innerText = scores.overall_score;
    document.getElementById("score-perf-val").innerText = scores.performance_score + "/100";
    document.getElementById("score-eng-val").innerText = scores.engagement_score + "/100";
    document.getElementById("score-growth-val").innerText = scores.growth_score + "/100";
    document.getElementById("score-consist-val").innerText = scores.consistency_score + "/100";
    document.getElementById("score-quality-val").innerText = scores.quality_score + "/100";

    document.getElementById("bar-perf").style.width = scores.performance_score + "%";
    document.getElementById("bar-eng").style.width = scores.engagement_score + "%";
    document.getElementById("bar-growth").style.width = scores.growth_score + "%";
    document.getElementById("bar-consist").style.width = scores.consistency_score + "%";
    document.getElementById("bar-quality").style.width = scores.quality_score + "%";

    document.getElementById("kpi-subs").innerText = info.subscriber_count_formatted;
    document.getElementById("kpi-views").innerText = info.view_count_formatted;
    document.getElementById("kpi-avg-views").innerText = metrics.avg_views_formatted;
    document.getElementById("kpi-engagement").innerText = metrics.avg_engagement_rate + "%";

    renderRadarChart(scores);
    renderTimelineChart(data.videos);
    renderCategoryChart(data.category_breakdown);
    renderTopVideos(data.top_videos);
    renderStrategyTab(ai);
    renderPowerBiStudio(data);
    renderTableauStudio(data);
    renderHistoricalChart(data.historical_data);
    renderVideoTable(data.videos);

    content.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ------------------------------------------------------------
   CHARTS RENDERING
   ------------------------------------------------------------ */
function destroyChart(id) {
    if (chartInstances[id]) {
        chartInstances[id].destroy();
        delete chartInstances[id];
    }
}

function renderRadarChart(scores) {
    destroyChart("radarChart");
    const ctx = document.getElementById("radarChart").getContext("2d");

    chartInstances["radarChart"] = new Chart(ctx, {
        type: "radar",
        data: {
            labels: ["Performance", "Engagement", "Growth", "Consistency", "Quality"],
            datasets: [{
                label: "Channel Scores",
                data: [scores.performance_score, scores.engagement_score, scores.growth_score, scores.consistency_score, scores.quality_score],
                backgroundColor: "rgba(239, 68, 68, 0.25)",
                borderColor: "#ef4444",
                borderWidth: 2,
                pointBackgroundColor: "#f59e0b",
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: "rgba(51, 65, 85, 0.5)" },
                    grid: { color: "rgba(51, 65, 85, 0.5)" },
                    pointLabels: { color: "#cbd5e1", font: { size: 10, weight: "bold" } },
                    ticks: { display: false },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function renderTimelineChart(videos) {
    destroyChart("timelineChart");
    if (!videos || !videos.length) return;

    const ctx = document.getElementById("timelineChart").getContext("2d");
    const reversed = [...videos].reverse();

    const labels = reversed.map(v => v.publish_date || v.title.substring(0, 15));
    const viewsData = reversed.map(v => v.views);
    const engData = reversed.map(v => v.engagement_rate);

    chartInstances["timelineChart"] = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Views",
                    data: viewsData,
                    borderColor: "#3b82f6",
                    backgroundColor: "rgba(59, 130, 246, 0.1)",
                    fill: true,
                    tension: 0.4,
                    yAxisID: "y"
                },
                {
                    label: "Engagement Rate (%)",
                    data: engData,
                    borderColor: "#ef4444",
                    backgroundColor: "rgba(239, 68, 68, 0.1)",
                    fill: true,
                    tension: 0.4,
                    yAxisID: "y1"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            scales: {
                x: { grid: { color: "rgba(51, 65, 85, 0.3)" }, ticks: { color: "#94a3b8", maxTicksLimit: 10 } },
                y: { type: "linear", display: true, position: "left", grid: { color: "rgba(51, 65, 85, 0.3)" }, ticks: { color: "#3b82f6" } },
                y1: { type: "linear", display: true, position: "right", grid: { drawOnChartArea: false }, ticks: { color: "#ef4444" } }
            },
            plugins: { legend: { labels: { color: "#cbd5e1" } } }
        }
    });
}

function renderCategoryChart(categories) {
    destroyChart("categoryChart");
    if (!categories || !categories.length) return;

    const ctx = document.getElementById("categoryChart").getContext("2d");

    chartInstances["categoryChart"] = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: categories.map(c => c.category),
            datasets: [{
                data: categories.map(c => c.views),
                backgroundColor: ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899"],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom", labels: { color: "#cbd5e1", font: { size: 10 } } }
            }
        }
    });
}

function renderHistoricalChart(historical) {
    destroyChart("historicalGrowthChart");
    if (!historical || !historical.monthly_uploads) return;

    const ctx = document.getElementById("historicalGrowthChart").getContext("2d");
    const months = historical.monthly_uploads.map(m => m.publish_month);
    const uploads = historical.monthly_uploads.map(m => m.uploads);
    const avgViews = historical.monthly_uploads.map(m => m.avg_views);

    chartInstances["historicalGrowthChart"] = new Chart(ctx, {
        type: "bar",
        data: {
            labels: months,
            datasets: [
                { label: "Upload Frequency", data: uploads, backgroundColor: "#10b981", borderRadius: 6, yAxisID: "y" },
                { label: "Avg Views", data: avgViews, type: "line", borderColor: "#f59e0b", tension: 0.3, yAxisID: "y1" }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: "#94a3b8" } },
                y: { type: "linear", display: true, position: "left", ticks: { color: "#10b981" } },
                y1: { type: "linear", display: true, position: "right", ticks: { color: "#f59e0b" }, grid: { drawOnChartArea: false } }
            },
            plugins: { legend: { labels: { color: "#cbd5e1" } } }
        }
    });
}

function renderTopVideos(videos) {
    const container = document.getElementById("top-videos-list");
    container.innerHTML = "";

    if (!videos || !videos.length) {
        container.innerHTML = `<p class="text-slate-400 text-xs">No video details found.</p>`;
        return;
    }

    videos.forEach(v => {
        const card = document.createElement("a");
        card.href = v.youtube_url;
        card.target = "_blank";
        card.className = "p-3 rounded-2xl bg-slate-950 border border-slate-800 hover:border-red-500/50 transition group flex flex-col justify-between relative overflow-hidden";

        let viralBadge = v.is_viral ? `<span class="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-gradient-to-r from-red-600 to-amber-500 text-white font-black text-[9px] shadow-lg">VIRAL</span>` : "";

        card.innerHTML = `
            ${viralBadge}
            <div>
                <img src="${v.thumbnail}" class="w-full h-24 object-cover rounded-xl mb-2 group-hover:scale-105 transition">
                <h5 class="text-xs font-bold text-white line-clamp-2 leading-snug">${v.title}</h5>
            </div>
            <div class="mt-3 pt-2 border-t border-slate-800 flex justify-between items-center text-[10px] text-slate-400">
                <span><i class="fa-solid fa-eye text-blue-400"></i> ${v.views.toLocaleString()}</span>
                <span class="text-rose-400 font-semibold">${v.engagement_rate}% ER</span>
            </div>
        `;
        container.appendChild(card);
    });
}

/* ------------------------------------------------------------
   AI POSTING SCHEDULE & STRATEGY TAB
   ------------------------------------------------------------ */
function renderStrategyTab(ai) {
    document.getElementById("rec-best-day").innerText = ai.best_day.day + "s";
    document.getElementById("rec-best-day-desc").innerText = `Avg engagement rate of ${ai.best_day.avg_engagement}% on ${ai.best_day.day}s.`;

    document.getElementById("rec-best-hour").innerText = ai.best_hour.hour_label + " UTC";
    document.getElementById("rec-best-hour-desc").innerText = `Peak audience view momentum around ${ai.best_hour.hour_label}.`;

    document.getElementById("rec-best-duration").innerText = ai.best_duration.name;
    document.getElementById("rec-best-duration-desc").innerText = `Averages ${ai.best_duration.avg_views.toLocaleString()} views per video.`;

    const grid = document.getElementById("heatmap-grid");
    grid.innerHTML = "";

    let headerHtml = `<div class="grid grid-cols-25 gap-1 mb-1 font-bold text-slate-400 text-[10px] text-center"><div class="text-left">Day \\ Hour</div>`;
    for (let h = 0; h < 24; h++) {
        headerHtml += `<div>${h}</div>`;
    }
    headerHtml += `</div>`;
    grid.innerHTML += headerHtml;

    ai.heatmap_matrix.forEach(row => {
        let rowHtml = `<div class="grid grid-cols-25 gap-1 mb-1 items-center"><div class="font-semibold text-slate-300 text-[11px]">${row.day.substring(0, 3)}</div>`;
        row.hours.forEach(val => {
            let bgClass = "bg-slate-900";
            if (val > 0.0) bgClass = "bg-emerald-950/60 text-emerald-400";
            if (val > 2.0) bgClass = "bg-emerald-800/80 text-emerald-200 font-bold";
            if (val > 5.0) bgClass = "bg-emerald-500 text-slate-950 font-black shadow-md shadow-emerald-500/50";

            rowHtml += `<div class="heatmap-cell text-[9px] py-1.5 rounded text-center cursor-pointer ${bgClass}" title="${row.day} ${val}% engagement">${val > 0 ? val : ''}</div>`;
        });
        rowHtml += `</div>`;
        grid.innerHTML += rowHtml;
    });

    const tipsContainer = document.getElementById("ai-tips-container");
    tipsContainer.innerHTML = "";
    ai.tips.forEach(t => {
        const item = document.createElement("div");
        item.className = "p-4 rounded-2xl bg-slate-950 border border-slate-800 flex gap-3";
        item.innerHTML = `
            <div class="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center text-sm shrink-0">
                <i class="fa-solid fa-lightbulb"></i>
            </div>
            <div>
                <span class="text-[10px] font-bold uppercase tracking-wider text-amber-400">${t.category}</span>
                <h5 class="text-xs font-bold text-white mt-0.5">${t.title}</h5>
                <p class="text-xs text-slate-400 mt-1 leading-relaxed">${t.detail}</p>
            </div>
        `;
        tipsContainer.appendChild(item);
    });
}

/* ------------------------------------------------------------
   POWER BI STUDIO & TABLEAU STUDIO
   ------------------------------------------------------------ */
function renderPowerBiStudio(data) {
    const ch = data.channel_info;
    const scores = data.scores;
    const metrics = data.metrics_summary;
    const videos = data.videos || [];

    document.getElementById("pbi-exec-subs").innerText = ch.subscriber_count_formatted;
    document.getElementById("pbi-exec-views").innerText = ch.view_count_formatted;
    document.getElementById("pbi-exec-score").innerText = scores.overall_score + "/100";
    document.getElementById("pbi-exec-eng").innerText = metrics.avg_engagement_rate + "%";

    // Page 1 Chart
    destroyChart("pbiExecChart");
    const ctx1 = document.getElementById("pbiExecChart").getContext("2d");
    chartInstances["pbiExecChart"] = new Chart(ctx1, {
        type: "bar",
        data: {
            labels: ["Performance", "Engagement", "Growth", "Consistency", "Quality"],
            datasets: [{
                label: "Score Metric",
                data: [scores.performance_score, scores.engagement_score, scores.growth_score, scores.consistency_score, scores.quality_score],
                backgroundColor: ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6"],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, max: 100, ticks: { color: "#94a3b8" } }, x: { ticks: { color: "#cbd5e1" } } }
        }
    });

    // Page 2 Chart (Likes vs Comments)
    destroyChart("pbiEngChart");
    const ctx2 = document.getElementById("pbiEngChart").getContext("2d");
    chartInstances["pbiEngChart"] = new Chart(ctx2, {
        type: "line",
        data: {
            labels: videos.slice(0, 15).map(v => v.title.substring(0, 12)),
            datasets: [
                { label: "Likes", data: videos.slice(0, 15).map(v => v.likes), borderColor: "#f59e0b", backgroundColor: "rgba(245, 158, 11, 0.1)", fill: true },
                { label: "Comments", data: videos.slice(0, 15).map(v => v.comments), borderColor: "#ef4444", backgroundColor: "rgba(239, 68, 68, 0.1)", fill: true }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { x: { ticks: { color: "#94a3b8" } }, y: { ticks: { color: "#cbd5e1" } } }
        }
    });

    // Page 3 Chart (Category & Top Comparison)
    destroyChart("pbiPerfChart");
    const ctx3 = document.getElementById("pbiPerfChart").getContext("2d");
    const cats = data.category_breakdown || [];
    chartInstances["pbiPerfChart"] = new Chart(ctx3, {
        type: "bar",
        data: {
            labels: cats.map(c => c.category),
            datasets: [{ label: "Views per Category", data: cats.map(c => c.views), backgroundColor: "#10b981", borderRadius: 6 }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { x: { ticks: { color: "#cbd5e1" } }, y: { ticks: { color: "#94a3b8" } } }
        }
    });

    // Page 4 Chart (Growth Upload Trends)
    destroyChart("pbiGrowthChart");
    const ctx4 = document.getElementById("pbiGrowthChart").getContext("2d");
    const months = (data.historical_data?.monthly_uploads || []).map(m => m.publish_month);
    const u_counts = (data.historical_data?.monthly_uploads || []).map(m => m.uploads);
    chartInstances["pbiGrowthChart"] = new Chart(ctx4, {
        type: "line",
        data: {
            labels: months,
            datasets: [{ label: "Monthly Upload Frequency", data: u_counts, borderColor: "#3b82f6", backgroundColor: "rgba(59, 130, 246, 0.2)", fill: true, tension: 0.3 }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { x: { ticks: { color: "#cbd5e1" } }, y: { ticks: { color: "#3b82f6" } } }
        }
    });
}

function switchPbiPage(pageKey) {
    document.querySelectorAll(".pbi-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".pbi-page").forEach(p => p.classList.add("hidden"));

    document.getElementById(`pbi-tab-${pageKey}`).classList.add("active");
    document.getElementById(`pbi-page-${pageKey}`).classList.remove("hidden");
}

function renderTableauStudio(data) {
    destroyChart("tableauScatterChart");
    destroyChart("tableauBarChart");

    const videos = data.videos || [];
    if (!videos.length) return;

    const ctxScatter = document.getElementById("tableauScatterChart").getContext("2d");
    const scatterData = videos.map(v => ({ x: v.duration_seconds / 60, y: v.views, r: Math.min(15, Math.max(4, v.engagement_rate * 2)) }));

    chartInstances["tableauScatterChart"] = new Chart(ctxScatter, {
        type: "bubble",
        data: {
            datasets: [{
                label: "Videos (Duration vs Views)",
                data: scatterData,
                backgroundColor: "rgba(59, 130, 246, 0.6)",
                borderColor: "#3b82f6"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: "Duration (Minutes)", color: "#cbd5e1" }, ticks: { color: "#94a3b8" } },
                y: { title: { display: true, text: "Total Views", color: "#cbd5e1" }, ticks: { color: "#94a3b8" } }
            }
        }
    });

    const ctxBar = document.getElementById("tableauBarChart").getContext("2d");
    const cats = data.category_breakdown || [];
    chartInstances["tableauBarChart"] = new Chart(ctxBar, {
        type: "bar",
        data: {
            labels: cats.map(c => c.category),
            datasets: [{
                label: "Category View Shares",
                data: cats.map(c => c.views),
                backgroundColor: "#6366f1",
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { ticks: { color: "#94a3b8" } }, x: { ticks: { color: "#cbd5e1" } } }
        }
    });
}

/* ------------------------------------------------------------
   VIDEO TABLE & SEARCH
   ------------------------------------------------------------ */
function renderVideoTable(videos) {
    const tbody = document.getElementById("video-table-body");
    tbody.innerHTML = "";

    if (!videos || !videos.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-slate-500">No videos available.</td></tr>`;
        return;
    }

    videos.forEach(v => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td class="p-3 flex items-center gap-3">
                <img src="${v.thumbnail}" class="w-12 h-8 object-cover rounded shadow">
                <span class="font-bold text-white line-clamp-1 max-w-xs">${v.title}</span>
            </td>
            <td class="p-3 text-slate-400">${v.publish_date || 'N/A'}</td>
            <td class="p-3 text-slate-400 font-mono text-[11px]">${v.duration_formatted}</td>
            <td class="p-3 font-semibold text-blue-400">${v.views.toLocaleString()}</td>
            <td class="p-3 text-slate-300">${v.likes.toLocaleString()}</td>
            <td class="p-3 text-slate-300">${v.comments.toLocaleString()}</td>
            <td class="p-3 font-bold text-rose-400">${v.engagement_rate}%</td>
            <td class="p-3 text-right">
                <a href="${v.youtube_url}" target="_blank" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-red-600 text-white transition text-[10px]">Watch</a>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterVideoTable() {
    const query = document.getElementById("video-search-input").value.toLowerCase();
    const rows = document.querySelectorAll("#video-table-body tr");
    rows.forEach(r => {
        const text = r.innerText.toLowerCase();
        r.style.display = text.includes(query) ? "" : "none";
    });
}

/* ------------------------------------------------------------
   TAB NAVIGATION
   ------------------------------------------------------------ */
function switchTab(tabId) {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.add("hidden"));

    const btn = document.getElementById(`tab-btn-${tabId}`);
    const pane = document.getElementById(`tab-content-${tabId}`);

    if (btn) btn.classList.add("active");
    if (pane) pane.classList.remove("hidden");
}

/* ------------------------------------------------------------
   SEARCH HISTORY MANAGEMENT
   ------------------------------------------------------------ */
function saveSearchHistory(name, query) {
    let history = JSON.parse(localStorage.getItem("yt_analytics_history") || "[]");
    history = history.filter(item => item.query.toLowerCase() !== query.toLowerCase());
    history.unshift({ name: name, query: query, date: new Date().toLocaleDateString() });
    if (history.length > 8) history.pop();
    localStorage.setItem("yt_analytics_history", JSON.stringify(history));
    loadSearchHistory();
}

function loadSearchHistory() {
    const list = document.getElementById("history-list");
    if (!list) return;
    const history = JSON.parse(localStorage.getItem("yt_analytics_history") || "[]");

    if (!history.length) {
        list.innerHTML = `<p class="text-slate-500 text-center py-3">No recent searches yet</p>`;
        return;
    }

    list.innerHTML = "";
    history.forEach(item => {
        const el = document.createElement("div");
        el.className = "p-2 rounded-lg hover:bg-slate-800 cursor-pointer flex justify-between items-center transition";
        el.onclick = () => {
            toggleHistoryDropdown();
            quickSearch(item.query);
        };
        el.innerHTML = `
            <span class="font-bold text-white truncate max-w-[150px]">${item.name}</span>
            <span class="text-[10px] text-slate-500">${item.query}</span>
        `;
        list.appendChild(el);
    });
}

function toggleHistoryDropdown() {
    const menu = document.getElementById("history-menu");
    menu.classList.toggle("hidden");
}

function clearSearchHistory() {
    localStorage.removeItem("yt_analytics_history");
    loadSearchHistory();
}

/* ------------------------------------------------------------
   PDF REPORT GENERATION
   ------------------------------------------------------------ */
function downloadPdfReport() {
    if (!currentChannelData) {
        alert("Please analyze a channel first before exporting PDF report.");
        return;
    }

    const element = document.getElementById("analytics-content");
    const opt = {
        margin: 0.3,
        filename: `${currentChannelData.channel_info.title}_Executive_Report.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: '#060913' },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save();
}
