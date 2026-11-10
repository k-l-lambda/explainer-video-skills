#!/usr/bin/env node
// After the narration is recorded: set a scene's length to its audio and inline its captions, as
// literals, so both stay editable in Remotion Studio. Run from the Remotion project's root.
//
//   node <skills>/scripts/sync-scene.mjs src/Video.tsx "S2" public/s2.wav \
//     [--captions public/s2.captions.json] [--captions-tag Captions] [--fps 30] [--tail 6]
//
// Finds the <Series.Sequence>, <TransitionSeries.Sequence> or <Sequence> whose `name` is the given
// literal, sets durationInFrames = ceil(audio seconds × fps) + tail, and if --captions is given,
// writes the Caption[] JSON into the `captions` prop of its direct child <Captions> (the tag set by
// --captions-tag). Uses @remotion/codemods from the project (a draft API; keep its version aligned).
import {readFileSync, writeFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {join} from 'node:path';

const args = process.argv.slice(2);
const flag = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i < 0 ? fallback : args.splice(i, 2)[1];
};
const capsFile = flag('captions', null);
const capsTag = flag('captions-tag', 'Captions');
const fps = Number(flag('fps', '30'));
const tail = Number(flag('tail', '6'));
const [file, seqName, audio] = args;
if (!file || !seqName || !audio) {
  console.error('usage: sync-scene.mjs <file> <sequence name> <audio> [--captions json] [--captions-tag Captions] [--fps 30] [--tail 6]');
  process.exit(2);
}

const require = createRequire(join(process.cwd(), 'package.json'));
const {getNodes, getNodeProps, updateNodeProps, applyCodemodChanges} = require('@remotion/codemods');

const seconds = Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio]).toString());
const frames = Math.ceil(seconds * fps) + tail;
let project = {rootDir: process.cwd(), files: {[file]: readFileSync(file, 'utf8')}};
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const nodes = getNodes({project, filePath: file});
const seq = nodes.find((n) => /^(Series\.Sequence|TransitionSeries\.Sequence|Sequence)$/.test(n.tagName)
  && getNodeProps({project, node: n, keys: ['name']}).props.name.codeValue === seqName);
if (!seq) throw new Error(`no sequence with name="${seqName}" in ${file}`);
const capsNode = capsFile ? nodes.find((n) => n.tagName === capsTag && same(n.parentNodePath, seq.nodePath)) : null;
if (capsFile && !capsNode) throw new Error(`no <${capsTag}> directly inside "${seqName}"`);

let result = updateNodeProps({project, node: seq, props: {durationInFrames: frames}});
project = applyCodemodChanges(project, result.changes);
if (capsNode) {
  const moved = result.nodePathRemappings?.find((m) => m.filePath === file && same(m.oldNodePath, capsNode.nodePath));
  const node = moved ? {filePath: file, nodePath: moved.newNodePath} : capsNode;
  const captions = JSON.parse(readFileSync(capsFile, 'utf8'));
  result = updateNodeProps({project, node, props: {captions}});
  project = applyCodemodChanges(project, result.changes);
}
writeFileSync(file, project.files[file]);
console.log(JSON.stringify({file, sequence: seqName, seconds, fps, durationInFrames: frames,
  captions: capsNode ? JSON.parse(readFileSync(capsFile, 'utf8')).length : null}));
