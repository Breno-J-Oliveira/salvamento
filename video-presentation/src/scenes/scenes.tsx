import React from 'react';
import {AbsoluteFill, interpolate, Sequence, useCurrentFrame} from 'remotion';
import {C, FONT, sec} from '../theme';
import {Body, Cam, Click, ease, Kicker, Logo, Reveal, Screen, Split, Steps, Title, useFade} from '../components/ui';

// Proporções reais das capturas (largura / altura).
const VIEW = 1920 / 1080;
const AR = {landingFull: 1920 / 5046, vagaFull: 1920 / 1687, formFull: 1920 / 2294, candFull: 1920 / 2089, dossieFull: 1920 / 5771, adminFull: 1920 / 2962};

type Shot = {src: string; ar?: number; dur: number; cams: Cam[]; url: string; label: string; click?: Click;
  highlight?: {x: number; y: number; w: number; h: number; from: number}};

/** Sequência de capturas com fusão entre elas e legenda do passo atual. */
const Shots: React.FC<{shots: Shot[]}> = ({shots}) => {
  let start = 0;
  return (
    <div style={{position: 'relative', width: 1240, height: 742 + 70}}>
      {shots.map((s) => {
        const from = start; start += s.dur;
        return (
          <Sequence key={s.src + from} from={from} durationInFrames={s.dur + 10} layout="none">
            <ShotView shot={s} />
          </Sequence>
        );
      })}
    </div>
  );
};

const ShotView: React.FC<{shot: Shot}> = ({shot}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 12, shot.dur, shot.dur + 10], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const lift = interpolate(f, [0, 16], [24, 0], {extrapolateRight: 'clamp', easing: ease});
  return (
    <div style={{position: 'absolute', inset: 0, opacity: o}}>
      <div style={{transform: `translateY(${lift}px)`}}>
        <Screen src={shot.src} ar={shot.ar ?? VIEW} cams={shot.cams} at={shot.cams.map((_, i) => (i * shot.dur) / Math.max(1, shot.cams.length - 1))}
          url={shot.url} highlight={shot.highlight} click={shot.click} dur={shot.dur} />
      </div>
      <div style={{position: 'absolute', left: 4, top: 742 + 22, fontFamily: FONT.mono, fontSize: 21, color: C.muted, display: 'flex', gap: 12, alignItems: 'center'}}>
        <span style={{width: 8, height: 8, borderRadius: 4, background: C.teal}} /> {shot.label}
      </div>
    </div>
  );
};

// ───────────── CENA 1 — ABERTURA ─────────────
export const Abertura: React.FC = () => {
  const f = useCurrentFrame();
  const o = useFade(1, 14);
  const line = interpolate(f, [20, 60], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const reveal = interpolate(f, [8, 44], [0, 100], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const scale = interpolate(f, [0, 210], [1.04, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{opacity: o, alignItems: 'center', justifyContent: 'center', transform: `scale(${scale})`}}>
      {/* trio Red · Purple · Blue, a ideia central do produto */}
      <div style={{display: 'flex', gap: 18, marginBottom: 54}}>
        {[C.red, C.purple, C.blue].map((c, i) => {
          const p = interpolate(f - i * 6, [0, 20], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
          return <div key={c} style={{width: 120, height: 8, borderRadius: 4, background: c, opacity: p, transform: `scaleX(${p})`}} />;
        })}
      </div>
      <div style={{clipPath: `inset(0 ${100 - reveal}% 0 0)`}}><Logo size={150} /></div>
      <div style={{width: 760 * line, height: 1, background: C.border, margin: '40px 0'}} />
      <Reveal delay={48}><div style={{fontFamily: FONT.body, fontSize: 36, color: C.muted}}>Recrutamento em cibersegurança por evidências</div></Reveal>
      <Reveal delay={70}><div style={{marginTop: 56, fontFamily: FONT.mono, fontSize: 22, letterSpacing: 3, color: C.lilac, textAlign: 'center'}}>PROJETO SAGA SENAI · ESCOLA SENAI A. JACOB LAFER</div></Reveal>
      <div style={{marginTop: 26, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '14px 18px', maxWidth: 1500}}>
        {['Ana Carolina', 'Breno José', 'João Pedro Tomazini', 'Leonardo Alves', 'Nicolas Tukaze', 'Paolla Veronêz', 'Rafaela Oliveira'].map((n, i) => (
          <Reveal key={n} delay={82 + i * 6} y={14}>
            <div style={{padding: '10px 22px', borderRadius: 999, border: `1px solid ${C.border}`, background: C.surface, fontFamily: FONT.body, fontSize: 27, color: C.text}}>{n}</div>
          </Reveal>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// ───────────── CENA 2 — PROPOSTA DE VALOR ─────────────
export const Proposta: React.FC = () => {
  const f = useCurrentFrame();
  const o = useFade(10, 12);
  const phase2 = sec(4.2);
  const p1 = interpolate(f, [phase2 - 10, phase2], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const pillars = [
    {t: 'Prática', d: 'Desafios CTF e laboratórios reais', c: C.red},
    {t: 'Evidências', d: 'Respostas e raciocínio por vaga', c: C.purple},
    {t: 'Avaliação humana', d: 'Rubrica, parecer e feedback', c: C.blue},
  ];
  return (
    <AbsoluteFill style={{opacity: o}}>
      <AbsoluteFill style={{opacity: p1, alignItems: 'center', justifyContent: 'center', textAlign: 'center', gap: 30}}>
        <Reveal><Kicker color={C.red}>O problema</Kicker></Reveal>
        <Reveal delay={8}><Title size={84}>Currículos não mostram<br />como alguém <span style={{color: C.lilac}}>investiga.</span></Title></Reveal>
      </AbsoluteFill>
      <Sequence from={phase2} layout="none">
        <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 70}}>
          <Reveal><Title size={70}>Talento se revela na <span style={{color: C.lilac}}>investigação.</span></Title></Reveal>
          <div style={{display: 'flex', gap: 34}}>
            {pillars.map((p, i) => (
              <Reveal key={p.t} delay={14 + i * 9}>
                <div style={{width: 430, padding: '38px 40px', borderRadius: 22, background: C.surface, border: `1px solid ${C.border}`, borderTop: `4px solid ${p.c}`}}>
                  <div style={{fontFamily: FONT.mono, fontSize: 20, color: p.c}}>0{i + 1}</div>
                  <div style={{fontFamily: FONT.display, fontWeight: 800, fontSize: 42, color: C.text, margin: '14px 0 10px'}}>{p.t}</div>
                  <div style={{fontFamily: FONT.body, fontSize: 25, color: C.muted}}>{p.d}</div>
                </div>
              </Reveal>
            ))}
          </div>
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};

// ───────────── CENA 3 — JORNADA DO CANDIDATO ─────────────
export const Candidato: React.FC = () => (
  <Split
    left={<>
      <Reveal><Kicker>Para candidatos</Kicker></Reveal>
      <Reveal delay={6}><Title>Da vaga à candidatura, em um só lugar.</Title></Reveal>
      <Steps delay={20} every={10} items={['Encontre vagas por área e modalidade', 'Conheça critérios e prazos', 'Responda o formulário da vaga', 'Acompanhe cada etapa']} />
    </>}
    right={<Shots shots={[
      {src: 'captures/02-vagas.png', dur: sec(4.2), url: '127.0.0.1:5000/opportunities', label: 'Vagas publicadas com busca e filtros', click: {x: 380, y: 896},
        cams: [{s: 1, x: 0.5, y: 0.5}, {s: 1.35, x: 0.55, y: 0.72}]},
      {src: 'captures/03-vaga-detalhe-full.png', ar: AR.vagaFull, dur: sec(4.4), url: '127.0.0.1:5000/opportunities/2', label: 'Detalhes, requisitos e próxima etapa', click: {x: 1408, y: 644},
        cams: [{s: 1, x: 0.5, y: 0}, {s: 1.15, x: 0.55, y: 0.45}]},
      {src: 'captures/05-formulario-full.png', ar: AR.formFull, dur: sec(4.6), url: '127.0.0.1:5000/applications/2/form', label: 'Formulário próprio de cada vaga, com rascunho salvo', click: {x: 518, y: 1796},
        cams: [{s: 1.25, x: 0.3, y: 0.15}, {s: 1.25, x: 0.3, y: 0.79}]},
      {src: 'captures/04-minhas-candidaturas-full.png', ar: AR.candFull, dur: sec(4.8), url: '127.0.0.1:5000/my-applications', label: 'Minhas candidaturas: etapa, datas e retorno', click: {x: 776, y: 50, menu: ['Desafios CTF', 'Purple Team', 'Laboratório', 'Guias de estudo', 'Ranking'], pick: 0},
        cams: [{s: 1, x: 0.5, y: 0.1}, {s: 1.3, x: 0.7, y: 0.5}, {s: 1, x: 0.5, y: 0}]},
    ]} />}
  />
);

// ───────────── CENA 4 — PRÁTICA (CTF + LABORATÓRIOS) ─────────────
export const Pratica: React.FC = () => (
  <Split
    left={<>
      <Reveal><Kicker color={C.red}>Prática real</Kicker></Reveal>
      <Reveal delay={6}><Title>Habilidade comprovada na prática.</Title></Reveal>
      <Reveal delay={18}><Body>Desafios CTF de Red e Blue Team, com validação de flag na hora.</Body></Reveal>
      <Reveal delay={sec(11)}><Body>Laboratórios individuais em <span style={{color: C.text}}>máquinas virtuais VirtualBox</span>, isolados e com flag única por pessoa.</Body></Reveal>
    </>}
    right={<Shots shots={[
      {src: 'captures/06-desafios.png', dur: sec(3.4), url: '127.0.0.1:5000/challenges', label: 'Catálogo de desafios por área', click: {x: 1516, y: 893},
        cams: [{s: 1, x: 0.5, y: 0.5}, {s: 1.15, x: 0.5, y: 0.65}]},
      {src: 'captures/07-desafio-digitado.png', dur: sec(3.8), url: '127.0.0.1:5000/challenge/3', label: 'O candidato decodifica a pista e envia a flag', click: {x: 1388, y: 768},
        cams: [{s: 1, x: 0.5, y: 0.5}, {s: 1.9, x: 0.72, y: 0.6}, {s: 1.9, x: 0.72, y: 0.6}]},
      {src: 'captures/07-desafio-correto.png', dur: sec(3.6), url: '127.0.0.1:5000/challenge/3', label: 'Validação imediata e pontos registrados', click: {x: 776, y: 50, menu: ['Desafios CTF', 'Purple Team', 'Laboratório', 'Guias de estudo', 'Ranking'], pick: 2},
        cams: [{s: 1.45, x: 0.62, y: 0.5}, {s: 1, x: 0.5, y: 0.5}]},
      {src: 'captures/08-labs.png', dur: sec(5.2), url: '127.0.0.1:5000/labs', label: 'Laboratórios: Intranet esquecida e Incidente em andamento', click: {x: 776, y: 50, menu: ['Desafios CTF', 'Purple Team', 'Laboratório', 'Guias de estudo', 'Ranking'], pick: 4},
        cams: [{s: 1, x: 0.5, y: 0.5}, {s: 1.3, x: 0.5, y: 0.75}, {s: 1, x: 0.5, y: 0.5}]},
      {src: 'captures/11-ranking.png', dur: sec(3.2), url: '127.0.0.1:5000/ranking', label: 'Talent Pool e ranking',
        cams: [{s: 1, x: 0.5, y: 0.5}, {s: 1.3, x: 0.4, y: 0.6}]},
    ]} />}
  />
);

// ───────────── CENA 5 — AVALIAÇÃO HUMANA (diferencial) ─────────────
const Flow: React.FC = () => {
  const f = useCurrentFrame();
  const o = useFade(8, 10);
  const nodes = [
    {t: 'Respostas', d: 'formulário da vaga', c: C.blue},
    {t: 'Evidências', d: 'avaliação prática', c: C.purple},
    {t: 'Rubrica', d: 'competências 0–5', c: C.lilac},
    {t: 'Feedback', d: 'retorno ao candidato', c: C.teal},
  ];
  const prog = interpolate(f, [16, 90], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  return (
    <AbsoluteFill style={{opacity: o, alignItems: 'center', justifyContent: 'center', gap: 60}}>
      <Reveal><Kicker color={C.blue}>Para a equipe</Kicker></Reveal>
      <Reveal delay={6}><Title size={76}>A decisão continua <span style={{color: C.lilac}}>humana.</span></Title></Reveal>
      <div style={{position: 'relative', display: 'flex', gap: 70, marginTop: 20}}>
        <div style={{position: 'absolute', left: 140, right: 140, top: 62, height: 3, background: C.border}} />
        <div style={{position: 'absolute', left: 140, width: `calc((100% - 280px) * ${prog})`, top: 62, height: 3, background: `linear-gradient(90deg, ${C.blue}, ${C.purple}, ${C.teal})`}} />
        {nodes.map((n, i) => {
          const on = prog >= i / 3 - 0.01;
          return (
            <div key={n.t} style={{width: 280, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18}}>
              <div style={{width: 124, height: 124, borderRadius: 28, background: C.surface, border: `2px solid ${on ? n.c : C.border}`,
                display: 'grid', placeItems: 'center', fontFamily: FONT.mono, fontSize: 36, color: on ? n.c : C.muted,
                transform: `scale(${on ? 1 : 0.9})`, zIndex: 1}}>0{i + 1}</div>
              <div style={{fontFamily: FONT.display, fontWeight: 800, fontSize: 36, color: on ? C.text : C.muted}}>{n.t}</div>
              <div style={{fontFamily: FONT.body, fontSize: 23, color: C.muted}}>{n.d}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Avaliacao: React.FC = () => (
  <>
    <Sequence durationInFrames={sec(4.6)}><Flow /></Sequence>
    <Sequence from={sec(4.6)}>
      <Split
        left={<>
          <Reveal><Kicker color={C.blue}>Dossiê da candidatura</Kicker></Reveal>
          <Reveal delay={6}><Title>Tudo o que importa para decidir.</Title></Reveal>
          <Steps delay={18} every={12} items={['Respostas e correção objetiva', 'Evidências da avaliação prática', 'Rubrica por competência', 'Nota interna separada do feedback']} />
        </>}
        right={<Shots shots={[
          {src: 'captures/13-dossie-full.png', ar: AR.dossieFull, dur: sec(4.2), url: '127.0.0.1:5000/admin/applications/1', label: 'Dossiê com respostas e etapa da candidatura', click: {x: 574, y: 592},
            cams: [{s: 1, x: 0.5, y: 0}, {s: 1.1, x: 0.5, y: 0.08}]},
          {src: 'captures/14-dossie-2.png', dur: sec(3.8), url: '127.0.0.1:5000/admin/applications/1', label: 'Revisão por competência, com justificativa', click: {x: 700, y: 955},
            cams: [{s: 1.1, x: 0.3, y: 0.45}, {s: 1.5, x: 0.3, y: 0.6}]},
          {src: 'captures/14-dossie-3.png', dur: sec(3.4), url: '127.0.0.1:5000/admin/applications/1', label: 'Parecer interno e feedback compartilhável', click: {x: 508, y: 48},
            cams: [{s: 1.1, x: 0.6, y: 0.5}, {s: 1.6, x: 0.85, y: 0.55}, {s: 1, x: 0.5, y: 0.5}]},
        ]} />}
      />
    </Sequence>
  </>
);

// ───────────── CENA 6 — GESTÃO E INDICADORES ─────────────
export const Gestao: React.FC = () => (
  <Split
    left={<>
      <Reveal><Kicker color={C.teal}>Gestão e mentoria</Kicker></Reveal>
      <Reveal delay={6}><Title>Visão clara do processo e da turma.</Title></Reveal>
      <Steps delay={18} every={10} items={['Painel de processos seletivos', 'Desempenho por equipe', 'Ranking e evolução por área', 'Controle dos ambientes virtuais']} />
    </>}
    right={<Shots shots={[
      {src: 'captures/12-admin.png', dur: sec(3.4), url: '127.0.0.1:5000/admin', label: 'Vagas, candidaturas e pendências de avaliação', click: {x: 1226, y: 137},
        cams: [{s: 1, x: 0.5, y: 0.5}, {s: 1.2, x: 0.5, y: 0.3}]},
      {src: 'captures/15-dashboard.png', dur: sec(3.6), url: '127.0.0.1:5000/dashboard', label: 'Avaliação Purple Team por equipe e participante', click: {x: 1410, y: 137},
        cams: [{s: 1.25, x: 0.4, y: 0.3}, {s: 1.25, x: 0.5, y: 0.75}, {s: 1, x: 0.5, y: 0.5}]},
      {src: 'captures/16-ambientes.png', dur: sec(3.6), url: '127.0.0.1:5000/ambientes', label: 'Ambientes virtuais ativos, com encerramento',
        cams: [{s: 1.2, x: 0.4, y: 0.35}, {s: 1, x: 0.5, y: 0.5}]},
    ]} />}
  />
);

// ───────────── CENA 7 — ENCERRAMENTO ─────────────
export const Encerramento: React.FC = () => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 14], [0, 1], {extrapolateRight: 'clamp'});
  const end = interpolate(f, [sec(7.2), sec(8)], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{opacity: o * end, alignItems: 'center', justifyContent: 'center', gap: 34}}>
      <Reveal><Logo size={130} /></Reveal>
      <Reveal delay={14}><div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 48, color: C.text}}>Prática para aprender. Evidências para conversar.</div></Reveal>
      <Reveal delay={24}><div style={{fontFamily: FONT.display, fontWeight: 700, fontSize: 48, color: C.lilac}}>Pessoas para decidir.</div></Reveal>
      <Reveal delay={40}><div style={{marginTop: 30, fontFamily: FONT.mono, fontSize: 22, color: C.muted, letterSpacing: 2}}>CTI · PROJETO ACADÊMICO</div></Reveal>
    </AbsoluteFill>
  );
};
