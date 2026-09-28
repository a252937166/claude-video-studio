# 3D lessons: one 20-second chorus, six versions

The same 20 s chorus was rebuilt six times over roughly 30+ hours. What each step taught:

| Version | Approach | What went wrong / right |
|---|---|---|
| v1 | three.js, a Rocketbox game avatar, the photo projected onto its head, JoyVASA lips, GFPGAN refine | "Crude, like last century." The lips were far off: JoyVASA opens about 5 times per 2.5 s bar against 14 sung syllables. |
| v2 | Poly Haven scenes (CC0), 22 AIST++ street-dance moves, lip frames re-timed to the vocal | The scenes were a clear step up. The body read "soft", and the mouth still didn't match. |
| v3 | A tee body, a sculpted physique, fur-shell hair, MuseTalk | "Deformed": the muscle sculpt was overdone, the head looked small, the shoulders ballooned under DQS skinning, and the hands were claws. |
| v3.1 | A lean build, arm-only DQS, hand presets, an upright rap stance in close-ups | Still a "rubber man". The model's quality was the ceiling. |
| v4 | Blender: cloth sim, hair curves, SSS skin, Bistro scene; a Naruto costume built on the same avatar | 「一点都不像」: re-dressing a generic avatar never becomes a specific person. |
| v5 | A ready-made high-quality community model (Sketchfab, CC-BY), the same motion retargeted | It finally read as the character. **The model was the bottleneck all along.** |

## Rules
1. **Model first.** Get a high-quality, rigged model before anything else. Sources:
   - Sketchfab: filter for downloadable, CC0/CC-BY; avoid game rips;
   - MetaHuman or Character Creator;
   - a photo-to-3D service, for a specific person who has consented.
2. **Real scenes are easy; real people are hard.**
   - Photogrammetry scans (Sketchfab CC-BY), Poly Haven (CC0) and NVIDIA ORCA Bistro (CC-BY) look real in Blender EEVEE.
   - Scans carry baked light: use them as mostly emissive, light the hero separately, and keep cameras inside the scanned area.
3. **Retarget by direction matching**, not raw rest-pose deltas. Scale the new model to the eye line the cameras frame, and check hands, feet and head against the source joints at the cut frames.
4. **Close-ups need a close-up-safe performance.** Use an upright stance, chest-level gestures and a clear face; save big dance moves for wide shots.
5. **Lip-sync on AI rap is hard.**
   - JoyVASA, MuseTalk 1.5 and LatentSync 1.5/1.6 all scored SyncNet about 1.6–1.8 (a static mouth: 0.9) on a reverb-heavy, doubled, AI-generated rap at 5.6 syllables/s.
   - Stylised characters: drive a jaw bone from the vocal envelope and syllable onsets instead.
6. **Budget honestly.**
   - EEVEE runs about 3–20 s per frame (the Bistro city is the slowest), so a 600-frame clip is about 1.5 h plus shader compile.
   - Each lip-sync model is 4–10 GB on disk. Ask before downloading, and delete what you don't use.
7. **Credits.** CC-BY needs attribution in the description. AIST++ motion is CC-BY, but its source database is research-only, so check before monetising.
