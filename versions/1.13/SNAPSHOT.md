# Tracer 1.13 source snapshot

This is the editable code snapshot for Tracer 1.13. It intentionally contains no downloaded models, Python environment, generated application, installer, verification media, or user library data.

For development and local launching, it shares the version 1 model/state repository at `C:\projects\TransPro\data`. The legacy folder and `TRANSPRO_DATA` environment name are retained so existing projects, models, analytics, and library records remain connected. Use `Launch Tracer 1.13.vbs` to start this exact code snapshot.

Version 1.13 replaces the Add media type menu with one read-only picker that accepts folders, individual videos, or both in one selection. The queue trash action and other functional glyphs use sharp, fully opaque white marks, while destructive hover feedback remains red. Video Library pagination uses compact icon-only arrows, matching search words are highlighted in the selected video's transcript, and Show in Explorer reveals the exact source file instead of opening only its parent folder.

Do not place minor-version model or analytics copies in this folder. Version 2 will receive a separate major-version shared model repository. Models should be bundled into `dist` and an installer only when an exportable build is explicitly requested.
