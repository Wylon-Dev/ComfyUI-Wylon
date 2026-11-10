import { copyFile, mkdir } from 'node:fs/promises';
const root = new URL('../', import.meta.url);
await mkdir(new URL('web', root), { recursive: true });
await copyFile(new URL('shared/model-capabilities.json', root), new URL('web/model-capabilities.json', root));
await copyFile(new URL('web_src/wylon.css', root), new URL('web/wylon.css', root));
await mkdir(new URL('web/locales', root), { recursive: true });
for (const lang of ['en', 'zh']) await copyFile(new URL(`locales/${lang}.json`, root), new URL(`web/locales/${lang}.json`, root));
