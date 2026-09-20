"""Tracer 1.21 release module: collection migration, state schema 121,
and integrated paper_sync diff synchronization.
"""
from __future__ import annotations

import copy
from pathlib import Path
import uuid

import core
import paper_edit
import paper_sync
import timeline


def migrate(state: dict) -> dict:
    """Migrate state to schema 121. Preserves existing 119/120 collections, sequences, and documents."""
    collections = [c for c in state.get('collections', []) if not c.get('builtin')]
    by_id = {c['id']: c for c in collections}

    # Ensure projects & collections are unified
    for project in state.get('projects', []):
        if project['id'] not in by_id:
            collections.append(project)
            by_id[project['id']] = project
        else:
            for key, value in project.items():
                by_id[project['id']].setdefault(key, value)

    for collection in collections:
        collection.setdefault('video_ids', [])
        collection.setdefault('folders', [])
        paths = {str(v.get('path', '')).casefold() for f in collection['folders'] for v in f.get('files', [])}
        for record in state.get('results', []):
            if record.get('project_id') == collection['id'] or str(record.get('source', '')).casefold() in paths:
                if record.get('id') not in collection['video_ids']:
                    collection['video_ids'].append(record['id'])
        timeline.ensure_project_editing(collection)

    # Ensure all paper edit documents conform to 1.21 passage model
    for doc in state.get('paper_edits', []):
        paper_sync.ensure_passage_model(doc)

    state['collections'] = [{'id': 'all', 'name': 'All footage', 'builtin': True}] + collections
    state['projects'] = collections
    state['schema_version'] = 121
    return state


def collection_records(state: dict, collection_id: str) -> list[dict]:
    ids = core.collection_video_ids(state, collection_id)
    return [r for r in state.get('results', []) if ids is None or r.get('id') in ids]


def attach(state: dict, collection_id: str, records: list[dict]):
    collection = next((c for c in state['collections'] if c['id'] == collection_id), None)
    if not collection:
        return
    core.add_to_collection(state, collection_id, [r['id'] for r in records])
    paths = {str(v.get('path', '')).casefold() for f in collection.get('folders', []) for v in f.get('files', [])}
    for record in records:
        source = str(record.get('source', ''))
        if source and source.casefold() not in paths:
            collection.setdefault('folders', []).append({
                'id': uuid.uuid4().hex, 'path': source, 'name': Path(source).name,
                'files': [{'path': source, 'name': Path(source).name, 'duration': record.get('duration', 0),
                           'selected': True, 'status': 'Completed', 'bytes': 0, 'error': ''}]})
            paths.add(source.casefold())
    migrate(state)


def sync_paper(state: dict, document: dict, collection: dict = None) -> tuple[dict, dict]:
    """Synchronize Paper Edit document with its Storyline sequence using diff synchronization."""
    migrate(state)
    collection = collection or next((c for c in state['projects'] if c['id'] == document.get('collection_id')), None)
    if collection is None:
        collection = core.create_collection(state, document.get('title', 'Paper Edit'))
        migrate(state)
    document['collection_id'] = collection['id']

    sequence = next((s for s in collection['sequences'] if s.get('paper_document_id') == document['id']), None)
    if sequence is None:
        sequence = timeline.new_sequence(document.get('title', 'Paper Edit'))
        collection['sequences'].append(sequence)

    # Perform diff synchronization
    sequence, diff_info = paper_sync.sync_paper_to_sequence(document, sequence)
    document['sequence_id'] = sequence['id']
    return collection, sequence


def export_paper_project(document: dict, parent: Path | str, progress_callback=None, cancel_check=None) -> Path:
    parent = Path(parent)
    sequence = paper_edit.paper_sequence(document)
    target = timeline.collect_sequence_media(sequence, parent, progress_callback=progress_callback, cancel_check=cancel_check)
    (target / 'script.txt').write_text(paper_edit.script_text(document), encoding='utf-8')
    core.atomic_json(target / 'paper-edit.json', document)
    return target
