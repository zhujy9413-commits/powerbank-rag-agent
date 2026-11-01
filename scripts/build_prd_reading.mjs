/** Build offline PRD reading pages from the maintained Markdown sources. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, '产品需求文档');
const assets = path.join(root, 'docs/assets');
let marked;
try { ({ marked } = await import('marked')); }
catch (error) {
  if (!process.env.PRD_NODE_MODULES) throw new Error('Install marked or set PRD_NODE_MODULES to its node_modules directory.', { cause: error });
  ({ marked } = await import(pathToFileURL(path.join(process.env.PRD_NODE_MODULES, 'marked/lib/marked.esm.js')).href));
}
fs.mkdirSync(out, { recursive: true });
fs.mkdirSync(assets, { recursive: true });
const escape = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const hash = value => crypto.createHash('sha256').update(value).digest('hex');

function lines(x, y, values, className = '') {
  return `<text x="${x}" y="${y - (values.length - 1) * 12}" text-anchor="middle" class="${className}">${values.map((v, i) => `<tspan x="${x}" dy="${i ? 24 : 0}">${escape(v)}</tspan>`).join('')}</text>`;
}
function box(x, y, width, height, text, tone = '') {
  return `<g class="node ${tone}"><rect x="${x}" y="${y}" width="${width}" height="${height}" rx="8"/>${lines(x + width / 2, y + height / 2 + 5, text)}</g>`;
}
function diamond(x, y, width, height, text) {
  return `<g class="node decision"><path d="M${x + width / 2},${y} L${x + width},${y + height / 2} L${x + width / 2},${y + height} L${x},${y + height / 2} Z"/>${lines(x + width / 2, y + height / 2 + 5, text)}</g>`;
}
const edge = (d, dashed = false) => `<path class="edge${dashed ? ' return' : ''}" d="${d}" marker-end="url(#arrow)"/>`;
function label(x, y, text) {
  if (text.length === 1) return lines(x, y, text, 'edge-label');
  return `<g><rect x="${x - 67}" y="${y - 31}" width="134" height="${text.length * 24 + 10}" fill="#fff"/>${lines(x, y, text, 'edge-label')}</g>`;
}
function diagram(name, width, height, title, description, content) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="title description"><title id="title">${escape(title)}</title><desc id="description">${escape(description)}</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#59766c"/></marker></defs><style>text{font:17px -apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;fill:#183b32}.edge{fill:none;stroke:#59766c;stroke-width:1.7}.return{stroke-dasharray:6 5}.node rect,.node path{fill:#f3f8f5;stroke:#9bb6aa;stroke-width:1.4}.node.emphasis rect{fill:#e4f1e9;stroke:#558b70}.node.decision path{fill:#fff7e6;stroke:#bea15f}.edge-label{font-size:15px;fill:#54685e}</style><rect width="100%" height="100%" fill="#fff"/>${content}</svg>`;
  fs.writeFileSync(path.join(assets, name), svg + '\n');
}

diagram('prd-ai-work-flow.svg', 680, 840, 'AI Work 报告评审业务流程',
  '上传报告后核对解析，确认依据、版本与清单。任务级前提明确后逐项核对，再人工复核和导出；前提缺失返回确认，补材料或更换依据产生新修订。',
  edge('M340 104 V142') + edge('M340 206 V244') + edge('M340 308 V350') +
  edge('M340 450 V506') + edge('M340 570 V616') + edge('M340 680 V726') +
  edge('M200 400 H65 V276 H160', true) + edge('M520 648 H610 V174 H520', true) +
  box(160, 40, 360, 64, ['上传本次报告', '保存报告身份与输入修订']) +
  box(160, 142, 360, 64, ['核对解析与原文', '修正明确错误，保留未知区域']) +
  box(160, 244, 360, 64, ['确认采用依据与版本', '确认检查清单和范围限制']) +
  diamond(200, 350, 280, 100, ['任务级启动前提', '是否明确？']) +
  box(160, 506, 360, 64, ['按检查单元找证与核对', '记录结果、未检查及失败原因'], 'emphasis') +
  box(160, 616, 360, 64, ['查看证据并人工复核', '记录处置理由和未决项']) +
  box(160, 726, 360, 64, ['导出评审清单', '保留范围、证据和完整状态']) +
  label(92, 354, ['否', '补充或更正']) + label(366, 480, ['是']) +
  label(609, 394, ['补材料或改依据', '新修订重新确认']));

diagram('prd-assistant-flow.svg', 720, 1060, '内部智能客服 搜索与单轮问答流程',
  '提交问题与显式范围，缺少影响适用性的条件时回填并提交完整新请求。条件明确后授权检索；搜索交付资料，回答按证据交付完整、部分或缺证状态，用户查看原文和反馈。',
  edge('M350 104 V144') + edge('M350 208 V252') + edge('M350 352 V408') +
  edge('M350 472 V522') + edge('M210 302 H62 V72 H170', true) +
  edge('M210 570 H145 V670') + edge('M350 618 V640 H500 V670') +
  edge('M500 750 V798') + edge('M500 862 V922 H350 V958') +
  edge('M145 750 V990 H170') +
  box(170, 40, 360, 64, ['选择搜索或回答模式', '提交问题与显式范围']) +
  box(170, 144, 360, 64, ['核对本次意图与范围', '以及必要的对象、版本和条件']) +
  diamond(210, 252, 280, 100, ['本次任务必要范围', '是否明确？']) +
  box(170, 408, 360, 64, ['按当前权限与版本检索', '整理来源、条件和证据'], 'emphasis') +
  diamond(210, 522, 280, 96, ['本次选择', '哪种模式？']) +
  box(20, 670, 250, 80, ['交付资料列表与命中位置', '支持查看原文']) +
  box(350, 670, 300, 80, ['生成可被证据支持的内容', '或说明缺少的依据']) +
  box(350, 798, 300, 64, ['校验引用与支持关系', '交付完成、部分或缺证状态']) +
  box(170, 958, 360, 64, ['用户查证并提供简单反馈', '新问题提交新的完整请求']) +
  label(90, 194, ['否：待补充', '回填完整条件', '提交新请求']) +
  label(376, 382, ['是']) + label(180, 632, ['搜索']) + label(535, 648, ['回答']));

const docs = [
  { source: 'docs/ai-work/PRD.md', output: 'ai-work-prd.html', short: 'AI Work', summary: '从单份报告到带依据、范围与人工处置的评审清单。' },
  { source: 'docs/internal-assistant/PRD.md', output: 'internal-assistant-prd.html', short: '内部智能客服', summary: '从内部问题到适用资料、带引用回答与可核验原文。' },
];
const mapped = new Map(docs.map(d => [path.join(root, d.source), d.output]));
const css = `
:root{color-scheme:light;--ink:#18352f;--muted:#60726a;--line:#dce5de;--paper:#fff;--ground:#f4f6f2;--green:#166446}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;color:var(--ink);background:var(--ground);font:16px/1.85 -apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif}a{color:var(--green);text-underline-offset:4px;overflow-wrap:anywhere}a:hover{color:#0a3d2a}.frame{max-width:1420px;margin:auto;padding:0 36px}.masthead{background:#173f33;color:#f5faf3;padding:30px 0 28px}.eyebrow{font-size:12px;letter-spacing:2px;color:#c6ddc9}.masthead h1{font-size:29px;line-height:1.45;margin:10px 0 8px;font-weight:650}.masthead p{color:#d4e4d5;font-size:14px;margin:0}.topnav{display:flex;gap:20px;flex-wrap:wrap;padding:14px 0;font-size:14px;align-items:center}.topnav a{text-decoration:none}.topnav .active{font-weight:650}.topnav button{margin-left:auto;font:inherit;color:var(--green);border:1px solid #bbcfc0;background:var(--paper);padding:5px 14px;border-radius:5px}.layout{display:grid;grid-template-columns:244px minmax(0,1fr);gap:34px;align-items:start;margin:14px auto 44px}.toc{position:sticky;top:24px;max-height:calc(100vh - 48px);overflow:auto;padding:16px 4px;font-size:13px}.toc h2{font-size:13px;margin:0 0 12px;color:var(--muted)}.toc a{display:block;line-height:1.65;padding:7px 10px;text-decoration:none;border-left:2px solid var(--line)}.toc a:hover{border-left-color:var(--green);background:#eaf1e9}.document{background:var(--paper);min-width:0;padding:32px 40px 40px;border:1px solid var(--line);border-radius:8px}.document p{margin:12px 0 16px}.document h2{font-size:23px;line-height:1.5;padding-top:28px;margin:30px 0 18px;border-top:1px solid var(--line);font-weight:650}.document h3{font-size:18px;line-height:1.55;margin:25px 0 13px;font-weight:620}.document ul,.document ol{padding-left:24px}.document li{margin:8px 0}.table-wrap{overflow-x:auto;margin:20px 0 24px}table{width:100%;min-width:0;border-collapse:collapse;font-size:14px;line-height:1.8}.table-three{min-width:520px}.table-wide{min-width:640px}th,td{text-align:left;vertical-align:top;padding:12px 13px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}th{background:#eef4ed;color:#244b35;font-weight:650}tbody tr:nth-child(even){background:#fbfcfa}td:first-child,th:first-child{min-width:102px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6f1;border:1px solid #dce7d9;border-radius:6px;padding:20px;font:13px/1.95 ui-monospace,SFMono-Regular,Menlo,Consolas,'PingFang SC',monospace;max-width:100%}code{font-size:.9em}blockquote{border-left:3px solid #a2b99d;margin:20px 0;padding:1px 18px;color:#52634f}.diagram{margin:24px 0;overflow-x:auto;border:1px solid var(--line);border-radius:6px;padding:20px 12px;background:#fff}.diagram svg{width:100%;height:auto;min-width:560px;max-width:720px;display:block;margin:auto}.diagram figcaption{font-size:13px;color:var(--muted);padding:14px 4px 0}.source{border-top:1px solid var(--line);padding-top:22px;margin-top:34px;color:var(--muted);font-size:13px}.intro-copy{max-width:800px;font-size:17px}.overview{padding-top:30px;padding-bottom:50px}.module-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin:24px 0}.module{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:26px 28px}.module h2{font-size:23px;margin:7px 0 12px}.module .order{font-size:12px;letter-spacing:2px;color:var(--muted)}.module a{display:inline-block;margin-top:10px;font-weight:600}.reading-order{margin-top:32px;border-top:1px solid var(--line);padding-top:24px;color:#4f6658}.reading-order h2{font-size:18px}.status-note{font-size:13px;color:var(--muted)}
@media(max-width:1000px){.frame{padding:0 24px}.layout{grid-template-columns:200px minmax(0,1fr);gap:20px}.document{padding:24px}.masthead h1{font-size:26px}}
@media(max-width:760px){.frame{padding:0 16px}.masthead{padding:26px 0}.masthead h1{font-size:24px}.layout{display:block;margin-top:0}.toc{position:static;max-height:none;margin-bottom:18px;padding:12px 0}.toc nav{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}.toc a{font-size:12px;padding:6px}.document{padding:20px 16px;border-radius:5px}.document h2{font-size:21px}.document h3{font-size:18px}.topnav{gap:8px 16px}.topnav button{margin-left:0}.module-grid{grid-template-columns:1fr}.module{padding:22px}.diagram{padding:12px 8px}table{font-size:13px}.table-wrap.is-wide::after{content:"表格可横向滚动查看";display:block;font-size:12px;color:var(--muted);padding-top:8px}.diagram figcaption::after{content:"（流程图可横向滚动查看）";display:block;margin-top:5px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{@page{size:A4;margin:16mm 14mm}body{background:#fff;font-size:10.5pt;line-height:1.65}.frame{max-width:none;padding:0}.masthead{background:#fff;color:#18352f;padding:0 0 10mm;border-bottom:1px solid #ccc}.masthead .eyebrow,.masthead p{color:#52634f}.masthead h1{font-size:23pt}.topnav,.toc,.status-note{display:none}.layout{display:block;margin:0}.document{padding:0;border:0}.document h2{font-size:15pt;break-after:avoid}.document h3{font-size:12pt;break-after:avoid}.table-wrap{overflow:visible}table,.table-three,.table-wide{min-width:0;font-size:9pt;line-height:1.55}th,td{padding:6px 7px}tr{break-inside:avoid}thead{display:table-header-group}pre{font-size:9pt;white-space:pre-wrap;break-inside:avoid}.diagram{break-inside:avoid;overflow:visible;padding:10px}.diagram svg{min-width:0;max-width:440px;max-height:220mm}.module-grid{grid-template-columns:1fr}.module{break-inside:avoid}a{color:inherit;text-decoration:none}}
`;

function linkFor(doc, target) {
  if (/^(https?:|mailto:|#)/.test(target)) return target;
  const [name, fragment] = target.split('#');
  const absolute = path.resolve(root, path.dirname(doc.source), name);
  return (mapped.get(absolute) || path.relative(out, absolute).split(path.sep).join('/')) + (fragment ? '#' + fragment : '');
}
function chrome(title, version, current, content) {
  const links = docs.map(d => `<a href="${d.output}"${current === d.output ? ' class="active" aria-current="page"' : ''}>${escape(d.short)} PRD</a>`).join('');
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(title)}</title><style>${css}</style></head><body><header class="masthead"><div class="frame"><div class="eyebrow">充电宝研发评审与知识助手</div><h1>${escape(title)}</h1><p>${escape(version)}</p></div></header><div class="frame"><nav class="topnav" aria-label="产品文档"><a href="index.html">文档首页</a>${links}<button type="button" onclick="window.print()">打印文档</button></nav></div>${content}</body></html>\n`;
}

for (const doc of docs) {
  const source = fs.readFileSync(path.join(root, doc.source), 'utf8');
  const title = source.match(/^# (.+)$/m)[1];
  const version = source.match(/^版本 (.+)$/m)[1];
  const headings = [];
  let section = 0, subsection = 0;
  const body = source.replace(/^# .+\n\n版本 .+\n\n/, '');
  const renderer = new marked.Renderer();
  renderer.heading = function (token) {
    if (token.depth === 2) {
      const id = `section-${++section}`; subsection = 0;
      headings.push({ id, text: token.text });
      return `<h2 id="${id}">${this.parser.parseInline(token.tokens)}</h2>`;
    }
    const id = `section-${section}-${++subsection}`;
    return `<h${token.depth} id="${id}">${this.parser.parseInline(token.tokens)}</h${token.depth}>`;
  };
  renderer.link = function (token) {
    return `<a href="${escape(linkFor(doc, token.href))}">${this.parser.parseInline(token.tokens)}</a>`;
  };
  renderer.image = function (token) {
    const file = path.resolve(root, path.dirname(doc.source), token.href);
    if (!file.startsWith(assets + path.sep) || path.extname(file) !== '.svg') throw new Error('Unexpected PRD image: ' + token.href);
    const svg = fs.readFileSync(file, 'utf8').replaceAll('id="title"', 'id="flow-title"').replaceAll('id="description"', 'id="flow-description"').replace('aria-labelledby="title description"', 'aria-labelledby="flow-title flow-description"');
    return `<figure class="diagram">${svg}<figcaption>${escape(token.text)}</figcaption></figure>`;
  };
  let html = marked.parse(body, { gfm: true, renderer });
  html = html.replace(/<table>[\s\S]*?<\/table>/g, table => {
    const columns = (table.match(/<thead>[\s\S]*?<\/thead>/)?.[0].match(/<th(?:>|\s)/g) || []).length;
    const kind = columns >= 4 ? 'table-wide' : columns === 3 ? 'table-three' : '';
    return `<div class="table-wrap${kind ? ' is-wide' : ''}">${table.replace('<table>', `<table class="${kind}">`)}</div>`;
  });
  html = html.replace(/<p>(<figure[\s\S]*?<\/figure>)<\/p>/g, '$1');
  const toc = `<aside class="toc" aria-label="章节目录"><h2>章节目录</h2><nav>${headings.map(h => `<a href="#${h.id}">${escape(h.text)}</a>`).join('')}</nav></aside>`;
  const content = `<div class="frame layout">${toc}<main class="document" data-source="${doc.source}" data-source-sha256="${hash(source)}">${html}<footer class="source">维护源：<a href="${escape(path.relative(out, path.join(root, doc.source)))}">${escape(doc.source)}</a>。本地阅读版与维护源正文对应；线上同步版本见项目同步记录。</footer></main></div>`;
  fs.writeFileSync(path.join(out, doc.output), chrome(title, version, doc.output, content));
  console.log(`${doc.output}: ${headings.length} sections, source ${hash(source).slice(0, 12)}`);
}

const content = `<main class="frame overview"><p class="intro-copy">两个内部业务模块共用受控知识底座。AI Work围绕报告组织核对与复核，内部智能客服围绕问题查找和解释资料。</p><div class="module-grid">${docs.map((d, i) => `<section class="module"><span class="order">0${i + 1} / 产品需求文档</span><h2>${escape(d.short)}</h2><p>${escape(d.summary)}</p><a href="${d.output}">阅读完整PRD →</a></section>`).join('')}</div><section class="reading-order"><h2>建议阅读顺序</h2><p>先看业务目标与范围取舍，再沿业务流程图查看页面行为，最后核对异常、验收与当前能力边界。知识库与RAG的设计分别位于两份PRD第七节。</p></section><p class="status-note">v0.1.3 阅读版 · 2026-11-02。需求范围沿用v0.1.1确认基线，本次补清技术适配、试用进入条件与执行口径；原型仍为v0.5.0，真实试用尚未启动；飞书原文档与GitHub现行PRD均为v0.1.3；历史材料保留其编制时版本。</p></main>`;
fs.writeFileSync(path.join(out, 'index.html'), chrome('产品需求文档', 'v0.1.3 · 2026-11-02 · 试用进入条件与执行口径澄清', '', content));
