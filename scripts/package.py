"""Build separate ComfyUI install and optional ComfyTV workflow archives.

Run from a source checkout; neither archive needs Node, tests or this script at runtime.
Only the files named below can enter a release. New release files require a deliberate
allowlist change and must not be supplied through symlinks.

Output collision checks resolve paths, casefold them, then apply Unicode NFC on
all filesystems. This conservative rule also rejects names that could be distinct
on a case-sensitive filesystem, keeping archives and checksums portable.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import stat
import sys
import tempfile
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = 'ComfyUI-Wylon'
WORKFLOW_NAME = 'Wylon-ComfyTV-Workflows'
VERSION = '0.3.0'
WORKFLOWS = (
    'image/wylon-qwen-2512', 'image/wylon-qwen-2-1',
    'video/wylon-h3-text', 'video/wylon-h3-first-last', 'video/wylon-ref2va',
)
EXISTING_TASK_EXAMPLES = ('wylon-get-image-task-result', 'wylon-get-video-task-result')
PLUGIN_FILES = (
    '__init__.py', 'pyproject.toml', 'requirements.txt',
    'README.md', 'README.zh-CN.md', 'CHANGELOG.md', 'CHANGELOG.zh-CN.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md',
    'CONTRIBUTING.md', 'CONTRIBUTING.zh-CN.md', 'SECURITY.md', 'SECURITY.zh-CN.md',
    'docs/USAGE.md', 'docs/USAGE.zh-CN.md', 'docs/VERIFICATION.md',
    'docs/API_CONVENTIONS.md', 'docs/API_CONVENTIONS.zh-CN.md',
    'wylon/__init__.py', 'wylon/api.py', 'wylon/client.py', 'wylon/contracts.py',
    'wylon/credentials.py', 'wylon/journal.py', 'wylon/media.py', 'wylon/nodes.py',
    'wylon/results.py', 'wylon/routes.py', 'wylon/runtime.py',
    'web/core.js', 'web/migration.js', 'web/wylon.js', 'web/wylon.css', 'web/model-capabilities.json',
    'web/locales/en.json', 'web/locales/zh.json',
    'locales/en.json', 'locales/zh.json', 'shared/model-capabilities.json',
    'locales/en/nodeDefs.json', 'locales/zh/nodeDefs.json',
    'locales/en/commands.json', 'locales/zh/commands.json',
    *(f'example_workflows/{Path(stem).name}.json' for stem in (*WORKFLOWS, *EXISTING_TASK_EXAMPLES)),
)
WORKFLOW_FILES = (
    'README.md', 'README.zh-CN.md', 'manifest.json', 'LICENSE', 'THIRD_PARTY_NOTICES.md',
    *(f'workflows/{stem}{suffix}.json' for stem in WORKFLOWS for suffix in ('', '_preset')),
)
# These expressions detect common accidental embedded keys or signed URLs; the
# primary boundary is the exact filename allowlist, excluding all credential stores.
SECRET_PATTERNS = (
    re.compile(rb'\bsk-[A-Za-z0-9_-]{24,}'),
    re.compile(rb'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----'),
    re.compile(rb'[?&](?:X-Amz-Signature|X-Goog-Signature|signature|access_token)=[A-Za-z0-9%_-]{16,}', re.I),
)


def _is_link_or_reparse_point(path: Path) -> bool:
    metadata = path.lstat()
    return (stat.S_ISLNK(metadata.st_mode)
            or bool(getattr(metadata, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT))


def _entries(root: Path, files: tuple[str, ...]) -> list[tuple[str, bytes]]:
    entries = []
    if _is_link_or_reparse_point(root):
        raise ValueError(f'Symlink or reparse source directory: {root.name}')
    for relative in sorted(files):
        path = root
        for part in Path(relative).parts:
            path = path / part
            if _is_link_or_reparse_point(path):
                raise ValueError(f'Symlink or reparse source is not releasable: {relative}')
        if not path.is_file():
            raise FileNotFoundError(f'Required release source missing: {relative}')
        data = path.read_bytes()
        if any(pattern.search(data) for pattern in SECRET_PATTERNS):
            raise ValueError(f'Possible credential in {relative}; packaging stopped')
        if relative == 'pyproject.toml':
            data = re.sub(rb'\[project.optional-dependencies\].*?(?=\[tool.comfy\])', b'', data, flags=re.S)
        entries.append((relative, data))
    return entries


def _write(destination: Path, name: str, entries: list[tuple[str, bytes]]) -> tuple[int, int]:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    checksum = destination.with_suffix(destination.suffix + '.sha256')
    temporary = None
    checksum_temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.part', delete=False) as handle:
            temporary = Path(handle.name)
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for relative, data in entries:
                info = zipfile.ZipInfo(f'{name}/{relative}', date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=destination.parent,
                                         suffix='.part', delete=False) as handle:
            checksum_temporary = Path(handle.name)
            handle.write(f'{digest}  {destination.name}\n')
        temporary.replace(destination)
        checksum_temporary.replace(checksum)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if checksum_temporary is not None:
            checksum_temporary.unlink(missing_ok=True)
    return len(entries), destination.stat().st_size


def package(destination: Path) -> tuple[int, int]:
    """Build a runtime-focused ComfyUI plugin archive and adjacent SHA-256 file."""
    return _write(destination, PLUGIN_NAME, _entries(ROOT, PLUGIN_FILES))


def package_workflows(destination: Path) -> tuple[int, int]:
    """Build the standalone optional workflow pack and adjacent SHA-256 file."""
    return _write(destination, WORKFLOW_NAME, _entries(ROOT / 'comfytv-workflows', WORKFLOW_FILES))


if __name__ == '__main__':
    # Redirected Windows output may otherwise inherit a legacy code page.
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', nargs='?', type=Path,
                        default=ROOT.parent / f'{PLUGIN_NAME}-{VERSION}.zip')
    parser.add_argument('--workflow-destination', type=Path,
                        help='Workflow archive path (default: next to plugin archive).')
    args = parser.parse_args()
    workflow_destination = args.workflow_destination or args.destination.parent / f'{WORKFLOW_NAME}-{VERSION}.zip'
    output_paths = [unicodedata.normalize('NFC', str(path.resolve()).casefold()) for destination in (args.destination, workflow_destination)
                    for path in (destination, destination.with_suffix(destination.suffix + '.sha256'))]
    if len(set(output_paths)) != len(output_paths):
        parser.error('Archive and checksum destinations must differ')
    # Validate both distributions before replacing either prior release.
    plugin_entries = _entries(ROOT, PLUGIN_FILES)
    workflow_entries = _entries(ROOT / 'comfytv-workflows', WORKFLOW_FILES)
    for destination, name, entries in (
        (args.destination, PLUGIN_NAME, plugin_entries),
        (workflow_destination, WORKFLOW_NAME, workflow_entries),
    ):
        count, size = _write(destination, name, entries)
        print(f'Archive: {destination} ({count} files, {size} bytes); SHA-256: {destination}.sha256')
