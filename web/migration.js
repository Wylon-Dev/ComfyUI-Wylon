const H = 'WylonH3Video', R = 'WylonRef2VAVideo', I = 'WylonGenerateImage', S = 'WylonReferenceVideoURL', VIDEO = 'WYLON_REFERENCE_VIDEO';
const models = { 'MiniMaxAI/MiniMax-H3': H, 'MiniMaxAI/MiniMax-H3-Ref2VA': R };
const common = ['prompt', 'duration', 'resolution', 'ratio', 'negative_prompt', 'seed', 'control_after_generate'];
const target = (link) => Array.isArray(link) ? [link[3], link[4]] : link && typeof link === 'object' ? [link.target_id, link.target_slot] : [undefined, undefined];
function fail(node, detail) { throw new Error(`Wylon node ${node.id}: ${detail}`); }
function emptyExtra(node, value) {
    if (typeof value === 'string' && value.length <= 65536) {
        try {
            const parsed = JSON.parse(value.trim() || '{}');
            if (parsed && typeof parsed === 'object' && !Array.isArray(parsed) && Object.keys(parsed).length === 0)
                return;
        }
        catch { }
    }
    fail(node, 'extra_parameters was removed; remove nonempty or invalid legacy JSON before loading. / 请先移除非空或无效的旧 JSON 配置。');
}
function checkNamed(node, names, values) {
    if (!values)
        return;
    names.forEach((name, index) => { if (name === 'extra_parameters')
        return; const named = node.widgets_values_named; if (named && Object.hasOwn(named, name) && named[name] !== values[index])
        fail(node, `conflicting saved widget values (${name})`); });
}
function imageWidgets(node) {
    const named = node.widgets_values_named;
    let values = node.widgets_values;
    if (values?.at(-1) === null && (values.length === 5 || values.length === 9))
        values = values.slice(0, -1);
    const legacy = values?.length === 8;
    if (values && values.length !== 4 && !legacy)
        fail(node, 'unsupported saved image widget layout');
    const removed = { ...(legacy ? { mode: values[3], seed: values[5], extra_parameters: values[7] } : {}), ...named };
    if (Object.hasOwn(removed, 'seed') && removed.seed !== -1)
        fail(node, 'image seed was removed; only the old default -1 can be migrated. / 图片已移除 seed，仅可迁移旧默认值 -1。');
    if (Object.hasOwn(removed, 'mode') && !['sync', 'async'].includes(String(removed.mode)))
        fail(node, 'unsupported removed image mode');
    if (legacy)
        emptyExtra(node, values[7]);
    if (named && Object.hasOwn(named, 'extra_parameters'))
        emptyExtra(node, named.extra_parameters);
    checkNamed(node, legacy ? ['model', 'prompt', 'size', 'mode', 'negative_prompt', 'seed', 'control_after_generate', 'extra_parameters'] : ['model', 'prompt', 'size', 'negative_prompt'], values);
    if (legacy)
        node.widgets_values = [values[0], values[1], values[2], values[4]];
    else if (values !== node.widgets_values)
        node.widgets_values = values;
    if (named)
        for (const name of ['mode', 'seed', 'control_after_generate', 'extra_parameters', 'wylon_configuration'])
            delete named[name];
}
function videoWidgets(node) {
    const stored = node.widgets_values, named = node.widgets_values_named;
    let values = stored;
    const oldPorts = node.inputs?.some(input => ['model', 'first_frame', 'last_frame'].includes(input.name));
    if (values?.at(-1) === null) {
        const count = values.length;
        if (count === 11 || (count === 10 && node.type === R && !oldPorts) || (count === 9 && !Object.hasOwn(named ?? {}, 'extra_parameters')) || count === 8)
            values = values.slice(0, -1);
    }
    const original = values?.length === 10;
    const selected = original ? String(values[9]) : undefined;
    if (original && (!selected || !Object.hasOwn(models, selected)))
        fail(node, `unsupported legacy model ${selected}`);
    if (named && Object.hasOwn(named, 'model') && (!selected || named.model !== selected))
        fail(node, 'conflicting or unsupported saved model values');
    const type = selected ? models[selected] : node.type;
    const interim = !original && values?.length === (node.type === H ? 8 : 9);
    const current = values?.length === 7 || (node.type === R && values?.length === 8);
    if (values && !original && !interim && !current)
        fail(node, 'unsupported saved model/widget layout');
    const extra = original || interim;
    if (extra)
        emptyExtra(node, values[7]);
    if (named && Object.hasOwn(named, 'extra_parameters'))
        emptyExtra(node, named.extra_parameters);
    const positionalUrl = original || interim ? values?.[8] : node.type === R && values?.length === 8 ? values[7] : undefined;
    const videoUrl = positionalUrl ?? named?.video_urls ?? '';
    if (type === H && (String(videoUrl ?? '').trim() || String(named?.video_urls ?? '').trim()))
        fail(node, 'video reference media cannot be used by H3. / H3 不支持参考视频。');
    const names = [...common, ...(extra ? ['extra_parameters'] : []), ...((original || interim && node.type === R || node.type === R && values?.length === 8) ? ['video_urls'] : []), ...(original ? ['model'] : [])];
    checkNamed(node, names, values);
    if (values && (original || interim || values.length === 8))
        node.widgets_values = values.slice(0, 7);
    else if (values !== stored)
        node.widgets_values = values;
    if (type !== node.type) {
        node.type = type;
        if (node.properties?.['Node name for S&R'])
            node.properties['Node name for S&R'] = type;
    }
    if (named) {
        delete named.model;
        delete named.extra_parameters;
        delete named.wylon_configuration;
        delete named.video_urls;
    }
    return videoUrl;
}
function urlText(node, value) {
    if (typeof value !== 'string')
        fail(node, 'reference video URLs must be text');
    const rows = value.split(/\r?\n/).map(row => row.trim()).filter(Boolean);
    if (rows.length > 3)
        fail(node, 'reference video URLs allow at most three HTTPS URLs');
    for (const row of rows) {
        let parsed;
        try {
            parsed = new URL(row);
        }
        catch {
            fail(node, 'invalid reference video URL');
        }
        if (parsed.protocol !== 'https:' || !parsed.hostname || parsed.username || parsed.password || parsed.hash || /\s/.test(row))
            fail(node, 'reference video URLs require public HTTPS URLs without credentials or fragments');
    }
    return value;
}
function allocationFor(root) {
    const ids = { root, graphs: [], node: new Set(), link: new Set(), lastNode: 0, lastLink: 0, addedNode: false, addedLink: false, invalidNumericId: false };
    const observe = (kind, value, counter = false) => {
        if (value === undefined)
            return;
        if (typeof value !== 'number' && typeof value !== 'string') {
            if (counter)
                ids.invalidNumericId = true;
            return;
        }
        ids[kind].add(String(value));
        const numeric = Number(value);
        if (typeof value === 'string' && !counter && Number.isNaN(numeric))
            return; // Keep UUID/string node IDs.
        if (!Number.isSafeInteger(numeric) || numeric < 0) {
            ids.invalidNumericId = true;
            return;
        }
        if (kind === 'node')
            ids.lastNode = Math.max(ids.lastNode, numeric);
        else
            ids.lastLink = Math.max(ids.lastLink, numeric);
    };
    const visit = (graph) => {
        ids.graphs.push(graph);
        for (const node of graph.nodes ?? [])
            observe('node', node.id);
        for (const link of [...graph.links ?? [], ...graph.floatingLinks ?? []])
            observe('link', linkId(link));
        observe('node', graph.last_node_id, true);
        observe('node', graph.state?.lastNodeId, true);
        observe('link', graph.last_link_id, true);
        observe('link', graph.state?.lastLinkId, true);
        for (const subgraph of graph.definitions?.subgraphs ?? [])
            visit(subgraph);
    };
    visit(root);
    return ids;
}
function idFor(ids, kind) {
    const key = kind === 'node' ? 'lastNode' : 'lastLink';
    if (ids.invalidNumericId || !Number.isSafeInteger(ids[key]))
        throw new Error('Wylon workflow: cannot allocate IDs; numeric node/link IDs and counters must be nonnegative safe integers.');
    if (ids[key] >= Number.MAX_SAFE_INTEGER)
        throw new Error('Wylon workflow: safe integer ID range exhausted; cannot add a reference video source.');
    let id = ids[key] + 1;
    while (ids[kind].has(String(id))) {
        if (id >= Number.MAX_SAFE_INTEGER)
            throw new Error('Wylon workflow: safe integer ID range exhausted.');
        id++;
    }
    ids[key] = id;
    ids[kind].add(String(id));
    if (kind === 'node')
        ids.addedNode = true;
    else
        ids.addedLink = true;
    return id;
}
function saveCounters(ids) {
    if (!ids.addedNode && !ids.addedLink)
        return;
    if (ids.root.version === 1)
        ids.root.state ??= {};
    for (const graph of ids.graphs) {
        // Native subgraphs share root state. Advance existing snapshots without
        // adding legacy counters to native definitions or changing other state.
        if (ids.addedNode) {
            if (graph.state)
                graph.state.lastNodeId = ids.lastNode;
            if (Object.hasOwn(graph, 'last_node_id') || (graph === ids.root && graph.version !== 1))
                graph.last_node_id = ids.lastNode;
        }
        if (ids.addedLink) {
            if (graph.state)
                graph.state.lastLinkId = ids.lastLink;
            if (Object.hasOwn(graph, 'last_link_id') || (graph === ids.root && graph.version !== 1))
                graph.last_link_id = ids.lastLink;
        }
    }
}
function linkId(link) { return Array.isArray(link) ? link[0] : link?.id; }
function urlsSource(graph, ids, node, text, oldInput, oldSlot, reference) {
    const links = graph.links ?? [];
    const incoming = links.filter(link => { const [id, slot] = target(link); return String(id) === String(node.id) && slot === oldSlot; });
    if (incoming.length > 1 || (oldInput?.link != null && (incoming.length !== 1 || String(linkId(incoming[0])) !== String(oldInput.link))))
        fail(node, 'ambiguous legacy video URL connection');
    if (reference.link != null && (text.trim() || incoming.length))
        fail(node, 'both dedicated reference media and legacy video URLs are connected');
    if (!text.trim() && !incoming.length)
        return;
    graph.links = links;
    const id = idFor(ids, 'node'), wire = idFor(ids, 'link');
    const source = { id, type: S, pos: [(node.pos?.[0] ?? 0) - 340, node.pos?.[1] ?? 0], size: [300, 130], flags: {}, order: node.order ?? 0, mode: 0, inputs: [], outputs: [{ name: 'reference_video', type: VIDEO, links: [wire], slot_index: 0 }], properties: { 'Node name for S&R': S }, widgets_values: [text], widgets_values_named: { urls: text } };
    if (incoming.length) {
        const old = incoming[0];
        const type = Array.isArray(old) ? old[5] : old.type;
        if (type !== 'STRING')
            fail(node, 'legacy video URL connection must have STRING type');
        if (Array.isArray(old)) {
            old[3] = id;
            old[4] = 0;
        }
        else {
            old.target_id = id;
            old.target_slot = 0;
        }
        source.inputs = [{ name: 'urls', type: 'STRING', widget: { name: 'urls' }, link: linkId(old) }];
    }
    const objectLinks = links.some(link => !Array.isArray(link)) || graph.version === 1;
    links.push(objectLinks ? { id: wire, origin_id: id, origin_slot: 0, target_id: node.id, target_slot: 0, type: VIDEO } : [wire, id, 0, node.id, 0, VIDEO]);
    reference.link = wire;
    (graph.nodes ??= []).push(source);
}
function migrate(graph, ids) {
    for (const node of graph.nodes ?? []) {
        if (![H, R, I].includes(node.type))
            continue;
        const urls = node.type === I ? (imageWidgets(node), '') : videoWidgets(node);
        const inputs = node.inputs ?? [];
        const originalLinks = [...(graph.links ?? [])];
        const urlSlots = inputs.flatMap((input, index) => input.name === 'video_urls' ? [index] : []);
        if (urlSlots.length > 1)
            fail(node, 'ambiguous legacy video URL inputs');
        const urlSlot = urlSlots[0] ?? -1;
        const typed = inputs.filter(input => input.name === 'reference_videos');
        if (typed.length > 1)
            fail(node, 'ambiguous dedicated reference video inputs');
        const reference = typed[0] ?? { name: 'reference_videos', type: VIDEO, link: null };
        if (node.type === R) {
            if (reference.type && reference.type !== VIDEO)
                fail(node, 'reference_videos must use the dedicated video type');
            reference.type = VIDEO;
            urlsSource(graph, ids, node, urlText(node, urls), inputs[urlSlot], urlSlot, reference);
        }
        const removed = (name) => name === 'extra_parameters' || (node.type === I ? ['mode', 'seed', 'control_after_generate'].includes(name) : name === 'model' || name === 'video_urls' || (node.type === H ? name === 'reference_videos' || name.startsWith('images.') || name.startsWith('audios.') : name === 'first_frame' || name === 'last_frame'));
        const slots = new Map();
        const kept = node.type === R ? [reference] : [];
        inputs.forEach((input, index) => {
            if (node.type === R && input.name === 'reference_videos') {
                slots.set(index, 0);
                return;
            }
            if (!removed(input.name)) {
                slots.set(index, kept.length);
                kept.push(input);
                return;
            }
            if (node.type === R && input.name === 'video_urls')
                return; // Its STRING wire was rerouted through the source.
            const linked = input.link != null || originalLinks.some(link => { const [id, slot] = target(link); return String(id) === String(node.id) && slot === index; });
            if (linked)
                fail(node, `incompatible media/model/removed-input connection (${input.name}). Disconnect or move it to a supported input before loading. / 媒体、模型或已移除输入连接冲突。`);
        });
        if (kept.length !== inputs.length || kept.some((input, index) => input !== inputs[index])) {
            node.inputs = kept;
            for (const link of graph.links ?? []) {
                const [id, slot] = target(link);
                if (String(id) !== String(node.id))
                    continue;
                // Newly added dedicated wires already target the final socket zero.
                const kind = Array.isArray(link) ? link[5] : link.type;
                if (kind === VIDEO && Number(slot) === 0 && String(linkId(link)) === String(reference.link))
                    continue;
                const next = slots.get(Number(slot));
                if (next === undefined)
                    continue;
                if (Array.isArray(link))
                    link[4] = next;
                else
                    link.target_slot = next;
            }
        }
    }
    for (const subgraph of graph.definitions?.subgraphs ?? [])
        migrate(subgraph, ids);
}
export function migrateWorkflow(value) {
    if (!value || typeof value !== 'object')
        return;
    // Validate and migrate a copy: one conflict leaves the complete original intact.
    const copy = structuredClone(value);
    const ids = allocationFor(copy);
    migrate(copy, ids);
    saveCounters(ids);
    if (JSON.stringify(copy) !== JSON.stringify(value))
        Object.assign(value, copy);
}
