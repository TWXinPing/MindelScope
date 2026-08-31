"""MOSAIC 1D simulation with trial- and step-level traces.

Merged from mosaic_simulation_colab.py (v1) and mosaic_simulation_colab-v2.py.
Based on Wolpert & Kawato (1998). This is a simplified 1D velocity controller,
not the full arm / multi-object MOSAIC architecture.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

DT = 0.1  # seconds per step; delay=1 ≈ 100 ms
DEFAULT_KEY_TRIALS = (5, 10, 20, 29, 30, 35, 40, 50, 60, 69, 70, 75, 85, 95)


class ForwardModel:
    """Predict next velocity: v_hat = v + w * u."""

    def __init__(self, learning_rate: float = 0.08, initial_w: float = 0.5):
        self.w = float(initial_w)
        self.lr = learning_rate

    def predict(self, v_t: float, u_t: float) -> float:
        return float(np.clip(v_t + self.w * u_t, -10.0, 10.0))

    def update(self, v_t: float, u_t: float, v_next: float, responsibility: float) -> None:
        pred = self.predict(v_t, u_t)
        error = float(np.clip(v_next - pred, -2.0, 2.0))
        grad = float(np.clip(u_t, -5.0, 5.0))
        self.w += self.lr * responsibility * error * grad
        self.w = float(np.clip(self.w, 0.01, 2.0))


class InverseModel:
    """Feedforward controller: u_ff = a * (v_des - v)."""

    def __init__(self, learning_rate: float = 0.03, initial_a: float = 0.5):
        self.a = float(initial_a)
        self.lr = learning_rate

    def control(self, v_desired: float, v_t: float) -> float:
        return self.a * (v_desired - v_t)

    def update(self, v_desired: float, v_t: float, u_feedback: float, responsibility: float) -> None:
        grad = v_desired - v_t
        self.a += self.lr * responsibility * u_feedback * grad
        self.a = float(np.clip(self.a, 0.01, 2.0))


def context_for_trial(trial: int) -> dict:
    if 30 <= trial < 70:
        return {"id": "viscous", "m": 1.0, "b": 2.5, "label": "viscous field"}
    return {"id": "free", "m": 1.0, "b": 0.0, "label": "free space"}


def scenario_events() -> list[dict]:
    return [
        {
            "trial": 0,
            "event": "session_start",
            "caption": "在空氣中伸手：自由空間，阻尼 b = 0。兩個模組從不同初始參數開始競爭。",
        },
        {
            "trial": 30,
            "event": "viscous_on",
            "caption": "黏滯力場開啟（b = 2.5）：像突然伸進水或蜂蜜。預測誤差上升，責任訊號應改掛到模組 2。",
        },
        {
            "trial": 70,
            "event": "viscous_off",
            "caption": "力場關掉，回到自由空間。若模組 1 的記憶被保留，責任訊號應迅速切回，而不必從頭學。",
        },
    ]


class MOSAICSimulation:
    def __init__(
        self,
        num_modules: int = 2,
        sigma: float = 0.15,
        feedback_delay: int = 0,
        k_fb: float | None = None,
        seed: int = 0,
    ):
        self.num_modules = num_modules
        self.sigma = sigma
        self.delay = int(feedback_delay)
        self.k_fb = 1.5 if self.delay == 0 and k_fb is None else (0.8 if k_fb is None else k_fb)
        self.rng = np.random.default_rng(seed)

        initials_w = [0.3, 0.7] + [0.5] * max(0, num_modules - 2)
        initials_a = [0.3, 0.8] + [0.5] * max(0, num_modules - 2)
        self.forward_models = [
            ForwardModel(learning_rate=0.08, initial_w=initials_w[i]) for i in range(num_modules)
        ]
        self.inverse_models = [
            InverseModel(learning_rate=0.03, initial_a=initials_a[i]) for i in range(num_modules)
        ]

    def run(
        self,
        num_trials: int = 100,
        steps_per_trial: int = 50,
        keep_steps_for: tuple[int, ...] | None = None,
        keep_all_steps: bool = False,
    ) -> dict:
        t_steps = np.linspace(0, np.pi, steps_per_trial)
        v_profile = np.sin(t_steps)

        trials = []
        step_traces = []

        for trial in range(num_trials):
            ctx = context_for_trial(trial)
            m, b = ctx["m"], ctx["b"]
            v_t = 0.0
            v_history = [0.0]
            u_history = [0.0]

            trial_v, trial_resp, trial_uff, trial_ufb = [], [], [], []
            trial_errors = []
            keep_this = keep_all_steps or (keep_steps_for is not None and trial in keep_steps_for)

            for step in range(steps_per_trial):
                v_des = float(v_profile[step])
                delayed_step = step - self.delay
                v_delayed = 0.0 if delayed_step < 0 else float(v_history[delayed_step])

                u_ff_i = [
                    float(inv.control(v_des, v_delayed)) for inv in self.inverse_models
                ]

                errors = [0.0] * self.num_modules
                if step == 0 or delayed_step <= 0:
                    resp = np.ones(self.num_modules) / self.num_modules
                else:
                    prev_v_delayed = float(v_history[delayed_step - 1])
                    prev_u_delayed = float(u_history[delayed_step - 1])
                    for i, fwd in enumerate(self.forward_models):
                        pred_v = fwd.predict(prev_v_delayed, prev_u_delayed)
                        errors[i] = float(v_delayed - pred_v)
                    likelihoods = np.exp(-(np.array(errors) ** 2) / (self.sigma**2))
                    total = float(np.sum(likelihoods))
                    resp = (
                        np.ones(self.num_modules) / self.num_modules
                        if total == 0
                        else likelihoods / total
                    )

                resp = np.asarray(resp, dtype=float)
                u_ff_total = float(np.sum(resp * np.array(u_ff_i)))
                u_fb = float(self.k_fb * (v_des - v_delayed))
                u_total = float(np.clip(u_ff_total + u_fb, -10.0, 10.0))

                dv = (u_total - b * v_t) / m
                v_next = float(np.clip(v_t + dv * DT + self.rng.normal(0, 0.01), -5.0, 5.0))
                v_t = v_next
                v_history.append(v_t)
                u_history.append(u_total)

                if delayed_step > 0:
                    prev_v_delayed = float(v_history[delayed_step - 1])
                    prev_u_delayed = float(u_history[delayed_step - 1])
                    for i in range(self.num_modules):
                        self.forward_models[i].update(
                            prev_v_delayed, prev_u_delayed, v_delayed, float(resp[i])
                        )
                        self.inverse_models[i].update(v_des, v_delayed, u_fb, float(resp[i]))

                trial_v.append(v_t)
                trial_resp.append(resp)
                trial_uff.append(u_ff_total)
                trial_ufb.append(u_fb)
                trial_errors.append(errors)

                if keep_this:
                    step_traces.append(
                        {
                            "trial": trial,
                            "step": step,
                            "context": ctx["id"],
                            "m": m,
                            "b": b,
                            "v": round(v_t, 6),
                            "v_des": round(v_des, 6),
                            "v_delayed": round(v_delayed, 6),
                            "u_ff_i": [round(u, 6) for u in u_ff_i],
                            "u_ff": round(u_ff_total, 6),
                            "u_fb": round(u_fb, 6),
                            "u_total": round(u_total, 6),
                            "errors": [round(e, 6) for e in errors],
                            "lambda": [round(float(x), 6) for x in resp],
                            "w": [round(f.w, 6) for f in self.forward_models],
                            "a": [round(inv.a, 6) for inv in self.inverse_models],
                        }
                    )

            trials.append(
                {
                    "trial": trial,
                    "context": ctx["id"],
                    "m": m,
                    "b": b,
                    "v_actual": round(float(np.mean(trial_v)), 6),
                    "v_desired": round(float(np.mean(v_profile)), 6),
                    "u_ff": round(float(np.mean(trial_uff)), 6),
                    "u_fb": round(float(np.mean(trial_ufb)), 6),
                    "lambda": [round(float(x), 6) for x in np.mean(trial_resp, axis=0)],
                    "errors": [round(float(x), 6) for x in np.mean(trial_errors, axis=0)],
                    "w": [round(f.w, 6) for f in self.forward_models],
                    "a": [round(inv.a, 6) for inv in self.inverse_models],
                }
            )

        return {
            "meta": {
                "model": "MOSAIC-1D",
                "citation": "Wolpert & Kawato (1998) Neural Networks 11:1317-1329",
                "interpretation": "unofficial",
                "num_modules": self.num_modules,
                "sigma": self.sigma,
                "feedback_delay_steps": self.delay,
                "feedback_delay_ms": int(self.delay * DT * 1000),
                "k_fb": self.k_fb,
                "dt": DT,
                "num_trials": num_trials,
                "steps_per_trial": steps_per_trial,
                "not_in_this_implementation": [
                    "responsibility_predictor",
                    "multi_object_mass",
                    "size_weight_illusion",
                    "full_arm_dynamics",
                ],
            },
            "events": scenario_events(),
            "trials": trials,
            "steps": step_traces,
        }


def build_bundle(
    delays: tuple[int, ...] = (0, 1, 2),
    seed: int = 42,
    keep_steps_for: tuple[int, ...] = DEFAULT_KEY_TRIALS,
    keep_all_steps: bool = False,
) -> dict:
    conditions = []
    for delay in delays:
        sim = MOSAICSimulation(feedback_delay=delay, seed=seed)
        conditions.append(sim.run(keep_steps_for=keep_steps_for, keep_all_steps=keep_all_steps))
    return {
        "schema": "mindelscope.traces/v0",
        "seed": seed,
        "conditions": conditions,
        "events": scenario_events(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MOSAIC 1D simulation and export traces.")
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("traces.json"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--all-steps", action="store_true", help="Export every step of every trial.")
    args = parser.parse_args()

    bundle = build_bundle(seed=args.seed, keep_all_steps=args.all_steps)
    args.out.write_text(json.dumps(bundle), encoding="utf-8")
    n_steps = sum(len(c["steps"]) for c in bundle["conditions"])
    print(f"Wrote {args.out} ({args.out.stat().st_size / 1024:.1f} KiB, {n_steps} step records)")


if __name__ == "__main__":
    main()
