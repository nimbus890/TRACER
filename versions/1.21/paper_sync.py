"""Tracer 1.21 Paper Edit <-> Storyline synchronization engine.

Provides diff-based synchronization between Paper Edit documents and Storyline sequences
using stable passage IDs, preserving Storyline-only tracks (B-roll, extra audio) and
propagating trims and reorders without full sequence rebuilds.
"""
from __future__ import annotations

import copy
from pathlib import Path
import time
import uuid

import timeline


DEFAULT_HANDLE = 0.2  # 0.2s head/tail dialogue handles


def ensure_passage_model(document: dict, source_duration: float = 0.0) -> dict:
    """Ensure every segment in the document has full 1.21 passage metadata."""
    segments = document.setdefault('segments', [])
    valid_ids = set()
    for index, seg in enumerate(segments):
        pid = seg.get('passage_id') or seg.get('id')
        if not pid:
            pid = uuid.uuid4().hex
        seg['id'] = pid
        seg['passage_id'] = pid
        valid_ids.add(pid)

        # Timing
        start = float(seg.get('start', 0.0) or 0.0)
        end = float(seg.get('end', start) or start)
        if end <= start:
            end = start + 1.0

        seg.setdefault('original_start', start)
        seg.setdefault('original_end', end)
        seg['start'] = start
        seg['end'] = end
        seg.setdefault('source_in', start)
        seg.setdefault('source_out', end)

        # Quality and handles
        seg.setdefault('timing_quality', 'source')  # 'source' | 'estimated' | 'manual'
        seg.setdefault('handle_start', DEFAULT_HANDLE)
        seg.setdefault('handle_end', DEFAULT_HANDLE)

        # Text and state
        seg.setdefault('text', '')
        seg.setdefault('original_text', seg.get('text', ''))
        seg.setdefault('speaker', '')
        seg.setdefault('included', True)
        seg.setdefault('note', '')
        seg.setdefault('revision', 1)

    order = [pid for pid in document.get('order', []) if pid in valid_ids]
    for pid in valid_ids:
        if pid not in order:
            order.append(pid)
    document['order'] = order
    return document


def apply_dialogue_handles(start: float, end: float, media_duration: float,
                           prev_end: float = 0.0, next_start: float = float('inf'),
                           handle: float = DEFAULT_HANDLE) -> tuple[float, float]:
    """Apply dialogue handles clamped to media boundaries and neighboring speech."""
    h_start = max(0.0, max(prev_end, start - handle))
    max_boundary = min(media_duration if media_duration > 0 else float('inf'), next_start)
    h_end = min(max_boundary, end + handle) if max_boundary < float('inf') else end + handle
    return round(h_start, 3), round(h_end, 3)


def sync_paper_to_sequence(document: dict, sequence: dict, source_map: dict = None) -> tuple[dict, dict]:
    """Diff-synchronize Paper Edit document into a Storyline sequence.
    
    Preserves:
    - Storyline-only tracks (V2, A2, etc.) and non-passage clips (B-roll, extra audio).
    - Existing clip IDs and linked audio/video relationships for unmodified passages.
    
    Updates:
    - Track V1 (index 1) and Track A1 (index 2) spoken-story assembly:
      reordered to match document passage order, retimed for trims, rippled to close gaps.
    """
    ensure_passage_model(document)
    source_map = source_map or {}
    default_source = document.get('source', '')

    tracks = sequence.setdefault('tracks', timeline.new_sequence()['tracks'])
    while len(tracks) < 4:
        tracks = timeline.new_sequence()['tracks']
        sequence['tracks'] = tracks

    v1_track = tracks[1]
    a1_track = tracks[2]

    # Index existing clips by passage_id
    existing_v1 = {c['passage_id']: c for c in v1_track.get('clips', []) if c.get('passage_id')}
    existing_a1 = {c['passage_id']: c for c in a1_track.get('clips', []) if c.get('passage_id')}

    # Non-passage clips on V1 and A1 (manual B-roll placed on V1/A1)
    other_v1 = [c for c in v1_track.get('clips', []) if not c.get('passage_id')]
    other_a1 = [c for c in a1_track.get('clips', []) if not c.get('passage_id')]

    # Passages to include
    segments_by_id = {s['id']: s for s in document.get('segments', [])}
    ordered_passages = [
        segments_by_id[pid] for pid in document.get('order', [])
        if pid in segments_by_id and segments_by_id[pid].get('included', True)
    ]

    new_v1_clips = []
    new_a1_clips = []
    cursor = 0.0

    for index, passage in enumerate(ordered_passages, 1):
        pid = passage['id']
        source = source_map.get(pid, default_source)
        start_t = float(passage.get('source_in', passage.get('start', 0.0)))
        end_t = float(passage.get('source_out', passage.get('end', start_t)))
        duration = max(0.04, round(end_t - start_t, 4))

        title = passage.get('speaker', '').strip() or document.get('title', 'Passage')
        clip_name = f"{index:02d} · {title}"

        # Re-use existing clip if present to preserve identity and links
        old_v = existing_v1.get(pid)
        old_a = existing_a1.get(pid)
        linked_id = (old_v or {}).get('linked') or (old_a or {}).get('linked') or uuid.uuid4().hex

        # Video clip
        v_clip = old_v if old_v else timeline.make_clip(source, duration, cursor, name=clip_name, linked=linked_id)
        v_clip['passage_id'] = pid
        v_clip['source'] = source
        v_clip['name'] = clip_name
        v_clip['start'] = round(cursor, 4)
        v_clip['end'] = round(cursor + duration, 4)
        v_clip['source_in'] = round(start_t, 4)
        v_clip['source_out'] = round(end_t, 4)
        v_clip['timing_quality'] = passage.get('timing_quality', 'source')
        v_clip['linked'] = linked_id
        new_v1_clips.append(v_clip)

        # Audio clip
        a_clip = old_a if old_a else timeline.make_clip(source, duration, cursor, name=clip_name, linked=linked_id)
        a_clip['passage_id'] = pid
        a_clip['source'] = source
        a_clip['name'] = clip_name
        a_clip['start'] = round(cursor, 4)
        a_clip['end'] = round(cursor + duration, 4)
        a_clip['source_in'] = round(start_t, 4)
        a_clip['source_out'] = round(end_t, 4)
        a_clip['timing_quality'] = passage.get('timing_quality', 'source')
        a_clip['linked'] = linked_id
        new_a1_clips.append(a_clip)

        cursor += duration

    # Preserve any other non-passage clips that were placed on V1/A1
    new_v1_clips.extend(other_v1)
    new_a1_clips.extend(other_a1)

    v1_track['clips'] = new_v1_clips
    a1_track['clips'] = new_a1_clips

    # Tracks V2 (index 0) and A2 (index 3) or extra tracks are left completely untouched!
    sequence['paper_document_id'] = document['id']
    sequence['paper_synced_at'] = time.time()
    document['sequence_id'] = sequence['id']

    diff_summary = {
        'included_count': len(ordered_passages),
        'total_duration': round(cursor, 3),
        'status': 'Synced',
    }
    return sequence, diff_summary


def sync_sequence_trim_to_paper(sequence: dict, document: dict, clip_id: str) -> bool:
    """When a linked spoken clip is trimmed in Storyline, update Paper Edit timing."""
    ensure_passage_model(document)
    for track in sequence.get('tracks', []):
        for clip in track.get('clips', []):
            if clip.get('id') == clip_id and clip.get('passage_id'):
                pid = clip['passage_id']
                passage = next((s for s in document.get('segments', []) if s['id'] == pid), None)
                if passage:
                    passage['source_in'] = float(clip.get('source_in', passage['start']))
                    passage['source_out'] = float(clip.get('source_out', passage['end']))
                    passage['start'] = passage['source_in']
                    passage['end'] = passage['source_out']
                    passage['timing_quality'] = 'manual'
                    passage['revision'] = passage.get('revision', 1) + 1
                    return True
    return False


def estimate_split_timing(passage: dict, split_char_ratio: float) -> tuple[dict, dict]:
    """Split a passage into two passages with estimated proportional timestamps."""
    split_char_ratio = max(0.05, min(0.95, split_char_ratio))
    start = float(passage.get('start', 0.0))
    end = float(passage.get('end', start + 1.0))
    split_time = round(start + (end - start) * split_char_ratio, 3)

    p1 = copy.deepcopy(passage)
    p2 = copy.deepcopy(passage)

    p1['end'] = split_time
    p1['source_out'] = split_time
    p1['timing_quality'] = 'estimated' if passage.get('timing_quality') != 'manual' else 'manual'
    p1['revision'] = passage.get('revision', 1) + 1

    p2['id'] = uuid.uuid4().hex
    p2['passage_id'] = p2['id']
    p2['start'] = split_time
    p2['source_in'] = split_time
    p2['timing_quality'] = 'estimated'
    p2['revision'] = 1

    return p1, p2


def status_badge_text(document: dict) -> str:
    """Return status line text: e.g. 'Synced to Storyline · 18 passages · 02:14'."""
    ensure_passage_model(document)
    included = [s for s in document.get('segments', []) if s.get('included', True)]
    total_sec = sum(max(0.0, float(s.get('end', 0)) - float(s.get('start', 0))) for s in included)
    m, s = divmod(int(round(total_sec)), 60)
    time_str = f"{m:02d}:{s:02d}"
    return f"Synced to Storyline · {len(included)} passage{'s' if len(included) != 1 else ''} · {time_str}"
