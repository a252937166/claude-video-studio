#!/usr/bin/env python3
"""One dancer becomes a crew (「一人成团」): copies of her dance beside her, each one a beat fraction later, like a canon.

Per frame: person mask from MediaPipe selfie segmentation (landscape model), refined with a guided filter and smoothed over
time; a ring buffer keeps the last clones*delay seconds of (frame, mask). Clone k on each side is the dancer from k*delay
seconds ago, shifted sideways by k*spread*width, scaled by scale**k around her feet (so it stands further back), dimmed by
dim**k and grounded with a soft contact shadow. Clones are drawn far-to-near, the live dancer last, so she stays in front.
With --bpm/--offset the clones pop in one by one on the beats after --intro (flash + scale-in), otherwise every 0.5 s.
Needs a locked-off shot of ONE person; the background must not move with her.
Usage: python clone_squad.py in.mp4 out.mp4 [--t0 S] [--dur S] [--width 1920] [--clones 2] [--delay 0.3125] [--spread 0.2]
                             [--scale 0.9] [--dim 0.82] [--intro 1.0] [--bpm 96 --offset 0]
                             [--audio music.wav [--audio-start S]] [--label "AI 拓展 · 一人成团"]
--clones is per side (2 -> four copies). Needs numpy, opencv-contrib, mediapipe 0.10.x, Pillow (for --label), ffmpeg."""
import os, sys, json, subprocess, shutil
if len(sys.argv) < 3 or sys.argv[1] in ("-h", "--help"): print(__doc__); sys.exit(0 if len(sys.argv) > 1 else 2)
_REQ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "requirements-face.txt"))
try:
    import numpy as np, cv2, mediapipe as mp
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    sys.exit(f"clone_squad.py: missing Python package '{e.name}'. Install (~600 MB): python3 -m pip install -r {_REQ}")
if not hasattr(mp, "solutions"):
    sys.exit(f"clone_squad.py: mediapipe {mp.__version__} has no legacy solutions API; python3 -m pip install -r {_REQ}")
if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
    sys.exit("clone_squad.py: needs ffmpeg + ffprobe on PATH (macOS: brew install ffmpeg)")
src, out = sys.argv[1], sys.argv[2]
opt = lambda n, d: type(d)(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
T0, DUR, OW = opt("--t0", 0.0), opt("--dur", 0.0), opt("--width", 1920)
K, DELAY, SPREAD, SCALE, DIM = opt("--clones", 2), opt("--delay", 0.3125), opt("--spread", 0.2), opt("--scale", 0.9), opt("--dim", 0.82)
INTRO, BPM, OFFSET = opt("--intro", 1.0), opt("--bpm", 0.0), opt("--offset", 0.0)
AUDIO, ASTART, LABEL = opt("--audio", ""), opt("--audio-start", 0.0), opt("--label", "")
info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                           "stream=width,height,r_frame_rate:format=duration", "-of", "json", src]))
W0, H0 = info["streams"][0]["width"], info["streams"][0]["height"]; RATE = info["streams"][0]["r_frame_rate"]
num, den = map(int, RATE.split("/")); FPS = num / den
DUR = DUR or float(info["format"]["duration"]) - T0
OH = int(round(OW * H0 / W0 / 2) * 2)
seg = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
GF = hasattr(cv2, "ximgproc") and hasattr(cv2.ximgproc, "guidedFilter")
# entry times: clone order inner-left, inner-right, outer-left, ... popping on successive beats after INTRO
slots = [(k, s) for k in range(1, K + 1) for s in (-1, 1)]
if BPM:
    bt = 60 / BPM; first = OFFSET + np.ceil((INTRO - OFFSET) / bt) * bt
    entry = {c: first + i * bt for i, c in enumerate(slots)}
else:
    entry = {c: INTRO + i * 0.5 for i, c in enumerate(slots)}
font = None
if LABEL:
    for fp in ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"):
        if os.path.exists(fp): font = ImageFont.truetype(fp, int(OH * 0.034)); break


def mask_of(rgb, prev):
    m = seg.process(rgb).segmentation_mask.astype(np.float32)
    m = cv2.ximgproc.guidedFilter(rgb, m, 8, 1e-3) if GF else cv2.GaussianBlur(m, (0, 0), 2)
    m = np.clip((m - 0.25) / 0.5, 0, 1)
    return m if prev is None else 0.65 * m + 0.35 * prev


def feet(m):
    """(x centre, y of the lowest solid row) of the person mask."""
    ys, xs = np.where(m > 0.5)
    if len(ys) < 50: return OW / 2, OH * 0.9
    yb = np.percentile(ys, 99.5); low = xs[ys > yb - OH * 0.05]
    return float(np.median(low)), float(yb)


def place(img, x_shift, s, fx, fy):
    """scale by s about the feet point and shift sideways (affine warp of a float image)."""
    M = np.float32([[s, 0, (1 - s) * fx + x_shift], [0, s, (1 - s) * fy]])
    return cv2.warpAffine(img, M, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{T0:.3f}", "-i", src, "-t", f"{DUR:.3f}", "-vf", f"scale={OW}:{OH}:flags=area",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
tmp = out + ".video.mp4"
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", RATE, "-i", "-",
                        "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-g", "12", tmp], stdin=subprocess.PIPE)
LAG = int(round(K * DELAY * FPS)) + 1
ring, prev_m, n = [], None, 0
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
while True:
    buf = dec.stdout.read(OW * OH * 3)
    if len(buf) < OW * OH * 3: break
    rgb = np.frombuffer(buf, np.uint8).reshape(OH, OW, 3)
    t = n / FPS
    m = mask_of(rgb, prev_m); prev_m = m
    f = rgb.astype(np.float32) / 255
    ring.append((f, m)); ring = ring[-LAG - 1:]
    base = f.copy()
    flash = 0.0
    for k, side in sorted(slots, key=lambda c: -c[0]):          # far clones first
        te = entry[(k, side)]
        if t < te: continue
        j = len(ring) - 1 - int(round(k * DELAY * FPS))
        if j < 0: continue
        cf, cm = ring[j]
        cm = np.clip((cm - 0.3) / 0.4, 0, 1)                    # firmer edges: no see-through clones on fast moves
        fx, fy = feet(cm)
        s = SCALE ** k
        pop = min(1.0, (t - te) / 0.18)                         # scale-in over 0.18 s
        s_now = s * (0.6 + 0.4 * (1 - (1 - pop) ** 3))
        shift = side * k * SPREAD * OW
        a = place(cm, shift, s_now, fx, fy)
        img = place(cf, shift, s_now, fx, fy) * (DIM ** k)
        # soft contact shadow under the clone's feet
        sx, sy = fx + shift, fy
        sh = np.exp(-(((xx - sx) / (OW * 0.06 * s_now)) ** 2 + ((yy - sy) / (OH * 0.018 * s_now)) ** 2)) * 0.45 * pop
        base *= (1 - sh[..., None])
        a3 = (a * pop)[..., None]
        base = base * (1 - a3) + img * a3
        if t - te < 0.12: flash = max(flash, 1 - (t - te) / 0.12)
    mm = m[..., None]
    base = base * (1 - mm) + f * mm                            # the live dancer in front
    if flash: base = np.clip(base + 0.18 * flash, 0, 1)
    out_img = (base * 255 + 0.5).astype(np.uint8)
    if font:
        im = Image.fromarray(out_img); d = ImageDraw.Draw(im); pad = int(OH * 0.014)
        tw = d.textlength(LABEL, font=font); x0, y0 = int(OW * 0.025), int(OH * 0.035)
        d.rounded_rectangle([x0, y0, x0 + tw + 2 * pad, y0 + font.size + 2 * pad], radius=pad * 2, fill=(14, 18, 28))
        d.text((x0 + pad, y0 + pad * 0.6), LABEL, font=font, fill=(255, 255, 255))
        out_img = np.asarray(im)
    enc.stdin.write(out_img.tobytes()); n += 1
enc.stdin.close(); enc.wait(); dec.wait()
if AUDIO:
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-ss", f"{ASTART:.3f}", "-i", AUDIO, "-map", "0:v:0", "-map", "1:a:0",
                           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", f"afade=t=out:st={max(0, n / FPS - 0.6):.2f}:d=0.6",
                           "-shortest", out])
    os.remove(tmp)
else: os.replace(tmp, out)
print(f"wrote {out}: {n} frames {OW}x{OH} @ {FPS:.3f} fps, {len(slots)} clones, delay {DELAY}s, guided filter: {GF}")
