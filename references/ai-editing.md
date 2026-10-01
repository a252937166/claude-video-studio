# Editing real footage with Claude (AI editing)

This comes from one real job. The input was a 2:25 locked-off 4K60 take of a rabies first-aid explainer: one person talks, the other throws a basin of water in the last seconds.

The output was a 2:08 "time freeze" edit: the thrower and her water hang in mid-air until the talk ends, then the splash plays in slow motion. It has subtitles, step cards, stickers, SFX and an end card. Raw file to export took 1 h 47 min, including model downloads and one rework.

Three popular Douyin edits were then recreated on free stock footage: 舞蹈残影, 人物定格出场 and 曲线变速卡点.

Later additions:
- the PSA was re-dubbed from Sichuanese into Mandarin (`redub.py`);
- three effects of our own were built: 一人成团, 时间扫描 and 横屏转竖屏;
- every result was shown as an 原片 → AI 成片 reel.

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

Typical render times on an M4 Pro, 1080p:
- echo trail, 12.5 s of video: about 2 min;
- freeze intro, 14 s: about 40 s;
- speed ramp, 12.5 s: about 20 s.

## Extensions (our own effects, no tutorial needed)
| Effect | Script | What matters |
|---|---|---|
| 一人成团 (clone squad) | `clone_squad.py` | Clone k is the dancer from k × delay ago (half a beat reads as a canon), shifted k × spread sideways, scaled scale^k about her feet so it stands further back, dimmed, with a soft contact shadow. Firm up the clone masks (`(m − 0.3) / 0.4`) or fast moves turn see-through. Clones pop in on successive beats. Locked-off shot, one person. 12.5 s at 1080p takes about 1 min 40 s. |
| 时间扫描 (time-warp scan) | `time_scan.py` | A frozen canvas is filled strip by strip as the line passes; output = canvas behind the line, live frame ahead. The line moves mostly linearly with soft ends; hold the fully frozen frame about 1.2 s, then flash back to live. Groups of dancers give the most fun distortions. About 12 s to render. |
| 横屏转竖屏 (auto reframe) | `auto_reframe.py` | Pose centre per frame (nose, shoulders, hips), gaps interpolated, then a **zero-lag** forward-backward Gaussian (offline, so the frame anticipates instead of chasing), plus look-room lead from the smoothed velocity, clamped inside the picture. `--preview` writes the side-by-side explainer. Choose a clip where the subject crosses the frame, or the demo shows nothing. |

## Re-dub: dialect to Mandarin, or a voice that must not be published
`redub.py lines.json voice.wav --subs subs.json --total S`

**Lines.** Write them from the transcript, on the output clock.
- Rewrite only the dialect words, e.g. 等一哈→等一下, 啥子→什么, 狗儿和猫儿→小狗、小猫, 板板车→板车.
- Keep the speaker's meaning and order.

**Voice.**
- Match the speaker. Measure the F0 with pyin: about 265 Hz means a woman's voice, so use `zh-CN-XiaoxiaoNeural`.
- Synthesise a sentence that the subtitles split into one group (one TTS call), or each fragment ends with a falling, final-sounding tone.

**Fitting the rate.**
- Slower than −10 % sounds drawled.
- Faster than about +22 % sounds rushed. Exceed it only if the line would otherwise run into the next one.
- Start each group where the original line started. Stickers and gestures then stay in sync.

**Subtitles.**
- edge-tts `boundary="WordBoundary"` gives word offsets. Spread them per character to cut the group back into its subtitle lines.
- Captions lead the voice by about 0.1 s, which reads well.

**Bed.** Never put the original track under the dub.
- Loop room tone cut from pauses of the cleaned original. Check every chunk with pyin first: zero voiced frames.
- Level-match the chunks (about −38.5 dBFS) or the loop pumps.
- Keep the original only where it is voice-free (the splash). Check that with pyin **and** a spectrogram: ASR "hears" words like 没有 or 嗯 in rustle and in SFX sweeps.

**Graphics.** Re-render the subtitles, and grep the composition for dialect text in stickers and labels (板板车 on a cart).

**Check.** Transcribe the dub back with `transcribe_zh.py`. The text should match the script.

## Before / after reels
`before_after.py out.mp4 --after effect.mp4 --before raw.mp4@T0-T1 [...] --note "…" --crf 22`
- Show 3 to 7 s of the untouched source:
  - scaled to the result's size;
  - labelled 「原片 · 没加任何特效」;
  - **silent**, so a private voice or plain noise isn't published.
- Then a 0.8 s card, then the result with its audio.
- Mosaic the faces in the raw part too: run `face_mosaic.py` on a 1080p cut of the raw ranges.
- For a time-freeze job, show both the start of the take and the real throw at the end. Viewers then see that the action happened minutes later.

## Researching tutorials for a "manual vs AI" write-up
- Read 1–2 popular tutorials per effect:
  - `douyin-skills get-video-detail` gives likes, collects and comments;
  - transcribe the narration locally with `transcribe_zh.py`;
  - read the on-screen steps from contact sheets.
- Keep the downloads in a scratch folder. Link and credit; never embed.
- Count operations with one rule: each tap, drag, slider move or text entry = 1. Mark the repeated unit (per person, per beat, per layer, per freeze). Say that the totals are estimates.
- Quotes: put words in quotation marks only when they are verbatim, from comments or the transcript. A research summary paraphrased two "quotes"; check them before publishing.

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
