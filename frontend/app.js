/* ── BirdBrain — App Logic ────────────────────────────────────────── */

let currentMode = "photo";
let currentQuestion = null;
let answered = false;
let sessionBird = 0;
let sessionTotal = 0;
let sessionCorrect = 0;
let sessionWrong = [];
let sessionSeen = new Set();

// ── Mode ────────────────────────────────────────────────────────────

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll(".mode-btn").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.mode === mode);
    });
    if (!answered) loadQuestion();
}

// ── Load Question ───────────────────────────────────────────────────

async function loadQuestion() {
    // Check if session is complete
    if (sessionTotal > 0 && sessionBird >= sessionTotal) {
        showSessionSummary();
        return;
    }

    answered = false;
    showScreen("loading");

    try {
        const seen = Array.from(sessionSeen).join(",");
        const res = await fetch(`/api/question?mode=${currentMode}&seen=${encodeURIComponent(seen)}`);
        currentQuestion = await res.json();

        // Track unique birds in session
        if (!sessionSeen.has(currentQuestion.bird_id)) {
            sessionSeen.add(currentQuestion.bird_id);
            sessionBird = sessionSeen.size;
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
    document.getElementById("prompt-image").style.display = "none";
    document.getElementById("prompt-audio").style.display = "none";
    document.getElementById("prompt-text").style.display = "none";

    // Show the right prompt
    if (q.prompt_type === "image") {
        const img = document.getElementById("prompt-image");
        img.src = q.prompt;
        img.style.display = "block";
    } else if (q.prompt_type === "audio") {
        document.getElementById("prompt-audio").style.display = "block";
        const audio = document.getElementById("audio-player");
        audio.src = q.prompt;
        document.getElementById("play-sound-btn").textContent = "▶ Play Bird Call";
        document.getElementById("play-sound-btn").classList.remove("playing");
    } else {
        document.getElementById("prompt-text").style.display = "block";
        document.getElementById("reverse-name").textContent = q.prompt;
    }

    // Render choices
    const choicesEl = document.getElementById("choices");
    choicesEl.innerHTML = "";

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
        btn.textContent = "⏸ Playing...";
        btn.classList.add("playing");

        audio.onended = () => {
            btn.textContent = "▶ Play Again";
            btn.classList.remove("playing");
        };
    } else {
        audio.pause();
        audio.currentTime = 0;
        btn.textContent = "▶ Play Bird Call";
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
        if (correct) {
            sessionCorrect++;
        } else {
            sessionWrong.push(data.correct_name || currentQuestion.bird_id);
        }
        sessionTotal = data.total_birds || 24;

        // Update header stats
        document.getElementById("streak").textContent = data.streak;
        document.getElementById("accuracy").textContent = data.accuracy;

        // Show result after brief pause
        setTimeout(() => showResult(data, correct), 800);
    } catch (err) {
        console.error("Failed to submit answer:", err);
        setTimeout(() => showResult({ streak: 0, box: 1, mastered: 0, total_birds: 20, total_rounds: 0 }, correct), 800);
    }
}

// ── Show Result ─────────────────────────────────────────────────────

function showResult(data, correct) {
    document.getElementById("result-icon").textContent = correct ? "✅" : "❌";
    document.getElementById("result-title").textContent = correct ? "Correct!" : "Not quite!";
    document.getElementById("result-bird-name").textContent = data.correct_name || "";
    document.getElementById("result-scientific").textContent = data.scientific_name || "";
    document.getElementById("result-fact").textContent = `💡 ${data.fun_fact || ""}`;

    // Show sound tip in sound mode
    const soundTipEl = document.getElementById("result-sound-tip");
    if (currentMode === "sound" && data.sound_tip) {
        soundTipEl.textContent = `🎵 Remember: ${data.sound_tip}`;
        soundTipEl.style.display = "block";
    } else {
        soundTipEl.style.display = "none";
    }

    document.getElementById("result-habitat").textContent = data.habitat ? `🌿 ${data.habitat}` : "";
    document.getElementById("result-spots").textContent = data.karnataka_spots ? `📍 ${data.karnataka_spots}` : "";
    document.getElementById("res-streak").textContent = data.streak;
    document.getElementById("res-box").textContent = data.box;

    // Update progress counter
    const total = data.total_birds || 24;
    document.getElementById("mastery-fill").style.width = `${(sessionBird / total) * 100}%`;
    document.getElementById("mastery-label").textContent = `${mastered}/${total} mastered`;
    document.getElementById("round-counter").textContent = `Bird ${sessionBird} of ${total}`;

    showScreen("result-screen");
}

// ── Next Question ───────────────────────────────────────────────────

function nextQuestion() {
    loadQuestion();
}

// ── Session Summary ─────────────────────────────────────────────────

function showSessionSummary() {
    const total = sessionTotal;
    const pct = total > 0 ? Math.round((sessionCorrect / total) * 100) : 0;

    let grade, emoji;
    if (pct >= 90) { grade = "Excellent!"; emoji = "🏆"; }
    else if (pct >= 70) { grade = "Great job!"; emoji = "🌟"; }
    else if (pct >= 50) { grade = "Good effort!"; emoji = "👍"; }
    else { grade = "Keep practising!"; emoji = "💪"; }

    let wrongHtml = "";
    if (sessionWrong.length > 0) {
        wrongHtml = `<div class="needs-work" style="margin-top:12px;text-align:left">
            <strong>⚠️ Work on these:</strong><br>${sessionWrong.join(", ")}
        </div>`;
    }

    document.getElementById("summary-screen").innerHTML = `
        <div style="font-size:48px;margin-bottom:8px">${emoji}</div>
        <h2>${grade}</h2>
        <p style="font-size:32px;font-weight:bold;color:var(--primary);margin:12px 0">${sessionCorrect}/${total}</p>
        <p style="color:var(--text-dim);margin-bottom:8px">${pct}% accuracy this session</p>
        ${wrongHtml}
        <button class="primary-btn" style="margin-top:20px" onclick="startNewSession()">Play Again →</button>
    `;
    showScreen("summary-screen");
}

function startNewSession() {
    sessionBird = 0;
    sessionCorrect = 0;
    sessionWrong = [];
    sessionSeen = new Set();
    loadQuestion();
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
    document.getElementById("s-streak").textContent = stats.best_streak;
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
    document.getElementById("streak").textContent = "0";
    document.getElementById("accuracy").textContent = "0";
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
    // Load initial stats
    try {
        const res = await fetch("/api/stats");
        const stats = await res.json();
        document.getElementById("streak").textContent = stats.current_streak;
        document.getElementById("accuracy").textContent = stats.accuracy;
    } catch (err) {
        // ignore
    }

    loadQuestion();
}

init();
