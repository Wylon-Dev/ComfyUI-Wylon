"""Six native V3 nodes, including a pure typed reference URL source. Wylon credentials never enter node inputs."""
from __future__ import annotations

import json
import re
from pathlib import Path

from comfy_api.latest import io
from comfy_execution.validation import validate_node_input
from .contracts import build_image_request, build_video_request, validate_video_parameters, validate_image_parameters, ReferenceVideoBundle, validate_reference_video_bundle
from .media import image_batch_count, tensor_to_data_urls, audio_to_data_url, audio_duration
from .runtime import execute_media, task_id_error

CAPS = json.loads((Path(__file__).resolve().parents[1] / 'shared/model-capabilities.json').read_text())
IMAGE_MODELS = list(CAPS['image_models'])
SIZES = ['server_default'] + list(dict.fromkeys(s for m in CAPS['image_models'].values() for s in m['sizes']))
RATIOS = CAPS['video']['ratios']
H3_MODEL = 'MiniMaxAI/MiniMax-H3'
REF2VA_MODEL = 'MiniMaxAI/MiniMax-H3-Ref2VA'
REFERENCE_VIDEO = io.Custom('WYLON_REFERENCE_VIDEO')


def output_schema(kind: str):
    return [
        (io.Image.Output('image', tooltip='Downloaded and decoded image.') if kind == 'image'
         else io.Video.Output('video', tooltip='Downloaded video, including its audio track.')),
        io.String.Output('task_id', tooltip='Existing asynchronous task ID; empty for synchronous images.'),
        io.String.Output('file_path', tooltip='Downloaded file in the ComfyUI output directory.'),
    ]


def video_advanced_inputs():
    return [
        io.String.Input('negative_prompt', default='', multiline=True, advanced=True,
                        tooltip='Negative prompt; support depends on the model.'),
        io.Int.Input('seed', default=-1, min=-1, max=4294967295, control_after_generate=io.ControlAfterGenerate.fixed, advanced=True,
                     tooltip='-1 omits the API seed. Nonnegative seeds are sent for video generation. Seed control after generation is local.'),
    ]


def video_inputs(*, reference=False):
    return [
        io.String.Input('prompt', default='', multiline=True, tooltip='Describe action, camera movement, and sound.'),
        io.Int.Input('duration', default=5, min=5, max=15, step=1, tooltip='Video duration in seconds, from 5 to 15.'),
        io.Combo.Input('resolution', options=['768p'], default='768p', tooltip='Video output resolution.'),
        io.Combo.Input('ratio', options=['server_default'] + RATIOS + ([] if reference else ['adaptive']), default='16:9',
                       tooltip=('Video aspect ratio; server_default omits the API ratio.' if reference else
                                'Video aspect ratio; adaptive requires a first or last frame and omits the API ratio.')),
        *video_advanced_inputs(),
    ]


def schema(node_id, name, inputs, kind, description, category='Wylon', *, output=False, legacy_inputs=False):
    return io.Schema(node_id=node_id, display_name=name, category=category, inputs=inputs,
                     outputs=output_schema(kind), description=description,
                     hidden=[io.Hidden.unique_id], not_idempotent=True,
                     has_intermediate_output=True, is_output_node=output, accept_all_inputs=legacy_inputs)


def frame_url(image):
    if image is None:
        return None
    if image_batch_count(image) != 1:
        raise ValueError('Each frame input accepts exactly one image')
    return tensor_to_data_urls(image, max_images=1)[0]


def ordered_values(group):
    if group is None:
        return []
    return [v for _, v in sorted(group.items(), key=lambda item: int(item[0].rsplit('_', 1)[-1])) if v is not None]


def removed_extra_error(values):
    if 'extra_parameters' not in values:
        return True
    text = values['extra_parameters']
    message = 'extra_parameters was removed. Remove the nonempty legacy JSON configuration before running this node.'
    if not isinstance(text, str) or len(text) > 65536:
        return message
    try:
        extra = json.loads(text.strip() or '{}')
    except (ValueError, TypeError):
        return message
    return True if isinstance(extra, dict) and not extra else message


def image_input_error(values, input_types=None):
    linked = input_types or {}
    widget_types = {'model': io.Combo.io_type, 'prompt': 'STRING', 'size': io.Combo.io_type,
                    'negative_prompt': 'STRING', 'mode': io.Combo.io_type, 'seed': 'INT',
                    'extra_parameters': 'STRING'}
    for name, received in linked.items():
        expected = widget_types.get(name)
        if expected is not None and not validate_node_input(received, expected):
            return f'{name} requires {expected}'
    unknown = set(values) - set(widget_types)
    if unknown:
        return 'Unsupported image input: ' + ', '.join(sorted(unknown))
    if 'mode' in values and values['mode'] != 'sync':
        return 'Wylon Generate Image is synchronous only; remove the legacy mode input or use mode=sync.'
    if 'seed' in values and (type(values['seed']) is not int or values['seed'] != -1):
        return 'seed is unsupported by synchronous Wylon Generate Image; remove the legacy seed input.'
    valid = removed_extra_error(values)
    if valid is not True:
        return valid
    parameters = {name: values[name] for name in ('model', 'prompt', 'size', 'negative_prompt')
                  if name in values and not (values[name] is None and name in linked)}
    try:
        validate_image_parameters(parameters)
    except ValueError as exc:
        return str(exc)
    return True


class WylonGenerateImage(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return schema('WylonGenerateImage', 'Wylon Generate Image', [
            io.Combo.Input('model', options=IMAGE_MODELS, default=IMAGE_MODELS[0], tooltip='Image generation model.'),
            io.String.Input('prompt', default='', multiline=True, tooltip='Describe the image to generate.'),
            io.Combo.Input('size', options=SIZES, default='server_default', tooltip='Image size presets depend on the selected model.'),
            io.String.Input('negative_prompt', default='', multiline=True, advanced=True,
                            tooltip='Negative prompt; support depends on the model.'),
        ], 'image', 'Generate and download one image synchronously. The task ID output is empty.', legacy_inputs=True)

    @classmethod
    def validate_inputs(cls, input_types=None, **values):
        return image_input_error(values, input_types)

    @classmethod
    async def execute(cls, model, prompt, size='server_default', negative_prompt='', **legacy):
        valid = image_input_error(dict(legacy, model=model, prompt=prompt, size=size, negative_prompt=negative_prompt))
        if valid is not True:
            raise ValueError(valid)
        payload = build_image_request(model, prompt, size=size, mode='sync', negative_prompt=negative_prompt)
        return await execute_media(cls, 'image', payload, mode='sync')


def video_input_error(fixed_model, values, input_types=None):
    """Retain legacy inputs for rejection, never to select another model."""
    linked = input_types or {}
    widget_types = {'prompt': 'STRING', 'duration': 'INT', 'resolution': io.Combo.io_type,
                    'ratio': io.Combo.io_type, 'negative_prompt': 'STRING', 'seed': 'INT',
                    'extra_parameters': 'STRING', 'video_urls': 'STRING', 'model': io.Combo.io_type,
                    'reference_videos': 'WYLON_REFERENCE_VIDEO'}
    # input_types opts out of native linked-type checks, so preserve them here.
    for name, received in linked.items():
        expected = ('IMAGE' if name in ('first_frame', 'last_frame') or name.startswith('images.')
                    else 'AUDIO' if name.startswith('audios.') else widget_types.get(name))
        if expected is not None and not validate_node_input(received, expected):
            return f'{name} requires {expected}'
    valid = removed_extra_error(values)
    if valid is not True:
        return valid
    if 'model' in values and values['model'] != fixed_model:
        return f'This node has a fixed model: {fixed_model}. Use the other video node for its supported roles.'
    known = set(widget_types) | {'first_frame', 'last_frame', 'images', 'audios'}
    unknown = [name for name in values if name not in known and not re.fullmatch(r'(images\.image_[0-8]|audios\.audio_[0-2])', name)]
    if unknown:
        return 'Unsupported video input: ' + ', '.join(sorted(unknown))

    def connected(name):
        # None is an unresolved queue link when this key is present. Empty legacy
        # widgets/groups are harmless; populated or unresolved roles are rejected.
        return name in linked or (name in values and values[name] != '' and values[name] != {})

    has_images = bool(ordered_values(values.get('images'))) or any(name.startswith('images.') for name in values) or any(name.startswith('images.') for name in linked)
    has_audios = bool(ordered_values(values.get('audios'))) or any(name.startswith('audios.') for name in values) or any(name.startswith('audios.') for name in linked)
    legacy_urls = values.get('video_urls', '')
    if not isinstance(legacy_urls, str) or legacy_urls.strip():
        return 'Use Wylon Reference Video URL and connect reference_video to the Ref2VA reference_videos input; video_urls was removed.'
    reference_videos = values.get('reference_videos')
    unresolved_videos = reference_videos is None and 'reference_videos' in linked
    if fixed_model == H3_MODEL:
        if has_images or has_audios or 'reference_videos' in values or 'reference_videos' in linked or ('images' in values and values['images'] is None) or ('audios' in values and values['audios'] is None):
            return 'Reference images/audio/video require the Wylon Ref2VA Video node.'
    else:
        roles = [name for name in ('first_frame', 'last_frame') if connected(name)]
        if roles:
            return 'Ref2VA does not accept ' + ', '.join(roles) + '; connect reference images to images or use the Wylon H3 Video node.'
        try:
            videos = validate_reference_video_bundle(reference_videos) if reference_videos is not None else ()
        except ValueError as exc:
            return str(exc)
        if not has_images and not videos and not unresolved_videos:
            return 'Ref2VA requires a reference image or video; audio alone is unsupported'
    scalar_names = ('prompt', 'duration', 'resolution', 'ratio', 'negative_prompt', 'seed')
    parameters = {name: values[name] for name in scalar_names
                  if name in values and not (values[name] is None and name in linked)}
    try:
        validate_video_parameters(fixed_model, parameters,
                                  has_frames=any(connected(name) for name in ('first_frame', 'last_frame')))
    except ValueError as exc:
        return str(exc)
    return True


async def execute_video(cls, model, prompt, duration, resolution, ratio, negative_prompt, seed,
                        first_frame=None, last_frame=None, images=None, audios=None, reference_videos=None):
    video_refs = list(validate_reference_video_bundle(reference_videos)) if reference_videos is not None else []
    image_inputs = ordered_values(images)
    audio_inputs = ordered_values(audios)
    if len(audio_inputs) > 3:
        raise ValueError('At most 3 reference audios')
    remaining_images = 9
    for image in image_inputs:
        remaining_images -= image_batch_count(image, max_images=remaining_images)
    for frame in (first_frame, last_frame):
        if frame is not None and image_batch_count(frame) != 1:
            raise ValueError('Each frame input accepts exactly one image')
    if sum(audio_duration(audio) for audio in audio_inputs) > 15:
        raise ValueError('Total reference audio must not exceed 15 seconds')
    image_urls = []
    for image in image_inputs:
        image_urls.extend(tensor_to_data_urls(image, max_images=9 - len(image_urls)))
    audio_urls = [audio_to_data_url(audio) for audio in audio_inputs]
    payload = build_video_request(model, prompt, first_frame=frame_url(first_frame), last_frame=frame_url(last_frame),
                                  images=image_urls, videos=video_refs, audios=audio_urls, duration=duration,
                                  resolution=resolution, ratio=ratio, negative_prompt=negative_prompt,
                                  seed=seed)
    return await execute_media(cls, 'video', payload)


class WylonH3Video(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return schema('WylonH3Video', 'Wylon H3 Video (Text / First & Last Frames)', [
            *video_inputs(),
            io.Image.Input('first_frame', optional=True, tooltip='H3 first frame; exactly one image.'),
            io.Image.Input('last_frame', optional=True, tooltip='H3 last frame; exactly one image.'),
        ], 'video', 'Generate with the fixed MiniMaxAI/MiniMax-H3 model using text and optional first/last frames. Submit, wait, and download.',
           category='Wylon/Video', legacy_inputs=True)

    @classmethod
    def validate_inputs(cls, input_types=None, **values):
        return video_input_error(H3_MODEL, values, input_types)

    @classmethod
    async def execute(cls, prompt, duration=5, resolution='768p', ratio='16:9', negative_prompt='', seed=-1,
                      first_frame=None, last_frame=None, **legacy):
        values = dict(legacy, prompt=prompt, duration=duration, resolution=resolution, ratio=ratio,
                      negative_prompt=negative_prompt, seed=seed)
        values.update({name: value for name, value in [('first_frame', first_frame), ('last_frame', last_frame)] if value is not None})
        valid = video_input_error(H3_MODEL, values)
        if valid is not True:
            raise ValueError(valid)
        return await execute_video(cls, H3_MODEL, prompt, duration, resolution, ratio, negative_prompt, seed,
                                   first_frame=first_frame, last_frame=last_frame)


class WylonRef2VAVideo(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return schema('WylonRef2VAVideo', 'Wylon Ref2VA Video (Reference Media)', [
            *video_inputs(reference=True),
            REFERENCE_VIDEO.Input('reference_videos', optional=True,
                                  tooltip='Validated reference video URLs from Wylon Reference Video URL; up to 3.'),
            io.Autogrow.Input('images', template=io.Autogrow.TemplatePrefix(io.Image.Input('image', tooltip='Reference image or image batch.'), prefix='image_', min=0, max=9), optional=True,
                              tooltip='Reference images; up to 9 images in total.'),
            io.Autogrow.Input('audios', template=io.Autogrow.TemplatePrefix(io.Audio.Input('audio', tooltip='Reference audio.'), prefix='audio_', min=0, max=3), optional=True,
                              tooltip='Up to 3 reference audios, 15 seconds total; also supply an image or video.'),
        ], 'video', 'Generate with the fixed MiniMaxAI/MiniMax-H3-Ref2VA model using reference images/video/audio. Audio requires an image or video. Submit, wait, and download.',
           category='Wylon/Video', legacy_inputs=True)

    @classmethod
    def validate_inputs(cls, input_types=None, **values):
        return video_input_error(REF2VA_MODEL, values, input_types)

    @classmethod
    async def execute(cls, prompt, duration=5, resolution='768p', ratio='16:9', negative_prompt='', seed=-1,
                      reference_videos=None, images=None, audios=None, **legacy):
        values = dict(legacy, prompt=prompt, duration=duration, resolution=resolution, ratio=ratio,
                      negative_prompt=negative_prompt, seed=seed,
                      reference_videos=reference_videos, images=images, audios=audios)
        valid = video_input_error(REF2VA_MODEL, values)
        if valid is not True:
            raise ValueError(valid)
        if any(name.startswith(('images.', 'audios.')) for name in legacy):
            raise ValueError('Reference inputs must use normalized images/audios groups')
        return await execute_video(cls, REF2VA_MODEL, prompt, duration, resolution, ratio, negative_prompt, seed,
                                   images=images, audios=audios, reference_videos=reference_videos)


def retrieval_input_error(task_id, input_types):
    if input_types and 'task_id' in input_types:
        if not validate_node_input(input_types['task_id'], 'STRING'):
            return 'task_id requires STRING'
        if task_id is None:
            return True  # Queue-time link; execute validates its resolved value.
    return task_id_error(task_id)


class WylonResumeImageTask(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return schema('WylonResumeImageTask', 'Wylon Get Image Task Result', [
            io.String.Input('task_id', default='', tooltip='Existing asynchronous image task ID from the Wylon panel or an error message.')],
            'image', 'Query an existing image task, wait for completion, and download its result. Runs standalone; each execution may save another copy.', output=True)

    @classmethod
    def validate_inputs(cls, task_id, input_types=None):
        return retrieval_input_error(task_id, input_types)

    @classmethod
    async def execute(cls, task_id):
        return await execute_media(cls, 'image', task_id=task_id)


class WylonResumeVideoTask(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return schema('WylonResumeVideoTask', 'Wylon Get Video Task Result', [
            io.String.Input('task_id', default='', tooltip='Existing asynchronous video task ID from the Wylon panel or an error message.')],
            'video', 'Query an existing video task, wait for completion, and download its result. Runs standalone; each execution may save another copy.', output=True)

    @classmethod
    def validate_inputs(cls, task_id, input_types=None):
        return retrieval_input_error(task_id, input_types)

    @classmethod
    async def execute(cls, task_id):
        return await execute_media(cls, 'video', task_id=task_id)


class WylonReferenceVideoURL(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(node_id='WylonReferenceVideoURL', display_name='Wylon Reference Video URL',
                         category='Wylon/References', inputs=[
                             io.String.Input('urls', default='', multiline=True,
                                             tooltip='Public HTTPS video URLs, one per line; up to 3. Leave empty for no reference video.')],
                         outputs=[REFERENCE_VIDEO.Output('reference_video',
                                  tooltip='Validated reference video URLs for the Ref2VA reference_videos input.')],
                         description='Validate up to three public HTTPS reference video URLs for Ref2VA. No upload, download, or generation.')

    @classmethod
    def validate_inputs(cls, urls, input_types=None):
        if input_types and 'urls' in input_types:
            if not validate_node_input(input_types['urls'], 'STRING'):
                return 'urls requires STRING'
            if urls is None:
                return True
        try:
            cls.execute(urls)
        except ValueError as exc:
            return str(exc)
        return True

    @classmethod
    def execute(cls, urls=''):
        if not isinstance(urls, str):
            raise ValueError('urls must be public HTTPS video URLs, one per line')
        return io.NodeOutput(ReferenceVideoBundle(tuple(line.strip() for line in urls.splitlines() if line.strip())))


NODE_CLASSES = [WylonGenerateImage, WylonH3Video, WylonRef2VAVideo, WylonResumeImageTask, WylonResumeVideoTask, WylonReferenceVideoURL]
