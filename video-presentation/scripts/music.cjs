// Trilha instrumental original, sintetizada por código (sem samples nem direitos de terceiros).
// Pad em Lá menor, arpejo, kick e hi-hat entrando progressivamente. Saída: public/audio/trilha.wav
const fs = require('node:fs');
const path = require('node:path');

const SR = 44100, DUR = 90, BPM = 100;
const N = SR * DUR, beat = 60 / BPM, bar = beat * 4;
const L = new Float32Array(N), R = new Float32Array(N);
const midi = m => 440 * Math.pow(2, (m - 69) / 12);
// Am - F - C - G (2 compassos cada)
const chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]];
const env = (t, a, d) => (t < 0 ? 0 : t < a ? t / a : Math.exp(-(t - a) / d));
let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647) * 2 - 1;

// Intensidade ao longo do vídeo (constrói até ~65s, respira no fim)
const level = t => Math.min(1, 0.35 + t / 60) * (t > 84 ? Math.max(0, (90 - t) / 6) : 1);

for (let i = 0; i < N; i++) {
  const t = i / SR, lv = level(t);
  const ci = Math.floor(t / (bar * 2)) % 4, chord = chords[ci];
  let pad = 0;
  for (const m of chord) for (const det of [-0.08, 0.08]) {
    const f = midi(m) * Math.pow(2, det / 12);
    pad += Math.sin(2 * Math.PI * f * t) * 0.5 + Math.sin(4 * Math.PI * f * t) * 0.12;
  }
  pad *= 0.045 * (0.8 + 0.2 * Math.sin(2 * Math.PI * t / 8));
  // baixo
  const bassF = midi(chord[0] - 12);
  const bt = (t % beat);
  const bass = t > 8 ? Math.sin(2 * Math.PI * bassF * t) * 0.11 * env(bt, 0.01, 0.35) : 0;
  // arpejo em semicolcheias
  const step = beat / 4, si = Math.floor(t / step), st = t - si * step;
  const arpNote = chord[[0, 1, 2, 1][si % 4]] + 12 + (si % 8 >= 4 ? 12 : 0);
  const arp = t > 4 ? Math.sin(2 * Math.PI * midi(arpNote) * t) * 0.05 * env(st, 0.004, 0.09) * Math.min(1, (t - 4) / 6) : 0;
  // kick
  const kick = t > 16 ? Math.sin(2 * Math.PI * (45 + 90 * Math.exp(-bt * 30)) * bt) * 0.35 * env(bt, 0.002, 0.12) : 0;
  // hi-hat no contratempo
  const ht = (t + beat / 2) % beat;
  const hat = t > 24 ? rnd() * 0.035 * env(ht, 0.001, 0.025) : 0;
  const s = (pad + bass + kick) * lv + (arp + hat) * lv;
  const pan = Math.sin(2 * Math.PI * t / 6) * 0.3;
  L[i] = s + arp * pan * lv; R[i] = s - arp * pan * lv;
}
// reverb simples (eco difuso) e normalização
for (const ch of [L, R]) for (const [d, g] of [[0.113, 0.25], [0.197, 0.18], [0.271, 0.12]]) {
  const k = Math.floor(d * SR); for (let i = N - 1; i >= k; i--) ch[i] += ch[i - k] * g;
}
let peak = 0; for (let i = 0; i < N; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
const buf = Buffer.alloc(44 + N * 4);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVEfmt ', 8);
buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24);
buf.writeUInt32LE(SR * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) {
  buf.writeInt16LE(Math.round(L[i] / peak * 0.85 * 32767), 44 + i * 4);
  buf.writeInt16LE(Math.round(R[i] / peak * 0.85 * 32767), 46 + i * 4);
}
const out = path.resolve(__dirname, '..', 'public', 'audio', 'trilha.wav');
fs.mkdirSync(path.dirname(out), {recursive: true}); fs.writeFileSync(out, buf);
console.log('trilha gerada:', out);
