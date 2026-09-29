# claude-video-studio

A Claude Code skill for making short videos (Douyin / TikTok / Reels / Shorts) with **Claude as a code-driven animator**. Claude writes HTML/GSAP that draws every frame, and [HyperFrames](https://hyperframes.heygen.com) renders it to MP4.

It comes out of one week of real projects: five pixel-art MVs and PSAs, flat-cutout World Cup edits, seven rounds of 3D experiments, and four 2D approaches to one anime illustration. It encodes what worked, what didn't, and the checks that stop broken renders from shipping.

## What it's good at

| Style | Verdict | Typical time |
|---|---|---|
| Pixel-art MV / explainer | ✅ publish-ready | 2-min MV in ~1–2 h |
| Flat cutout / motion graphics | ✅ publish-ready | 1-min in ~1.5–2 h |
| 2D character via AI motion transfer (Kling 「动作控制」 on a Claude-rendered driver) | ✅ keeps the illustration's style; needs a Kling account | driver ~1 h + post ~0.5 h |
| 2D rig animation of one illustration | ⚠️ idle or talking loops only; dance reads as a puppet | 20 s in ~1–3 h |
| 3D realistic | ❌ unless you bring a high-quality model | 20 s in 10–30+ h |

## Install

```bash
# 1) HyperFrames skills (the rendering engine and its authoring rules)
npx skills add heygen-com/hyperframes -s '*' -a claude-code -y

# 2) this skill
git clone https://github.com/a252937166/claude-video-studio ~/.claude/skills/claude-video-studio
```

Then ask Claude Code something like:

- 「用像素风给这首歌做个 MV」 — a pixel-art MV for this song
- 「把这个 docx 剧本做成科普动画，要配音」 — a narrated explainer from a docx script
- 「照着这个参考视频，用扁平风重做」 — remake a reference video in flat cutout style

## What's inside

- `SKILL.md` — the workflow:
  - pick the style first;
  - timed lyrics for AI music;
  - beat alignment;
  - the pixel and flat pipelines;
  - voice-over and SFX;
  - QA;
  - 3D caveats.
- `scripts/timed_lyrics.py` — lyrics → a bar-by-bar music prompt, plus `lyrics.json` and `.srt`.
- `scripts/align_beats.py` — measures the real song's offset against the planned bar grid (uses HyperFrames' `audiomap.json`).
- `scripts/pixel_sprite.py` — a stdlib pixel-sprite kit: palette grids → PNG, auto-outline, preview sheet.
- `scripts/qa_video.sh` — probes the MP4, scans every frame for black frames, and builds a contact sheet from frames extracted one by one.
- `scripts/add_cover.sh` — prepends a 1 s designed cover (sync-safe), embeds it as cover art, and exports 16:9, 4:3 and 3:4 covers.
- `scripts/make_green.py` — frames a cut-out character on flat green to match a driver video's first frame (for Kling / Veo).
- `scripts/standin_from_driver.py` — difference-keys a driver video against its clean plate into an alpha stand-in, so the camera plan can be rehearsed before paying for generation.
- `scripts/key_diff.py` — colour-difference keyer for AI green-screen footage, writing VP9-alpha WebM. Unlike chromakey, it keeps dark clothes solid; it also blanks a watermark corner.
- `scripts/lip_sync_check.py` — mouth openness against the vocal envelope with a lag scan. FaceMesh runs on 2× head crops, and an `area` metric handles drawn anime mouths.
- `scripts/recolor_iris.py` — recolours irises across a clip when an AI generator changes a character's eye colour.
- `references/hyperframes-gotchas.md` — seek-safety and render-leak rules for parallel frame workers.
- `references/qa-checklist.md` — pre-publish checklist, including China's AI-content labeling rule (2025-09-01).
- `references/3d-lessons.md` — seven 3D iterations of the same 20 s chorus, why the model is the bottleneck, and the per-frame motion and lip checks.
- `references/2d-motion-transfer.md` — the 2D pipeline that worked: driver → aligned image → Kling / Veo → keying, timing and lip checks → edit. It also covers the consistency traps.
- `references/2d-rig-lessons.md` — the mesh-rig route and its per-frame QA, and why dance still reads as a puppet.

## Requirements

- Claude Code (tested with Opus 5.5).
- Node 18+ (for `npx hyperframes`).
- Python 3 and ffmpeg.
- Optional:
  - `edge-tts` for voice-over;
  - `numpy` and `soundfile` for SFX;
  - Blender 4.5 LTS for 3D;
  - `mediapipe`, `scipy` and Pillow for the 2D motion-transfer scripts.

## Responsible use

- Label AI-generated videos (「AI 合成」 / "AI-generated").
- Don't make photoreal doubles of real people without their consent.
- Respect IP: fan-art characters, athletes and brands.
- Credit CC-BY assets.

## License

MIT
