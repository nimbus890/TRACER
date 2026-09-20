"""Build a standalone Windows application with its own GPU runtime and Tiny model."""
from pathlib import Path
import shutil
import sys
import importlib.metadata
import os

import core


def main():
    if not core.model_ready('tiny'):
        core.download_model('tiny', print)
    import PyInstaller.__main__
    root = Path(__file__).resolve().parent
    version_root = root.parent
    dist_root = version_root / 'portable'
    work_root = version_root / '.build'
    packages = Path(sys.prefix) / 'Lib' / 'site-packages'
    # Avoid collecting unrelated DLLs (for example Poppler's incompatible ICU)
    # from the developer machine's PATH. Windows provides Qt's ICU dependency.
    windows = Path(os.environ.get('WINDIR', 'C:/Windows'))
    os.environ['PATH'] = os.pathsep.join([str(Path(sys.base_prefix)), str(Path(sys.base_prefix) / 'DLLs'),
                                        str(windows / 'System32'), str(windows)])
    args = [str(root / 'app.py'), '--name=Tracer', '--noconfirm', '--windowed', '--onedir',
            '--distpath=' + str(dist_root), '--workpath=' + str(work_root),
            '--specpath=' + str(work_root), '--noupx', '--collect-all=faster_whisper',
            '--collect-all=ctranslate2', '--collect-all=av', '--collect-all=onnxruntime',
            '--collect-all=tokenizers', '--collect-all=huggingface_hub', '--copy-metadata=tqdm',
            '--copy-metadata=regex', '--copy-metadata=requests', '--hidden-import=PIL.ImageQt']
    # Only pass metadata for actually installed optional packages.
    for option in args[:]:
        if option.startswith('--copy-metadata='):
            try:
                importlib.metadata.distribution(option.split('=', 1)[1])
            except importlib.metadata.PackageNotFoundError:
                args.remove(option)
    for dll in (packages / 'nvidia').rglob('*.dll'):
        args.extend(['--add-binary', str(dll) + ';' + str(dll.parent.relative_to(packages))])
    if (root / 'assets' / 'transpro.ico').exists():
        args.extend([
            '--icon', str(root / 'assets' / 'transpro.ico'),
            '--add-data', str(root / 'assets') + ';assets',
        ])
    args.extend(['--add-data', str(root / 'VERSION') + ';.'])
    PyInstaller.__main__.run(args)
    dest = dist_root / 'Tracer'
    # Carry every locally available model into the portable build so an
    # existing installation never has to redownload its transcription or
    # visual-index dependencies after an upgrade.
    for model_dir in core.MODELS.iterdir():
        if model_dir.is_dir():
            shutil.copytree(model_dir, dest / 'data' / 'models' / model_dir.name,
                            dirs_exist_ok=True, ignore=shutil.ignore_patterns('.cache'))
    for file in ('README.md', 'THIRD-PARTY-NOTICES.md', 'VERSION'):
        shutil.copy2(root / file, dest / file)
    licenses = dest / 'licenses'
    licenses.mkdir(exist_ok=True)
    for distribution in importlib.metadata.distributions():
        for file in distribution.files or []:
            if any(word in str(file).lower() for word in ('license', 'copying', 'notice')) and str(file).lower().endswith(('.txt', '.md', 'license', 'copying', 'notice', '.rst')):
                source = Path(distribution.locate_file(file))
                if source.is_file():
                    target = licenses / distribution.metadata['Name'] / str(file).replace('/', '_').replace('\\', '_')
                    target.parent.mkdir(exist_ok=True)
                    shutil.copy2(source, target)
    print('Standalone application ready: ' + str(dest / 'Tracer.exe'))


if __name__ == '__main__':
    main()
