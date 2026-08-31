"""Save static diagnostic figures next to the sandbox simulator (not workshop assets)."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

TRACES = Path(__file__).with_name("traces.json")
OUT = Path(__file__).with_name("figures")


def main() -> None:
    bundle = json.loads(TRACES.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    zero = next(c for c in bundle["conditions"] if c["meta"]["feedback_delay_steps"] == 0)

    trials = np.array([t["trial"] for t in zero["trials"]])
    lam = np.array([t["lambda"] for t in zero["trials"]])
    uff = np.array([t["u_ff"] for t in zero["trials"]])
    ufb = np.array([t["u_fb"] for t in zero["trials"]])
    w = np.array([t["w"] for t in zero["trials"]])

    fig, axes = plt.subplots(3, 1, figsize=(10, 11), sharex=True)
    axes[0].plot(trials, lam[:, 0], label="λ₁ free-space module", color="#2f5d8c", lw=2.2)
    axes[0].plot(trials, lam[:, 1], label="λ₂ viscous module", color="#c46b1a", lw=2.2)
    axes[0].axvspan(30, 70, color="0.5", alpha=0.12, label="viscous field")
    axes[0].set_ylabel("Responsibility λ")
    axes[0].set_title("MOSAIC module selection (delay = 0)")
    axes[0].legend(loc="upper right", frameon=False)

    axes[1].plot(trials, uff, label="u_ff", color="#3d6b4f", lw=2)
    axes[1].plot(trials, ufb, label="u_fb", color="#a33b32", lw=2)
    axes[1].axvspan(30, 70, color="0.5", alpha=0.12)
    axes[1].set_ylabel("Motor command")
    axes[1].set_title("Feedback-error learning: reflex gives way to feedforward")
    axes[1].legend(loc="upper right", frameon=False)

    axes[2].plot(trials, w[:, 0], label="w₁", color="#2f5d8c", lw=2)
    axes[2].plot(trials, w[:, 1], label="w₂", color="#c46b1a", lw=2)
    axes[2].axvspan(30, 70, color="0.5", alpha=0.12)
    axes[2].set_xlabel("Trial")
    axes[2].set_ylabel("Forward-model parameter")
    axes[2].set_title("Gated learning: modules specialise without wiping each other")
    axes[2].legend(loc="upper right", frameon=False)

    fig.tight_layout()
    fig.savefig(OUT / "mosaic-delay0-diagnostics.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for cond, color, label in [
        (0, "#3d6b4f", "0 ms"),
        (1, "#c46b1a", "100 ms"),
        (2, "#a33b32", "200 ms"),
    ]:
        c = next(x for x in bundle["conditions"] if x["meta"]["feedback_delay_steps"] == cond)
        axes[0].plot([t["lambda"][1] for t in c["trials"]], color=color, lw=2, label=label)
        axes[1].plot([t["u_fb"] for t in c["trials"]], color=color, lw=2, label=label)
    for ax in axes:
        ax.axvspan(30, 70, color="0.5", alpha=0.12)
        ax.legend(frameon=False)
    axes[0].set_ylabel("λ₂")
    axes[0].set_title("Delay slows module switching")
    axes[1].set_ylabel("u_fb")
    axes[1].set_xlabel("Trial")
    axes[1].set_title("Delay inflates feedback corrections")
    fig.tight_layout()
    fig.savefig(OUT / "mosaic-delay-comparison.png", dpi=160)
    plt.close(fig)
    print(f"Wrote figures in {OUT}")


if __name__ == "__main__":
    main()
