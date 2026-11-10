"""Five native V3 nodes. Wylon credentials never enter node inputs."""
from __future__ import annotations

import json
from pathlib import Path

from comfy_api.latest import io
from comfy_execution.validation import validate_node_input
from .contracts import build_image_request, build_video_request, validate_media_url
from .media import image_batch_count, tensor_to_data_urls, audio_to_data_url, audio_duration
from .runtime import execute_media, parse_extra

CAPS = json.loads((Path(__file__).resolve().parents[1] / 'shared/model-capabilities.json').read_text())
IMAGE_MODELS = list(CAPS['image_models'])
SIZES = ['server_default'] + list(dict.fromkeys(s for m in CAPS['image_models'].values() for s in m['sizes']))
RATIOS = CAPS['video']['ratios']
VIDEO_MODELS = ['MiniMaxAI/MiniMax-H3', 'MiniMaxAI/MiniMax-H3-Ref2VA']


def output_schema(kind: str):
    return [
        (io.Image.Output('image') if kind == 'image' else io.Video.Output('video')),
        io.String.Output('task_id', tooltip='Async task ID for recovery / 异步任务恢复ID'),
        io.String.Output('file_path', tooltip='Downloaded local file / 本地结果文件'),
    ]


def advanced_inputs():
    return [
        io.String.Input('negative_prompt', default='', multiline=True, advanced=True,
                        tooltip='Model-dependent API parameter / 是否生效由模型决定'),
        io.Int.Input('seed', default=-1, min=-1, max=4294967295, control_after_generate=True, advanced=True,
                     tooltip='-1 omits seed; image seed is async-only / -1省略，图片仅异步可用'),
        io.String.Input('extra_parameters', default='{}', multiline=True, advanced=True,
                        tooltip='Other documented API parameters as JSON / 其他文档参数的JSON对象'),
    ]


def video_inputs():
    return [
        io.String.Input('prompt', default='', multiline=True, tooltip='Describe action, camera and sound / 描述动作、运镜与声音'),
        io.Int.Input('duration', default=5, min=5, max=15, step=1, tooltip='Seconds / 秒'),
        io.Combo.Input('resolution', options=['768p'], default='768p'),
        io.Combo.Input('ratio', options=['server_default'] + RATIOS + ['adaptive'], default='16:9',
                       tooltip='Adaptive is H3 frame mode only / 自适应仅H3首尾帧模式'),
        *advanced_inputs(),
    ]


def schema(node_id, name, inputs, kind, description, category='Wylon'):
    return io.Schema(node_id=node_id, display_name=name, category=category, inputs=inputs,
                     outputs=output_schema(kind), description=description,
                     hidden=[io.Hidden.unique_id], not_idempotent=True,
                     has_intermediate_output=True)


def frame_url(image):
    if image is None:
        return None
    if image_batch_count(image) != 1:
        raise ValueError('Each frame input accepts exactly one image / 首尾帧端口各只接受一张图')
    return tensor_to_data_urls(image, max_images=1)[0]


def ordered_values(group):
    if group is None:
        return []
    return [v for _, v in sorted(group.items(), key=lambda item: int(item[0].rsplit('_', 1)[-1])) if v is not None]


class WylonGenerateImage(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return schema('WylonGenerateImage', 'Wylon Generate Image', [
            io.Combo.Input('model', options=IMAGE_MODELS, default=IMAGE_MODELS[0]),
            io.String.Input('prompt', default='', multiline=True),
            io.Combo.Input('size', options=SIZES, default='server_default', tooltip='Presets depend on selected model / 尺寸按模型切换'),
            io.Combo.Input('mode', options=['async', 'sync'], default='async'),
            *advanced_inputs(),
        ], 'image', 'Generate one image through Wylon / Wylon生图。Sync returns no task ID; async supports recovery.')

    @classmethod
    async def execute(cls, model, prompt, size='server_default', mode='async', negative_prompt='', seed=-1, extra_parameters='{}'):
        payload = build_image_request(model, prompt, size=size, mode=mode, negative_prompt=negative_prompt,
                                      seed=seed if mode == 'async' else -1, extra=parse_extra(extra_parameters))
        return await execute_media(cls, 'image', payload, mode=mode)


def video_reference_inputs(default_model):
    # Widgets stay in their original positions; new widgets follow existing ones.
    return [
        io.String.Input('video_urls', default='', multiline=True, optional=True,
                        tooltip='Ref2VA: public HTTPS URL per line, up to 3 / 参考模型：每行一个公网HTTPS视频URL，最多3个'),
        io.Image.Input('first_frame', optional=True, tooltip='H3 first frame, exactly one image / H3首帧，单张图'),
        io.Image.Input('last_frame', optional=True, tooltip='H3 last frame, exactly one image / H3尾帧，单张图'),
        io.Autogrow.Input('images', template=io.Autogrow.TemplatePrefix(io.Image.Input('image'), prefix='image_', min=0, max=9), optional=True,
                          tooltip='Ref2VA reference images / 参考模型：参考图片，最多9张'),
        io.Autogrow.Input('audios', template=io.Autogrow.TemplatePrefix(io.Audio.Input('audio'), prefix='audio_', min=0, max=3), optional=True,
                          tooltip='Ref2VA audio; also connect an image or video / 参考音频，须同时提供图片或视频'),
        io.Combo.Input('model', options=VIDEO_MODELS, default=default_model, optional=True,
                       tooltip='H3: text/first/last frames; Ref2VA: reference image/video/audio. Never switches automatically / H3文生与首尾帧；Ref2VA全模态参考，不自动切换'),
    ]


def video_input_error(model, first_frame=None, last_frame=None, images=None, audios=None, video_urls='', input_types=None):
    """Check roles before encoding, also recognizing unresolved queue-time links."""
    linked = input_types or {}
    # Requesting input_types disables ComfyUI's standard linked-type checks, so
    # retain those checks for every known input, including ordinary widgets.
    widget_types = {'prompt': 'STRING', 'duration': 'INT', 'resolution': io.Combo.io_type,
                    'ratio': io.Combo.io_type, 'negative_prompt': 'STRING', 'seed': 'INT',
                    'extra_parameters': 'STRING', 'video_urls': 'STRING', 'model': io.Combo.io_type}
    for name, received in linked.items():
        expected = ('IMAGE' if name in ('first_frame', 'last_frame') or name.startswith('images.')
                    else 'AUDIO' if name.startswith('audios.') else widget_types.get(name))
        if expected is not None and not validate_node_input(received, expected):
            return f'{name} requires {expected} / 该端口需要{expected}类型'
    unresolved_model = model is None and 'model' in linked
    if not unresolved_model and model not in VIDEO_MODELS:
        return 'Choose a supported video model / 请选择支持的视频模型'
    def connected(name, value):
        return value is not None or name in linked
    has_images = bool(ordered_values(images)) or any(name.startswith('images.') for name in linked)
    has_audios = bool(ordered_values(audios)) or any(name.startswith('audios.') for name in linked)
    unresolved_urls = video_urls is None and 'video_urls' in linked
    if not unresolved_urls and not isinstance(video_urls, str):
        return 'video_urls must contain HTTPS URLs, one per line / 每行填写一个HTTPS视频URL'
    videos = [line.strip() for line in (video_urls or '').splitlines() if line.strip()]
    if model == VIDEO_MODELS[0]:
        if has_images or has_audios or videos:
            return 'Reference images/audio/video require MiniMaxAI/MiniMax-H3-Ref2VA; choose Ref2VA in model / 图片、音频和视频参考须在model中选择Ref2VA模型'
    elif not unresolved_model:
        roles = [name for name, value in (('first_frame', first_frame), ('last_frame', last_frame)) if connected(name, value)]
        if roles:
            return ('Ref2VA does not accept ' + ', '.join(roles) + '; connect reference images to images, or choose H3 for first/last frames / '
                    'Ref2VA不接受首尾帧角色；参考图片请连接images，首尾帧生成请选择H3')
        if not has_images and not videos and not unresolved_urls:
            return 'Ref2VA requires a reference image or video; audio alone is unsupported / Ref2VA须提供参考图片或视频，不支持仅音频或空参考'
    if len(videos) > 3:
        return 'At most 3 reference video URLs / 最多3个参考视频URL'
    for url in videos:
        try:
            validate_media_url(url, 'video')
        except ValueError:
            return 'Each reference video must be a public HTTPS URL / 每个参考视频须使用公网HTTPS URL'
    return True


async def execute_video(cls, model, prompt, duration, resolution, ratio, negative_prompt, seed,
                        extra_parameters, first_frame, last_frame, images, audios, video_urls):
    valid = video_input_error(model, first_frame, last_frame, images, audios, video_urls)
    if valid is not True:
        raise ValueError(valid)
    image_inputs = ordered_values(images)
    audio_inputs = ordered_values(audios)
    if len(audio_inputs) > 3:
        raise ValueError('At most 3 reference audios / 最多3个参考音频')
    remaining_images = 9
    for image in image_inputs:
        remaining_images -= image_batch_count(image, max_images=remaining_images)
    for frame in (first_frame, last_frame):
        if frame is not None and image_batch_count(frame) != 1:
            raise ValueError('Each frame input accepts exactly one image / 首尾帧端口各只接受一张图')
    if sum(audio_duration(audio) for audio in audio_inputs) > 15:
        raise ValueError('Total reference audio must not exceed 15 seconds / 参考音频总时长不能超过15秒')
    image_urls = []
    for image in image_inputs:
        image_urls.extend(tensor_to_data_urls(image, max_images=9 - len(image_urls)))
    audio_urls = [audio_to_data_url(audio) for audio in audio_inputs]
    video_refs = [line.strip() for line in video_urls.splitlines() if line.strip()]
    payload = build_video_request(model, prompt, first_frame=frame_url(first_frame), last_frame=frame_url(last_frame),
                                  images=image_urls, videos=video_refs, audios=audio_urls, duration=duration,
                                  resolution=resolution, ratio=ratio, negative_prompt=negative_prompt,
                                  seed=seed, extra=parse_extra(extra_parameters))
    return await execute_media(cls, 'video', payload)


class WylonH3Video(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return schema('WylonH3Video', 'Wylon H3 Video · 音视频（可切换模型）', [
            *video_inputs(), *video_reference_inputs(VIDEO_MODELS[0]),
        ], 'video', 'Choose H3 for text/first/last frames, Ref2VA for image/video/audio references / H3文生与首尾帧，Ref2VA全模态参考',
           category='Wylon/Video 音视频')

    @classmethod
    def validate_inputs(cls, model=VIDEO_MODELS[0], first_frame=None, last_frame=None, images=None, audios=None,
                        video_urls='', input_types=None):
        return video_input_error(model, first_frame, last_frame, images, audios, video_urls, input_types)

    @classmethod
    async def execute(cls, prompt, duration=5, resolution='768p', ratio='16:9', negative_prompt='', seed=-1,
                      extra_parameters='{}', first_frame=None, last_frame=None, video_urls='', images=None,
                      audios=None, model=VIDEO_MODELS[0]):
        return await execute_video(cls, model, prompt, duration, resolution, ratio, negative_prompt, seed,
                                   extra_parameters, first_frame, last_frame, images, audios, video_urls)


class WylonRef2VAVideo(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return schema('WylonRef2VAVideo', 'Wylon Ref2VA Video · 参考音视频（可切换模型）', [
            *video_inputs(), *video_reference_inputs(VIDEO_MODELS[1]),
        ], 'video', 'Choose Ref2VA for references; audio requires an image/video. Switch to H3 for text/first/last frames / 参考音频须配图片或视频；文生和首尾帧请选择H3',
           category='Wylon/Video 音视频')

    @classmethod
    def validate_inputs(cls, model=VIDEO_MODELS[1], first_frame=None, last_frame=None, images=None, audios=None,
                        video_urls='', input_types=None):
        return video_input_error(model, first_frame, last_frame, images, audios, video_urls, input_types)

    @classmethod
    async def execute(cls, prompt, duration=5, resolution='768p', ratio='16:9', negative_prompt='', seed=-1,
                      extra_parameters='{}', video_urls='', images=None, audios=None, first_frame=None,
                      last_frame=None, model=VIDEO_MODELS[1]):
        return await execute_video(cls, model, prompt, duration, resolution, ratio, negative_prompt, seed,
                                   extra_parameters, first_frame, last_frame, images, audios, video_urls)


class WylonResumeImageTask(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return schema('WylonResumeImageTask', 'Wylon Resume Image Task', [io.String.Input('task_id', default='')],
                      'image', 'Query and download an existing image task; no new generation / 恢复图片任务，不重新生成')

    @classmethod
    async def execute(cls, task_id):
        return await execute_media(cls, 'image', task_id=task_id)


class WylonResumeVideoTask(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return schema('WylonResumeVideoTask', 'Wylon Resume Video Task', [io.String.Input('task_id', default='')],
                      'video', 'Query and download an existing video task; no new generation / 恢复视频任务，不重新生成')

    @classmethod
    async def execute(cls, task_id):
        return await execute_media(cls, 'video', task_id=task_id)


NODE_CLASSES = [WylonGenerateImage, WylonH3Video, WylonRef2VAVideo, WylonResumeImageTask, WylonResumeVideoTask]
