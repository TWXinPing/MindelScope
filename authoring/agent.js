function suggestMindelSpec(spec) {
  const notes = [];
  const byType = (t) => spec.modules.filter((m) => m.type === t);
  const ids = new Set(spec.modules.map((m) => m.id));

  if (!byType("plant").length) {
    notes.push({ kind: "add-module", type: "plant", label: "Plant / world", reason: "A cognitive control model needs an explicit body or environment node." });
  }
  for (const fwd of spec.modules.filter((m) => m.role === "predictor" || /^forward/i.test(m.label || ""))) {
    const cmp = spec.modules.find((m) => m.type === "comparator" && m.group === fwd.group);
    if (!cmp) notes.push({ kind: "add-module", type: "comparator", group: fwd.group, label: `Error for ${fwd.label}`, reason: `${fwd.id} predicts but has no comparator.` });
  }
  if (byType("process").some((m) => m.role === "controller") && !byType("gate").length) {
    notes.push({ kind: "add-module", type: "gate", label: "λ gate", reason: "Multiple controllers should mix through a gate, not a silent sum." });
  }
  if (byType("comparator").length && !byType("distribution").length) {
    notes.push({ kind: "add-module", type: "distribution", label: "Hypothesis λ", reason: "Prediction errors should land in an explicit distribution node." });
  }
  for (const edge of spec.edges) {
    if (!ids.has(edge.source) || !ids.has(edge.target)) {
      notes.push({ kind: "remove-edge", id: edge.id, reason: `${edge.id} points at a missing module.` });
    }
    const src = spec.modules.find((m) => m.id === edge.source);
    const tgt = spec.modules.find((m) => m.id === edge.target);
    const gatingOk = src && tgt && (
      src.type === "gate" || src.type === "distribution" ||
      tgt.type === "gate" || tgt.type === "distribution" ||
      edge.gatedBy
    );
    if (edge.type === "gating" && !gatingOk) {
      notes.push({ kind: "retype-edge", id: edge.id, to: "information", reason: "Gating edges should touch a gate or distribution, or set gatedBy." });
    }
    if (edge.type === "error" && src && src.type !== "comparator" && src.type !== "distribution" && src.role !== "error_corrector") {
      notes.push({ kind: "retype-edge", id: edge.id, to: "information", reason: "Error edges should start from a comparator, distribution, or reflex." });
    }
  }
  for (const mod of spec.modules) {
    if (!mod.annotation?.goal) notes.push({ kind: "annotate", id: mod.id, field: "goal", reason: `${mod.id} has no computational goal.` });
    if (!mod.annotation?.equation && ["process", "comparator", "distribution", "gate", "plant"].includes(mod.type)) {
      notes.push({ kind: "annotate", id: mod.id, field: "equation", reason: `${mod.id} should carry an equation.` });
    }
    if (!mod.annotation?.scenario) notes.push({ kind: "annotate", id: mod.id, field: "scenario", reason: `${mod.id} is not mapped onto a real situation.` });
  }
  return notes;
}

function applySuggestions(spec, notes) {
  const next = JSON.parse(JSON.stringify(spec));
  let added = 0;
  notes.forEach((n, i) => {
    if (n.kind === "add-module") {
      const id = `${n.type}_${added + 1}`;
      next.modules.push({
        id,
        type: n.type,
        label: n.label,
        group: n.group,
        implemented: true,
        annotation: { goal: n.reason, equation: "", scenario: "" },
      });
      next.layout = next.layout || {};
      next.layout[id] = { x: 40 + (added % 4) * 180, y: 40 + Math.floor(added / 4) * 90 };
      added += 1;
    }
    if (n.kind === "remove-edge") next.edges = next.edges.filter((e) => e.id !== n.id);
    if (n.kind === "retype-edge") {
      const e = next.edges.find((x) => x.id === n.id);
      if (e) e.type = n.to;
    }
  });
  return next;
}

function llmPrompt(spec, notes) {
  return `You are editing a MindelSpec JSON document for a cognitive neuroscience model.
Rules:
- Only modify the JSON. Do not invent simulation parameter values.
- Keep module types in {process, representation, comparator, gate, distribution, delay, plant, scenario_event}.
- Keep edge types in {information, gating, error, context}.
- Grey / implemented:false nodes are paper-only; do not pretend they were simulated.
- Every module needs annotation.goal, annotation.equation, annotation.scenario.

Current document:
${JSON.stringify(spec, null, 2)}

Consistency notes from a local agent:
${notes.map((n) => `- ${n.kind}: ${n.reason}`).join("\n")}

Return the full revised MindelSpec JSON.`;
}

if (typeof window !== "undefined") {
  window.MindelAgent = { suggestMindelSpec, applySuggestions, llmPrompt };
}
if (typeof module !== "undefined") module.exports = { suggestMindelSpec, applySuggestions, llmPrompt };
