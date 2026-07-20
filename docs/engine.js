/* ── BirdBrain Engine — JS port of backend/spaced_rep.py + backend/quiz.py ── */

const BirdEngine = (() => {
    const STORAGE_KEY = "birdbrain_progress";
    const BOX_INTERVALS = { 1: 1, 2: 3, 3: 5, 4: 10 };
    const VARIANT_CHANCE = 0.3;

    let _birds = [];
    let _birdMap = {};
    let _soundIds = [];
    let _state = null;

    // ── Persistence ──────────────────────────────────────────────────

    function _load() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (raw) return JSON.parse(raw);
        } catch (e) {}
        return _fresh();
    }

    function _fresh() {
        return {
            round: 0,
            birds: {},
            history: [],
            stats: { total_correct: 0, total_wrong: 0, best_streak: 0, current_streak: 0 },
        };
    }

    function _save() {
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(_state)); } catch (e) {}
    }

    // ── State helpers ─────────────────────────────────────────────────

    function _ensureBird(id) {
        if (!_state.birds[id]) {
            _state.birds[id] = { box: 1, correct_streak: 0, total_correct: 0, total_wrong: 0, last_seen_round: 0 };
        }
        return _state.birds[id];
    }

    // ── Bird picking (port of SpacedRepetition.pick_bird) ─────────────

    function _pickBird(ids) {
        const round = _state.round;
        ids.forEach(id => _ensureBird(id));

        const eligible = [];
        for (const id of ids) {
            const b = _state.birds[id];
            const interval = BOX_INTERVALS[b.box] || 10;
            if (round - b.last_seen_round >= interval) {
                eligible.push([id, Math.pow(5 - b.box, 2)]);
            }
        }

        if (!eligible.length) {
            // All seen recently — pick most overdue
            const overdue = ids.map(id => {
                const b = _state.birds[id];
                const interval = BOX_INTERVALS[b.box] || 10;
                return [id, (round - b.last_seen_round) / interval];
            });
            overdue.sort((a, b) => b[1] - a[1]);
            const top = overdue.slice(0, Math.max(3, Math.floor(overdue.length / 4)));
            return top[Math.floor(Math.random() * top.length)][0];
        }

        // Weighted random
        const total = eligible.reduce((s, [, w]) => s + w, 0);
        let r = Math.random() * total;
        for (const [id, w] of eligible) {
            r -= w;
            if (r <= 0) return id;
        }
        return eligible[eligible.length - 1][0];
    }

    // ── Variant picking (port of quiz._pick_image / _pick_sound) ──────

    function _pickImage(bird) {
        const extras = (bird.extra_images || []).filter(e => e.url);
        if (extras.length && Math.random() < VARIANT_CHANCE) {
            const v = extras[Math.floor(Math.random() * extras.length)];
            return [v.url, v.label || null];
        }
        return [bird.image_url, null];
    }

    function _pickSound(bird) {
        const extras = bird.extra_sounds || [];
        if (extras.length && Math.random() < VARIANT_CHANCE) {
            const v = extras[Math.floor(Math.random() * extras.length)];
            return [v.url, v.label || null, v.tip || null];
        }
        return [bird.sound_url || "", null, null];
    }

    // ── Shuffle ───────────────────────────────────────────────────────

    function _shuffle(arr) {
        for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
        return arr;
    }

    // ── Question generation (port of quiz.generate_question) ──────────

    function _generateQuestion(target, mode) {
        const others = _birds.filter(b => b.id !== target.id);
        const pool = [...others];
        const distractors = [];
        for (let i = 0; i < 3 && pool.length; i++) {
            const idx = Math.floor(Math.random() * pool.length);
            distractors.push(pool.splice(idx, 1)[0]);
        }

        if (mode === "reverse") {
            const choices = _shuffle([
                { label: target.name, image_url: target.image_url, id: target.id },
                ...distractors.map(d => ({ label: d.name, image_url: d.image_url, id: d.id })),
            ]);
            return {
                mode: "reverse",
                prompt: target.name,
                prompt_type: "text",
                choices,
                correct_index: choices.findIndex(c => c.id === target.id),
                bird_id: target.id,
                fun_fact: target.fun_fact || "",
                unlocked_count: _birds.length,
                total_bird_count: _birds.length,
            };
        }

        const choices = _shuffle([
            { label: target.name, id: target.id },
            ...distractors.map(d => ({ label: d.name, id: d.id })),
        ]);
        const correct_index = choices.findIndex(c => c.id === target.id);

        let prompt, variantLabel = null, variantTip = null, prompt_type;
        if (mode === "sound") {
            [prompt, variantLabel, variantTip] = _pickSound(target);
            prompt_type = "audio";
        } else {
            [prompt, variantLabel] = _pickImage(target);
            prompt_type = "image";
        }

        const q = {
            mode, prompt, prompt_type, choices, correct_index,
            bird_id: target.id, fun_fact: target.fun_fact || "",
            unlocked_count: _birds.length, total_bird_count: _birds.length,
        };
        if (variantLabel) q.variant_label = variantLabel;
        if (mode === "sound" && variantTip) q.variant_sound_tip = variantTip;
        return q;
    }

    // ── Public API (mirrors /api/ endpoints) ──────────────────────────

    function init(birds) {
        _birds = birds;
        _birdMap = Object.fromEntries(birds.map(b => [b.id, b]));
        _soundIds = birds.filter(b => b.sound_url).map(b => b.id);
        _state = _load();
    }

    function getQuestion(mode, overrideIds) {
        let ids = overrideIds
            ? (mode === "sound"
                ? overrideIds.filter(id => _birdMap[id]?.sound_url)
                : overrideIds.filter(id => !!_birdMap[id]))
            : (mode === "sound" ? _soundIds : _birds.map(b => b.id));
        if (!ids.length) ids = mode === "sound" ? _soundIds : _birds.map(b => b.id);
        const id = _pickBird(ids);
        const q = _generateQuestion(_birdMap[id], mode);
        q.unlocked_count = ids.length;
        q.total_bird_count = ids.length;
        return q;
    }

    function submitAnswer(birdId, chosenIndex, correctIndex) {
        const correct = chosenIndex === correctIndex;
        _state.round++;
        const b = _ensureBird(birdId);
        b.last_seen_round = _state.round;
        const st = _state.stats;

        if (correct) {
            b.correct_streak++;
            b.total_correct++;
            st.total_correct++;
            st.current_streak++;
            if (st.current_streak > st.best_streak) st.best_streak = st.current_streak;
            if (b.box < 4) b.box++;
        } else {
            b.correct_streak = 0;
            b.total_wrong++;
            st.total_wrong++;
            st.current_streak = 0;
            b.box = 1;
        }

        _state.history.push({ bird_id: birdId, correct, round: _state.round, ts: Date.now() });
        _state.history = _state.history.slice(-50);
        _save();

        const bird = _birdMap[birdId] || {};
        const total = st.total_correct + st.total_wrong;
        return {
            correct,
            correct_name: bird.name || "",
            image_url: bird.image_url || "",
            fun_fact: bird.fun_fact || "",
            sound_tip: bird.sound_tip || "",
            scientific_name: bird.scientific_name || "",
            habitat: bird.habitat || "",
            karnataka_spots: bird.karnataka_spots || "",
            sound_url: bird.sound_url || "",
            ebird_code: bird.ebird_code || "",
            box: b.box,
            streak: st.current_streak,
            best_streak: st.best_streak,
            accuracy: total ? Math.round(st.total_correct / total * 100) : 0,
            total_rounds: _state.round,
            mastered: Object.values(_state.birds).filter(v => v.box >= 4).length,
            total_birds: _birds.length,
        };
    }

    function getStats() {
        const st = _state.stats;
        const total = st.total_correct + st.total_wrong;
        return {
            total_rounds: _state.round,
            accuracy: total ? Math.round(st.total_correct / total * 100) : 0,
            current_streak: st.current_streak,
            best_streak: st.best_streak,
            mastered: Object.values(_state.birds).filter(v => v.box >= 4).length,
            learning: Object.values(_state.birds).filter(v => v.box >= 2 && v.box <= 3).length,
            new: Object.values(_state.birds).filter(v => v.box === 1).length,
            total_birds: _birds.length,
            birds: Object.fromEntries(
                Object.entries(_state.birds).map(([id, v]) => [id, { box: v.box, correct: v.total_correct, wrong: v.total_wrong }])
            ),
        };
    }

    function sessionComplete() {
        return { unlocked_count: _birds.length, total_birds: _birds.length, newly_unlocked: 0 };
    }

    function reset() {
        _state = _fresh();
        _save();
    }

    return { init, getQuestion, submitAnswer, getStats, sessionComplete, reset };
})();
