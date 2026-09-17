# Tracer

A local Windows desktop app for folder-based video transcription, screenshot extraction, and offline footage search.

## Open the app

Double-click **Launch Tracer.vbs** in this folder to open the current working build. A future export build will be created as **dist/Tracer/Tracer.exe**.
The standalone app includes Python, the video decoder, NVIDIA runtime libraries, Tiny Whisper, and the small visual-search model.
The editable 1.11 source is preserved under **versions/1.11**. Its installer is intentionally deferred until an exportable build is requested; completed earlier TransPro installers remain in **release**.

## Workflow

1. Click **Add folders**. Ctrl-click to select multiple folders; add more with the same button.
2. Double-click a folder to expand its videos. Check or uncheck individual videos, or the entire folder.
3. Use the arrow buttons to change the folder order. **Rescan** discovers new files; **Remove** removes only the queue entry.
4. Click **Process folders** and choose any combination of the three small, opaque icon tiles above Start. Hover an icon for its Transcript, Screenshots, or searchable Visual Index explanation; unrelated settings fade when that output is off.
5. For screenshots, choose a 0.1–30 second interval (type an exact value or use the slider), or activate **Scene change** on the same row. Image quality and the joined JPEG/PNG selector share one row; hover either format for details.
6. Click the gear icon to open **Advanced settings** beside the main controls only when you need to change the processing device, the default Standard 1280 px screenshot size, or choose among multiple installed Whisper models. A model selector is not shown when only one model is installed.
7. Review the single-line totals for screenshot count, estimated processing time and output size. Choose an alternate results location if desired, then start.
8. Open **Video library** to search transcripts, source names, and visual keywords from one bar. The icon-only Audio and Visual controls choose which indexed information to search, while the depth menu can narrow visual matches to foreground, midground, or background. Hover either icon for its meaning.
9. Results appear as videos first. Choosing one slides the browser away, replaces the page heading with the selected filename, and leaves a transcript-first workspace, source preview, and full-width frame gallery. **See All** slides the list over the left edge of the workspace without resizing the media dashboard. Drag the divider between transcript and preview left or right to suit the footage. Separate buttons open the generated results and original video's folder.

## Projects

The Project Dashboard sits below the Folder Queue. Create a named project, then add any combination of source folders and individual videos. A project remembers its sources and selections and runs them as one batch. Project results are tagged in the Video Library. Removing a project or source only removes the dashboard reference; it does not delete source media, transcripts, screenshots, or library results.

During processing, the percentage represents the entire selected batch, weighted by video duration and by the enabled transcription, screenshot, and visual-index work. A finished or failed item advances the total. Cancelling preserves the percentage reached instead of showing a misleading 100%.

## Unified offline search in 1.11

The included NanoDet object detector samples footage every 30 seconds by default and stores a small thumbnail plus up to five unique object keywords for each approximate foreground, midground, and background layer. The per-video `visual-index.json` file is saved beside other outputs. Detection runs locally and never uploads footage. Layer labels are screen-space estimates based on object size and position, not true depth measurements.

Search lives inside Video Library instead of a separate Footage Search page. Source names are always searchable; the Audio and Visual icons independently include transcript text and visual-index keywords. Results are grouped by video to avoid flooding the screen with repeated frames. Selecting a video reveals its matching coarse moments. Double-clicking one creates a lazy contact strip at five-second intervals for that 30-second region; those detail frames are cached in the result folder.

## Processing and files

Folders are processed in order, one video at a time. Screenshot extraction, transcription, and visual indexing run concurrently for that video. Pause and cancel are cooperative: they take effect at the next decoded or analysed frame or transcription segment, so an active calculation may take a little time to stop. No new video starts after cancellation.

By default, new outputs live in a **Tracer Results** folder inside each selected folder, with a separate subfolder per video/run. Names include a source-path identifier and timestamp to avoid collisions. Original videos are not modified. Recursive scans exclude both Tracer Results and legacy TransPro Results folders. An alternate destination groups results by source folder.

Transcripts are exported in TXT, SRT, VTT, and JSON, with a processing-details.json manifest linking each image to its actual video timestamp. Videos without audio still get screenshots and clearly marked empty transcripts. Transcription-only runs create no screenshots directory.

Completed runs with matching input file size/modification time and processing settings are reused by default. Turn on **Redo existing results** to make a fresh result instead. Failed and cancelled runs retain their partial files with a status manifest. A retry starts that video again; it does not resume halfway through a transcription. App restarts preserve the queue, results and options, and mark unfinished work as interrupted.

Every processing attempt also appends a local performance record to `data/analytics/processing-history.jsonl`. It includes the app version, selected modes and settings, source media properties, elapsed time, processing speed, model/device/language, output size, screenshot/index counts, transcript word and segment counts, reuse/completion/failure state, and error details. It does not duplicate transcript sentences or visual keywords, and nothing is uploaded. Settings includes **Open performance data** for inspection. This shared data folder is not copied into minor-version source snapshots.

## Models and GPU

Tiny Whisper and the lightweight visual-search model are included during installation. Settings can download Base, Small, Medium, and Large v3. Downloads can be retried if interrupted. Inference runs locally after download; no account or API key is required. Downloading models contacts Hugging Face; it does not upload videos.

The engine is faster-whisper, running the open-source Whisper models through CTranslate2. Automatic mode prefers NVIDIA CUDA with int8/float16 computation; it can fall back to CPU. GPU-only mode reports a failure instead of silently switching. NVIDIA drivers must support the bundled CUDA 12 runtime. Medium and Large consume more memory and time. Tiny is fast but may be less accurate, particularly with noise or mixed-language speech.

The Settings page keeps every Whisper download in one compact, readable row. Model removals are recoverable: they move into data/removed-models. They do not free space until those backups are deleted. The app provides a button to open that folder.

## Estimates and limitations

- JPEG and PNG sizes are approximate and depend strongly on image detail; the estimate uses dimensions, format, and JPEG quality rather than a full encode. Scene-mode estimates assume one cut per five seconds and can vary substantially.
- Scene mode detects abrupt changes in downsampled frames. It may miss fades and can react to flashes or fast motion.
- At a 0.1-second interval, an hour of video can create 36,000 images. Sampling is limited by the source frame rate; capture times correspond to actual decoded frames.
- The app checks estimated free space before each video and stops frame extraction if the destination falls below 100 MB free.
- Transcript timing and text are model predictions. Automatic speaker identification and translation are not part of this version.
- Visual search recognises 80 common object categories. It does not yet understand mood, lighting, composition, camera movement, identity, or production design; those belong to the planned offline-analysis beta.
- Video playback depends on Qt/FFmpeg codec support. Exported images and transcripts remain accessible if playback is unavailable.
- Keep the entire future standalone Tracer folder together. Its data folder stores models and library history. The per-user installer will preserve data on uninstall.

## Development

Use Python 3.12 on Windows x64. Create a virtual environment and install requirements.txt. Run `python app.py`. Build with `python build.py`, then compile Tracer.iss using Inno Setup 6.7 or newer. The Inno compiler is a build tool, not an app dependency; commercial use of that compiler may require a license.

Editable minor-version snapshots live under `versions`. They contain code, tests, assets, and build files, but intentionally exclude downloaded models, environments, generated builds, and verification media. Every 1.x snapshot reads the shared v1 model store at `data/models`; a new shared model store will be created for version 2. Models are copied into a distributable installer only for an explicitly requested export build.

Tests: `python -m unittest discover -s tests -v`. `verify.py gpu` uses verification/speech.wav to test actual GPU transcription and screenshot processing. `verify.py ui` checks controls and saves offscreen screenshots. These use generated test media, not user videos.
