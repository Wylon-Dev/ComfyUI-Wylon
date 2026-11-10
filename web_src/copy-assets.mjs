import { copyFile, cp, mkdir } from 'node:fs/promises';
const root = new URL('../', import.meta.url);
await mkdir(new URL('web', root), { recursive: true });
await copyFile(new URL('shared/model-capabilities.json', root), new URL('web/model-capabilities.json', root));
await copyFile(new URL('web_src/wylon.css', root), new URL('web/wylon.css', root));
await cp(new URL('locales', root), new URL('web/locales', root), { recursive: true });
