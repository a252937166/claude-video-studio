# claude-video-studio

A Claude Code skill for making short videos (Douyin / TikTok / Reels / Shorts) with **Claude as a code-driven animator**. Claude writes HTML/GSAP that draws every frame, and [HyperFrames](https://hyperframes.heygen.com) renders it to MP4.

It comes out of one week of real projects: five pixel-art MVs and PSAs, flat-cutout World Cup edits, and six rounds of 3D experiments. It encodes what worked, what didn't, and the checks that stop broken renders from shipping.

## What it's good at

| Style | Verdict | Typical time |
|---|---|---|
| Pixel-art MV / explainer | ✅ publish-ready | 2-min MV in ~1–2 h |
| Flat cutout / motion graphics | ✅ publish-ready | 1-min in ~1.5–2 h |
| 2D rig animation | ⚠️ simple acting only | — |
| 3D realistic | ❌ unless you bring a high-quality model | 20 s in 10–30+ h |

## Install

```bash
# 1) HyperFrames skills (the rendering engine and its authoring rules)
npx skills add heygen-com/hyperframes -s '*' -a claude-code -y

# 2) this skill
git clone https://github.com/<you>/claude-video-studio ~/.claude/skills/claude-video-studio
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
- `references/hyperframes-gotchas.md` — seek-safety and render-leak rules for parallel frame workers.
- `references/qa-checklist.md` — pre-publish checklist, including China's AI-content labeling rule (2025-09-01).
- `references/3d-lessons.md` — six 3D iterations of the same 20 s chorus, and why the model is the bottleneck.

## Requirements

- Claude Code (tested with Opus 5.5).
- Node 18+ (for `npx hyperframes`).
- Python 3 and ffmpeg.
- Optional:
  - `edge-tts` for voice-over;
  - `numpy` and `soundfile` for SFX;
  - Blender 4.5 LTS for 3D.

## Responsible use

- Label AI-generated videos (「AI 合成」 / "AI-generated").
- Don't make photoreal doubles of real people without their consent.
- Respect IP: fan-art characters, athletes and brands.
- Credit CC-BY assets.

## License

MIT
