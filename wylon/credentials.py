"""Server-only credentials; API status and workflows never contain key material."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import tempfile
import threading


def _valid_key(key) -> bool:
    return isinstance(key, str) and 8 <= len(key) <= 4096 and all(33 <= ord(char) <= 126 for char in key)


def _is_link(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    # Directory junctions have directory mode on Windows, not symbolic-link mode.
    return (stat.S_ISLNK(metadata.st_mode) or
            getattr(metadata, 'st_reparse_tag', None) == getattr(stat, 'IO_REPARSE_TAG_MOUNT_POINT', 0xA0000003))


class CredentialStore:
    def __init__(self, path: Path, *, directory_root: Path | None = None):
        self.path = Path(path)
        # Inspect only plugin-owned directories; the configured host user root is trusted.
        self.directory_root = Path(directory_root) if directory_root is not None else self.path.parent
        if self.directory_root != self.path.parent and self.directory_root not in self.path.parent.parents:
            raise ValueError('Credential directory root must contain the credential file')
        self._session_key = ''
        self._lock = threading.RLock()

    def _unsafe_directory(self) -> bool:
        directory = self.path.parent
        while True:
            if _is_link(directory):
                return True
            if directory == self.directory_root:
                return False
            directory = directory.parent

    def _local_key(self) -> str:
        try:
            # O_NOFOLLOW is unavailable on Windows; reject existing links there too.
            if _is_link(self.path) or self._unsafe_directory():
                return ''
            fd = os.open(self.path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
            with os.fdopen(fd, 'r', encoding='utf-8') as stream:
                value = json.loads(stream.read(16385))
            key = value.get('api_key') if isinstance(value, dict) else None
            return key if _valid_key(key) else ''
        except (OSError, ValueError, UnicodeError):
            return ''

    def _resolve(self):
        local = self._local_key()
        environment = os.environ.get('WYLON_API_KEY', '').strip()
        if self._session_key:
            return self._session_key, 'session', bool(local)
        if local:
            return local, 'local', True
        return environment, 'environment' if environment else 'none', False

    def effective_key(self) -> str:
        with self._lock:
            return self._resolve()[0]

    def status(self) -> dict:
        with self._lock:
            key, source, persisted = self._resolve()
            return {'configured': bool(key), 'source': source, 'persisted': persisted, 'session': bool(self._session_key)}

    def configure(self, api_key: str, *, persist: bool = False) -> None:
        if not _valid_key(api_key):
            raise ValueError('API key must contain 8–4096 printable ASCII characters without whitespace / 密钥须为8–4096个无空格的可打印字符')
        if type(persist) is not bool:
            raise ValueError('persist must be a boolean')
        with self._lock:
            if persist:
                if self._unsafe_directory():
                    raise OSError('Credential directory must not be a symlink or junction')
                self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                if self._unsafe_directory():
                    raise OSError('Credential directory must not be a symlink or junction')
                self.path.parent.chmod(0o700)
                fd, temporary = tempfile.mkstemp(prefix='.credentials-', suffix='.tmp', dir=self.path.parent)
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                        # Older Windows Python lacks fchmod; host-account ACLs control access.
                        if hasattr(os, 'fchmod'):
                            os.fchmod(stream.fileno(), 0o600)
                        json.dump({'api_key': api_key}, stream)
                        stream.flush()
                        os.fsync(stream.fileno())
                    os.replace(temporary, self.path)
                finally:
                    Path(temporary).unlink(missing_ok=True)
            self._session_key = api_key

    def clear(self, scope: str) -> None:
        if scope not in ('session', 'local', 'all'):
            raise ValueError('scope must be session, local, or all')
        with self._lock:
            if scope in ('local', 'all'):
                if self._unsafe_directory():
                    raise OSError('Credential directory must not be a symlink or junction')
                self.path.unlink(missing_ok=True)
            if scope in ('session', 'all'):
                self._session_key = ''


_store = None
_store_lock = threading.Lock()


def get_store() -> CredentialStore:
    global _store
    with _store_lock:
        if _store is None:
            import folder_paths
            owned = Path(folder_paths.get_user_directory()) / 'wylon'
            _store = CredentialStore(owned / 'private' / 'credentials.json', directory_root=owned)
        return _store
