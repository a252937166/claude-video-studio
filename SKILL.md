---
name: claude-video-studio
description: Make short videos (Douyin/TikTok/Reels/Shorts) with Claude Code as a code-driven animator. Use it when the user wants a music video, lyric MV, pixel-art or flat-cutout animation, a narrated explainer or PSA, or asks which video style Claude does well. It picks a style by what renders reliably (pixel and flat cutout first; 2D rig animation and 3D only with caveats), writes timed lyrics for AI music, builds pixel characters from photos, cuts to the beat with HyperFrames, and QA-checks the MP4 before publishing.
---

# Claude Video Studio

Claude makes video by **writing code that draws every frame**: HTML, CSS and GSAP, rendered to MP4 by [HyperFrames](https://hyperframes.heygen.com). It does not generate pixels the way Sora, Kling or Veo do. Pick styles that code can draw well, and be honest about the rest.

## 0. Prerequisites

- **HyperFrames** CLI and skills. Pin a version so re-renders stay identical:

  ```bash
  npx skills add heygen-com/hyperframes -s '*' -a claude-code -y   # installs the /hyperframes skill family
  npx --yes hyperframes@0.8.70 init my-video                        # or: HYPERFRAMES_SKIP_SKILLS=1 if the skill fetch hangs
  ```

  Load `/hyperframes` for the core authoring contract.
- **Python 3** for the scripts in `scripts/`. They use the standard library only, except `align_beats.py`, which reads HyperFrames' `audiomap.json`.
- Optional:
  - `edge-tts` for voice-over;
  - `numpy` and `soundfile` for 8-bit SFX;
  - `ffmpeg` for QA and covers.

## 1. Choose the style first

Answer with this table before building anything. Don't promise a style that will disappoint.

| Style | Reliability | Typical time | Use for |
|---|---|---|---|
| **Pixel art** (characters as sprite sheets, game UI) | ★★★★★ | 2-min MV ≈ 1–2 h | lyric MVs, personal stories, PSAs, game-style narratives |
| **Flat cutout / motion graphics** (shapes, flat characters, kinetic type) | ★★★★★ | 1-min ≈ 1.5–2 h | famous-moment remakes, product launches, explainers, data |
| **2D rig animation** (layered parts on bones, like Live2D or Spine) | ★★ | varies | simple character acting, talking heads. **Not** frame-by-frame hand-drawn motion |
| **3D realistic** (three.js or Blender) | ★ | 20 s ≈ 10–30+ h | only with a **high-quality ready-made model**; scenes can be real (scans, Poly Haven) |

Rules of thumb:

- **Realism of a specific person in 3D depends almost entirely on the model.** Re-dressing a generic game avatar never becomes that person. Say so up front, and offer:
  - a downloaded high-quality model (Sketchfab CC0/CC-BY, MetaHuman, Character Creator);
  - or an AI video model for the human shots, with Claude doing edit, captions and packaging.
- A few or low-res photos of a person → draw a **pixel character** from them instead of using the photos directly.
- Real people's likeness: don't make a photoreal double of a real person without their real consent. Use a fictional or AI-generated person, or a stylised character.

## 2. Music with an exact timeline (for lyric MVs)

AI music apps (Gemini/Lyria, Suno, …) follow timing much better when you give it bar by bar.

1. Write the lyrics as **one line per bar**. Fix the tempo: 96 BPM gives 1 bar = 2.5 s; 120 BPM gives 2.0 s.
2. `python3 scripts/timed_lyrics.py lyrics.txt --bpm 96 --title "…" --style "…"` writes:
   - `prompt.txt` to paste into the music app;
   - `lyrics.json` with start and end per line;
   - `lyrics.srt`.
3. The user generates the song and hands you the MP3.
4. Run HyperFrames' `analyze-beatgrid.py` on it (`music-to-video` skill) → `audiomap.json`.
5. `python3 scripts/align_beats.py audiomap.json --bpm 96` measures the **offset** between the plan grid and the real downbeats. It is usually +0.1 to +0.3 s. Every lyric and cut time is then `plan + offset`.
6. If the generated song is shorter, or stops early, re-time the ending to the real audio. Never stretch the music.

## 3. Pixel pipeline

- **Characters.**
  - Hand-author sprite grids in Python: `scripts/pixel_sprite.py` is a stdlib PNG writer with a palette, an auto-outline and preview sheets.
  - Use 15–25 poses per hero: idle, blink, talk, walk-a/b, jump/squat, cheer, sad, point, plus actions specific to the story.
  - Draw from the photo's traits: hair shape and colour, glasses, outfit.
- **Rig (seek-safe).**
  - Stack one `<img>` per pose.
  - A pose swap is **one** `tl.set(list, {autoAlpha: i => el === show ? 1 : 0}, t)`. Two sets at the same instant break backward seeking.
  - Hidden poses start with `visibility: hidden; opacity: 0`.
  - Scale by integers only, with `image-rendering: pixelated`.
- **Structure.**
  - Split the song into 6–8 frames (sub-compositions) by section, and let sub-agents write them in parallel from a shared kit (CSS, rig, HUD) and a `WORKER-NOTES.md` with the hard rules (see `references/hyperframes-gotchas.md`).

## 4. Flat cutout / motion-graphics pipeline

- **Kit.** Keep all drawing in `assets/kit.js`: characters as SVG/DOM parts, stadium, UI chrome. Put one file per scene in `assets/scene1..N.js` and beat times in `assets/data.js`.
- **Timing.** Hit the beat grid: every cut, hit and text pop lands on `beats[i] + offset`.
- **Reference-driven.** When the user sends a reference video, describe its structure beat by beat first, then rebuild it in your own drawing style. Don't copy assets.

## 5. Voice-over and SFX (explainers / PSAs)

- **Script.** Take the user's script **verbatim**; don't paraphrase medical or legal text.
- **Voices** (edge-tts):
  - narrator `zh-CN-YunyangNeural`;
  - young man `zh-CN-YunxiNeural`;
  - young woman `zh-CN-XiaoyiNeural`;
  - elder sister `zh-CN-XiaoxiaoNeural`;
  - doctor `zh-CN-YunjianNeural`.
  - Generate per line, trim the silence, then place each line on a timeline.
- **Timing.** The picture follows the voice: build `timeline.json` from the real line durations, then animate.
- **SFX.** Synthesize 8-bit SFX with numpy (blips, steps, heartbeat, rewind) and mix them into one voice track. Offer a no-voice version too, with the music louder and loudnorm at −16 LUFS.

## 6. QA — never trust the preview alone

Run the checklist in `references/qa-checklist.md`. The essentials:

- `npx hyperframes check --no-contrast` passes, and snapshots are reviewed.
- **Extract frames from the rendered MP4 one by one** (`ffmpeg -ss T -i out.mp4 -frames:v 1`). Renders can differ from snapshots: a stray `visibility: visible` showed one frame over the whole video.
- Scan every frame for black or blank frames (`signalstats` YAVG).
- **Cover.** The first frame must be a designed cover, never black. Add 1 s of cover plus 1 s of silence at the start. Embed the cover as `attached_pic`. Export 16:9, 4:3 and 3:4 cover PNGs.
- **AI label.** Burn in 「AI 合成」 / "AI-generated" for the whole clip. China's labeling rules are in force since 2025-09-01. Tick the platform's AI declaration when posting.
- Put credits for CC-BY assets (models, scenes, motion data) in the description.

## 7. 3D (only if the user insists) — see `references/3d-lessons.md`

- Scenes:
  - real scans (Sketchfab CC-BY);
  - Poly Haven (CC0);
  - NVIDIA ORCA Bistro (CC-BY);
  - rendered in Blender EEVEE (a few seconds to 20 s per frame).
- Characters: a ready-made high-quality rigged model (Mixamo-style rigs retarget cleanly). Retarget by direction matching, not raw rest deltas.
- Motion:
  - dance from mocap (AIST++ is CC-BY, but its source DB is research-only, so check before monetising);
  - close-ups need upright, face-clear "rap stance" gestures.
- Lip-sync on AI-generated, reverb-heavy rap stays weak. JoyVASA, MuseTalk and LatentSync all scored SyncNet ≈ 1.6–1.8 on it (a static mouth scored 0.9). Say so honestly.
- Budget: disk (models of 4–10 GB each) and hours. **Ask before any multi-GB download.**

## 8. Working style (lessons from real sessions)

- Show a storyboard or a still first, and render after approval.
- Give honest limits early. Don't burn hours polishing a dead end: the 3D re-dress was.
- Keep the user posted with short progress lines during long runs.
- Delete intermediates and ask before large downloads. Disk fills fast.
