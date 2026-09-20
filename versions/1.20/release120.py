"""Tracer 1.20 collection migration and document/sequence integration.

The legacy projects key remains the storage adapter for Storyline. Collections
and projects reference the same objects in memory after migration.
"""
import copy
from pathlib import Path
import uuid

import core
import paper_edit
import timeline


def migrate(state):
    collections = [c for c in state.get('collections', []) if not c.get('builtin')]
    by_id = {c['id']: c for c in collections}
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
    state['collections'] = [{'id': 'all', 'name': 'All footage', 'builtin': True}] + collections
    state['projects'] = collections
    state['schema_version'] = 120
    return state


def collection_records(state, collection_id):
    ids = core.collection_video_ids(state, collection_id)
    return [r for r in state.get('results', []) if ids is None or r.get('id') in ids]


def attach(state, collection_id, records):
    collection = next(c for c in state['collections'] if c['id'] == collection_id)
    core.add_to_collection(state, collection_id, [r['id'] for r in records])
    paths = {str(v.get('path', '')).casefold() for f in collection.get('folders', []) for v in f.get('files', [])}
    for record in records:
        source = str(record.get('source', ''))
        if source.casefold() not in paths:
            collection.setdefault('folders', []).append({
                'id': uuid.uuid4().hex, 'path': source, 'name': Path(source).name,
                'files': [{'path': source, 'name': Path(source).name, 'duration': record.get('duration', 0),
                           'selected': True, 'status': 'Completed', 'bytes': 0, 'error': ''}]})
            paths.add(source.casefold())
    migrate(state)


def sync_paper(state, document, collection=None):
    """Update one stable linked sequence; preserve a manually edited cut as a copy."""
    migrate(state)
    collection = collection or next((c for c in state['projects'] if c['id'] == document.get('collection_id')), None)
    if collection is None:
        collection = core.create_collection(state, document.get('title', 'Paper Edit'))
        migrate(state)
    document['collection_id'] = collection['id']
    sequence = next((s for s in collection['sequences'] if s.get('paper_document_id') == document['id']), None)
    fresh = paper_edit.paper_sequence(document)
    if sequence:
        if sequence.get('paper_snapshot') is not None and sequence['tracks'] != sequence['paper_snapshot']:
            preserved = copy.deepcopy(sequence)
            preserved['id'] = uuid.uuid4().hex
            preserved['name'] += ' — Storyline cut'
            preserved.pop('paper_document_id', None)
            preserved.pop('paper_snapshot', None)
            collection['sequences'].append(preserved)
        fresh['id'] = sequence['id']
        fresh['view'] = sequence.get('view', fresh['view'])
        sequence.clear()
        sequence.update(fresh)
    else:
        sequence = fresh
        collection['sequences'].append(sequence)
    sequence['paper_document_id'] = document['id']
    sequence['paper_snapshot'] = copy.deepcopy(sequence['tracks'])
    document['sequence_id'] = sequence['id']
    return collection, sequence


def export_paper_project(document, parent):
    sequence = paper_edit.paper_sequence(document)
    target = timeline.collect_sequence_media(sequence, parent)
    (target / 'script.txt').write_text(paper_edit.script_text(document), encoding='utf-8')
    core.atomic_json(target / 'paper-edit.json', document)
    return target
