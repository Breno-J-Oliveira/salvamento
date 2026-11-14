import {staticFile} from 'remotion';

// Identidade do Purple Talent (static/style.css, camada "presentation").
export const C = {
  bg: '#0e0c17',
  surface: '#161326',
  deep: '#110e1e',
  border: '#2d2748',
  text: '#ece8fa',
  muted: '#b3a8ce',
  purple: '#a855f7',
  lilac: '#c28aff',
  blue: '#71b6ff',
  red: '#ff788d',
  teal: '#42d9c5',
};

export const FONT = {
  display: 'Jakarta, Inter, sans-serif',
  body: 'Inter, sans-serif',
  mono: 'Mono, monospace',
};

export const fontFaces = `
@font-face{font-family:Jakarta;src:url(${staticFile('assets/plus-jakarta-sans-latin-wght-normal.woff2')}) format('woff2');font-weight:200 800}
@font-face{font-family:Inter;src:url(${staticFile('assets/inter-latin-wght-normal.woff2')}) format('woff2');font-weight:100 900}
@font-face{font-family:Mono;src:url(${staticFile('assets/jetbrains-mono-latin-wght-normal.woff2')}) format('woff2');font-weight:100 800}
`;

export const FPS = 30;
export const sec = (s: number) => Math.round(s * FPS);
