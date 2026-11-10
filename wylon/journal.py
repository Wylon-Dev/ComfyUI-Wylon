"""Small atomic, metadata-only journal; no prompts, credentials or asset URLs."""
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from .contracts import IMAGE_MODELS, VIDEO_MODELS

STATUSES = {'queued', 'running', 'succeeded', 'failed', 'cancelled', 'expired', 'downloaded', 'interrupted', 'error'}
FIELDS = {'id', 'kind', 'model', 'status', 'updated_at'}


def _validate(task_id, kind, model, status):
    if not isinstance(task_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}', task_id):
        raise ValueError('Invalid task ID')
    if kind not in ('image', 'video') or status not in STATUSES:
        raise ValueError('Invalid task metadata')
    if model not in (IMAGE_MODELS if kind == 'image' else VIDEO_MODELS):
        raise ValueError('Invalid model for task kind')


class Journal:
    def __init__(self, directory):
        self.directory = Path(directory)

    def record(self, task_id, kind, model, status):
        _validate(task_id, kind, model, status)
        self.directory.mkdir(parents=True, exist_ok=True)
        record = {'id': task_id, 'kind': kind, 'model': model, 'status': status, 'updated_at': datetime.now(timezone.utc).isoformat()}
        target = self.directory / (hashlib.sha256(task_id.encode()).hexdigest() + '.json')
        fd, temporary = tempfile.mkstemp(prefix='.journal-', suffix='.tmp', dir=self.directory)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(record, stream, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def iter_records(self):
        """Validate one record at a time without materializing directory entries."""
        try:
            entries = os.scandir(self.directory)
        except FileNotFoundError:
            return
        with entries:
            for entry in entries:
                if not entry.name.endswith('.json'):
                    continue
                path = Path(entry.path)
                try:
                    if entry.is_symlink() or not entry.is_file(follow_symlinks=False) or entry.stat(follow_symlinks=False).st_size > 4096:
                        continue
                    row = json.loads(path.read_text(encoding='utf-8'))
                    if not isinstance(row, dict) or set(row) != FIELDS:
                        continue
                    _validate(row['id'], row['kind'], row['model'], row['status'])
                    datetime.fromisoformat(row['updated_at'])
                    yield row
                except (ValueError, TypeError, OSError, KeyError):
                    continue

    def list(self):
        # Legacy callers retain their complete newest-first list contract.
        return sorted(self.iter_records(), key=lambda row: row['updated_at'], reverse=True)
