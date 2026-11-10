"""ComfyUI IMAGE/AUDIO codecs using real torch tensors, Pillow and PCM WAV."""
import base64
import io
import wave
from pathlib import Path
import numpy as np
import torch
from PIL import Image, ImageOps

IMAGE_LIMIT = 30 * 1024 * 1024
IMAGE_RESULT_LIMIT = 64 * 1024 * 1024
AUDIO_LIMIT = 15 * 1024 * 1024


def _image_dimensions(width, height):
    if not (300 <= width <= 5760 and 300 <= height <= 5760 and 0.4 <= width / height <= 2.5):
        raise ValueError('Images require dimensions 300..5760 pixels and aspect ratio 0.4..2.5')


def image_batch_count(tensor, max_images=9) -> int:
    if not isinstance(tensor, torch.Tensor) or tensor.ndim != 4 or tensor.shape[-1] not in (3, 4) or tensor.shape[0] < 1:
        raise ValueError('IMAGE must be a nonempty [batch,height,width,3 or 4] tensor')
    if tensor.shape[0] > max_images:
        raise ValueError(f'IMAGE batch exceeds the remaining {max_images} image count limit / 图片批次超过剩余数量限制')
    _image_dimensions(tensor.shape[2], tensor.shape[1])
    return tensor.shape[0]


def tensor_to_data_urls(tensor, max_images=9) -> list[str]:
    image_batch_count(tensor, max_images)
    if not tensor.is_floating_point():
        raise ValueError('IMAGE must contain finite floating point samples')
    urls = []
    for item in tensor:
        if not torch.isfinite(item).all():
            raise ValueError('IMAGE must contain finite floating point samples')
        pixels = (item.detach().to(device='cpu', dtype=torch.float32).clamp(0, 1) * 255).round().to(torch.uint8)
        image = Image.fromarray(pixels.numpy()).convert('RGB')
        encoded = io.BytesIO()
        image.save(encoded, format='PNG')
        if encoded.tell() > IMAGE_LIMIT:
            raise ValueError('Encoded image exceeds 30MB')
        urls.append('data:image/png;base64,' + base64.b64encode(encoded.getvalue()).decode('ascii'))
    return urls


def _audio_parts(audio):
    if not isinstance(audio, dict):
        raise ValueError('AUDIO must contain waveform and sample_rate')
    waveform = audio.get('waveform')
    sample_rate = audio.get('sample_rate')
    if type(sample_rate) is not int or not 1 <= sample_rate <= 0x7FFFFFFF:
        raise ValueError('AUDIO sample_rate must be a positive integer')
    if not isinstance(waveform, torch.Tensor) or waveform.ndim != 3 or waveform.shape[0] != 1 or waveform.shape[1] < 1:
        raise ValueError('AUDIO waveform must be [1,channels,samples]')
    if not waveform.is_floating_point():
        raise ValueError('AUDIO samples must be finite floating point values')
    duration = waveform.shape[-1] / sample_rate
    if not 2 <= duration <= 15:
        raise ValueError('Each reference audio clip must last 2..15 seconds')
    if waveform.numel() * 2 + 44 > AUDIO_LIMIT or waveform.shape[1] * 2 * sample_rate > 0xFFFFFFFF or waveform.shape[1] * 2 > 0xFFFF:
        raise ValueError('Encoded WAV exceeds the 15MB audio limit')
    return waveform, sample_rate


def audio_duration(audio: dict) -> float:
    waveform, sample_rate = _audio_parts(audio)
    return waveform.shape[-1] / sample_rate


def audio_to_data_url(audio: dict) -> str:
    waveform, sample_rate = _audio_parts(audio)
    if not torch.isfinite(waveform).all():
        raise ValueError('AUDIO samples must be finite floating point values')
    samples = (waveform[0].detach().to(device='cpu', dtype=torch.float32).clamp(-1, 1) * 32767).round().to(torch.int16)
    pcm = samples.transpose(0, 1).contiguous().numpy().astype('<i2', copy=False).tobytes()
    encoded = io.BytesIO()
    with wave.open(encoded, 'wb') as output:
        output.setnchannels(waveform.shape[1])
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pcm)
    if encoded.tell() > AUDIO_LIMIT:
        raise ValueError('Encoded WAV exceeds 15MB')
    return 'data:audio/wav;base64,' + base64.b64encode(encoded.getvalue()).decode('ascii')


def load_image(path) -> torch.Tensor:
    path = Path(path)
    if path.stat().st_size > IMAGE_RESULT_LIMIT:
        raise ValueError('Image result exceeds 64 MiB')
    try:
        with Image.open(path) as image:
            _image_dimensions(*image.size)
            image = ImageOps.exif_transpose(image).convert('RGB')
            pixels = np.array(image, dtype=np.float32) / 255.0
    except (OSError, Image.DecompressionBombError):
        raise ValueError('Result is not a supported image') from None
    return torch.from_numpy(pixels).unsqueeze(0)
