export interface Capabilities { image_models: Record<string, { sizes: string[] }> }
export interface SizeWidget { value: unknown; options: { values?: string[] } }
export function imageSizes(capabilities: Capabilities, model: string): string[] {
  return ['server_default', ...(capabilities.image_models[model]?.sizes ?? [])];
}
export function applyImageSize(widget: SizeWidget, capabilities: Capabilities, model: string): void {
  const values = imageSizes(capabilities, model);
  widget.options.values = values;
  if (!values.includes(String(widget.value))) widget.value = 'server_default';
}
export const statuses = ['submitting','queued','pending','running','processing','completed','succeeded','success','failed','canceled','cancelled','expired','unknown','downloading','downloaded','interrupted','error','resuming'] as const;
export type StatusName = typeof statuses[number];
export interface TaskStatus { node_id: string; status: StatusName; task_id?: string; elapsed: number; message?: string }
export interface Model { id: string; type: string }
export interface Task { id: string; kind: string; model: string; status: string; updated_at: string }
const record = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
export function parseStatus(value: unknown): TaskStatus | null {
  if (!record(value) || !['string','number'].includes(typeof value.node_id) || !statuses.includes(value.status as StatusName)) return null;
  const elapsed = value.elapsed ?? 0;
  if (typeof elapsed !== 'number' || !Number.isFinite(elapsed) || elapsed < 0) return null;
  const result: TaskStatus = {node_id: String(value.node_id), status: value.status as StatusName, elapsed};
  if (typeof value.task_id === 'string') result.task_id = value.task_id;
  if (typeof value.message === 'string') result.message = value.message;
  return result;
}
export function parseModels(value: unknown): { configured: boolean; models: Model[] } {
  if (!record(value) || typeof value.configured !== 'boolean' || !Array.isArray(value.models)) throw new Error('Invalid model response');
  return { configured: value.configured, models: value.models.filter(record).filter(v => typeof v.id === 'string' && typeof v.type === 'string').map(v=>({id:String(v.id),type:String(v.type)})) };
}
export function parseTasks(value: unknown): Task[] {
  if (!record(value) || !Array.isArray(value.tasks)) throw new Error('Invalid task response');
  return value.tasks.filter(record).filter(v=>['id','kind','model','status','updated_at'].every(k=>typeof v[k] === 'string')).map(v=>({id:String(v.id),kind:String(v.kind),model:String(v.model),status:String(v.status),updated_at:String(v.updated_at)}));
}
export function languageFor(setting: unknown, browser: string): 'en' | 'zh' {
  return (typeof setting === 'string' && setting ? setting : browser).toLowerCase().startsWith('zh') ? 'zh' : 'en';
}
export function formatTaskTimestamp(value: string, locale: 'en' | 'zh', timeZone?: string): string {
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return value;
  return new Intl.DateTimeFormat(locale === 'zh' ? 'zh-CN' : 'en-US', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZoneName: 'short',
    ...(timeZone ? {timeZone} : {}),
  }).format(date);
}

export function parsePageToken(value: unknown): string {
  if (!record(value)) throw new Error('Invalid page response');
  if (value.next_page_token === undefined) return ''; // Legacy responses have no pagination metadata.
  if (typeof value.next_page_token !== 'string' || value.next_page_token.length > 2048) throw new Error('Invalid page token');
  return value.next_page_token;
}
export function apiErrorMessage(value: unknown, fallback: string): string {
  if (!record(value)) return fallback;
  if (typeof value.error === 'string') return value.error;
  return record(value.error) && typeof value.error.message === 'string' ? value.error.message : fallback;
}
