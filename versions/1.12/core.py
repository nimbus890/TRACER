"""Local video processing. UI independent, with cooperative batch controls."""
from __future__ import annotations

import concurrent.futures
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import sys
import threading
import time
import uuid

APP_VERSION = '1.12.0'
ROOT = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
if getattr(sys, 'frozen', False):
    default_data = ROOT / 'data'
elif ROOT.parent.name.casefold() == 'versions':
    # Minor-version source snapshots share one model/state store for their major version.
    default_data = ROOT.parent.parent / 'data'
else:
    default_data = ROOT / 'data'
DATA = Path(os.environ.get('TRANSPRO_DATA', str(default_data)))
MODELS = DATA / 'models'
VISUAL_MODEL_NAME = 'object_detection_nanodet_2022nov.onnx'
VISUAL_MODEL_REPO = 'opencv/opencv_zoo'
VISUAL_MODEL_FILE = 'models/object_detection_nanodet/' + VISUAL_MODEL_NAME
OUTPUT_NAME = 'Tracer Results'
LEGACY_OUTPUT_NAMES = {OUTPUT_NAME, 'TransPro Results'}
EXTENSIONS = {'.mp4', '.mkv', '.mov', '.avi', '.webm', '.m4v', '.mpeg', '.mpg', '.mts', '.m2ts', '.wmv', '.flv'}
MODEL_INFO = {
    'tiny': ('Tiny · Fast', '75 MB', 'Systran/faster-whisper-tiny'),
    'base': ('Base · Light', '145 MB', 'Systran/faster-whisper-base'),
    'small': ('Small · Balanced', '465 MB', 'Systran/faster-whisper-small'),
    'medium': ('Medium · Accurate', '1.5 GB', 'Systran/faster-whisper-medium'),
    'large-v3': ('Large v3 · Highest accuracy', '3.1 GB', 'Systran/faster-whisper-large-v3'),
}
DEFAULTS = dict(model='tiny', interval=5.0, mode='interval', scene_threshold=0.22,
                language='', device='auto', recursive=True, width=1280, quality=85,
                image_format='jpeg',
                screenshots=True, transcribe=True, visual_index=True, visual_interval=30.0,
                skip_existing=True, output='')
_dll_handles = []
_analytics_lock = threading.Lock()


def configure_gpu():
    if os.name != 'nt':
        return
    roots = [Path(sys.prefix) / 'Lib' / 'site-packages', Path(getattr(sys, '_MEIPASS', ROOT))]
    paths = []
    for root in roots:
        for name in ('cublas', 'cudnn', 'cuda_nvrtc'):
            paths.extend(p for p in (root / 'nvidia' / name / 'bin', root / 'nvidia' / name / 'lib') if p.is_dir())
    for p in paths:
        _dll_handles.append(os.add_dll_directory(str(p)))
    os.environ['PATH'] = os.pathsep.join(map(str, paths)) + os.pathsep + os.environ.get('PATH', '')


configure_gpu()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def analytics_file():
    override = os.environ.get('TRANSPRO_ANALYTICS_FILE')
    return Path(override) if override else DATA / 'analytics' / 'processing-history.jsonl'


def processing_analytics(path, video, options, outcome, started_at, elapsed, result=None, error=None):
    """Append a privacy-conscious local run summary; analytics must never break processing."""
    result = result or {}
    segments = result.get('segments', [])
    visual = result.get('visual_index', {})
    transcript_words = sum(len(s.get('text', '').split()) for s in segments)
    duration = float(video.get('duration', 0) or 0)
    event = {
        'schema_version': 1,
        'event_id': uuid.uuid4().hex,
        'recorded_at': time.time(),
        'app_version': APP_VERSION,
        'outcome': outcome,
        'source': {
            'path': str(path),
            'name': Path(path).name,
            'extension': Path(path).suffix.casefold(),
            'bytes': int(video.get('bytes', 0) or 0),
            'duration_seconds': duration,
            'width': int(video.get('width', 0) or 0),
            'height': int(video.get('height', 0) or 0),
            'fps': float(video.get('fps', 0) or 0),
            'has_audio': bool(video.get('audio', False)),
        },
        'settings': {
            'transcript': bool(options.get('transcribe')),
            'screenshots': bool(options.get('screenshots')),
            'visual_index': bool(options.get('visual_index')),
            'whisper_model': options.get('model') if options.get('transcribe') else None,
            'device_requested': options.get('device') if options.get('transcribe') else None,
            'language_requested': options.get('language') or 'automatic' if options.get('transcribe') else None,
            'screenshot_mode': options.get('mode') if options.get('screenshots') else None,
            'screenshot_interval_seconds': options.get('interval') if options.get('screenshots') and options.get('mode') == 'interval' else None,
            'screenshot_width': options.get('width') if options.get('screenshots') else None,
            'image_format': options.get('image_format') if options.get('screenshots') else None,
            'image_quality': options.get('quality') if options.get('screenshots') and options.get('image_format') == 'jpeg' else None,
            'ai_sampling_seconds': options.get('visual_interval') if options.get('visual_index') else None,
            'redo_existing': not bool(options.get('skip_existing')),
        },
        'performance': {
            'started_at': started_at,
            'processing_seconds': round(float(elapsed), 3),
            'realtime_factor': round(float(elapsed) / duration, 4) if duration else None,
            'footage_speed_x': round(duration / float(elapsed), 3) if elapsed else None,
        },
        'result': {
            'id': result.get('id'),
            'output': result.get('output'),
            'bytes': int(result.get('bytes', 0) or 0),
            'device_used': result.get('device'),
            'language_detected': result.get('language'),
            'screenshot_count': len(result.get('frames', [])),
            'transcript_segments': len(segments),
            'transcript_words': transcript_words,
            'visual_index_frames': len(visual.get('frames', [])),
            'visual_keyword_count': len(visual.get('search_words', [])),
        },
        'error': ({'type': type(error).__name__, 'message': str(error)} if error else None),
    }
    try:
        target = analytics_file()
        target.parent.mkdir(parents=True, exist_ok=True)
        with _analytics_lock, target.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(event, ensure_ascii=False, separators=(',', ':')) + '\n')
    except (OSError, TypeError, ValueError):
        pass
    return event


def load_state():
    try:
        value = json.loads((DATA / 'library.json').read_text(encoding='utf-8'))
        value.setdefault('projects', [])
        for collection in [value.get('folders', [])] + [project.get('folders', []) for project in value['projects']]:
            for folder in collection:
                for video in folder.get('files', []):
                    if video.get('status') in ('Processing', 'Queued', 'Paused'):
                        video['status'] = 'Interrupted'
        return value
    except FileNotFoundError:
        return dict(folders=[], projects=[], settings=DEFAULTS.copy(), results=[])
    except (ValueError, TypeError, KeyError):
        backup = DATA / f'library-recovery-{int(time.time())}.json'
        shutil.copy2(DATA / 'library.json', backup)
        return dict(folders=[], projects=[], settings=DEFAULTS.copy(), results=[], recovery=str(backup))


def model_ready(name):
    p = MODELS / name
    return (p / 'ready.json').exists() and all((p / f).is_file() for f in ('model.bin', 'config.json', 'tokenizer.json'))


def visual_model_path():
    direct = MODELS / 'visual-index' / VISUAL_MODEL_NAME
    if direct.is_file():
        return direct
    return next((p for p in (MODELS / 'visual-index').rglob(VISUAL_MODEL_NAME) if p.is_file()), direct)


def visual_model_ready():
    return visual_model_path().is_file()


def download_visual_model(notify=lambda s: None):
    if visual_model_ready():
        notify('Visual search model is ready')
        return
    notify('Downloading visual search model · about 4 MB…')
    from huggingface_hub import hf_hub_download
    target = MODELS / 'visual-index'
    target.mkdir(parents=True, exist_ok=True)
    source = Path(hf_hub_download(VISUAL_MODEL_REPO, VISUAL_MODEL_FILE, local_dir=str(target)))
    shutil.copy2(source, target / VISUAL_MODEL_NAME)
    notify('Visual search model is installed and ready')


def download_model(name, notify=lambda s: None):
    if name not in MODEL_INFO:
        raise ValueError('Unknown model')
    from huggingface_hub import snapshot_download
    if model_ready(name):
        notify(f'{name} is ready')
        return
    notify(f'Downloading {MODEL_INFO[name][0]} ({MODEL_INFO[name][1]})…')
    folder = MODELS / name
    snapshot_download(MODEL_INFO[name][2], local_dir=str(folder),
                      allow_patterns=['model.bin', 'config.json', 'tokenizer.json', 'vocabulary.*', 'preprocessor_config.json'])
    from faster_whisper import WhisperModel
    check = WhisperModel(str(folder), device='cpu', compute_type='int8', local_files_only=True)
    del check
    atomic_json(folder / 'ready.json', {'model': name, 'downloaded': time.time()})
    notify(f'{MODEL_INFO[name][0]} is installed and ready')


def model_bytes(name):
    return sum(p.stat().st_size for p in (MODELS / name).rglob('*') if p.is_file())


def remove_model(name):
    if name not in MODEL_INFO:
        raise ValueError('Unknown model')
    p = (MODELS / name).resolve()
    if p.parent != MODELS.resolve():
        raise ValueError('Invalid model path')
    if p.exists():
        # Recoverable deletion; an explicit cleanup can be performed outside the app.
        dest = DATA / 'removed-models' / f'{name}-{uuid.uuid4().hex[:8]}'
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dest))
        return str(dest)


def gpu_info():
    import subprocess
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                                capture_output=True, text=True, timeout=8, creationflags=0x08000000 if os.name == 'nt' else 0)
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return 'No NVIDIA GPU detected · CPU available'


def probe(path):
    import av
    with av.open(str(path)) as container:
        if not container.streams.video:
            raise ValueError('No video stream')
        stream = container.streams.video[0]
        duration = float(stream.duration * stream.time_base) if stream.duration is not None else float(container.duration or 0) / av.time_base
        if duration <= 0:
            raise ValueError('Video duration could not be determined')
        return dict(duration=duration, width=stream.width, height=stream.height,
                    fps=float(stream.average_rate or 25), audio=bool(container.streams.audio))


def scan_folder(path, recursive=True, notify=lambda s: None):
    root = Path(path).resolve()
    old_files = []
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in LEGACY_OUTPUT_NAMES and not Path(current, d).is_symlink()) if recursive else []
        for name in sorted(files):
            p = Path(current, name)
            if p.suffix.lower() not in EXTENSIONS or p.is_symlink():
                continue
            notify(str(p))
            item = dict(path=str(p), name=str(p.relative_to(root)), selected=True, status='Ready', error='')
            try:
                item.update(probe(p))
                item['bytes'] = p.stat().st_size
            except Exception as exc:
                item.update(status='Unreadable', selected=False, error=str(exc), duration=0, bytes=0)
            old_files.append(item)
    return dict(id=uuid.uuid4().hex, path=str(root), name=root.name, files=old_files)


def scan_files(paths, notify=lambda s: None):
    """Probe explicitly selected videos and group them by their source folder."""
    groups = {}
    seen = set()
    for raw in paths:
        p = Path(raw).resolve()
        canonical = str(p).casefold()
        if canonical in seen or p.suffix.lower() not in EXTENSIONS:
            continue
        seen.add(canonical)
        notify(str(p))
        root = p.parent
        group = groups.setdefault(str(root).casefold(), dict(id=uuid.uuid4().hex, path=str(root), name=root.name, files=[]))
        item = dict(path=str(p), name=p.name, selected=True, status='Ready', error='')
        try:
            item.update(probe(p))
            item['bytes'] = p.stat().st_size
        except Exception as exc:
            item.update(status='Unreadable', selected=False, error=str(exc), duration=0, bytes=0)
        group['files'].append(item)
    return list(groups.values())


def validate_options(options):
    o = {**DEFAULTS, **options}
    if o['model'] not in MODEL_INFO or o['mode'] not in ('interval', 'scene') or o['device'] not in ('auto', 'cuda', 'cpu'):
        raise ValueError('Invalid processing option')
    if not math.isfinite(float(o['interval'])) or not 0.1 <= float(o['interval']) <= 30:
        raise ValueError('Screenshot interval must be between 0.1 and 30 seconds')
    if o['width'] not in (640, 1280, 1920, 0) or not 40 <= int(o['quality']) <= 95:
        raise ValueError('Invalid screenshot quality')
    if o['image_format'] not in ('jpeg', 'png'):
        raise ValueError('Invalid screenshot format')
    if not math.isfinite(float(o['visual_interval'])) or not 5 <= float(o['visual_interval']) <= 120:
        raise ValueError('Visual indexing interval must be between 5 and 120 seconds')
    if not (o['screenshots'] or o['transcribe'] or o['visual_index']):
        raise ValueError('Choose screenshots, transcription, visual search, or a combination')
    if o['visual_index'] and not visual_model_ready():
        raise ValueError('The visual search model is missing. Open Settings to install it.')
    return o


def estimate(files, options):
    o = validate_options(options)
    selected = [v for v in files if v.get('selected') and v.get('status') != 'Unreadable']
    count = 0
    size = 0
    for v in selected:
        # Scene count cannot be known before analysis. Use an explicit planning assumption.
        interval = o['interval'] if o['mode'] == 'interval' else 5.0
        frames = math.ceil(v['duration'] / max(interval, 1 / max(1, v.get('fps', 25)))) if o['screenshots'] else 0
        count += frames
        width = min(v.get('width', 1280), o['width'] or v.get('width', 1280))
        height = width * v.get('height', 720) / max(1, v.get('width', 1280))
        size += frames * width * height * ((0.08 + o['quality'] / 1000) if o['image_format'] == 'jpeg' else .55)
        if o['transcribe']:
            size += v['duration'] * 100
        if o['visual_index']:
            visual_frames = max(1, math.ceil(v['duration'] / o['visual_interval']))
            size += visual_frames * 90_000
    return dict(count=count, bytes=int(size), duration=sum(v['duration'] for v in selected), videos=len(selected), approximate=True)


def estimate_runtime(duration, options):
    """Return a rough job duration, preferring comparable local completed runs."""
    duration = max(0.0, float(duration))
    if not duration:
        return 0.0
    wanted = {
        'transcript': bool(options.get('transcribe')),
        'screenshots': bool(options.get('screenshots')),
        'visual_index': bool(options.get('visual_index')),
    }
    rates = []
    target = analytics_file()
    try:
        lines = target.read_text(encoding='utf-8').splitlines()[-200:]
        for line in lines:
            event = json.loads(line)
            settings = event.get('settings', {})
            source_seconds = float(event.get('source', {}).get('duration_seconds') or 0)
            processing_seconds = float(event.get('performance', {}).get('processing_seconds') or 0)
            if event.get('outcome') != 'Completed' or source_seconds <= 0 or processing_seconds <= 0:
                continue
            if any(bool(settings.get(key)) != value for key, value in wanted.items()):
                continue
            if wanted['transcript'] and settings.get('whisper_model') != options.get('model'):
                continue
            if wanted['screenshots']:
                if settings.get('screenshot_mode') != options.get('mode'):
                    continue
                old_interval = float(settings.get('screenshot_interval_seconds') or 0)
                if options.get('mode') == 'interval' and abs(old_interval - float(options.get('interval', 5))) > .05:
                    continue
            if wanted['visual_index'] and abs(float(settings.get('ai_sampling_seconds') or 0) - float(options.get('visual_interval', 30))) > .05:
                continue
            rates.append(processing_seconds / source_seconds)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    if rates:
        rates.sort()
        rate = rates[len(rates) // 2]
    else:
        device = options.get('device', 'auto')
        gpu = device != 'cpu'
        rate = 0.0
        if wanted['transcript']:
            model_rate = {'tiny': .08, 'base': .12, 'small': .22, 'medium': .45, 'large-v3': .65}.get(options.get('model'), .12)
            rate += model_rate if gpu else model_rate * 5
        if wanted['screenshots']:
            interval = 5.0 if options.get('mode') == 'scene' else max(.1, float(options.get('interval', 5)))
            rate += .044 / interval
        if wanted['visual_index']:
            rate += .015 * (30 / max(5, float(options.get('visual_interval', 30))))
    return max(1.0, duration * max(.005, rate))


def signature(path, options):
    p = Path(path)
    st = p.stat()
    relevant = {k: v for k, v in options.items() if k not in ('recursive', 'output', 'skip_existing', 'device')}
    raw = json.dumps([str(p.resolve()).casefold(), st.st_size, st.st_mtime_ns, relevant, 1], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def output_base(folder, options):
    if options.get('output'):
        tag = hashlib.sha256(str(Path(folder).resolve()).casefold().encode()).hexdigest()[:8]
        return Path(options['output']) / OUTPUT_NAME / f'{Path(folder).name}-{tag}'
    return Path(folder) / OUTPUT_NAME


def completed_result(base, key):
    if not base.exists():
        return None
    for p in base.glob('*/processing-details.json'):
        try:
            value = json.loads(p.read_text(encoding='utf-8'))
            if value.get('signature') != key or value.get('status') != 'Completed':
                continue
            if any(not (p.parent / f).is_file() for f in value.get('outputs', [])):
                continue
            if any(not (p.parent / f['file']).is_file() for f in value.get('frames', [])):
                continue
            if any(not (p.parent / f['file']).is_file() for f in value.get('visual_index', {}).get('frames', [])):
                continue
            return value
        except (ValueError, OSError):
            continue
    return None


class Cancelled(Exception):
    pass


class Control:
    def __init__(self):
        self.cancel = threading.Event()
        self.running = threading.Event()
        self.running.set()

    def checkpoint(self):
        while not self.running.wait(0.15):
            if self.cancel.is_set():
                raise Cancelled('Cancelled by user')
        if self.cancel.is_set():
            raise Cancelled('Cancelled by user')


class BranchControl:
    """Stop a video's sibling branch on failure without cancelling the entire batch."""
    def __init__(self, parent):
        self.parent = parent
        self.stopped = threading.Event()

    def checkpoint(self):
        while not self.parent.running.wait(0.15):
            if self.stopped.is_set() or self.parent.cancel.is_set():
                raise Cancelled('Processing stopped')
        if self.stopped.is_set() or self.parent.cancel.is_set():
            raise Cancelled('Processing stopped')


def timestamp(seconds, separator='.'):
    ms = max(0, round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02}{separator}{ms:03}'


def export_transcript(folder, segments):
    Path(folder, 'transcript.txt').write_text('\n'.join(s['text'].strip() for s in segments), encoding='utf-8')
    srt = []
    vtt = ['WEBVTT\n']
    for i, s in enumerate(segments, 1):
        srt.append(f"{i}\n{timestamp(s['start'], ',')} --> {timestamp(s['end'], ',')}\n{s['text'].strip()}\n")
        vtt.append(f"{timestamp(s['start'])} --> {timestamp(s['end'])}\n{s['text'].strip()}\n")
    Path(folder, 'transcript.srt').write_text('\n'.join(srt), encoding='utf-8')
    Path(folder, 'transcript.vtt').write_text('\n'.join(vtt), encoding='utf-8')
    atomic_json(Path(folder, 'transcript.json'), segments)


def extract_frames(path, out, options, control, progress):
    import av
    import numpy as np
    from PIL import Image
    images = out / 'screenshots'
    images.mkdir(exist_ok=True)
    frames = []
    next_time = 0.0
    previous = None
    last_saved = -10.0
    last_emit = 0.0
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        stream.thread_type = 'AUTO'
        origin = float((stream.start_time or 0) * stream.time_base)
        for frame in container.decode(stream):
            control.checkpoint()
            if frame.time is None:
                continue
            t = max(0, float(frame.time) - origin)
            save = False
            if options['mode'] == 'interval':
                if t + 1e-6 >= next_time:
                    save = True
                    next_time = (math.floor((t + 1e-6) / options['interval']) + 1) * options['interval']
            else:
                small = frame.reformat(width=64, height=36, format='gray').to_ndarray().astype('float32') / 255
                score = float(np.abs(small - previous).mean()) if previous is not None else 1.0
                save = (not frames or score >= options['scene_threshold']) and t - last_saved >= 0.1
                previous = small
            if save:
                if shutil.disk_usage(out).free < 100 * 1024**2:
                    raise OSError('Less than 100 MB of free space remains. Processing stopped.')
                im = frame.to_image()
                if options['width'] and im.width > options['width']:
                    im.thumbnail((options['width'], 100000), Image.Resampling.LANCZOS)
                extension = 'jpg' if options['image_format'] == 'jpeg' else 'png'
                relative = f'screenshots/{len(frames) + 1:07}_{timestamp(t).replace(":", "-")}.{extension}'
                if options['image_format'] == 'jpeg':
                    im.save(out / relative, 'JPEG', quality=options['quality'])
                else:
                    im.save(out / relative, 'PNG', compress_level=6)
                frames.append(dict(time=t, file=relative))
                last_saved = t
            if time.monotonic() - last_emit >= 0.3:
                progress(t, len(frames))
                last_emit = time.monotonic()
    return frames


def frame_at(path, seconds):
    """Read the first decoded frame at or just after a requested time."""
    import av
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        target = max(0.0, float(seconds))
        container.seek(int(target / stream.time_base), stream=stream, backward=True)
        best = None
        origin = float((stream.start_time or 0) * stream.time_base)
        for frame in container.decode(stream):
            if frame.time is None:
                continue
            actual = max(0.0, float(frame.time) - origin)
            best = (frame.to_image(), actual)
            if actual + .03 >= target:
                return best
        return best


class VisualIndexer:
    def __init__(self):
        self.detector = None

    def load(self):
        if self.detector is None:
            if not visual_model_ready():
                raise ValueError('The visual search model is missing. Open Settings to install it.')
            from vision_index import Detector
            self.detector = Detector(visual_model_path())

    def index(self, path, out, duration, options, control, progress):
        from PIL import Image as PILImage
        from vision_index import compact_keywords, searchable_words
        self.load()
        folder = out / 'visual-index'
        folder.mkdir(exist_ok=True)
        interval = float(options.get('visual_interval', 30.0))
        times = [min(duration, n * interval) for n in range(max(1, math.ceil(duration / interval)))]
        entries = []
        combined = {'foreground': [], 'midground': [], 'background': []}
        for index, requested in enumerate(times):
            control.checkpoint()
            sample = frame_at(path, requested)
            if not sample:
                continue
            image, actual = sample
            detections = self.detector.detect(image)
            keywords = compact_keywords(detections)
            for layer, values in keywords.items():
                for value in values:
                    if value not in combined[layer]:
                        combined[layer].append(value)
            thumb = image.copy()
            thumb.thumbnail((640, 360), PILImage.Resampling.LANCZOS)
            relative = f'visual-index/{index + 1:06}_{timestamp(actual).replace(":", "-")}.jpg'
            thumb.save(out / relative, 'JPEG', quality=82)
            entries.append({'time': actual, 'file': relative, 'keywords': keywords,
                            'search_words': searchable_words(keywords), 'detections': detections})
            progress(min(duration, requested + interval), len(entries))
        summary = {layer: values[:5] for layer, values in combined.items()}
        value = {'version': 1, 'interval': interval, 'keywords': summary,
                 'search_words': searchable_words(summary), 'frames': entries}
        atomic_json(out / 'visual-index.json', value)
        return value


def extract_detail_frames(source, output, start, duration, step=5.0):
    """Create a lazy 5-second contact strip for one coarse search result."""
    from PIL import Image as PILImage
    folder = Path(output) / 'visual-index' / 'detail'
    folder.mkdir(parents=True, exist_ok=True)
    start = max(0.0, float(start))
    end = min(float(duration), start + 30.0)
    values = []
    current = start
    while current <= end + .01:
        sample = frame_at(source, current)
        if sample:
            image, actual = sample
            image.thumbnail((800, 450), PILImage.Resampling.LANCZOS)
            name = f'{round(start * 1000):010}_{round(actual * 1000):010}.jpg'
            path = folder / name
            if not path.exists():
                image.save(path, 'JPEG', quality=84)
            values.append({'time': actual, 'file': str(path)})
        current += step
    return values


class Transcriber:
    def __init__(self):
        self.model = None
        self.key = None
        self.device = ''

    def transcribe(self, path, out, options, control, progress, notice):
        from faster_whisper import WhisperModel
        import ctranslate2
        control.checkpoint()
        if not model_ready(options['model']):
            raise ValueError('Download the selected model in Settings first')
        device = options['device']
        if device == 'auto':
            device = 'cuda' if ctranslate2.get_cuda_device_count() else 'cpu'
        key = (options['model'], device)
        def run(target):
            if self.key != (options['model'], target):
                self.model = None
                self.key = None
                self.model = WhisperModel(str(MODELS / options['model']), device=target,
                                          compute_type='int8_float16' if target == 'cuda' else 'int8',
                                          local_files_only=True, cpu_threads=min(8, os.cpu_count() or 4))
                self.key = (options['model'], target)
            self.device = target
            notice('Transcribing on NVIDIA GPU' if target == 'cuda' else 'Transcribing on CPU')
            iterator, info = self.model.transcribe(str(path), language=options['language'] or None,
                                                  beam_size=5, vad_filter=True, condition_on_previous_text=False)
            segments = []
            for s in iterator:
                control.checkpoint()
                segments.append(dict(start=s.start, end=s.end, text=s.text))
                progress(s.end, len(segments))
            control.checkpoint()
            export_transcript(out, segments)
            return dict(segments=segments, language=info.language, device=target)
        try:
            return run(device)
        except RuntimeError as exc:
            if options['device'] == 'auto' and device == 'cuda':
                notice(f'GPU unavailable ({exc}); using CPU')
                return run('cpu')
            raise


def process_video(folder, video, options, control, transcriber, emit, visual_indexer=None):
    options = validate_options(options)
    started_at = time.time()
    timer = time.perf_counter()
    control.checkpoint()
    path = Path(video['path'])
    key = signature(path, options)
    base = output_base(folder, options)
    base.mkdir(parents=True, exist_ok=True)
    if options['skip_existing']:
        previous = completed_result(base, key)
        if previous:
            processing_analytics(path, video, options, 'Reused', started_at,
                                 time.perf_counter() - timer, previous)
            emit('notice', 'Existing matching result reused')
            return previous
    estimate_bytes = estimate([{**video, 'selected': True}], options)['bytes']
    if shutil.disk_usage(base).free < estimate_bytes + 100 * 1024**2:
        error = OSError('Not enough free disk space for the estimated output. Choose a larger interval or another location.')
        processing_analytics(path, video, options, 'Failed', started_at,
                             time.perf_counter() - timer, error=error)
        raise error
    tag = hashlib.sha256(str(path.resolve()).casefold().encode()).hexdigest()[:8]
    name = path.stem[:85].rstrip('. ') or 'video'
    out = base / f'{name}-{tag}-{time.strftime("%Y%m%d-%H%M%S")}-{uuid.uuid4().hex[:4]}'
    out.mkdir()
    result = dict(id=uuid.uuid4().hex, source=str(path), folder=str(folder), output=str(out),
                  signature=key, options=options, created=time.time(), duration=video['duration'],
                  status='Processing', frames=[], segments=[], visual_index={}, outputs=[])
    atomic_json(out / 'processing-details.json', result)
    local_control = BranchControl(control)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            futures = {}
            if options['screenshots']:
                futures[pool.submit(extract_frames, path, out, options, local_control,
                                    lambda t, n: emit('frames', (t, n)))] = 'frames'
            if options['transcribe'] and video.get('audio', True):
                futures[pool.submit(transcriber.transcribe, path, out, options, local_control,
                                    lambda t, n: emit('transcript', (t, n)), lambda s: emit('notice', s))] = 'transcript'
            elif options['transcribe']:
                export_transcript(out, [])
                result['notice'] = 'No audio track; empty transcript exported'
                result['outputs'] += ['transcript.txt', 'transcript.srt', 'transcript.vtt', 'transcript.json']
                emit('notice', result['notice'])
            if options['visual_index']:
                visual_indexer = visual_indexer or VisualIndexer()
                futures[pool.submit(visual_indexer.index, path, out, video['duration'], options, local_control,
                                    lambda t, n: emit('visual', (t, n)))] = 'visual'
            try:
                for future in concurrent.futures.as_completed(futures):
                    branch = futures[future]
                    value = future.result()
                    if branch == 'frames':
                        result['frames'] = value
                        emit('frames', (video['duration'], len(value)))
                    elif branch == 'transcript':
                        result.update(value)
                        emit('transcript', (video['duration'], len(value['segments'])))
                        result['outputs'] += ['transcript.txt', 'transcript.srt', 'transcript.vtt', 'transcript.json']
                    else:
                        result['visual_index'] = value
                        emit('visual', (video['duration'], len(value['frames'])))
                        result['outputs'].append('visual-index.json')
            except Exception:
                local_control.stopped.set()
                raise
        control.checkpoint()
        result['status'] = 'Completed'
        result['bytes'] = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
        event = processing_analytics(path, video, options, 'Completed', started_at,
                                     time.perf_counter() - timer, result)
        result['performance'] = {**event['performance'], 'analytics_event_id': event['event_id']}
        atomic_json(out / 'processing-details.json', result)
        return result
    except Exception as exc:
        result.update(status='Cancelled' if isinstance(exc, Cancelled) else 'Failed', error=str(exc))
        result['bytes'] = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
        event = processing_analytics(path, video, options, result['status'], started_at,
                                     time.perf_counter() - timer, result, exc)
        result['performance'] = {**event['performance'], 'analytics_event_id': event['event_id']}
        atomic_json(out / 'processing-details.json', result)
        raise
