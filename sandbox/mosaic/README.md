# MOSAIC sandbox (WIP)

This folder is **not** the workshop demo. Do not link here from `docs/workshop/` or `platform/` until [STATUS.md](STATUS.md) is green.

## What you are looking at

[`viewer/`](viewer/) is an **illustrative / unofficial** visualisation of Wolpert & Kawato (1998). It is meant to make the idea visible:

two inverse–forward pairs share a hand. Click an arrow or **Send next message** to watch one signal travel, with the matching human example (reaching for a mug / through a viscous medium).

It does **not** replay the Colab 1D traces. Dynamics live in `viewer/app.js` (same plant form \(\dot v = (u - b v)/m\), parameters chosen so the switch is visible). Not a quantitative reproduction of the 1998 paper.

## 怎麼打開（不要用 8000 那個網址，除非你已經自己開了伺服器）

最省事：在檔案總管雙擊

`sandbox\mosaic\viewer\index.html`

或雙擊 repo 根目錄的 `open-mosaic.bat`。

也可以：

```text
python sandbox/mosaic/open_viewer.py
```

這會開瀏覽器到本機頁面。Cursor 裡點 README 的 `http://127.0.0.1:8000/...` 連結，若沒先開伺服器會打不開。

## Also in this folder (not driving the viewer)

- [simulate.py](simulate.py) / `traces.json` — earlier Colab-style 1D run
- [mosaic.mindel.json](mosaic.mindel.json) — MindelSpec draft
- [source/](source/) — original notebooks

When this graduates, copy a frozen viewer into the workshop pack; do not move this folder in place.
