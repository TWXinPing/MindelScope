(() => {
  try {
  const CYCLE_DT = 0.18;
  const MASS = 1;
  const KP = 9;
  const KD = 5;
  const SIGMA = 0.045;
  const LR_A = 0.04;
  const LR_W = 3.2;
  const X0 = 0.04;
  const TARGET = 1;

  const MODS = [
    { id: "air", a: 0, w: 0 },
    { id: "viscous", a: 7, w: 7 },
  ];

  const STORY = [
    {
      b: 0,
      ct: "air",
      caption: "Air: the mug is in free space. Inverse 1’s motor command fits; Forward 1’s held prediction matches the next current state.",
    },
    {
      b: 11,
      ct: "viscous",
      caption: "Viscous: like reaching through water or honey. Forward 1’s held x̂_t+1 misses the next current x_t+1; that error switches λ onto module 2.",
    },
    {
      b: 0,
      ct: "air",
      caption: "The medium is gone. Module 1 was not overwritten, so λ can switch back — the old skill is still there.",
    },
  ];

  const INFO = {
    desired: {
      title: "desired state x*",
      body: "The intended hand position. Copied into every inverse model.",
      eq: "x* → Inverse",
    },
    inv1: {
      title: "Inverse 1 (air controller)",
      body: "Takes desired state and current state; emits motor command u₁ assuming no damping.",
      eq: "u₁ = a*(x*, x) + â₁ v",
    },
    inv2: {
      title: "Inverse 2 (viscous controller)",
      body: "Same inputs, but the motor command already compensates for damping.",
      eq: "u₂ = a*(x*, x) + â₂ v",
    },
    gate: {
      title: "λ mix",
      body: "The two motor commands are not averaged blindly. λ scales each contribution.",
      eq: "u = λ₁ u₁ + λ₂ u₂",
    },
    plant: {
      title: "Plant",
      body: "The real arm and world. Receives mixed motor command u and context c_t; produces the next actual state x_t+1.",
      eq: "x_t+1 = f(x_t, u_t, c_t)",
    },
    context: {
      title: "context c_t",
      body: "The movement’s world at time t (air vs viscous medium). It changes the plant, not the internal models. Forward models never receive c_t; they infer context from prediction error.",
      eq: "x_t+1 = f(x_t, u_t, c_t)  —  c_t → Plant only",
    },
    next: {
      title: "next current state x_t+1",
      body: "The plant’s outcome. It is sent at the same time to the forward models (as the new current input) and to the comparators (to score the held prediction).",
      eq: "x_t+1 → Forward and Comparator",
    },
    current: {
      title: "current state x_t",
      body: "Where the hand is now. Input to Inverse and Forward. It is not subtracted from the prediction until it has become the next current state.",
      eq: "x_t → Inverse, Forward",
    },
    fwd1: {
      title: "Forward 1",
      body: "Takes motor command u_t and current state x_t; predicts the next hand position if the world is air.",
      eq: "x̂₁_t+1 = f₁(x_t, u_t; ŵ₁)",
    },
    fwd2: {
      title: "Forward 2",
      body: "Same inputs; predicts as if the world is viscous.",
      eq: "x̂₂_t+1 = f₂(x_t, u_t; ŵ₂)",
    },
    delay1: {
      title: "delay (hold x̂₁)",
      body: "The prediction is made at time t but must wait. Paper Fig. 1: the predicted next state is delayed so it can meet the actual next state.",
      eq: "x̂₁_t+1 held until x_t+1 arrives",
    },
    delay2: {
      title: "delay (hold x̂₂)",
      body: "Same hold for Forward 2’s prediction. Without this wait, the figure would look as if x̂ were compared with the same x_t that produced it.",
      eq: "x̂₂_t+1 held until x_t+1 arrives",
    },
    cmp1: {
      title: "prediction error e₁",
      body: "Next current state minus the held prediction from Forward 1. Large error lowers that module’s responsibility.",
      eq: "e₁ = x_t+1 − x̂₁_t+1",
    },
    cmp2: {
      title: "prediction error e₂",
      body: "Next current state minus the held prediction from Forward 2.",
      eq: "e₂ = x_t+1 − x̂₂_t+1",
    },
    lambda: {
      title: "responsibility λ",
      body: "Turns prediction errors into a belief over which world is current. That belief gates the inverse mix and which forward model is trusted / updated.",
      eq: "λᵢ ∝ exp(−eᵢ² / σ²)",
    },
    predictor: {
      title: "responsibility predictor",
      body: "In the paper, sensory cues y_t (object look, a tone) drive a prior over modules before movement. That is not the true c_t, which acts only on the plant. Not run here.",
      eq: "λ_prior = h(y_t) — not in this implementation",
    },
  };

  const MESSAGES = [
    {
      id: "des_inv",
      paths: ["p_des_inv1", "p_des_inv2"],
      nodes: ["desired", "inv1", "inv2"],
      step: "Desired state → inverse models",
      model: "x* is copied into Inverse 1 and Inverse 2 so each can compute a motor command toward the target.",
      human: "You decide the mug handle is where the fingertip should be. That intention is the desired state.",
    },
    {
      id: "x_inv",
      paths: ["p_x_inv1", "p_x_inv2"],
      nodes: ["current", "inv1", "inv2"],
      step: "Current state → inverse models",
      model: "The same inverses also receive current state x_t (and velocity), because the command depends on where the hand is now.",
      human: "You also feel the arm’s posture. Without that, you would not know how large a command is needed.",
    },
    {
      id: "inv_u",
      paths: ["p_inv1_gate", "p_inv2_gate"],
      nodes: ["inv1", "inv2", "gate"],
      step: "Inverse models → motor commands",
      model: "Each inverse emits its own motor command u₁, u₂. They are proposals, not the final descending signal yet.",
      human: "Two internal controllers each suggest how hard to push — one tuned to air, one to a heavy/viscous object.",
    },
    {
      id: "lam_gate",
      paths: ["p_lam_gate"],
      nodes: ["lambda", "gate"],
      step: "Responsibility λ → mix",
      model: "λ scales the two motor commands before they are added: u = λ₁ u₁ + λ₂ u₂.",
      human: "If this already feels like moving through honey, you lean on the viscous controller instead of the air one.",
    },
    {
      id: "u_plant",
      paths: ["p_gate_plant"],
      nodes: ["gate", "plant"],
      step: "Mixed motor command → plant",
      model: "The mixed u is the signal that actually drives the arm.",
      human: "Muscles receive a single command. You do not fire both controllers at full strength.",
    },
    {
      id: "ctx_plant",
      paths: ["p_c_plant"],
      nodes: ["context", "plant"],
      step: "Context c_t → plant",
      model: "Paper Eq. (4): x_t+1 = f(x_t, u_t, c_t). Context (air vs viscous) changes the plant only. Forward models do not receive c_t; they infer it later from prediction error.",
      human: "The world is air or honey. That fact is not written on a label you can read before you move — unless a cue like ‘it looks metallic’ is available (the paper’s responsibility predictor, not run here).",
    },
    {
      id: "xu_fwd",
      paths: ["p_x_fwd1", "p_x_fwd2", "p_u_fwd1", "p_u_fwd2"],
      nodes: ["current", "gate", "fwd1", "fwd2"],
      step: "Motor command u_t + current x_t → forward models",
      model: "Each forward model receives the issued u_t and current x_t. This is the start of a forward cycle — not yet a comparison.",
      human: "Before the new sensation arrives, you take the command you just sent and the posture you feel now, and ask what should happen next.",
    },
    {
      id: "pred_hold",
      paths: ["p_fwd1_delay1", "p_fwd2_delay2"],
      nodes: ["fwd1", "fwd2", "delay1", "delay2"],
      step: "Forward models → hold predicted next state",
      model: "Each forward model emits x̂_t+1, the predicted next current state. That guess is delayed: it waits in the hold until the actual next current state exists.",
      human: "You commit to a guess — ‘if this is still air, the fingertip should be here’ — and keep it until the next feeling arrives.",
    },
    {
      id: "plant_next",
      paths: ["p_plant_next", "p_next_current"],
      nodes: ["plant", "next", "current"],
      step: "Plant → next current state x_t+1",
      model: "The world responds with the actual next state x_t+1. That value is the next current state.",
      human: "The arm moves. If you dipped into water, the felt position is the new current state — later than the prediction you already made.",
    },
    {
      id: "next_arrive",
      paths: ["p_next_fwd1", "p_next_fwd2", "p_next_cmp1", "p_next_cmp2", "p_delay1_cmp1", "p_delay2_cmp2"],
      nodes: ["next", "fwd1", "fwd2", "delay1", "delay2", "cmp1", "cmp2"],
      step: "Next current x_t+1 → forward models and comparators",
      model: "The same x_t+1 is copied two ways at once: into the forward models as the new current input, and into the comparators to be subtracted from the held x̂_t+1. Error is e = x_t+1 − x̂_t+1, never x_t − x̂.",
      human: "The next felt position updates what you will predict from, and at the same instant is checked against the guess you were holding.",
    },
    {
      id: "err_lam",
      paths: ["p_e1_lam", "p_e2_lam"],
      nodes: ["cmp1", "cmp2", "lambda"],
      step: "Prediction error → responsibility λ",
      model: "Errors become a distribution: λᵢ ∝ exp(−eᵢ²/σ²). That belief will gate both the inverse mix and the forward models.",
      human: "The brain updates which context it thinks it is in, so the next command and the next predictor can come from the matching skill.",
    },
    {
      id: "lam_fwd",
      paths: ["p_lam_fwd1", "p_lam_fwd2"],
      nodes: ["lambda", "fwd1", "fwd2"],
      step: "λ gates / updates forward models",
      model: "λ scales which forward model is trusted, then gates learning: Δŵᵢ ∝ λᵢ (x̂ᵢ − x_t+1). The module that predicted well (high λ) takes the larger parameter step.",
      human: "The predictor that guessed well is allowed to keep speaking — and to adjust itself. The one that missed is turned down.",
    },
  ];

  const CYCLES = {
    inverse: ["des_inv", "x_inv", "inv_u", "lam_gate", "u_plant", "ctx_plant", "plant_next"],
    forward: ["xu_fwd", "pred_hold", "plant_next", "next_arrive", "err_lam", "lam_fwd"],
  };

  const TOKEN_PATHS = [
    { id: "p_des_inv1", cls: "t1" },
    { id: "p_des_inv2", cls: "t2" },
    { id: "p_x_inv1", cls: "t1" },
    { id: "p_x_inv2", cls: "t2" },
    { id: "p_inv1_gate", cls: "t1", mod: 0 },
    { id: "p_inv2_gate", cls: "t2", mod: 1 },
    { id: "p_gate_plant", cls: "" },
    { id: "p_c_plant", cls: "" },
    { id: "p_plant_next", cls: "" },
    { id: "p_next_current", cls: "" },
    { id: "p_x_fwd1", cls: "t1" },
    { id: "p_x_fwd2", cls: "t2" },
    { id: "p_u_fwd1", cls: "t1" },
    { id: "p_u_fwd2", cls: "t2" },
    { id: "p_fwd1_delay1", cls: "t1", mod: 0 },
    { id: "p_fwd2_delay2", cls: "t2", mod: 1 },
    { id: "p_delay1_cmp1", cls: "t1", mod: 0 },
    { id: "p_delay2_cmp2", cls: "t2", mod: 1 },
    { id: "p_next_cmp1", cls: "" },
    { id: "p_next_cmp2", cls: "" },
    { id: "p_next_fwd1", cls: "t1" },
    { id: "p_next_fwd2", cls: "t2" },
    { id: "p_e1_lam", cls: "t1", mod: 0 },
    { id: "p_e2_lam", cls: "t2", mod: 1 },
    { id: "p_lam_fwd1", cls: "t1", mod: 0 },
    { id: "p_lam_fwd2", cls: "t2", mod: 1 },
    { id: "p_lam_gate", cls: "" },
  ];

  const PATH_TO_MSG = {};
  MESSAGES.forEach((m) => m.paths.forEach((p) => { PATH_TO_MSG[p] = m.id; }));

  const state = {
    x: X0,
    xIn: X0,
    xNext: X0,
    v: 0,
    vIn: 0,
    lam: [0.55, 0.45],
    pred: [X0, X0],
    err: [0, 0],
    u: [0, 0],
    uMix: 0,
    predV: 0,
    predU: 0,
    phase: 0,
    t: 0,
    pendingNext: false,
    playing: false,
    cycleKind: null,
    cycleGen: 0,
    tokenT: 0,
    msgIndex: 0,
    sending: false,
  };

  const $ = (id) => document.getElementById(id);

  function inputState() {
    if (state.pendingNext) return { x: state.xIn, v: state.vIn };
    return { x: state.x, v: state.v };
  }

  function computeInverse() {
    const { x, v } = inputState();
    if (!state.pendingNext) {
      state.xIn = x;
      state.vIn = v;
    }
    const aStar = KP * (TARGET - x) + KD * (0 - v);
    state.u = MODS.map((m) => aStar + m.a * v);
    state.uMix = state.lam[0] * state.u[0] + state.lam[1] * state.u[1];
  }

  function predictForward() {
    const x = state.xIn;
    const v = state.vIn;
    const u = state.uMix;
    state.predV = v;
    state.predU = u;
    state.pred = MODS.map((m) => {
      const aHat = (u - m.w * v) / MASS;
      return x + (v + aHat * CYCLE_DT) * CYCLE_DT;
    });
  }

  function stepPlant() {
    const bWorld = STORY[state.phase].b;
    const v = state.vIn;
    const x = state.xIn;
    const a = (state.uMix - bWorld * v) / MASS;
    state.v = v + a * CYCLE_DT;
    state.x = x + state.v * CYCLE_DT;
    if (state.x < 0) {
      state.x = 0;
      state.v = 0;
    }
    state.xNext = state.x;
    state.t += CYCLE_DT;
    state.pendingNext = true;
  }

  function updateLambda() {
    state.err = state.pred.map((p) => state.xNext - p);
    const like = state.err.map((e) => Math.exp(-(e * e) / (SIGMA * SIGMA)));
    const z = like[0] + like[1] || 1;
    const raw = [like[0] / z, like[1] / z];
    state.lam = state.lam.map((l, i) => l * 0.65 + raw[i] * 0.35);
    const s = state.lam[0] + state.lam[1];
    state.lam = [state.lam[0] / s, state.lam[1] / s];
  }

  function clamp(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v));
  }

  function updateInverse() {
    const ufb = KP * (TARGET - state.xNext) + KD * (0 - state.v);
    const grad = state.vIn !== 0 ? state.vIn : state.v;
    MODS.forEach((m, i) => {
      m.a = clamp(m.a + LR_A * state.lam[i] * ufb * grad, -2, 16);
    });
  }

  function updateForward() {
    MODS.forEach((m, i) => {
      const miss = state.pred[i] - state.xNext;
      m.w = clamp(m.w + LR_W * state.lam[i] * miss, -2, 16);
    });
  }

  function applyCycleStep(id, kind) {
    if (id === "inv_u" || id === "lam_gate" || id === "u_plant") computeInverse();
    if (id === "xu_fwd") computeInverse();
    if (id === "pred_hold") predictForward();
    if (id === "plant_next") {
      if (kind === "inverse") {
        state.pendingNext = false;
        computeInverse();
        stepPlant();
        updateInverse();
      } else if (!state.pendingNext) {
        computeInverse();
        stepPlant();
      }
    }
    if (id === "next_arrive") {
      state.err = state.pred.map((p) => state.xNext - p);
      state.xIn = state.xNext;
      state.vIn = state.v;
    }
    if (id === "err_lam") updateLambda();
    if (id === "lam_fwd") {
      updateForward();
      state.pendingNext = false;
    }
  }

  function resetReach() {
    state.x = X0;
    state.v = 0;
    state.t = 0;
    state.xIn = X0;
    state.xNext = X0;
    state.vIn = 0;
    state.pred = [X0, X0];
    state.err = [0, 0];
    state.pendingNext = false;
  }

  function miniX(x) {
    return 40 + Math.max(0, Math.min(1.05, x)) * 240;
  }

  function drawFlow() {
    $("vDes").textContent = `x* = ${TARGET.toFixed(2)}`;
    $("vX").textContent = `x_t = ${state.xIn.toFixed(2)}`;
    $("vXnext").textContent = `x_t+1 = ${state.xNext.toFixed(2)}`;
    $("vP1").textContent = `x̂₁ = ${state.pred[0].toFixed(2)}  ŵ = ${MODS[0].w.toFixed(2)}`;
    $("vP2").textContent = `x̂₂ = ${state.pred[1].toFixed(2)}  ŵ = ${MODS[1].w.toFixed(2)}`;
    $("vD1").textContent = `hold ${state.pred[0].toFixed(2)}`;
    $("vD2").textContent = `hold ${state.pred[1].toFixed(2)}`;
    $("vU").textContent = `u = ${state.uMix.toFixed(2)}`;
    $("vU1").textContent = `u₁ = ${state.u[0].toFixed(2)}  â = ${MODS[0].a.toFixed(2)}`;
    $("vU2").textContent = `u₂ = ${state.u[1].toFixed(2)}  â = ${MODS[1].a.toFixed(2)}`;
    $("vCt").textContent = STORY[state.phase].ct;
    $("vE1").textContent = state.err[0].toFixed(3);
    $("vE2").textContent = state.err[1].toFixed(3);
    $("vL1").textContent = `λ₁ air = ${state.lam[0].toFixed(2)}`;
    $("vL2").textContent = `λ₂ viscous = ${state.lam[1].toFixed(2)}`;
    $("lamFill1").setAttribute("width", String(140 * state.lam[0]));
    $("miniHand").setAttribute("cx", miniX(state.xNext));
    $("miniPred1").setAttribute("cx", miniX(state.pred[0]));
    $("miniPred1").setAttribute("opacity", String(0.3 + 0.7 * state.lam[0]));
    $("miniPred2").setAttribute("cx", miniX(state.pred[1]));
    $("miniPred2").setAttribute("opacity", String(0.3 + 0.7 * state.lam[1]));
    $("viscousMini").setAttribute("opacity", STORY[state.phase].b > 0 ? "1" : "0");
    document.querySelectorAll('[data-id="inv1"], [data-id="fwd1"], [data-id="cmp1"], [data-id="delay1"]').forEach((el) => {
      el.classList.toggle("dim", state.lam[0] < 0.34);
    });
    document.querySelectorAll('[data-id="inv2"], [data-id="fwd2"], [data-id="cmp2"], [data-id="delay2"]').forEach((el) => {
      el.classList.toggle("dim", state.lam[1] < 0.34);
    });
    document.querySelectorAll(".edge.e1, .elbl.e1").forEach((el) => {
      el.classList.toggle("dim", state.lam[0] < 0.34);
    });
    document.querySelectorAll(".edge.e2, .elbl.e2").forEach((el) => {
      el.classList.toggle("dim", state.lam[1] < 0.34);
    });
    $("caption").textContent = STORY[state.phase].caption;
    document.querySelectorAll(".beats li").forEach((li) => {
      li.classList.toggle("active", Number(li.dataset.phase) === state.phase);
    });
  }

  function showMessage(msg, cycle) {
    const seq = cycle
      ? CYCLES[cycle].map((id) => MESSAGES.find((m) => m.id === id))
      : MESSAGES;
    const idx = Math.max(0, seq.findIndex((m) => m.id === msg.id));
    const label = cycle === "forward" ? "Forward cycle" : cycle === "inverse" ? "Inverse cycle" : "Message";
    $("stepLabel").textContent = `${label} ${idx + 1} of ${seq.length}: ${msg.step}`;
    $("inModel").textContent = msg.model;
    $("inHuman").textContent = msg.human;
    document.querySelectorAll(".edge").forEach((el) => el.classList.remove("live"));
    document.querySelectorAll(".node").forEach((el) => el.classList.remove("selected"));
    msg.paths.forEach((id) => $(id)?.classList.add("live"));
    msg.nodes.forEach((id) => {
      document.querySelectorAll(`[data-id="${id}"]`).forEach((el) => el.classList.add("selected"));
    });
  }

  function sendAlong(msg, done, cycle) {
    const gen = state.cycleGen;
    if (state.sending) {
      if (done) done();
      return;
    }
    state.sending = true;
    showMessage(msg, cycle);
    const packets = msg.paths.map((id) => {
      const path = $(id);
      const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      c.setAttribute("r", "7");
      c.setAttribute("class", "token");
      $("tokens").appendChild(c);
      return { path, c, t: 0 };
    });
    const start = performance.now();
    function anim(now) {
      const u = Math.min(1, (now - start) / 900);
      packets.forEach((p) => {
        if (!p.path) return;
        const pt = p.path.getPointAtLength(u * p.path.getTotalLength());
        p.c.setAttribute("cx", pt.x);
        p.c.setAttribute("cy", pt.y);
      });
      if (u < 1) requestAnimationFrame(anim);
      else {
        packets.forEach((p) => p.c.remove());
        state.sending = false;
        if (gen !== state.cycleGen) return;
        if (done) done();
      }
    }
    requestAnimationFrame(anim);
  }

  function setupHits() {
    const g = $("hits");
    MESSAGES.forEach((msg) => {
      msg.paths.forEach((id) => {
        const src = $(id);
        if (!src) return;
        const hit = src.cloneNode();
        hit.removeAttribute("marker-end");
        hit.setAttribute("class", "hit");
        hit.dataset.msg = msg.id;
        g.appendChild(hit);
      });
    });
    g.addEventListener("click", (ev) => {
      const id = ev.target.dataset.msg;
      const msg = MESSAGES.find((m) => m.id === id);
      if (!msg) return;
      state.msgIndex = MESSAGES.indexOf(msg);
      sendAlong(msg);
    });
  }

  function setupTokens() {
    TOKEN_PATHS.forEach((spec, i) => {
      const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      c.setAttribute("r", "4");
      c.setAttribute("class", `token ${spec.cls}`);
      c.dataset.loop = String(i);
      $("tokens").appendChild(c);
    });
  }

  function drawTokens() {
    TOKEN_PATHS.forEach((spec, i) => {
      const path = $(spec.id);
      const tok = $("tokens").querySelector(`[data-loop="${i}"]`);
      if (!path || !tok) return;
      const dim = spec.mod != null && state.lam[spec.mod] < 0.34;
      tok.style.opacity = dim || !state.playing || state.cycleKind ? "0" : "1";
      if (!state.playing || state.cycleKind) return;
      const len = path.getTotalLength();
      const p = path.getPointAtLength((state.tokenT * 40 + i * 18) % Math.max(len, 1));
      tok.setAttribute("cx", p.x);
      tok.setAttribute("cy", p.y);
    });
  }

  function inspect(id) {
    if (id === "inv1" || id === "inv2") {
      playCycle("inverse");
      return;
    }
    if (id === "fwd1" || id === "fwd2") {
      playCycle("forward");
      return;
    }
    const info = INFO[id];
    if (!info) return;
    const related = MESSAGES.find((m) => m.nodes.includes(id));
    if (related) {
      state.msgIndex = MESSAGES.indexOf(related);
      sendAlong(related);
    } else {
      $("inModel").textContent = `${info.body} ${info.eq}`;
      $("inHuman").textContent = "Click an arrow to pair this box with a human example.";
      $("stepLabel").textContent = info.title;
    }
  }

  function setCycleButtons(kind) {
    $("playInv").classList.toggle("active", kind === "inverse");
    $("playFwd").classList.toggle("active", kind === "forward");
    $("playInv").textContent = kind === "inverse" ? "Stop" : "Inverse cycle";
    $("playFwd").textContent = kind === "forward" ? "Stop" : "Forward cycle";
    document.body.dataset.cycle = kind || "";
  }

  function stopCycle() {
    state.cycleGen += 1;
    state.playing = false;
    state.cycleKind = null;
    state.sending = false;
    setCycleButtons(null);
    document.body.removeAttribute("data-cycle");
    drawTokens();
  }

  function playCycle(kind) {
    if (state.playing && state.cycleKind === kind) {
      stopCycle();
      return;
    }
    state.cycleGen += 1;
    const gen = state.cycleGen;
    state.playing = true;
    state.cycleKind = kind;
    state.sending = false;
    setCycleButtons(kind);
    const ids = CYCLES[kind];
    let i = 0;
    function next() {
      if (gen !== state.cycleGen) return;
      if (i >= ids.length) {
        const doneKind = kind;
        stopCycle();
        $("stepLabel").textContent = doneKind === "forward"
          ? "Forward cycle complete. Inverse cycle will use the updated λ."
          : "Inverse cycle complete. Play Forward cycle to hold x̂_t+1 and score the next current state.";
        return;
      }
      const msg = MESSAGES.find((m) => m.id === ids[i]);
      applyCycleStep(msg.id, kind);
      drawFlow();
      sendAlong(msg, () => {
        if (gen !== state.cycleGen) return;
        setTimeout(() => {
          if (gen !== state.cycleGen) return;
          i += 1;
          next();
        }, 380);
      }, kind);
    }
    next();
  }

  setupTokens();
  setupHits();
  document.querySelectorAll(".node").forEach((el) => {
    el.addEventListener("click", () => inspect(el.dataset.id));
  });
  $("send").addEventListener("click", () => {
    const msg = MESSAGES[state.msgIndex % MESSAGES.length];
    sendAlong(msg);
    state.msgIndex = (state.msgIndex + 1) % MESSAGES.length;
  });
  $("playInv").addEventListener("click", () => playCycle("inverse"));
  $("playFwd").addEventListener("click", () => playCycle("forward"));
  document.querySelectorAll(".beats li").forEach((li) => {
    li.addEventListener("click", () => {
      state.phase = Number(li.dataset.phase);
      resetReach();
      drawFlow();
    });
  });
  $("showPaper").addEventListener("change", (e) => {
    $("paperNode").style.display = e.target.checked ? "block" : "none";
    const pe = $("p_pred_lam");
    if (pe) pe.style.display = e.target.checked ? "block" : "none";
  });
  $("paperNode").style.display = "none";
  drawFlow();
  drawTokens();
  showMessage(MESSAGES[0]);

  if (new URLSearchParams(location.search).get("tour") === "1") {
    playCycle("inverse");
    const wait = (CYCLES.inverse.length + CYCLES.forward.length) * 1400 + 800;
    setTimeout(() => {
      if (!state.playing) playCycle("forward");
      setTimeout(() => {
        stopCycle();
        document.body.setAttribute("data-tour", "done");
      }, wait);
    }, CYCLES.inverse.length * 1400 + 600);
  }
} catch (err) {
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<pre style="padding:1rem;background:#ead8a8">MOSAIC viewer error: ${err}</pre>`
  );
}
})();
