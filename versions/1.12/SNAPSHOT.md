# Tracer 1.12 source snapshot

This is the editable code snapshot for Tracer 1.12. It intentionally contains no downloaded models, Python environment, generated application, installer, verification media, or user library data.

For development and local launching, it shares the version 1 model/state repository at `C:\projects\TransPro\data`. The legacy folder and `TRANSPRO_DATA` environment name are retained so existing projects, models, analytics, and library records remain connected. Use `Launch Tracer 1.12.vbs` to start this exact code snapshot.

Version 1.12 moves queue removal into an icon-only trash action beside Add media. Add media offers native Windows Explorer pickers for a source folder or multiple individual video files. Added groups expand automatically for immediate per-video selection, and deleting a child row removes only that queue entry—not the source file.

Do not place minor-version model or analytics copies in this folder. Version 2 will receive a separate major-version shared model repository. Models should be bundled into `dist` and an installer only when an exportable build is explicitly requested.
