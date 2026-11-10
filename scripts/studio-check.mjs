#!/usr/bin/env node
// Report how Remotion Studio's static analysis reads a file: for every sequence and interactive
// element, whether each prop is static (editable), keyframed (editable keyframes) or computed
// (greyed out). Uses @remotion/codemods from the project; run from the Remotion project's root.
//
//   node <skills>/scripts/studio-check.mjs src/Video.tsx [--keys name,durationInFrames,from,style.opacity,...] [--fps 30]
//
// Exit code 1 if any prop listed by --strict reads computed, e.g. --strict durationInFrames,style.opacity.
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {join} from 'node:path';

const args = process.argv.slice(2);
const flag = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i < 0 ? fallback : args.splice(i, 2)[1];
};
const keys = flag('keys', 'name,from,durationInFrames,captions,style.opacity,style.translate,style.scale,style.rotate,style.transformOrigin').split(',');
const strict = new Set((flag('strict', '') || '').split(',').filter(Boolean));
const fps = Number(flag('fps', '30'));
const [file] = args;
if (!file) {
  console.error('usage: studio-check.mjs <file> [--keys a,b] [--strict a,b] [--fps 30]');
  process.exit(2);
}
const require = createRequire(join(process.cwd(), 'package.json'));
const {getNodes, getNodeProps} = require('@remotion/codemods');
const project = {rootDir: process.cwd(), files: {[file]: readFileSync(file, 'utf8')}};
const videoConfig = {width: 1920, height: 1080, fps, durationInFrames: 1};
let failed = 0;
for (const node of getNodes({project, filePath: file})) {
  if (!/Sequence|^Interactive\.|^[A-Z]/.test(node.tagName) || /^(AbsoluteFill|Composition|Series|TransitionSeries)$/.test(node.tagName)) continue;
  const {props} = getNodeProps({project, node, keys, videoConfig});
  const shown = [];
  for (const [k, v] of Object.entries(props)) {
    if (v.status === 'static' && v.codeValue === undefined) continue; // not written
    if (v.status === 'computed' && strict.has(k)) failed++;
    shown.push(v.status === 'keyframed' ? `${k}=keyframed(${(v.keyframes ?? []).length})`
      : v.status === 'static' ? `${k}=static` : `${k}=COMPUTED`);
  }
  if (shown.length) console.log(`${file}:${node.location?.line ?? '?'} <${node.tagName}> ${shown.join('  ')}`);
}
if (failed) {
  console.error(`${failed} strict prop(s) read as computed: Studio cannot edit them`);
  process.exit(1);
}
