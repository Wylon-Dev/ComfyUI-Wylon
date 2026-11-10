"""Internal Wylon extension. Host imports are deferred for standalone tooling."""
WEB_DIRECTORY = './web'


async def comfy_entrypoint():
    from comfy_api.latest import ComfyExtension
    from .wylon.nodes import NODE_CLASSES

    class WylonExtension(ComfyExtension):
        async def on_load(self):
            from .wylon.routes import register_routes
            register_routes()

        async def get_node_list(self):
            return NODE_CLASSES

    return WylonExtension()
