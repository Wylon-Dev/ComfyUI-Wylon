"""Request builders shared by nodes; presets come from the shipped capability file."""
import base64
from dataclasses import dataclass
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

CAPABILITIES = json.loads((Path(__file__).parent.parent / 'shared/model-capabilities.json').read_text())
IMAGE_MODELS = CAPABILITIES['image_models']
VIDEO_MODELS = CAPABILITIES['video_models']


def validate_media_url(url: str, kind: str) -> str:
    if not isinstance(url, str) or not url or any(c.isspace() for c in url):
        raise ValueError('Media must be a public HTTPS URL or supported data URI')
    if url.startswith('data:'):
        if kind not in ('image', 'audio'):
            raise ValueError('Reference video requires a public HTTPS URL; Base64 is unsupported')
        match = re.fullmatch(r'data:' + kind + r'/[a-zA-Z0-9.+-]+;base64,([A-Za-z0-9+/=]+)', url)
        if not match:
            raise ValueError('Invalid media data URI')
        try:
            size = len(base64.b64decode(match[1], validate=True))
        except ValueError:
            raise ValueError('Invalid media Base64') from None
        if size > (30 if kind == 'image' else 15) * 1024 * 1024:
            raise ValueError('Media exceeds file size limit')
        return url
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or '').lower().rstrip('.')
        port = parsed.port
    except ValueError:
        raise ValueError('Invalid media URL') from None
    if parsed.scheme != 'https' or not host or parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise ValueError('Media requires a public HTTPS URL without credentials or fragments')
    if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
        raise ValueError('Private media addresses are unsupported')
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if '.' not in host or re.fullmatch(r'[0-9.]+', host) or host.startswith('0x'):
            raise ValueError('Private or ambiguous media address') from None
    else:
        if not address.is_global:
            raise ValueError('Private media addresses are unsupported')
    return url


@dataclass(frozen=True)
class ReferenceVideoBundle:
    urls: tuple[str, ...]

    def __post_init__(self):
        validate_reference_video_bundle(self)


def validate_reference_video_bundle(value):
    if not isinstance(value, ReferenceVideoBundle) or type(getattr(value, 'urls', None)) is not tuple:
        raise ValueError('reference_videos requires a WYLON_REFERENCE_VIDEO value from Wylon Reference Video URL')
    if len(value.urls) > 3:
        raise ValueError('At most 3 reference video URLs')
    for url in value.urls:
        validate_media_url(url, 'video')
    return value.urls


def _text(value, name, required=False):
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError(f'{name} must be a nonempty string' if required else f'{name} must be a string')


def _seed(payload, seed):
    if type(seed) is not int or seed < -1:
        raise ValueError('seed must be -1 or a nonnegative integer')
    if seed >= 0:
        payload['seed'] = seed


def _extra(payload, extra, kind):
    if extra is None:
        return
    if not isinstance(extra, dict):
        raise ValueError('extra must be a JSON object')
    image_fields = {'style', 'user', 'user_id', 'moderation', 'background', 'quality', 'output_compression', 'output_format', 'n', 'stream', 'partial_images'}
    allowed = image_fields if kind == 'image' else {'safety_identifier', 'execution_expires_after'}
    if set(extra) - allowed:
        raise ValueError('Unsupported or reserved advanced parameter')
    for key, value in extra.items():
        fixed = {'n': 1, 'stream': False, 'partial_images': 0, 'output_format': 'png'}
        if key in fixed:
            if type(value) is not type(fixed[key]) or value != fixed[key]:
                raise ValueError(f'Unsupported {key} value')
        elif key in ('output_compression', 'execution_expires_after'):
            if type(value) is not int or value < (1 if key == 'execution_expires_after' else 0) or (key == 'output_compression' and value > 100):
                raise ValueError(f'Invalid {key}')
        else:
            _text(value, key)
        payload[key] = value


def validate_image_parameters(parameters):
    """Validate resolved image widgets; defer model-specific size checks for links."""
    if 'model' in parameters and parameters['model'] not in IMAGE_MODELS:
        raise ValueError('Unsupported image model')
    if 'prompt' in parameters:
        _text(parameters['prompt'], 'prompt', True)
    if 'negative_prompt' in parameters:
        _text(parameters['negative_prompt'], 'negative_prompt')
    if 'size' in parameters and parameters['size'] != 'server_default':
        models = [parameters['model']] if 'model' in parameters else IMAGE_MODELS
        if not any(parameters['size'] in IMAGE_MODELS[model]['sizes'] for model in models):
            raise ValueError('Unsupported size for selected image model')


def build_image_request(model, prompt, size='server_default', mode='async', negative_prompt='', seed=-1, extra=None):
    validate_image_parameters({'model': model, 'prompt': prompt, 'size': size, 'negative_prompt': negative_prompt})
    if mode not in ('async', 'sync'):
        raise ValueError('mode must be sync or async')
    payload = {'model': model, 'prompt': prompt, 'n': 1}
    if mode == 'async':
        payload['type'] = 'image'
    else:
        payload['response_format'] = 'url'
        if seed != -1:
            raise ValueError('seed is only supported by async image generation')
    if size != 'server_default':
        payload['size'] = size
    if negative_prompt:
        payload['negative_prompt'] = negative_prompt
    _seed(payload, seed)
    if extra is not None and isinstance(extra, dict) and 'response_format' in extra:
        if mode != 'sync' or extra['response_format'] not in ('url', 'b64_json'):
            raise ValueError('response_format must be url or b64_json and is sync-only')
        payload['response_format'] = extra['response_format']
        extra = {key: value for key, value in extra.items() if key != 'response_format'}
    _extra(payload, extra, 'image')
    return payload


def validate_video_parameters(model, parameters, *, has_frames=False):
    """Validate supplied scalar fields without inspecting or encoding media.

    Queue validation may omit unresolved linked fields. Request construction
    supplies every scalar, so the same rules apply after links resolve.
    """
    if 'prompt' in parameters:
        _text(parameters['prompt'], 'prompt', True)
    if 'negative_prompt' in parameters:
        _text(parameters['negative_prompt'], 'negative_prompt')
    if 'duration' in parameters:
        duration = parameters['duration']
        if type(duration) is not int or duration not in CAPABILITIES['video']['durations']:
            raise ValueError('duration must be an integer from 5 to 15 seconds')
    if 'resolution' in parameters and parameters['resolution'] != '768p':
        raise ValueError('Unsupported resolution')
    if 'ratio' in parameters:
        ratio = parameters['ratio']
        adaptive = ratio == 'adaptive' and model == 'MiniMaxAI/MiniMax-H3' and has_frames
        if ratio not in CAPABILITIES['video']['ratios'] and ratio != 'server_default' and not adaptive:
            raise ValueError('Unsupported ratio; adaptive ratio requires an H3 first or last frame')
    if 'seed' in parameters:
        seed = parameters['seed']
        _seed({}, seed)
        if seed > 4294967295:
            raise ValueError('seed must not exceed 4294967295')
    if 'extra' in parameters:
        _extra({}, parameters['extra'], 'video')


def build_video_request(model, prompt, images=(), videos=(), audios=(), first_frame=None, last_frame=None, duration=5, resolution='768p', ratio='16:9', negative_prompt='', seed=-1, extra=None):
    if model not in VIDEO_MODELS:
        raise ValueError('Unsupported video model')
    validate_video_parameters(model, {
        'prompt': prompt, 'negative_prompt': negative_prompt, 'duration': duration,
        'resolution': resolution, 'ratio': ratio, 'seed': seed, 'extra': extra,
    }, has_frames=first_frame is not None or last_frame is not None)
    for values in (images, videos, audios):
        if not isinstance(values, (tuple, list)):
            raise ValueError('Reference media must be lists of URLs')
    content = [{'type': 'text', 'text': prompt}]
    if model.endswith('-Ref2VA'):
        if first_frame is not None or last_frame is not None:
            raise ValueError('First/last frames cannot be mixed with reference media')
        if not images and not videos:
            raise ValueError('Ref2VA requires a reference image or video; audio alone is unsupported')
        if len(images) > 9 or len(videos) > 3 or len(audios) > 3:
            raise ValueError('Reference media count exceeds model limits')
        groups = [('image', images, 'reference_image'), ('video', videos, 'reference_video'), ('audio', audios, 'reference_audio')]
    else:
        if images or videos or audios:
            raise ValueError('H3 supports first/last frames only')
        groups = [('image', [first_frame] if first_frame is not None else [], 'first_frame'), ('image', [last_frame] if last_frame is not None else [], 'last_frame')]
    for kind, values, role in groups:
        for url in values:
            validate_media_url(url, kind)
            content.append({'type': kind + '_url', kind + '_url': {'url': url}, 'role': role})
    payload = {'type': 'video', 'model': model, 'content': content, 'duration': duration, 'resolution': resolution, 'ratio': ratio}
    if ratio in ('server_default', 'adaptive'):
        del payload['ratio']
    if negative_prompt:
        payload['negative_prompt'] = negative_prompt
    _seed(payload, seed)
    _extra(payload, extra, 'video')
    return payload
