import React from 'react';
import {Composition} from 'remotion';
import {Promo, PROMO_DURATION} from './Promo';

const common = {component: Promo, durationInFrames: PROMO_DURATION, fps: 30, width: 1080, height: 1920} as const;

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Promo" {...common} defaultProps={{lang: 'ru' as const}} />
    <Composition id="PromoEn" {...common} defaultProps={{lang: 'en' as const}} />
  </>
);
