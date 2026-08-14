/* ============================================================
   SOCIALPULSE DASHBOARD JAVASCRIPT
============================================================ */

document.addEventListener("DOMContentLoaded", function () {

    const data = window.dashboardData;

    if (!data) {
        console.error("Dashboard data was not received.");
        return;
    }


    /* ========================================================
       HELPERS
    ======================================================== */

    function formatNumber(value) {

        return new Intl.NumberFormat("en-IN").format(
            Number(value || 0)
        );
    }


    function formatCompactNumber(value) {

        value = Number(value || 0);

        if (value >= 10000000) {
            return (value / 10000000).toFixed(1) + " Cr";
        }

        if (value >= 100000) {
            return (value / 100000).toFixed(1) + " L";
        }

        if (value >= 1000) {
            return (value / 1000).toFixed(1) + "K";
        }

        return formatNumber(value);
    }


    function formatPercentage(value) {

        return Number(value || 0).toFixed(2) + "%";
    }


    function escapeHTML(value) {

        const div = document.createElement("div");

        div.textContent = value ?? "";

        return div.innerHTML;
    }


    /* ========================================================
       KPI CARDS
    ======================================================== */

    const kpis = data.kpis;

    document.getElementById("totalVideos").textContent =
        formatNumber(kpis.total_videos);

    document.getElementById("totalViews").textContent =
        formatCompactNumber(kpis.total_views);

    document.getElementById("totalLikes").textContent =
        formatCompactNumber(kpis.total_likes);

    document.getElementById("totalComments").textContent =
        formatCompactNumber(kpis.total_comments);

    document.getElementById("averageEngagement").textContent =
        formatPercentage(kpis.average_engagement);

    document.getElementById("totalChannels").textContent =
        formatNumber(kpis.total_channels);


    /* ========================================================
       PERFORMANCE INSIGHT
    ======================================================== */

    const performanceLabels = data.performance.labels;

    const performanceValues = data.performance.values;

    let maxPerformanceIndex = 0;

    performanceValues.forEach(function (value, index) {

        if (
            value >
            performanceValues[maxPerformanceIndex]
        ) {
            maxPerformanceIndex = index;
        }

    });


    const topPerformance =
        performanceLabels[maxPerformanceIndex];

    const topPerformanceCount =
        performanceValues[maxPerformanceIndex];


    document.getElementById("topPerformance").textContent =
        topPerformance;


    document.getElementById("mainInsight").textContent =
        `${topPerformance} performance is the largest segment`;


    document.getElementById("mainInsightText").textContent =
        `${topPerformanceCount} of ${kpis.total_videos} analyzed videos fall into the ${topPerformance.toLowerCase()} performance category.`;


    /* ========================================================
       RECOMMENDATIONS
    ======================================================== */

    const recommendations = data.recommendations;


    document.getElementById("bestDay").textContent =
        recommendations.best_day;


    document.getElementById("bestDayEngagement").textContent =
        formatPercentage(
            recommendations.best_day_engagement
        );


    document.getElementById("bestHour").textContent =
        `${String(recommendations.best_hour).padStart(2, "0")}:00`;


    document.getElementById("bestHourEngagement").textContent =
        formatPercentage(
            recommendations.best_hour_engagement
        );


    /* ========================================================
       CHART DEFAULTS
    ======================================================== */

    Chart.defaults.font.family =
        "Inter, sans-serif";

    Chart.defaults.font.size = 10;

    Chart.defaults.color = "#64748b";


    const gridColor =
        "rgba(148, 163, 184, 0.16)";


    /* ========================================================
       PERFORMANCE DONUT
    ======================================================== */

    new Chart(
        document.getElementById("performanceChart"),
        {

            type: "doughnut",

            data: {

                labels: performanceLabels,

                datasets: [
                    {
                        data: performanceValues,

                        backgroundColor: [
                            "#ef4444",
                            "#f97316",
                            "#facc15",
                            "#22c55e"
                        ],

                        borderWidth: 0,

                        hoverOffset: 8
                    }
                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                cutout: "67%",

                plugins: {

                    legend: {

                        position: "bottom",

                        labels: {

                            padding: 15,

                            usePointStyle: true,

                            pointStyle: "circle",

                            font: {
                                size: 9
                            }
                        }
                    },

                    tooltip: {

                        callbacks: {

                            label: function (context) {

                                return (
                                    " " +
                                    context.label +
                                    ": " +
                                    context.raw +
                                    " videos"
                                );

                            }

                        }

                    }

                }

            }

        }
    );


    /* ========================================================
       VIDEO LENGTH
    ======================================================== */

    new Chart(
        document.getElementById("videoLengthChart"),
        {

            type: "bar",

            data: {

                labels: data.video_length.labels,

                datasets: [
                    {
                        label: "Average Engagement",

                        data: data.video_length.values,

                        backgroundColor:
                            "rgba(37, 99, 235, 0.72)",

                        borderRadius: 6,

                        borderSkipped: false
                    }
                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        grid: {
                            color: gridColor
                        },

                        ticks: {
                            callback: function(value) {
                                return value + "%";
                            }
                        }
                    },

                    x: {

                        grid: {
                            display: false
                        }
                    }

                }

            }

        }
    );


    /* ========================================================
       PUBLISHING DAY
    ======================================================== */

    new Chart(
        document.getElementById("dayChart"),
        {

            type: "bar",

            data: {

                labels: data.publishing_day.labels,

                datasets: [
                    {
                        label: "Average Engagement",

                        data: data.publishing_day.values,

                        backgroundColor:
                            "rgba(124, 58, 237, 0.72)",

                        borderRadius: 6,

                        borderSkipped: false
                    }
                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        grid: {
                            color: gridColor
                        },

                        ticks: {
                            callback: function(value) {
                                return value + "%";
                            }
                        }
                    },

                    x: {

                        grid: {
                            display: false
                        }
                    }

                }

            }

        }
    );


    /* ========================================================
       PUBLISHING HOUR
    ======================================================== */

    new Chart(
        document.getElementById("hourChart"),
        {

            type: "line",

            data: {

                labels: data.publishing_hour.labels.map(
                    function(hour) {

                        return `${String(hour).padStart(2, "0")}:00`;

                    }
                ),

                datasets: [
                    {

                        label: "Average Engagement",

                        data: data.publishing_hour.values,

                        borderColor: "#2563eb",

                        backgroundColor:
                            "rgba(37, 99, 235, 0.10)",

                        borderWidth: 3,

                        pointRadius: 3,

                        pointHoverRadius: 6,

                        fill: true,

                        tension: 0.35
                    }
                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        grid: {
                            color: gridColor
                        },

                        ticks: {

                            callback: function(value) {

                                return value + "%";

                            }

                        }

                    },

                    x: {

                        grid: {
                            display: false
                        }

                    }

                }

            }

        }
    );


    /* ========================================================
       TOP CHANNELS TABLE
    ======================================================== */

    const channelsTable =
        document.getElementById("channelsTable");


    data.top_channels.forEach(
        function(channel, index) {

            const row =
                document.createElement("tr");


            row.innerHTML = `

                <td class="rank">
                    ${index + 1}
                </td>

                <td>
                    <strong>
                        ${escapeHTML(channel.channel)}
                    </strong>
                </td>

                <td>
                    ${formatNumber(channel.videos)}
                </td>

                <td>
                    ${formatCompactNumber(channel.total_views)}
                </td>

                <td class="engagement-value">
                    ${formatPercentage(channel.avg_engagement)}
                </td>

            `;


            channelsTable.appendChild(row);

        }
    );


    /* ========================================================
       VIDEO TABLE
    ======================================================== */

    const videosTable =
        document.getElementById("videosTable");


    const searchInput =
        document.getElementById("videoSearch");


    const sortSelect =
        document.getElementById("videoSort");


    function renderVideos() {

        const search =
            searchInput.value
                .toLowerCase()
                .trim();


        const sortBy =
            sortSelect.value;


        let videos =
            [...data.top_videos];


        /* Search */

        if (search) {

            videos =
                videos.filter(
                    function(video) {

                        return (

                            String(video.title)
                                .toLowerCase()
                                .includes(search)

                            ||

                            String(video.channel)
                                .toLowerCase()
                                .includes(search)

                        );

                    }
                );

        }


        /* Sort */

        videos.sort(
            function(a, b) {

                if (sortBy === "views") {

                    return b.views - a.views;

                }

                if (sortBy === "likes") {

                    return b.likes - a.likes;

                }

                if (sortBy === "comments") {

                    return b.comments - a.comments;

                }

                return (
                    b.engagement_rate -
                    a.engagement_rate
                );

            }
        );


        videosTable.innerHTML = "";


        videos.forEach(
            function(video, index) {

                const performance =
                    String(
                        video.performance_category
                    );


                const badgeClass =
                    "badge-" +
                    performance
                        .toLowerCase()
                        .replace(" ", "-");


                const row =
                    document.createElement("tr");


                row.innerHTML = `

                    <td class="rank">
                        ${index + 1}
                    </td>

                    <td class="video-title"
                        title="${escapeHTML(video.title)}">

                        ${escapeHTML(video.title)}

                    </td>

                    <td>
                        ${escapeHTML(video.channel)}
                    </td>

                    <td>
                        ${formatCompactNumber(video.views)}
                    </td>

                    <td>
                        ${formatCompactNumber(video.likes)}
                    </td>

                    <td>
                        ${formatNumber(video.comments)}
                    </td>

                    <td class="engagement-value">
                        ${formatPercentage(video.engagement_rate)}
                    </td>

                    <td>

                        <span class="badge ${badgeClass}">
                            ${escapeHTML(performance)}
                        </span>

                    </td>

                `;


                videosTable.appendChild(row);

            }
        );


        if (videos.length === 0) {

            videosTable.innerHTML = `

                <tr>

                    <td
                        colspan="8"
                        style="
                            text-align:center;
                            padding:30px;
                            color:#94a3b8;
                        "
                    >

                        No videos found.

                    </td>

                </tr>

            `;

        }

    }


    renderVideos();


    searchInput.addEventListener(
        "input",
        renderVideos
    );


    sortSelect.addEventListener(
        "change",
        renderVideos
    );


    /* ========================================================
       DARK MODE
    ======================================================== */

    const themeToggle =
        document.getElementById("themeToggle");


    const savedTheme =
        localStorage.getItem("dashboard-theme");


    if (savedTheme === "dark") {

        document.body.classList.add("dark");

        themeToggle.textContent = "☀";

    }


    themeToggle.addEventListener(
        "click",
        function() {

            document.body.classList.toggle("dark");


            const dark =
                document.body.classList.contains("dark");


            themeToggle.textContent =
                dark ? "☀" : "☾";


            localStorage.setItem(
                "dashboard-theme",
                dark ? "dark" : "light"
            );

        }
    );


    /* ========================================================
       REFRESH
    ======================================================== */

    document.getElementById("refreshButton")
        .addEventListener(
            "click",
            function() {

                location.reload();

            }
        );


    /* ========================================================
       ACTIVE SIDEBAR LINK
    ======================================================== */

    const navItems =
        document.querySelectorAll(".nav-item");


    navItems.forEach(
        function(item) {

            item.addEventListener(
                "click",
                function() {

                    navItems.forEach(
                        function(nav) {

                            nav.classList.remove(
                                "active"
                            );

                        }
                    );


                    item.classList.add("active");

                }
            );

        }
    );


    console.log(
        "SocialPulse Dashboard loaded successfully."
    );

});