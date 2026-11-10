"""Recent local Wylon results; only relative ComfyUI view URLs leave the server."""
from datetime import datetime, timezone
import heapq
import os
from pathlib import Path
import re
from urllib.parse import urlencode
from aiohttp import web


def output_directory() -> Path:
    import folder_paths
    return Path(folder_paths.get_output_directory())


def result_entries():
    """Yield validated metadata without retaining a whole output directory in memory."""
    directory = output_directory() / 'wylon'
    if not directory.is_dir():
        return
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_symlink() or not re.fullmatch(r'[A-Za-z0-9_.-]+\.(png|mp4)', entry.name):
                continue
            try:
                if not entry.is_file(follow_symlinks=False):
                    continue
                metadata = entry.stat(follow_symlinks=False)
                created_at = datetime.fromtimestamp(metadata.st_mtime, timezone.utc).isoformat()
            except (OSError, ValueError, OverflowError):
                continue
            yield {
                'filename': entry.name, 'subfolder': 'wylon', 'type': 'output',
                'kind': 'image' if entry.name.endswith('.png') else 'video',
                'created_at': created_at,
                'url': '/view?' + urlencode({'filename': entry.name, 'subfolder': 'wylon', 'type': 'output'}),
            }



async def recent_results(request):
    results = heapq.nlargest(24, result_entries(), key=lambda row: (row['created_at'], row['filename']))
    return web.json_response({'results': results})
