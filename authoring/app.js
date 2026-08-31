const NS = "http://www.w3.org/2000/svg";
const paletteType = { waiting: null };
let spec = blankSpec();
let selected = null;
let connectFrom = null;

function blankSpec() {
  return {
    mindelspec: "0.0",
    id: "untitled",
    title: "Untitled model",
    interpretation: "unofficial",
    description: "",
    modules: [],
    edges: [],
    layout: {},
    unimplemented: [],
  };
}

function $(id) { return document.getElementById(id); }

function newId(type) {
  let i = 1;
  while (spec.modules.some((m) => m.id === `${type}_${i}`)) i += 1;
  return `${type}_${i}`;
}

function draw() {
  const svg = $("canvas");
  svg.innerHTML = `<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#5c564c"/></marker></defs>`;
  const byId = Object.fromEntries(spec.modules.map((m) => [m.id, m]));
  for (const e of spec.edges) {
    const a = spec.layout[e.source];
    const b = spec.layout[e.target];
    if (!a || !b) continue;
    const path = document.createElementNS(NS, "path");
    path.setAttribute("d", `M ${a.x + 70} ${a.y + 20} C ${a.x + 120} ${a.y + 20}, ${b.x - 20} ${b.y + 20}, ${b.x} ${b.y + 20}`);
    path.setAttribute("class", "edge");
    path.style.stroke = e.type === "error" ? "#a33b32" : e.type === "gating" ? "#2f5d8c" : "#5c564c";
    path.style.strokeDasharray = e.type === "context" ? "5 4" : "";
    svg.appendChild(path);
  }
  for (const m of spec.modules) {
    const p = spec.layout[m.id] || { x: 40, y: 40 };
    const g = document.createElementNS(NS, "g");
    g.setAttribute("transform", `translate(${p.x},${p.y})`);
    const rect = document.createElementNS(NS, "rect");
    rect.setAttribute("width", "140");
    rect.setAttribute("height", "40");
    rect.setAttribute("rx", m.type === "gate" ? "20" : "6");
    rect.setAttribute("fill", selected === m.id ? "#ead8a8" : "#fffdf8");
    rect.setAttribute("stroke", m.implemented === false ? "#9a958c" : "#1c1915");
    if (m.implemented === false) rect.setAttribute("stroke-dasharray", "6 4");
    const t = document.createElementNS(NS, "text");
    t.setAttribute("x", "70");
    t.setAttribute("y", "24");
    t.setAttribute("text-anchor", "middle");
    t.setAttribute("font-size", "12");
    t.textContent = m.label;
    g.appendChild(rect);
    g.appendChild(t);
    g.addEventListener("click", (ev) => {
      ev.stopPropagation();
      if (connectFrom && connectFrom !== m.id) {
        spec.edges.push({
          id: `e_${connectFrom}_${m.id}_${spec.edges.length}`,
          type: $("edgeType").value,
          source: connectFrom,
          target: m.id,
        });
        connectFrom = null;
      } else {
        selected = m.id;
        connectFrom = m.id;
      }
      draw();
      renderForm();
    });
    svg.appendChild(g);
  }
}

function renderForm() {
  const m = spec.modules.find((x) => x.id === selected);
  if (!m) {
    $("form").innerHTML = `<label>Model id</label><input id="modelId" value="${spec.id}" />
      <label>Title</label><input id="modelTitle" value="${spec.title}" />`;
    $("modelId").oninput = (e) => { spec.id = e.target.value; };
    $("modelTitle").oninput = (e) => { spec.title = e.target.value; };
    return;
  }
  m.annotation = m.annotation || {};
  $("form").innerHTML = `
    <label>id</label><input id="f_id" value="${m.id}" />
    <label>label</label><input id="f_label" value="${m.label}" />
    <label>type</label><input value="${m.type}" disabled />
    <label>role</label><input id="f_role" value="${m.role || ""}" />
    <label>goal</label><textarea id="f_goal">${m.annotation.goal || ""}</textarea>
    <label>equation (LaTeX)</label><textarea id="f_eq">${m.annotation.equation || ""}</textarea>
    <label>scenario</label><textarea id="f_sc">${m.annotation.scenario || ""}</textarea>
    <label><input id="f_impl" type="checkbox" ${m.implemented === false ? "" : "checked"} /> implemented</label>
    <button type="button" id="delNode">Delete node</button>
  `;
  const bind = (id, fn) => { $(id).oninput = (e) => fn(e.target); };
  bind("f_id", (el) => { const old = m.id; m.id = el.value; spec.layout[m.id] = spec.layout[old]; delete spec.layout[old]; spec.edges.forEach((e) => { if (e.source === old) e.source = m.id; if (e.target === old) e.target = m.id; }); selected = m.id; });
  bind("f_label", (el) => { m.label = el.value; draw(); });
  bind("f_role", (el) => { m.role = el.value; });
  bind("f_goal", (el) => { m.annotation.goal = el.value; });
  bind("f_eq", (el) => { m.annotation.equation = el.value; });
  bind("f_sc", (el) => { m.annotation.scenario = el.value; });
  $("f_impl").onchange = (e) => { m.implemented = e.target.checked; draw(); };
  $("delNode").onclick = () => {
    spec.modules = spec.modules.filter((x) => x.id !== m.id);
    spec.edges = spec.edges.filter((e) => e.source !== m.id && e.target !== m.id);
    selected = null;
    draw();
    renderForm();
  };
}

document.querySelectorAll(".palette button[data-type]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const type = btn.dataset.type;
    const id = newId(type);
    spec.modules.push({ id, type, label: type, implemented: true, annotation: { goal: "", equation: "", scenario: "" } });
    spec.layout[id] = { x: 60 + spec.modules.length * 12, y: 60 + spec.modules.length * 18 };
    selected = id;
    draw();
    renderForm();
  });
});

$("loadMosaic").onclick = async () => {
  spec = await (await fetch("../sandbox/mosaic/mosaic.mindel.json")).json();
  selected = null;
  draw();
  renderForm();
};

$("runAgent").onclick = () => {
  const notes = window.MindelAgent.suggestMindelSpec(spec);
  $("agentLog").textContent = notes.length ? notes.map((n) => `• ${n.reason}`).join("\n") : "Looks consistent with v0 rules.";
  spec = window.MindelAgent.applySuggestions(spec, notes.filter((n) => n.kind === "add-module" || n.kind === "remove-edge" || n.kind === "retype-edge"));
  draw();
};

$("copyPrompt").onclick = async () => {
  const notes = window.MindelAgent.suggestMindelSpec(spec);
  await navigator.clipboard.writeText(window.MindelAgent.llmPrompt(spec, notes));
  $("agentLog").textContent = "LLM prompt copied. Paste into your own model; the agent must return MindelSpec JSON only.";
};

$("exportBtn").onclick = () => {
  const blob = new Blob([JSON.stringify(spec, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${spec.id || "model"}.mindel.json`;
  a.click();
};

$("validateBtn").onclick = () => {
  const notes = window.MindelAgent.suggestMindelSpec(spec);
  const missing = ["id", "title", "modules", "edges"].filter((k) => spec[k] == null || spec[k].length === 0);
  $("agentLog").textContent = [
    spec.mindelspec === "0.0" ? "mindelspec field OK" : "mindelspec should be \"0.0\"",
    missing.length ? `Missing: ${missing.join(", ")}` : "Required fields present",
    `${notes.length} consistency notes (see agent log rules).`,
  ].join("\n") + "\n" + notes.map((n) => `• ${n.reason}`).join("\n");
};

$("canvas").addEventListener("click", () => { connectFrom = null; });
draw();
renderForm();
