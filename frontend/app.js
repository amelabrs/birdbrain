/* ── BirdBrain — App Logic ────────────────────────────────────────── */

let currentMode = "photo";
let currentQuestion = null;
let answered = false;
let totalBirdCount = 0;
let autoPlaySound = localStorage.getItem("birdbrain_autoplay") !== "false"; // on by default
let resultAudio = null; // track auto-played sound for stopping

// Per-mode session tracking
let sessions = {
    photo: { bird: 0, total: 0, correct: 0, wrong: [], seen: new Set() },
    sound: { bird: 0, total: 0, correct: 0, wrong: [], seen: new Set() },
    reverse: { bird: 0, total: 0, correct: 0, wrong: [], seen: new Set() },
};

function getSession() { return sessions[currentMode]; }

// ── Bird data (for extra plumages / calls on the result screen) ──────
let birdDataMap = {};
let extraCallAudio = null;

async function loadBirdData() {
    try {
        const res = await fetch("/data/birds.json");
        const arr = await res.json();
        birdDataMap = Object.fromEntries(arr.map((b) => [b.id, b]));
    } catch (e) { /* extras are optional */ }
}

function sizedUrl(url, px) {
    if (!url) return url;
    url = url.replace(/[\u0000-\u001f]/g, "").trim();
    return url.replace(/(\/api\/v\d\/asset\/\d+)\/\d+$/, `$1/${px}`);
}

function renderExtras(birdId) {
    const plumesWrap = document.getElementById("result-plumes-wrap");
    const plumesEl = document.getElementById("result-plumes");
    const callsWrap = document.getElementById("result-calls-wrap");
    const callsEl = document.getElementById("result-calls");
    plumesEl.innerHTML = "";
    callsEl.innerHTML = "";
    plumesWrap.style.display = "none";
    callsWrap.style.display = "none";

    const bird = birdDataMap[birdId];
    if (!bird) return;

    const extras = (bird.extra_images || []).filter((e) => e.url);
    if (extras.length) {
        const main = document.createElement("div");
        main.className = "plume main";
        main.innerHTML = `<img src="${sizedUrl(bird.image_url, 480)}" alt=""><div class="cap">As shown</div>`;
        plumesEl.appendChild(main);
        extras.forEach((e) => {
            const d = document.createElement("div");
            d.className = "plume";
            d.innerHTML = `<img src="${sizedUrl(e.url, 480)}" alt=""><div class="cap">${e.label || ""}</div>`;
            plumesEl.appendChild(d);
        });
        plumesWrap.style.display = "block";
    }

    const calls = (bird.extra_sounds || []).filter((c) => c.url);
    if (calls.length) {
        calls.forEach((c, i) => {
            const btn = document.createElement("button");
            btn.className = "call-btn";
            btn.textContent = c.label || `Call ${i + 1}`;
            btn.onclick = () => {
                const wasPlaying = btn.classList.contains("playing");
                if (extraCallAudio) extraCallAudio.pause();
                document.querySelectorAll(".call-btn").forEach((x) => x.classList.remove("playing"));
                if (wasPlaying) return;
                extraCallAudio = new Audio(sizedUrl(c.url, 480));
                extraCallAudio.play().then(() => btn.classList.add("playing")).catch(() => {});
                extraCallAudio.onended = () => btn.classList.remove("playing");
            };
            callsEl.appendChild(btn);
        });
        callsWrap.style.display = "block";
    }
}


function toggleAutoPlay(checked) {
    autoPlaySound = checked;
    localStorage.setItem("birdbrain_autoplay", checked ? "true" : "false");
}

// ── Mode ────────────────────────────────────────────────────────────

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll(".mode-btn").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.mode === mode);
    });
    loadQuestion();
}

// ── Load Question ───────────────────────────────────────────────────

function stopAllAudio() {
    // Stop result audio (post-answer auto-play)
    if (resultAudio) {
        resultAudio.pause();
        resultAudio = null;
    }
    // Stop extra-call audio (plumage panel)
    if (extraCallAudio) {
        extraCallAudio.pause();
        extraCallAudio = null;
    }
    // Stop prompt audio (sound mode player)
    const player = document.getElementById("audio-player");
    if (player) {
        player.pause();
        player.currentTime = 0;
    }
}

async function loadQuestion() {
    stopAllAudio();
    const s = getSession();
    // Check if session is complete
    if (s.total > 0 && s.bird >= s.total) {
        showSessionSummary();
        return;
    }

    answered = false;
    showScreen("loading");

    try {
        const seen = Array.from(s.seen).join(",");
        const res = await fetch(`/api/question?mode=${currentMode}&seen=${encodeURIComponent(seen)}`);
        currentQuestion = await res.json();

        // Track pool size from backend
        s.total = currentQuestion.unlocked_count || s.total;
        totalBirdCount = currentQuestion.total_bird_count || s.total;

        // Track unique birds in session
        if (!s.seen.has(currentQuestion.bird_id)) {
            s.seen.add(currentQuestion.bird_id);
            s.bird = s.seen.size;
        }

        renderQuestion();
        showScreen("question-screen");
    } catch (err) {
        console.error("Failed to load question:", err);
        setTimeout(loadQuestion, 2000);
    }
}

function renderQuestion() {
    const q = currentQuestion;

    // Hide all prompt types
    document.getElementById("prompt-image-wrap").style.display = "none";
    document.getElementById("prompt-audio").style.display = "none";
    document.getElementById("prompt-text").style.display = "none";

    // Variant label
    const variantEl = document.getElementById("variant-label");
    if (q.variant_label) {
        variantEl.textContent = q.variant_label;
        variantEl.style.display = "block";
    } else {
        variantEl.style.display = "none";
    }

    // Show the right prompt
    if (q.prompt_type === "image") {
        const wrap = document.getElementById("prompt-image-wrap");
        const img = document.getElementById("prompt-image");
        const bgImg = document.getElementById("prompt-image-bg");
        img.src = q.prompt;
        bgImg.src = q.prompt;
        wrap.style.display = "block";
    } else if (q.prompt_type === "audio") {
        document.getElementById("prompt-audio").style.display = "block";
        const audio = document.getElementById("audio-player");
        audio.src = q.prompt;
        document.getElementById("play-sound-btn").textContent = "Play again";
        document.getElementById("play-sound-btn").classList.remove("playing");
        // Auto-play the sound prompt
        audio.play().then(() => {
            document.getElementById("play-sound-btn").textContent = "Playing\u2026";
            document.getElementById("play-sound-btn").classList.add("playing");
        }).catch(() => {});
        audio.onended = () => {
            document.getElementById("play-sound-btn").textContent = "Play again";
            document.getElementById("play-sound-btn").classList.remove("playing");
        };
    } else {
        document.getElementById("prompt-text").style.display = "block";
        document.getElementById("reverse-name").textContent = q.prompt;
    }

    // Render choices
    const choicesEl = document.getElementById("choices");
    choicesEl.innerHTML = "";
    choicesEl.classList.toggle("image-grid", q.mode === "reverse");

    q.choices.forEach((choice, i) => {
        const btn = document.createElement("button");
        btn.className = "choice-btn";

        if (q.mode === "reverse" && choice.image_url) {
            btn.className += " image-choice";
            btn.innerHTML = `<img src="${choice.image_url}" alt="Bird option">`;
        } else {
            btn.textContent = choice.label;
        }

        btn.onclick = () => submitAnswer(i);
        choicesEl.appendChild(btn);
    });
}

// ── Play Sound ──────────────────────────────────────────────────────

function playSound() {
    const audio = document.getElementById("audio-player");
    const btn = document.getElementById("play-sound-btn");

    if (audio.paused) {
        audio.play();
        btn.textContent = "Playing\u2026";
        btn.classList.add("playing");

        audio.onended = () => {
            btn.textContent = "Play again";
            btn.classList.remove("playing");
        };
    } else {
        audio.pause();
        audio.currentTime = 0;
        btn.textContent = "Play call";
        btn.classList.remove("playing");
    }
}

// ── Submit Answer ───────────────────────────────────────────────────

async function submitAnswer(chosenIndex) {
    if (answered) return;
    answered = true;

    const q = currentQuestion;
    const correct = chosenIndex === q.correct_index;

    // Highlight choices
    const buttons = document.querySelectorAll(".choice-btn");
    buttons.forEach((btn, i) => {
        if (i === q.correct_index) {
            btn.classList.add("correct");
        } else if (i === chosenIndex && !correct) {
            btn.classList.add("wrong");
        }
        if (i !== chosenIndex && i !== q.correct_index) {
            btn.classList.add("disabled");
        }
    });

    // Send to backend
    try {
        const res = await fetch("/api/answer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                bird_id: q.bird_id,
                chosen_index: chosenIndex,
                correct_index: q.correct_index,
            }),
        });
        const data = await res.json();

        // Track session score
        const s = getSession();
        if (correct) {
            s.correct++;
        } else {
            s.wrong.push(data.correct_name || currentQuestion.bird_id);
        }

        // Show result after brief pause
        setTimeout(() => showResult(data, correct), 800);
    } catch (err) {
        console.error("Failed to submit answer:", err);
        setTimeout(() => showResult({ streak: 0, box: 1, total_birds: getSession().total, total_rounds: 0 }, correct), 800);
    }
}

// ── Show Result ─────────────────────────────────────────────────────

function showResult(data, correct) {
    const iconEl = document.getElementById("result-icon");
    iconEl.classList.toggle("no", !correct);
    iconEl.innerHTML = correct
        ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';
    const titleEl = document.getElementById("result-title");
    titleEl.textContent = correct ? "Correct" : "Not quite";
    titleEl.classList.toggle("no", !correct);

    // Always show bird photo on result — reinforces the image-name link
    const resultImg = document.getElementById("result-image");
    if (data.image_url) {
        resultImg.src = data.image_url;
        resultImg.style.display = "block";
    } else {
        resultImg.style.display = "none";
    }

    document.getElementById("result-bird-name").textContent = data.correct_name || "";
    document.getElementById("result-scientific").textContent = data.scientific_name || "";
    document.getElementById("result-fact").textContent = data.fun_fact || "";

    // Show sound tip in sound mode
    const soundTipEl = document.getElementById("result-sound-tip");
    if (currentMode === "sound") {
        const tip = currentQuestion.variant_sound_tip || data.sound_tip;
        if (tip) {
            const prefix = currentQuestion.variant_label ? `${currentQuestion.variant_label}: ` : "";
            soundTipEl.textContent = `${prefix}${tip}`;
            soundTipEl.style.display = "block";
        } else {
            soundTipEl.style.display = "none";
        }
    } else {
        soundTipEl.style.display = "none";
    }

    // Show sound + eBird links after correct answer in photo/reverse modes
    const linksEl = document.getElementById("result-links");
    if (correct && (currentMode === "photo" || currentMode === "reverse")) {
        let linksHtml = "";
        if (data.sound_url) {
            if (autoPlaySound) {
                resultAudio = new Audio(data.sound_url);
                resultAudio.volume = 0.7;
                resultAudio.play().catch(() => {});
            }
            linksHtml += `<a href="${data.sound_url}" target="_blank" class="result-link">Listen to call</a>`;
        }
        if (data.ebird_code) {
            linksHtml += `<a href="https://ebird.org/species/${data.ebird_code}" target="_blank" class="result-link">eBird page</a>`;
        }
        if (linksHtml) {
            linksEl.innerHTML = linksHtml;
            linksEl.style.display = "flex";
        } else {
            linksEl.style.display = "none";
        }
    } else {
        linksEl.style.display = "none";
    }

    document.getElementById("result-habitat").textContent = data.habitat || "";
    document.getElementById("result-spots").textContent = data.karnataka_spots || "";

    // Show extra plumages (female / immature) + extra calls from birds.json
    try { renderExtras(currentQuestion.bird_id); } catch (e) {}

    // Update progress counter
    const s = getSession();
    document.getElementById("round-counter").textContent = `Bird ${s.bird} of ${s.total}`;

    showScreen("result-screen");
}

// ── Next Question ───────────────────────────────────────────────────

function nextQuestion() {
    stopAllAudio();
    loadQuestion();
}

// ── Session Summary ─────────────────────────────────────────────────

function showSessionSummary() {
    const s = getSession();
    const total = s.total;
    const pct = total > 0 ? Math.round((s.correct / total) * 100) : 0;

    let grade;
    if (pct >= 90) grade = "Excellent";
    else if (pct >= 70) grade = "Great round";
    else if (pct >= 50) grade = "Good effort";
    else grade = "Keep practising";

    let wrongHtml = "";
    if (s.wrong.length > 0) {
        wrongHtml = `<div class="needs-work" style="margin-top:16px;text-align:left">
            <strong>Review these</strong>${s.wrong.join(", ")}
        </div>`;
    }

    const lockHtml = s.total < totalBirdCount
        ? `<p class="summary-unlock">${s.total} of ${totalBirdCount} birds unlocked${pct >= 80 ? " \u00b7 scoring 80%+ unlocks more" : " \u00b7 score 80%+ to unlock more"}</p>`
        : `<p class="summary-unlock">All ${totalBirdCount} birds unlocked</p>`;

    const modeLabel = currentMode === "photo" ? "Photo" : currentMode === "sound" ? "Sound" : "Reverse";

    document.getElementById("summary-screen").innerHTML = `
        <div class="summary-eyebrow">Session complete \u00b7 ${modeLabel}</div>
        <h2>${grade}</h2>
        <div class="summary-score">${s.correct}<span>/${total}</span></div>
        <div class="summary-acc">${pct}% accuracy this round</div>
        ${wrongHtml}
        ${lockHtml}
        <div id="unlock-msg"></div>
        <button class="primary-btn" onclick="startNewSession()">New round</button>
    `;
    showScreen("summary-screen");

    // Check for unlocks
    checkUnlock(pct);
}

function startNewSession() {
    const s = getSession();
    s.bird = 0;
    s.correct = 0;
    s.wrong = [];
    s.seen = new Set();
    loadQuestion();
}

async function checkUnlock(pct) {
    try {
        const res = await fetch("/api/session-complete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ score_pct: pct }),
        });
        const data = await res.json();
        const msgEl = document.getElementById("unlock-msg");
        if (data.newly_unlocked > 0) {
            const s = getSession();
            s.total = data.unlocked_count;
            totalBirdCount = data.total_birds;
            msgEl.innerHTML = `<div class="unlock-banner">
                <b>${data.newly_unlocked} new bird${data.newly_unlocked > 1 ? 's' : ''} unlocked</b><br>
                <span style="color:var(--text-dim);font-size:12px">${data.unlocked_count} of ${data.total_birds} now available</span>
            </div>`;
        }
    } catch (err) {
        console.error("Failed to check unlock:", err);
    }
}

// ── Stats Panel ─────────────────────────────────────────────────────

async function toggleStats() {
    const panel = document.getElementById("stats-panel");
    if (panel.classList.contains("hidden")) {
        // Load stats
        try {
            const res = await fetch("/api/stats");
            const stats = await res.json();
            renderStats(stats);
        } catch (err) {
            console.error("Failed to load stats:", err);
        }
        panel.classList.remove("hidden");
    } else {
        panel.classList.add("hidden");
    }
}

function renderStats(stats) {
    document.getElementById("s-accuracy").textContent = `${stats.accuracy}%`;
    document.getElementById("s-mastered").textContent = stats.mastered;
    document.getElementById("s-rounds").textContent = stats.total_rounds;

    // Bird progress
    const listEl = document.getElementById("bird-progress-list");
    listEl.innerHTML = "";

    if (stats.birds) {
        // Sort: lowest box first
        const entries = Object.entries(stats.birds).sort((a, b) => a[1].box - b[1].box);

        // Identify birds that need work (box 1 with wrong > 0)
        const needsWork = entries.filter(([, b]) => b.box === 1 && b.wrong > 0);
        if (needsWork.length > 0) {
            const tipEl = document.createElement("div");
            tipEl.className = "needs-work";
            tipEl.innerHTML = `<strong>⚠️ Needs work:</strong> ${needsWork.map(([id]) => id.replace(/-/g, " ").replace(/\b\w/g, c => c.toUpperCase())).join(", ")}`;
            listEl.appendChild(tipEl);
        }

        for (const [birdId, bData] of entries) {
            const name = birdId.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
            const row = document.createElement("div");
            row.className = "bird-row";

            let boxes = "";
            for (let i = 1; i <= 4; i++) {
                boxes += `<div class="box-dot ${i <= bData.box ? "filled" : ""}"></div>`;
            }

            const total = bData.correct + bData.wrong;
            const pct = total > 0 ? Math.round((bData.correct / total) * 100) : 0;

            row.innerHTML = `
                <span class="bird-name">${name}</span>
                <div class="boxes">${boxes}</div>
                <span style="font-size:12px;color:var(--text-dim)">${pct}% (${bData.correct}✓ ${bData.wrong}✗)</span>
            `;
            listEl.appendChild(row);
        }
    }
}

async function resetProgress() {
    if (!confirm("Reset all progress? This cannot be undone.")) return;
    await fetch("/api/reset", { method: "POST" });
    toggleStats();
    startNewSession();
}

// ── Screen Management ───────────────────────────────────────────────

function showScreen(id) {
    document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
    document.getElementById(id).classList.add("active");
}

// ── Init ────────────────────────────────────────────────────────────

async function init() {
    // Restore toggle states
    const apToggle = document.getElementById("autoplay-toggle");
    if (apToggle) apToggle.checked = autoPlaySound;

    // Show deploy timestamp
    try {
        const res = await fetch("/api/version");
        const v = await res.json();
        document.getElementById("build-stamp").textContent = v.deploy_time;
    } catch (e) {}

    await loadBirdData();
    loadQuestion();
}

init();
