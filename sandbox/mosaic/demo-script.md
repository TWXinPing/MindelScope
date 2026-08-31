# Live MOSAIC demo script (parked)

Use this only after [STATUS.md](STATUS.md) is complete. Until then the workshop talk has no live MOSAIC.

Open `/sandbox/mosaic/viewer/`. Keep delay at 0 ms, scenario “Viscous field & memory”, view “This implementation”.

1. **Structure (30 s).** Click Inverse 1, Forward 1, λ, Plant. Read the equation aloud once. Point at the grey responsibility predictor: “in the paper, not in this simulator.”
2. **Play trials (60 s).** Hit **Play trials**. Narrate: air → water/honey at trial 30 → air again at 70. Watch λ₂ rise in the field and fall when the field dies. That is memory retention, not unlearning.
3. **One reach (45 s).** Jump to beat `viscous_on` (trial 30). Hit **Play reach**. Line width on the inverse arrows should follow λ; the feedback reflex goes rust when |u_fb| is large.
4. **Paper toggle (20 s).** Switch view to “Paper architecture”. The predictor comes back in ink. Switch back.
5. **If time (30 s).** Delay = 200 ms, scenario “Sensory delay”, beat `switch_200ms`. u_fb gets noisy. “That is why a forward model is computationally motivated.”
