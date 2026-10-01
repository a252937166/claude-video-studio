# Editing real footage with Claude (AI editing)

This comes from one real job. The input was a 2:25 locked-off 4K60 take of a rabies first-aid explainer: one person talks, the other throws a basin of water in the last seconds.

The output was a 2:08 "time freeze" edit: the thrower and her water hang in mid-air until the talk ends, then the splash plays in slow motion. It has subtitles, step cards, stickers, SFX and an end card. Raw file to export took 1 h 47 min, including model downloads and one rework.

Three popular Douyin edits were then recreated on free stock footage: 舞蹈残影, 人物定格出场 and 曲线变速卡点.

> **Dependencies** (run `python3 scripts/check_env.py`, then ask the user before installing anything):
> - `requirements-edit.txt`: OpenCV and friends, about 250 MB.
> - `requirements-face.txt`: mediapipe, about 600 MB.
> - `requirements-asr.txt`: FunASR and torch, about 1 GB, plus 1–3 GB of models on first run.
> - `noisereduce` for speech cleanup.

## Pipeline for talking-head and explainer footage
1. **Look first.**
   - Make a 540p proxy: `ffmpeg -hwaccel videotoolbox -i raw.mp4 -vf scale=960:540,fps=30 …`.
   - Make contact sheets: the whole take at 1 fps, then the start and end at 2–6 fps.
   - Find where the talk really starts (e.g. once the speaker sits down), where it ends, and the action moment.
2. **Transcribe.** Run `scripts/transcribe_zh.py raw.mp4 asr.json --srt asr.srt --hotwords "…"`.
   - It gives per-character timestamps, pauses of 1.2 s or more, and repeat candidates. Candidates include scrambled restarts like 「消口伤毒…消毒伤口」.
   - For dialects (e.g. Sichuanese), add `--nano` and cross-check the two models' readings. One model heard 「科普」 as 「泡泡」 and the other as 「客泼」; together they decode it.
   - whisper hallucinates on short dialect chunks: repeated words, and fake "subtitle volunteer" credits. Don't trust it alone for Chinese dialects.
3. **Cuts, as an EDL in JSON** (source ranges, speed, camera).
   - Trim the head and tail, cut the slips, and cut dead pauses of about 3 s. Keep natural breaths.
   - Snap every segment to whole output frames, so audio placed at the EDL times stays frame-locked.
   - With one fixed framing, put 8-frame dissolves on the jump cuts.
4. **Framing.** Use one fixed crop (e.g. 1.4×, everyone in frame, feet clear) unless the user asks for camera moves.
   - Auto push-ins and zoom punches were rejected: 「视频不要放大缩小」.
5. **Time freeze.** Run `scripts/time_freeze.py raw.mp4 out.mp4 --freeze-at T --from A --empty-at E --zone …`.
   - Pick the freeze frame by stepping through the action at the source fps, and take the most photogenic one (the water arc at full extension).
   - The region is the union of every pose the frozen person takes while the freeze is on screen, plus the freeze frame's own content (the water).
   - Only blobs connected to the freeze frame are kept, so another person walking through the zone is not frozen.
   - Per channel, the frozen patch is gain-matched to a ring of background, because clouds change the light.
6. **Watermark.** Run `scripts/dewatermark.py in.mp4 out.mp4 --box … --shift 0,-H`.
   - The stroke mask comes from the temporal-minimum luminance.
   - Texture is transplanted from just above the box, so it moves with the scene. Use `--method inpaint` on flat backgrounds.
7. **Graphics layer in HyperFrames.** The EDL feeds a `data.js`.
   - Subtitles go under the speaker, with keywords enlarged: yellow, or red for warnings.
   - Step cards slam in on 「第X步」 and collapse into a top tracker.
   - Use impact words that dim the frame, stickers at cue times, a pause/play tag on the freeze, and an end card that summarises the steps.
8. **Audio.**
   - Cut the speech with the same EDL, using 12 ms fades.
   - Run `noisereduce` with a noise print taken from the pauses (stationary, `prop_decrease` 0.75), then a 110 Hz high-pass, a gentle compressor and `loudnorm` at −16 LUFS. On the real job SNR went from 6.4 to 12.4 dB.
   - Synthesise the SFX with numpy (pop, whoosh, impact, freeze, resume, chime) at the cue times.
9. **Slow motion.**
   - A 60 fps source simply plays at 0.5×.
   - A 24/30 fps source needs optical-flow interpolation (`scripts/speed_ramp.py` does this).
10. **Privacy.** Before footage of people who did not agree to be shown goes into an article or tutorial, run `scripts/face_mosaic.py in.mp4 out.mp4 --pose --expect N`.
    - It detects on 2× tiles plus a pose-based head box (masks, sunglasses, turned heads), tracks, holds and back-fills.
    - The audit JSON lists frames with fewer boxes than expected. Look at those: usually the person has simply left the frame.
11. **QA on the render.**
    - Run a frozen-frame scan.
    - Scan for freeze-zone leaks: the per-frame mean difference inside the frozen zone should stay below about 1/255, and spikes mean live pixels are showing.
    - Check lip sync on the render with `scripts/lip_sync_check.py`, expecting −1 to −2 frames.
    - Check loudness, check that the first frame is a designed cover, and check sync after the cover.

## Popular edits: recipes
| Effect | Script | What matters |
|---|---|---|
| 舞蹈残影 (afterimage) | `echo_trail.py` | Locked-off shot of one dancer. Selfie segmentation plus a guided filter, last N×delay frames recoloured neon behind the live dancer, background dimmed. Beat flash and zoom punch, with white silhouettes on downbeats. |
| 人物定格出场 (freeze intro) | `freeze_intro.py` | Full-frame segmentation fails on groups in low light, and MediaPipe Pose picks the most prominent person. So paint everything outside the target's box with the clean plate (temporal median), segment a square crop, and intersect with a pose envelope. Confident skeleton-core pixels survive the plate check; fill holes. Name cards on stock people: describe clothing, never invent real names. |
| 曲线变速卡点 (speed ramp) | `speed_ramp.py` | Speed is `fast − (fast − slow)·exp(−((t − hit)/w)²)`, with the hit frame on a beat. The script errors if the source range leaves the clip. DIS optical-flow interpolation below 0.9×, frame-blend motion blur above 1.4×. A live 「速度 ×0.25」 readout teaches the curve. |

Typical render times on an M4 Pro, 1080p: echo trail 12.5 s in about 2 min, freeze intro 14 s in about 40 s, speed ramp 12.5 s in about 20 s.

## Sourcing and rights
- **Stock video.** The Mixkit Stock Video Free License allows commercial and non-commercial use, modification and distribution, with no attribution required (credit is appreciated). Check each clip's licence on Pexels or Pixabay the same way.
- **Someone else's video used as the reference for an effect.** Link to it and describe it; don't download it into your article or re-post it.
- **Music.** Use the user's own tracks or properly licensed ones. Don't put copyrighted song lyrics on screen.
- **Faces.** Mosaic people who didn't agree to appear (see the privacy step).

## Lessons from the real job
- **Ghost arm.** A freeze region built from the throw alone leaked the thrower's arm when she bent down later to pick up the basin. The user caught it from a screenshot. Fix: the union of all poses (now built into `time_freeze.py`).
- **Auto camera moves.** Unrequested zooms were rejected. Default to one fixed framing.
- **Downloads.** Ask before downloading ASR models (1.6–3 GB). ModelScope is much faster than Hugging Face from China.
- **ffmpeg builds without `drawtext`.** Render text with Pillow or HyperFrames instead.
