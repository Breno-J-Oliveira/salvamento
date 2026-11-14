import React from 'react';
import {AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {Background} from './components/ui';
import {fontFaces, sec} from './theme';
import {Abertura, Avaliacao, Candidato, Encerramento, Gestao, Pratica, Proposta} from './scenes/scenes';

// Duração de cada cena (segundos). Ajuste aqui; o total é calculado automaticamente.
export const SCENES: [string, number, React.FC][] = [
  ['Abertura', 10, Abertura],
  ['Proposta de valor', 11, Proposta],
  ['Jornada do candidato', 18, Candidato],
  ['Prática: CTF e laboratórios', 19.4, Pratica],
  ['Avaliação humana', 16, Avaliacao],
  ['Gestão e indicadores', 11, Gestao],
  ['Encerramento', 8, Encerramento],
];
export const TOTAL = sec(SCENES.reduce((a, [, s]) => a + s, 0));

export const Video: React.FC = () => {
  const f = useCurrentFrame();
  let start = 0;
  return (
    <AbsoluteFill>
      <style>{fontFaces}</style>
      <Background />
      {SCENES.map(([name, s, Scene]) => {
        const from = start; start += sec(s);
        return <Sequence key={name} name={name} from={from} durationInFrames={sec(s)}><Scene /></Sequence>;
      })}
      <Audio src={staticFile('audio/trilha.wav')} volume={(fr) => interpolate(fr, [0, 20, TOTAL - 45, TOTAL], [0, 0.9, 0.9, 0], {extrapolateRight: 'clamp'})} />
    </AbsoluteFill>
  );
};
