import { migrateWorkflow } from './migration.js';
import { app } from '../../../scripts/app.js';
import { api } from '../../../scripts/api.js';
import { apiErrorMessage, parsePageToken, formatTaskTimestamp, applyImageSize, languageFor, parseModels, parseStatus, parseTasks, type Capabilities, type TaskStatus } from './core.js';
interface Widget {serialize?:boolean;inputEl?:HTMLInputElement|HTMLTextAreaElement;label?:string; tooltip?:string; name:string; value:unknown; options:{values?:string[];tooltip?:string}; callback?:(...args:unknown[])=>unknown}
interface Slot {name:string;label?:string;localized_name?:string;tooltip?:string}
interface Node {title?:string;inputs?:Slot[];outputs?:Slot[];onConnectionsChange?:(...args:unknown[])=>unknown;comfyClass?:string; widgets?:Widget[]; setDirtyCanvas?:(foreground:boolean,background:boolean)=>void; addWidget?:(type:string,name:string,value:unknown,callback:()=>void,options:Record<string,unknown>)=>unknown}
interface Strings { [key: string]: string | Record<string,string> }
let capabilities: Capabilities = {image_models:{}};
let strings: Strings = {};
let locale: 'en' | 'zh' = 'en';
interface NodeText {display_name:string;inputs:Record<string,{name:string;tooltip:string}>;outputs:Record<string,{name:string;tooltip:string}>}
let native:Partial<Record<'en'|'zh',{nodeDefs:Record<string,NodeText>}>>={};
const nodes=new Set<WeakRef<Node>>();
let localeRevision=0;
let localeSetting:unknown;
let dialog: HTMLDialogElement | undefined;
let liveContainer: HTMLElement | undefined;
let configFeedback: HTMLElement | undefined;
let configSummary: HTMLElement | undefined;
const live = new Map<string,TaskStatus>();
const t = (key:string) => typeof strings[key] === 'string' ? strings[key] as string : key;
const label = (status:string) => (strings.status as Record<string,string> | undefined)?.[status] ?? status;
function element<K extends keyof HTMLElementTagNameMap>(tag:K, text?:string, className?:string):HTMLElementTagNameMap[K] {
  const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;
}
function button(text:string,action:()=>void):HTMLButtonElement {const b=element('button',text);b.type='button';b.addEventListener('click',action);return b;}
function taskRow(id:string,status:string,detail:string):HTMLElement {
  const row=element('article',undefined,'wylon-task');
  const heading=element('div',undefined,'wylon-task-head');heading.append(element('strong',label(status)),element('small',detail));
  const code=element('code',id);code.tabIndex=0;
  const feedback=element('span');feedback.setAttribute('role','status');
  const copy=button(t('copy'),()=>{void (async()=>{try{await navigator.clipboard.writeText(id);feedback.textContent=t('copied');}catch{feedback.textContent=t('copyFailed');code.focus();}})();});
  row.append(heading,code,copy,feedback);return row;
}
function renderLive():void {
  if(!liveContainer)return;liveContainer.replaceChildren();
  for(const status of [...live.values()].reverse()) {
    const row=status.task_id ? taskRow(status.task_id,status.status,`${status.node_id} · ${Math.floor(status.elapsed)}s`) : element('p',`${status.node_id} · ${label(status.status)} · ${Math.floor(status.elapsed)}s`);
    // Event messages are deliberately not rendered: task identifiers and states are sufficient here.
    liveContainer.append(row);
  }
}
function configurationForm(): HTMLElement {
  const section=element('section',undefined,'wylon-config');
  section.append(element('h3',t('apiKeyTitle')));
  configSummary=element('p',t('loading'),'wylon-connection');section.append(configSummary);
  const form=element('form');
  const keyLabel=element('label',t('apiKeyLabel'));keyLabel.htmlFor='wylon-api-key';
  const input=element('input');input.type='password';input.id='wylon-api-key';input.autocomplete='off';input.placeholder=t('apiKeyPlaceholder');input.spellcheck=false;
  const rememberLabel=element('label',undefined,'wylon-remember');const remember=element('input');remember.type='checkbox';remember.checked=false;
  rememberLabel.append(remember,document.createTextNode(t('rememberKey')));
  const save=element('button',t('saveKey'));save.type='submit';
  const actions=element('div',undefined,'wylon-actions');
  actions.append(save,button(t('clearSession'),()=>{void clearConfiguration('session');}),button(t('deleteLocalKey'),()=>{void clearConfiguration('local');}));
  configFeedback=element('p',undefined,'wylon-config-feedback');configFeedback.setAttribute('role','status');
  form.append(keyLabel,input,rememberLabel,actions,configFeedback);
  form.addEventListener('submit',(event)=>{event.preventDefault();void (async()=>{
    save.disabled=true;configFeedback!.textContent='';
    try {
      const response=await api.fetchApi('/v1/wylon/configuration',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:input.value.trim(),persist:remember.checked})});
      if(!response.ok)throw new Error(apiErrorMessage(await response.json(),t('keySaveFailed')));
      input.value='';configFeedback!.textContent=t('keySaved');
      configFeedback!.textContent=(await refreshMetadata())?t('keyVerified'):t('connectionFailed');
    } catch (error) {configFeedback!.textContent=error instanceof Error?error.message:t('keySaveFailed');}
    finally {save.disabled=false;}
  })();});
  section.append(form,element('p',t('keyStorageHelp'),'wylon-muted'));
  const help=element('details');help.append(element('summary',t('environmentHelpTitle')),element('p',t('environmentHelp'),'wylon-muted'));
  section.append(help);return section;
}
async function clearConfiguration(scope:'session'|'local'):Promise<void> {
  try {
    const response=await api.fetchApi('/v1/wylon/configuration',{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({scope})});
    if(!response.ok)throw new Error(apiErrorMessage(await response.json(),t('keySaveFailed')));
    if(configFeedback)configFeedback.textContent=t('keyCleared');await refreshMetadata();
  } catch (error) {if(configFeedback)configFeedback.textContent=error instanceof Error?error.message:t('keySaveFailed');}
}
async function showDialog():Promise<void> {
  if(!dialog) {
    dialog=element('dialog',undefined,'wylon-panel');dialog.setAttribute('aria-labelledby','wylon-dialog-title');
    const head=element('header');const title=element('h2',t('title'));title.id='wylon-dialog-title';head.append(title,button(t('close'),()=>dialog?.close()));
    const privacy=element('p',t('privacy'),'wylon-muted');
    const liveTitle=element('h3',t('live'));liveContainer=element('section');liveContainer.setAttribute('aria-live','polite');
    const body=element('section');body.id='wylon-remote';body.setAttribute('aria-live','polite');
    const refresh=button(t('refresh'),()=>{void refreshMetadata();});refresh.id='wylon-refresh';
    dialog.append(head,privacy,configurationForm(),refresh,liveTitle,liveContainer,body,element('p',t('resume'),'wylon-muted'));
    dialog.addEventListener('close',()=>{const input=dialog?.querySelector<HTMLInputElement>('input[type=password]');if(input)input.value='';});
    dialog.addEventListener('click',(e)=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
    document.body.append(dialog);
  }
  renderLive();if(!dialog.open)dialog.showModal();await refreshMetadata();
}
function gallery(data:unknown):HTMLElement {
  const section=element('section');section.append(element('h3',t('results')));
  const grid=element('div',undefined,'wylon-gallery');
  const rows=(data&&typeof data==='object'&&Array.isArray((data as {results?:unknown}).results))?(data as {results:Record<string,unknown>[]}).results:[];
  for(const row of rows) {
    if(!row||typeof row!=='object'||typeof row.filename!=='string'||!/^[A-Za-z0-9_.-]+\.(png|mp4)$/.test(row.filename)||row.subfolder!=='wylon'||row.type!=='output'||!['image','video'].includes(String(row.kind)))continue;
    const url='/view?'+new URLSearchParams({filename:row.filename,subfolder:'wylon',type:'output'}).toString();
    const card=element('figure');
    if(row.kind==='image') {const media=element('img');media.src=url;media.loading='lazy';media.alt=t('generatedImage');card.append(media);}
    else {const media=element('video');media.src=url;media.controls=true;media.preload='metadata';media.playsInline=true;media.setAttribute('aria-label',t('generatedVideo'));card.append(media);}
    const caption=element('figcaption');const link=element('a',t('openResult'));link.href=url;link.target='_blank';link.rel='noopener';
    caption.append(link);if(typeof row.created_at==='string')caption.append(element('small',formatTaskTimestamp(row.created_at,locale)));
    card.append(caption);grid.append(card);
  }
  if(!grid.childElementCount)section.append(element('p',t('noResults'),'wylon-muted'));else section.append(grid);
  return section;
}
async function refreshMetadata():Promise<boolean> {
  const body=dialog?.querySelector<HTMLElement>('#wylon-remote');if(!body)return false;
  const refresh=dialog?.querySelector<HTMLButtonElement>('#wylon-refresh');if(refresh)refresh.disabled=true;
  body.replaceChildren(element('p',t('loading')));
  try {
    const responses=await Promise.allSettled(['/v1/wylon/configuration','/v1/wylon/models?page_size=100','/v1/wylon/tasks?page_size=12','/v1/wylon/results?page_size=24'].map(path=>api.fetchApi(path)));
    const data=await Promise.all(responses.map(async result=>result.status==='fulfilled'&&result.value.ok?result.value.json():null));
    const config=data[0];
    if(configSummary)configSummary.textContent=config?.configured?`${t('configured')} · ${t('source_'+String(config.source))}${config.persisted?' · '+t('localKeyPresent'):''}`:t('unconfigured');
    const fragment=document.createDocumentFragment();fragment.append(gallery(data[3]));
    if(data.slice(1).some(page=>page&&parsePageToken(page)))fragment.append(element('p',t('moreAvailable'),'wylon-muted'));
    if(data[1]) {const models=parseModels(data[1]);const details=element('details');details.append(element('summary',t('models')));const list=element('ul');for(const model of models.models)list.append(element('li',`${model.id} · ${model.type}`));details.append(list);fragment.append(details);}
    else fragment.append(element('p',t('connectionFailed'),'wylon-muted'));
    const tasks=data[2]?parseTasks(data[2]):[];
    const entries=element('section');entries.append(element('h3',t('tasks')));for(const task of tasks.slice(0,12))entries.append(taskRow(task.id,task.status,`${task.kind} · ${task.model} · ${formatTaskTimestamp(task.updated_at,locale)}`));
    if(!tasks.length)entries.append(element('p',t('empty')));fragment.append(entries);body.replaceChildren(fragment);
    return !!data[1];
  } catch {body.replaceChildren(element('p',t('failedLoad')));return false;}
  finally {if(refresh)refresh.disabled=false;}
}
function translateNode(node:Node):void {
  const id=node.comfyClass;if(!id)return;const def=native[locale]?.nodeDefs[id];if(!def)return;
  const titles=['Wylon H3 Video · 音视频（可切换模型）','Wylon Ref2VA Video · 全模态参考','Wylon Ref2VA Video · 参考音视频（可切换模型）','Wylon Resume Image Task','Wylon Resume Video Task'];
  for(const catalog of Object.values(native)){const title=catalog?.nodeDefs[id]?.display_name;if(title)titles.push(title);}
  if(!node.title||titles.includes(node.title))node.title=def.display_name;
  for(const widget of node.widgets??[]){const text=def.inputs[widget.name];if(text){widget.label=text.name;widget.tooltip=text.tooltip;widget.options.tooltip=text.tooltip;if(widget.inputEl){widget.inputEl.placeholder=text.name;widget.inputEl.setAttribute('aria-label',text.name);widget.inputEl.title=text.tooltip;}}}
  for(const input of node.inputs??[]){const text=def.inputs[input.name.replaceAll('.','_')];if(text){input.label=text.name;input.localized_name=text.name;input.tooltip=text.tooltip;}}
  node.outputs?.forEach((output,index)=>{const text=def.outputs[String(index)];if(text){output.label=text.name;output.localized_name=text.name;output.tooltip=text.tooltip;}});
  const configure=node.widgets?.find(w=>w.name==='wylon_configuration');if(configure)configure.label=t('configureNode');
  node.setDirtyCanvas?.(true,true);
}
function bindNodeText(node:Node):void {
  if(!node.comfyClass?.startsWith('Wylon'))return;
  nodes.add(new WeakRef(node));translateNode(node);
  const original=node.onConnectionsChange;
  node.onConnectionsChange=function(...args:unknown[]){const result=original?.apply(this,args);queueMicrotask(()=>translateNode(node));return result;};
}
async function changeLocale(setting:unknown):Promise<void> {
  const revision=++localeRevision;
  const next=languageFor(setting,navigator.language);if(next===locale&&Object.keys(strings).length)return;
  const response=await fetch(new URL(`./locales/${next}.json`,import.meta.url));const nextStrings:Strings=await response.json();if(revision!==localeRevision)return;
  const previous=strings;strings=nextStrings;locale=next;
  // Relabel existing text nodes in place: the password input and its value never move.
  if(dialog){const text=document.createTreeWalker(dialog,4);while(text.nextNode()){const node=text.currentNode;for(const [key,value] of Object.entries(previous)){if(typeof value==='string'&&node.nodeValue===value){node.nodeValue=t(key);break;}}}const input=dialog.querySelector<HTMLInputElement>('input[type=password]');if(input)input.placeholder=t('apiKeyPlaceholder');renderLive();if(dialog.open)void refreshMetadata();}
  for(const ref of nodes){const node=ref.deref();if(node)translateNode(node);else nodes.delete(ref);}
}
function bindConfiguration(node:Node):void {
  if(!node.comfyClass?.startsWith('Wylon')||node.comfyClass==='WylonReferenceVideoURL')return;
  const widget=node.addWidget?.('button','wylon_configuration',null,()=>{void showDialog();},{serialize:false}) as Widget|undefined;if(widget){widget.label=t('configureNode');widget.serialize=false;}
}
function guardGraphLoads():void {
  // The host isolates extension-hook errors; preflight its public entry point
  // before it cleans the canvas or registers subgraphs.
  const original=app.loadGraphData;
  app.loadGraphData=function(...args:unknown[]) {
    try {migrateWorkflow(args[0]);}
    catch(error) {
      const notice=element('dialog',undefined,'wylon-panel');notice.setAttribute('role','alertdialog');
      const heading=element('h2',t('workflowRejected'));const message=element('p',error instanceof Error?error.message:String(error));
      notice.append(heading,message,button(t('close'),()=>{notice.close();notice.remove();}));document.body.append(notice);notice.showModal();
      return Promise.reject(error);
    }
    return original.apply(this,args);
  };
}
function bindImageNode(node:Node):void {
  if(node.comfyClass!=='WylonGenerateImage')return;
  const model=node.widgets?.find(w=>w.name==='model');const size=node.widgets?.find(w=>w.name==='size');if(!model||!size)return;
  const update=()=>{applyImageSize(size,capabilities,String(model.value));node.setDirtyCanvas?.(true,true);};
  const original=model.callback;
  model.callback=function(...args:unknown[]){const result=original?.apply(this,args);update();return result;};update();
}
app.registerExtension({
  name:'Wylon.Controls',
  commands:[{id:'Wylon.ShowTasks',label:'Wylon tasks and configuration',function:()=>{void showDialog();}}],
  menuCommands:[{path:['Wylon'],commands:['Wylon.ShowTasks']}],
  async init(){
    guardGraphLoads();
    localeSetting=app.extensionManager?.setting?.get('Comfy.Locale') ?? app.ui?.settings?.getSettingValue('Comfy.Locale');
    const [i18n,capResponse]=await Promise.all([api.fetchApi('/i18n'),fetch(new URL('./model-capabilities.json',import.meta.url))]);
    native=await i18n.json();capabilities=await capResponse.json();
    await changeLocale(localeSetting);
    app.ui?.settings?.addEventListener('Comfy.Locale.change',(event:CustomEvent<{value?:unknown}>)=>{localeSetting=event.detail.value;void changeLocale(localeSetting);});
    globalThis.addEventListener?.('languagechange',()=>{void changeLocale(localeSetting);});
    const sheet=element('link');sheet.rel='stylesheet';sheet.href=new URL('./wylon.css',import.meta.url).href;document.head.append(sheet);
  },
  setup(){
    api.addEventListener('wylon.status',(event:CustomEvent<unknown>)=>{const status=parseStatus(event.detail);if(!status)return;live.delete(status.node_id);live.set(status.node_id,status);while(live.size>100)live.delete(live.keys().next().value!);renderLive();if(status.status==='downloaded'&&dialog?.open)void refreshMetadata();});
  },
  nodeCreated(node:Node){bindImageNode(node);bindConfiguration(node);bindNodeText(node);},
  loadedGraphNode(node:Node){
    translateNode(node);
    // Workflows restore widgets after nodeCreated; preserve valid model-specific values.
    if(node.comfyClass==='WylonGenerateImage'){const model=node.widgets?.find(w=>w.name==='model');const size=node.widgets?.find(w=>w.name==='size');if(model&&size)applyImageSize(size,capabilities,String(model.value));}
  }
});
