import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, FONT} from '../theme';

export const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const inOut = Easing.bezier(0.65, 0, 0.35, 1);

/** 0→1 ao entrar e 1→0 ao sair, para a duração atual da Sequence. */
export const useFade = (inF = 12, outF = 12) => {
  const f = useCurrentFrame();
  const {durationInFrames: d} = useVideoConfig();
  return interpolate(f, [0, inF, d - outF, d], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
};

export const Background: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{background: C.bg, overflow: 'hidden'}}>
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${C.border}55 1px, transparent 1px), linear-gradient(90deg, ${C.border}55 1px, transparent 1px)`,
          backgroundSize: '80px 80px',
          backgroundPosition: `0 ${-f * 0.3}px`,
          maskImage: 'radial-gradient(ellipse at 70% 40%, black 10%, transparent 70%)',
          WebkitMaskImage: 'radial-gradient(ellipse at 70% 40%, black 10%, transparent 70%)',
        }}
      />
      <div style={{position: 'absolute', width: 1100, height: 1100, right: -300, top: -420, borderRadius: '50%',
        background: `radial-gradient(circle, ${C.purple}26, transparent 65%)`}} />
    </AbsoluteFill>
  );
};

/** Texto que entra deslizando, com atraso em frames. */
export const Reveal: React.FC<{delay?: number; children: React.ReactNode; y?: number; style?: React.CSSProperties}> = ({delay = 0, children, y = 26, style}) => {
  const f = useCurrentFrame();
  const p = interpolate(f - delay, [0, 18], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  return <div style={{opacity: p, transform: `translateY(${(1 - p) * y}px)`, ...style}}>{children}</div>;
};

export const Kicker: React.FC<{children: React.ReactNode; color?: string}> = ({children, color = C.lilac}) => (
  <div style={{fontFamily: FONT.mono, fontSize: 22, letterSpacing: 3, textTransform: 'uppercase', color, display: 'flex', alignItems: 'center', gap: 14}}>
    <span style={{width: 34, height: 2, background: color}} />{children}
  </div>
);

export const Title: React.FC<{children: React.ReactNode; size?: number}> = ({children, size = 64}) => (
  <div style={{fontFamily: FONT.display, fontWeight: 800, fontSize: size, lineHeight: 1.08, letterSpacing: '-0.035em', color: C.text}}>{children}</div>
);

export const Body: React.FC<{children: React.ReactNode}> = ({children}) => (
  <div style={{fontFamily: FONT.body, fontSize: 28, lineHeight: 1.45, color: C.muted}}>{children}</div>
);

export type Cam = {s: number; x: number; y: number}; // escala e ponto focal (0–1) da imagem

/** Clique simulado: posição em pixels da captura (1920 de largura); `menu` abre um submenu e clica no item `pick`. */
export type Click = {x: number; y: number; menu?: string[]; pick?: number};

const Arrow: React.FC<{press: number}> = ({press}) => (
  <svg width={30} height={36} viewBox="0 0 30 36" style={{transform: `scale(${1 - 0.18 * press})`, transformOrigin: '2px 2px', filter: 'drop-shadow(0 3px 6px #000a)'}}>
    <path d="M2 2 L2 28 L9 21 L14 33 L19 31 L14 19.5 L24 19.5 Z" fill="#fff" stroke="#0e0c17" strokeWidth={2} strokeLinejoin="round" />
  </svg>
);

const Ripple: React.FC<{x: number; y: number; t: number}> = ({x, y, t}) => {
  if (t < 0 || t > 1) return null;
  return <div style={{position: 'absolute', left: x - 34 * t - 8, top: y - 34 * t - 8, width: 16 + 68 * t, height: 16 + 68 * t, borderRadius: '50%',
    border: `3px solid ${C.lilac}`, background: `${C.purple}33`, opacity: 1 - t, pointerEvents: 'none'}} />;
};

/**
 * Captura real da plataforma dentro de uma janela de navegador, com câmera animada.
 * `cams` são keyframes distribuídos em `at` (frames relativos à Sequence).
 */
export const Screen: React.FC<{
  src: string; ar: number; cams: Cam[]; at: number[]; w?: number; h?: number; url?: string;
  highlight?: {x: number; y: number; w: number; h: number; from: number}; // em fração da viewport
  click?: Click; dur?: number;
}> = ({src, ar, cams, at, w = 1240, h = 698, url = '127.0.0.1:5000', highlight, click, dur = 0}) => {
  const f = useCurrentFrame();
  const pick = (k: keyof Cam) => interpolate(f, at, cams.map((c) => c[k]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: inOut});
  const s = pick('s'), x = pick('x'), y = pick('y');
  const imgW = w * s, imgH = imgW / ar;
  // mantém o ponto focal no centro, sem mostrar bordas vazias
  let left = w / 2 - x * imgW, top = h / 2 - y * imgH;
  left = Math.min(0, Math.max(w - imgW, left));
  top = Math.min(0, Math.max(h - imgH, top));
  const hp = highlight ? interpolate(f - highlight.from, [0, 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease}) : 0;
  return (
    <div style={{width: w, borderRadius: 18, overflow: 'hidden', border: `1px solid ${C.border}`, background: C.deep,
      boxShadow: '0 40px 120px #00000080, 0 0 0 1px #ffffff08'}}>
      <div style={{height: 44, display: 'flex', alignItems: 'center', gap: 9, padding: '0 18px', background: '#151224', borderBottom: `1px solid ${C.border}`}}>
        {['#ff5f57', '#febc2e', '#28c840'].map((c) => <span key={c} style={{width: 12, height: 12, borderRadius: 6, background: c, opacity: 0.8}} />)}
        <div style={{marginLeft: 18, flex: 1, maxWidth: 520, height: 26, borderRadius: 8, background: C.bg, color: C.muted,
          fontFamily: FONT.mono, fontSize: 14, display: 'flex', alignItems: 'center', padding: '0 14px'}}>{url}</div>
      </div>
      <div style={{position: 'relative', width: w, height: h, overflow: 'hidden'}}>
        <Img src={staticFile(src)} style={{position: 'absolute', left, top, width: imgW, height: imgH}} />
        {highlight && hp > 0 && (
          <div style={{position: 'absolute', left: highlight.x * w, top: highlight.y * h, width: highlight.w * w, height: highlight.h * h,
            border: `3px solid ${C.lilac}`, borderRadius: 14, opacity: hp, transform: `scale(${1.08 - 0.08 * hp})`,
            boxShadow: `0 0 0 4000px #0e0c1766`}} />
        )}
        {click && <CursorLayer click={click} f={f} dur={dur} map={(px, py) => [left + (px / 1920) * imgW, top + (py / 1920) * ar * imgH]} />}
      </div>
    </div>
  );
};

/** Layout padrão de cena: texto à esquerda, captura à direita. */
export const Split: React.FC<{left: React.ReactNode; right: React.ReactNode}> = ({left, right}) => {
  const o = useFade(10, 10);
  return (
    <AbsoluteFill style={{opacity: o}}>
      <div style={{position: 'absolute', left: 90, top: 0, bottom: 0, width: 470, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 26}}>{left}</div>
      <div style={{position: 'absolute', right: 70, top: 0, bottom: 0, display: 'flex', alignItems: 'center'}}>{right}</div>
    </AbsoluteFill>
  );
};

export const Logo: React.FC<{size?: number}> = ({size = 96}) => (
  <div style={{fontFamily: FONT.display, fontWeight: 800, fontSize: size, letterSpacing: '-0.05em', color: C.text, whiteSpace: 'nowrap'}}>
    PURPLE <span style={{color: C.purple}}>TALENT</span>
  </div>
);

export const Steps: React.FC<{items: string[]; delay?: number; every?: number}> = ({items, delay = 0, every = 8}) => (
  <div style={{display: 'flex', flexDirection: 'column', gap: 14}}>
    {items.map((t, i) => (
      <Reveal key={t} delay={delay + i * every} y={14}>
        <div style={{display: 'flex', alignItems: 'center', gap: 14, fontFamily: FONT.body, fontSize: 24, color: C.text}}>
          <span style={{width: 30, height: 30, borderRadius: 8, border: `1px solid ${C.border}`, background: C.surface, color: C.lilac,
            display: 'grid', placeItems: 'center', fontFamily: FONT.mono, fontSize: 15}}>{i + 1}</span>{t}
        </div>
      </Reveal>
    ))}
  </div>
);

/** Cursor que entra, vai até o elemento clicável e clica; com `menu`, abre o submenu e clica no item. */
const CursorLayer: React.FC<{click: Click; f: number; dur: number; map: (x: number, y: number) => [number, number]}> = ({click, f, dur, map}) => {
  const [tx, ty] = map(click.x, click.y);
  const hasMenu = !!click.menu;
  const c1 = dur - (hasMenu ? 42 : 14); // primeiro clique
  const sx = tx + 260, sy = ty + 190;
  const mv = interpolate(f, [c1 - 40, c1 - 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: inOut});
  let cx = sx + (tx - sx) * mv, cy = sy + (ty - sy) * mv;
  const appear = interpolate(f, [c1 - 46, c1 - 36], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const press = (c: number) => interpolate(f, [c - 3, c, c + 4], [0, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  let p = press(c1);
  let menu: React.ReactNode = null, ripple2: React.ReactNode = null;
  if (hasMenu && f >= c1) {
    const items = click.menu!, pick = click.pick ?? 0;
    const mx = tx - 22, my = ty + 16, ih = 23;
    const c2 = dur - 12;
    const ix = mx + 48, iy = my + 10 + ih * pick + ih / 2;
    const m2 = interpolate(f, [c1 + 8, c2 - 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: inOut});
    cx = tx + (ix - tx) * m2; cy = ty + (iy - ty) * m2;
    p = Math.max(p, press(c2));
    const mo = interpolate(f, [c1, c1 + 6], [0, 1], {extrapolateRight: 'clamp'});
    menu = (
      <div style={{position: 'absolute', left: mx, top: my, opacity: mo, transform: `translateY(${(1 - mo) * -6}px)`, background: '#1b1730',
        border: `1px solid ${C.border}`, borderRadius: 9, padding: '6px 0', minWidth: 128, boxShadow: '0 16px 40px #000a'}}>
        {items.map((it, i) => {
          const hover = i === pick && m2 > 0.85;
          return <div key={it} style={{height: ih, display: 'flex', alignItems: 'center', padding: '0 12px', fontFamily: FONT.body, fontSize: 11.5,
            color: hover ? C.text : C.muted, background: hover ? `${C.purple}40` : 'transparent'}}>{it}</div>;
        })}
      </div>
    );
    ripple2 = <Ripple x={ix} y={iy} t={(f - c2) / 12} />;
  }
  return (
    <div style={{position: 'absolute', inset: 0, pointerEvents: 'none', opacity: appear}}>
      <Ripple x={tx} y={ty} t={(f - c1) / 12} />
      {menu}{ripple2}
      <div style={{position: 'absolute', left: cx - 2, top: cy - 2}}><Arrow press={p} /></div>
    </div>
  );
};
