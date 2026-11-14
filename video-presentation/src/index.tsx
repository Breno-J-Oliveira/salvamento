import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {TOTAL, Video} from './Video';
import {FPS} from './theme';

const Root: React.FC = () => (
  <Composition id="PurpleTalent" component={Video} durationInFrames={TOTAL} fps={FPS} width={1920} height={1080} />
);
registerRoot(Root);
