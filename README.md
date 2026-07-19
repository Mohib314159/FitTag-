# FitTag

**The truth layer for secondhand fit.** Lay a garment on a marker mat, take one photo, and
FitTag measures it to the centimetre with honest error bars — then tells a buyer whether it
will actually fit. Built for the Fleek × a16z hackathon.

> **Geometry measures; the model only names.** ArUco markers + homography rectify the photo to
> a metric top-down plane; silhouette geometry extracts measurements; a vision model is used
> *only* to classify the garment type. No model ever emits a number.

See **PITCH.md** for the full story, demo script, and judge calibration.

## Run
```bash
pip install -r requirements.txt          # add --break-system-packages if needed
uvicorn api.server:app --reload          # from the repo root
# open http://127.0.0.1:8000
```
The front end auto-detects the backend: with it running you can upload a flat-lay (or hit
*Run a sample*) for a real measurement; without it, the page stays on demo data.

## Architecture
Two layers: a **TRUTH** layer (measured fit — the product) and a **VISUAL** layer (generative
try-on — explicitly illustrative, never drives a verdict).

```
core/
  calibrate.py   ArUco detection; MAT mode (>=2 markers -> homography over all corners, accurate)
                 vs SINGLE mode (1 marker fallback); calibrate_by_rectangle (markerless A4/card,
                 experimental); capture_guidance (glare/light/marker checks)
  segment.py     segment_auto = rembg (U^2-Net, optional) -> auto-seeded GrabCut (robust framing)
  classify.py    garment TYPE only: VLM -> CLIP (JeansFinder) -> deterministic silhouette heuristic
  measure.py     silhouette geometry via row-by-row width profile (armpit = width step-down;
                 crotch = first split into two legs); t-shirt + jeans; honest tolerances
  fit.py         ease arithmetic -> per-zone verdict; manual (body) or reference_garment mode;
                 fit confidence propagates the measurement tolerance into the verdict
  sizing.py      approximate size translation (alpha / waist-inches + UK), always caveated
  feedback.py    fit-feedback flywheel: append-only outcomes -> suggested band shift (the data moat)
  catalog.py     fit-based search: rank a catalog of measured listings by how well each fits you
  tryon.py       generative try-on (FASHN / Gemini), gated on an API key; labelled illustrative
  contracts.py   dataclasses (Measurement, GarmentMeasurement, BodyProfile, FitZone, FitReport)
api/server.py    FastAPI: /measure, /measure-reference, /fit, /guidance, /search-fit, /feedback,
                 /tryon, /overlays, serves the UI
web/index.html   single-file UI: live measurement, interactive fit (tops + bottoms), size badge,
                 fit confidence, feedback buttons, "items that fit you", reference-photo upload
viz/overlay.py   draws measurement lines + tolerances on the rectified image
adapters/        from_vinted.py — JeansFinder reuse (listing ingestion; CLIP classifier path)
validation/      make_dataset.py + validate.py + ground_truth.csv -> engine-vs-truth error table
tests/           synth.py (marker mat + known garments under tilt); test_measure, test_jeans
demo.py          end-to-end: calibrate -> segment -> classify -> measure -> fit (+ overlay)
```

## Validation
```bash
python -m validation.make_dataset        # synthetic photos + ground_truth.csv (swap in real data)
python -m validation.validate            # -> per-measurement MAE + within-tolerance table
```
Current synthetic result: **MAE 0.14 cm over 30 measurements, 100% within tolerance.** For real
photos, replace `validation/photos/` + tape-measured numbers in `ground_truth.csv` and re-run.

## Tests
```bash
python -m tests.test_measure   # tops  4/4
python -m tests.test_jeans     # bottoms 3/3
```

## Print the calibration kit
`python make_mat.py` regenerates `print/`: four A4 corner sheets (tape so the red outer
corners form a **1000 x 1400 mm** rectangle; both diagonals = 1720 mm), a quick single-marker
sheet, and a placement guide. Print at 100% and verify the 100 mm bar. The script self-tests
the kit end-to-end: it composites the real sheet PNGs, tilts the scene like a handheld photo,
and asserts `calibrate()` -> mat mode with all four markers.

## Pitch deck
Open `deck.html` — 8 slides + 2 backup (arrow keys / tap / swipe; speaker cues in the strip
above the tape-measure progress bar). Pairs with the live app in a second tab; PITCH.md section 12
is the demo-day runbook.

## Prior art / reuse
- ArUco px->cm measurement reuses the approach from my climbing-route optimiser. FitTag's
  multi-marker mat is **more rigorous than the published `mkurc1/climbingcrux_model`** (single
  marker + bbox centres → extrapolation): homography over all corners avoids that error.
- `adapters/from_vinted.py` reuses my **JeansFinder** Vinted client + CLIP scorer for listing
  ingestion and the offline garment-type classifier path.

MIT licensed (see LICENSE).
