from __future__ import annotations

from collections import Counter
import copy
from fractions import Fraction
import json
from pathlib import Path
import re
import time
import uuid

import core
import timeline


STOPWORDS = {
    'about', 'after', 'again', 'also', 'and', 'because', 'before', 'being', 'but', 'could',
    'does', 'from', 'have', 'into', 'just', 'like', 'more', 'not', 'only', 'other', 'our',
    'really', 'should', 'some', 'than', 'that', 'the', 'their', 'then', 'there', 'these',
    'they', 'this', 'through', 'very', 'was', 'were', 'what', 'when', 'where', 'which',
    'while', 'who', 'will', 'with', 'would', 'you', 'your',
}


def _segment_id(result, index, segment):
    seed = f"{result.get('id') or result.get('source')}:{index}:{segment.get('start', 0)}"
    return uuid.uuid5(uuid.NAMESPACE_URL, seed).hex


def ensure_paper_document(state, result):
    """Create or gently update the non-destructive writer document for a library result."""
    documents = state.setdefault('paper_edits', [])
    source = str(result.get('source', ''))
    document = next((value for value in documents
                     if (result.get('id') and value.get('result_id') == result.get('id')) or
                     (source and str(value.get('source', '')).casefold() == source.casefold())), None)
    if document is not None:
        return document
    if document is None:
        document = {
            'id': uuid.uuid4().hex,
            'result_id': result.get('id'),
            'source': source,
            'title': Path(source).stem or 'Untitled transcript',
            'segments': [],
            'order': [],
            'strokes': [],
            'created': time.time(),
        }
        documents.append(document)
    existing = {value['id']: value for value in document.get('segments', [])}
    refreshed = []
    for index, segment in enumerate(result.get('segments', [])):
        segment_id = _segment_id(result, index, segment)
        value = existing.get(segment_id, {})
        original = str(segment.get('text', '')).strip()
        value.update({
            'id': segment_id,
            'start': float(segment.get('start', 0) or 0),
            'end': float(segment.get('end', segment.get('start', 0)) or 0),
            'original_text': value.get('original_text', original),
        })
        value.setdefault('text', original)
        value.setdefault('speaker', '')
        value.setdefault('included', True)
        value.setdefault('highlighted', False)
        value.setdefault('note', '')
        refreshed.append(value)
    document['segments'] = refreshed
    valid_ids = {value['id'] for value in refreshed}
    order = [value for value in document.get('order', []) if value in valid_ids]
    order.extend(value['id'] for value in refreshed if value['id'] not in order)
    document['order'] = order
    document.setdefault('strokes', [])
    document['source'] = source
    document['result_id'] = result.get('id')
    return document


def ordered_segments(document, included_only=False):
    values = {value['id']: value for value in document.get('segments', [])}
    ordered = [values[value] for value in document.get('order', []) if value in values]
    ordered.extend(value for value in document.get('segments', []) if value not in ordered)
    return [value for value in ordered if value.get('included', True)] if included_only else ordered


def transcript_analysis(document):
    segments = document.get('segments', [])
    words = re.findall(r"\b[^\W_]+(?:['’-][^\W_]+)*\b", ' '.join(value.get('text', '') for value in segments))
    frequencies = Counter(word.casefold() for word in words
                          if len(word) > 2 and word.casefold() not in STOPWORDS)
    speakers = {value.get('speaker', '').strip() for value in segments if value.get('speaker', '').strip()}
    duration = max((float(value.get('end', 0)) for value in segments), default=0.0)
    return {
        'words': len(words),
        'segments': len(segments),
        'speakers': len(speakers),
        'duration': duration,
        'repeated_terms': [(word, count) for word, count in frequencies.most_common() if count > 1][:6],
    }


def paper_sequence(document, sources=None):
    """Build a Premiere-ready sequence from included passages in paper order."""
    sequence = timeline.new_sequence(document.get('title', 'Paper Edit'))
    source_map = sources or {}
    cursor = 0.0
    for index, segment in enumerate(ordered_segments(document, included_only=True), 1):
        source = source_map.get(segment['id'], document.get('source', ''))
        duration = max(0.04, float(segment.get('end', 0)) - float(segment.get('start', 0)))
        linked = uuid.uuid4().hex
        for track_index in (1, 2):
            clip = timeline.make_clip(source, duration, cursor, name=f'{index:02d} · {document.get("title", "Passage")}', linked=linked)
            clip['source_in'] = 0.0 if segment['id'] in source_map else float(segment.get('start', 0))
            clip['source_out'] = duration if segment['id'] in source_map else float(segment.get('end', 0))
            clip['end'] = round(cursor + duration, 4)
            sequence['tracks'][track_index]['clips'].append(clip)
        cursor += duration
    return sequence


def script_text(document):
    blocks = []
    for segment in ordered_segments(document, included_only=True):
        speaker = segment.get('speaker', '').strip()
        heading = f"[{segment.get('start', 0):.2f}–{segment.get('end', 0):.2f}]"
        if speaker:
            heading += '  ' + speaker.upper()
        blocks.append(heading + '\n' + segment.get('text', '').strip())
        if segment.get('note', '').strip():
            blocks.append('NOTE: ' + segment['note'].strip())
    return '\n\n'.join(blocks).strip() + '\n'


def trim_media(source, start, end, destination):
    """Accurately transcode one selected passage to a standalone MP4."""
    import av

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_container = av.open(str(source))
    output = av.open(str(destination), 'w')
    output_streams = {}
    counters = {'video': 0, 'audio': 0}
    try:
        for stream in source_container.streams:
            if stream.type == 'video' and 'video' not in output_streams:
                rate = stream.average_rate or 25
                target = output.add_stream('libx264', rate=rate)
                target.width = stream.codec_context.width
                target.height = stream.codec_context.height
                target.pix_fmt = 'yuv420p'
                output_streams['video'] = target
            elif stream.type == 'audio' and 'audio' not in output_streams:
                target = output.add_stream('aac', rate=stream.codec_context.sample_rate or 48000)
                if stream.codec_context.layout:
                    target.layout = stream.codec_context.layout.name
                output_streams['audio'] = target
        for frame in source_container.decode():
            if frame.time is None or float(frame.time) < float(start):
                continue
            if float(frame.time) >= float(end):
                continue
            kind = 'video' if frame.__class__.__name__ == 'VideoFrame' else 'audio'
            target = output_streams.get(kind)
            if target is None:
                continue
            if kind == 'video':
                rate = target.average_rate or 25
                frame.pts = counters[kind]
                frame.time_base = Fraction(rate.denominator, rate.numerator)
                counters[kind] += 1
            else:
                rate = target.rate or frame.sample_rate or 48000
                frame.pts = counters[kind]
                frame.time_base = Fraction(1, int(rate))
                counters[kind] += frame.samples
            for packet in target.encode(frame):
                output.mux(packet)
        for target in output_streams.values():
            for packet in target.encode(None):
                output.mux(packet)
    finally:
        source_container.close()
        output.close()
    return destination


def export_paper_package(document, parent, trim=True):
    document = copy.deepcopy(document)
    selected = ordered_segments(document, included_only=True)
    if not selected:
        raise ValueError('Include at least one passage before exporting.')
    for segment in selected:
        start, end = float(segment.get('start', 0)), float(segment.get('end', 0))
        if not (0 <= start < end < float('inf')):
            raise ValueError('A selected passage has invalid source timing.')
    if trim and not Path(document.get('source', '')).is_file():
        raise FileNotFoundError('The source video is offline. Restore it before exporting.')
    parent = Path(parent)
    safe_title = ''.join(char if char.isalnum() or char in ' -_' else '_' for char in document.get('title', 'Paper Edit')).strip() or 'Paper Edit'
    target = parent / f'{safe_title} - Paper Edit'
    suffix = 2
    while target.exists():
        target = parent / f'{safe_title} - Paper Edit {suffix}'
        suffix += 1
    target.mkdir(parents=True)
    core.atomic_json(target / 'manifest.json', {'status': 'building', 'source': document.get('source')})
    (target / 'script.txt').write_text(script_text(document), encoding='utf-8')
    core.atomic_json(target / 'paper-edit.json', copy.deepcopy(document))
    sources = {}
    media = []
    if trim:
        media_dir = target / 'Media'
        media_dir.mkdir()
        for index, segment in enumerate(ordered_segments(document, included_only=True), 1):
            destination = media_dir / f'{index:03d}_{Path(document.get("source", "source.mp4")).stem}.mp4'
            try:
                trim_media(document['source'], segment['start'], segment['end'], destination)
            except Exception as exc:
                core.atomic_json(target / 'manifest.json', {
                    'status': 'failed', 'error': str(exc), 'source': document.get('source')})
                raise
            sources[segment['id']] = str(destination)
            media.append({'segment_id': segment['id'], 'path': str(Path('Media') / destination.name),
                          'source_in': segment['start'], 'source_out': segment['end']})
    sequence = paper_sequence(document, sources)
    timeline.write_final_cut_xml(sequence, target / (safe_title + '.xml'))
    core.atomic_json(target / 'manifest.json', {
        'version': 1,
        'status': 'complete',
        'source': document.get('source'),
        'trimmed': bool(trim),
        'passages': len(ordered_segments(document, included_only=True)),
        'media': media,
    })
    return target
