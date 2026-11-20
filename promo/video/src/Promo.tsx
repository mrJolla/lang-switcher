import React from 'react';
import {Audio} from '@remotion/media';
import {AbsoluteFill, Img, interpolate, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export const PROMO_DURATION = 270; // 9 s @ 30 fps

const FONT = '-apple-system, "SF Pro Display", "Helvetica Neue", Arial, sans-serif';
const INK = '#0b1f3a';
const ACCENT = '#0a62d6';
const MUTED = '#4a6285';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Timeline (frames)
const T = {
  typeEn: [14, 46] as const, // "Hello, "
  keysIn: 40,
  press: 66, // Cmd+Shift tap
  typeRu: [90, 128] as const, // "привет!"
  sceneSwap: [138, 156] as const, // demo -> poster
  iconIn: 150,
  nameIn: 164,
  titleIn: [172, 180, 188],
  metaIn: 194,
  posterKeysIn: 204,
  posterPress: 228,
};
const EN_TEXT = 'Hello, ';
const RU_TEXT = 'привет!';

const useSpring = (from: number, damping = 14, durationInFrames?: number) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - from, fps, config: {damping, mass: 0.8}, durationInFrames});
};

const typed = (text: string, frame: number, [a, b]: readonly [number, number]) =>
  text.slice(0, Math.round(interpolate(frame, [a, b], [0, text.length], clamp)));

/** 0..1..0 dip around `at`: key goes down and comes back up. */
const pressDepth = (frame: number, at: number) =>
  interpolate(frame, [at - 4, at, at + 6, at + 12], [0, 1, 1, 0], clamp);

const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const drift = Math.sin(frame / 40) * 30;
  return (
    <AbsoluteFill style={{background: 'radial-gradient(1100px 1000px at 50% 40%, #dcecff 0, #eef6ff 45%, #fbfdff 82%)'}}>
      <div style={{position: 'absolute', width: 760, height: 760, left: -300 + drift, top: 1250, borderRadius: '50%', filter: 'blur(70px)', background: 'rgba(120,190,255,.35)'}} />
      <div style={{position: 'absolute', width: 640, height: 640, right: -260 - drift, top: -140, borderRadius: '50%', filter: 'blur(70px)', background: 'rgba(80,150,255,.24)'}} />
    </AbsoluteFill>
  );
};

const Key: React.FC<{glyph: string; label: string; depth: number; scale?: number}> = ({glyph, label, depth, scale = 1}) => (
  <div
    style={{
      width: 260 * scale, height: 220 * scale, borderRadius: 44 * scale, padding: `${30 * scale}px ${34 * scale}px`,
      display: 'flex', flexDirection: 'column', justifyContent: 'space-between', textAlign: 'left',
      background: depth > 0.5 ? 'linear-gradient(#e9f1ff, #dbe8fb)' : 'linear-gradient(#ffffff, #eef3fa)',
      transform: `translateY(${depth * 10 * scale}px) scale(${1 - depth * 0.04})`,
      boxShadow: `0 2px 0 #fff inset, 0 ${-10 * (1 - depth)}px 0 rgba(30,70,140,.10) inset, 0 ${26 * (1 - depth * 0.6)}px 46px -14px rgba(20,70,160,${0.4 + depth * 0.2}), 0 0 0 ${1.5 + depth * 2}px rgba(10,98,214,${0.12 + depth * 0.5})`,
    }}
  >
    <span style={{fontSize: 76 * scale, lineHeight: 1, alignSelf: 'flex-end', color: INK}}>{glyph}</span>
    <span style={{fontSize: 38 * scale, fontWeight: 600, color: MUTED}}>{label}</span>
  </div>
);

const Keys: React.FC<{depth: number; scale?: number}> = ({depth, scale = 1}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: 40 * scale}}>
    <Key glyph="⌘" label="command" depth={depth} scale={scale} />
    <div style={{fontSize: 96 * scale, fontWeight: 300, color: '#7d94b5'}}>+</div>
    <Key glyph="⇧" label="shift" depth={depth} scale={scale} />
  </div>
);

/** Scene 1: typing in an editor, Cmd+Shift switches EN -> RU. */
const Demo: React.FC = () => {
  const frame = useCurrentFrame();
  const winIn = useSpring(0, 16);
  const keysIn = useSpring(T.keysIn, 13);
  const flip = useSpring(T.press + 2, 11);
  const depth = pressDepth(frame, T.press);
  const isRu = frame >= T.press + 2;
  const caretOn = Math.floor(frame / 8) % 2 === 0 || (frame > T.typeEn[0] && frame < T.typeEn[1]) || (frame > T.typeRu[0] && frame < T.typeRu[1]);
  const ripple = interpolate(frame, [T.press, T.press + 20], [0, 1], clamp);

  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', gap: 120, fontFamily: FONT}}>
      <div
        style={{
          width: 900, borderRadius: 40, overflow: 'hidden', background: 'rgba(255,255,255,.85)',
          boxShadow: '0 40px 80px -30px rgba(20,70,160,.45), 0 0 0 1.5px rgba(30,70,140,.10)',
          opacity: winIn, transform: `translateY(${(1 - winIn) * 60}px) scale(${0.94 + winIn * 0.06})`,
        }}
      >
        {/* menu bar with layout indicator */}
        <div style={{height: 96, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 36px', background: 'rgba(235,240,248,.9)', borderBottom: '1.5px solid rgba(30,70,140,.08)'}}>
          <div style={{display: 'flex', gap: 16}}>
            {['#ff5f57', '#febc2e', '#28c840'].map((c) => (
              <div key={c} style={{width: 26, height: 26, borderRadius: 13, background: c}} />
            ))}
          </div>
          <div style={{position: 'relative'}}>
            <div style={{position: 'absolute', inset: -12, borderRadius: 22, border: `4px solid ${ACCENT}`, opacity: (1 - ripple) * (ripple > 0 ? 1 : 0), transform: `scale(${1 + ripple * 0.6})`}} />
            <div
              style={{
                fontSize: 40, fontWeight: 700, letterSpacing: 1, padding: '6px 22px', borderRadius: 14,
                background: isRu ? ACCENT : 'rgba(255,255,255,.9)', color: isRu ? '#fff' : INK,
                boxShadow: '0 0 0 1.5px rgba(30,70,140,.15)',
                transform: isRu ? `scale(${0.6 + flip * 0.4}) rotateX(${(1 - flip) * 90}deg)` : 'none',
              }}
            >
              {isRu ? 'RU' : 'EN'}
            </div>
          </div>
        </div>
        <div style={{padding: '60px 56px', minHeight: 300, fontSize: 76, fontWeight: 500, color: INK, letterSpacing: -1}}>
          {typed(EN_TEXT, frame, T.typeEn)}
          <span style={{color: ACCENT}}>{typed(RU_TEXT, frame, T.typeRu)}</span>
          <span style={{display: 'inline-block', width: 6, height: 84, marginLeft: 4, verticalAlign: -12, background: ACCENT, opacity: caretOn ? 1 : 0}} />
        </div>
      </div>

      <div style={{opacity: keysIn, transform: `translateY(${(1 - keysIn) * 200}px)`}}>
        <Keys depth={depth} />
      </div>
    </AbsoluteFill>
  );
};

/** Scene 2: the poster assembles itself. */
const Poster: React.FC = () => {
  const frame = useCurrentFrame();
  const icon = useSpring(T.iconIn, 10);
  const name = useSpring(T.nameIn, 18);
  const lines = T.titleIn.map((t) => useSpring(t, 18)); // fixed-length array, hook order is stable
  const meta = useSpring(T.metaIn, 18);
  const keys = useSpring(T.posterKeysIn, 13);
  const depth = pressDepth(frame, T.posterPress);
  const glow = 0.42 + Math.sin(frame / 12) * 0.08;
  const title = [
    {text: 'Удобная', color: INK},
    {text: 'смена языка', color: INK},
    {text: 'на клавиатуре', color: 'gradient'},
  ];

  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', textAlign: 'center', fontFamily: FONT, color: INK, paddingBottom: 40}}>
      <div style={{width: 360, height: 360, position: 'relative', transform: `scale(${icon}) rotate(${(1 - icon) * -25}deg)`}}>
        <div style={{position: 'absolute', inset: -140, background: `radial-gradient(closest-side, rgba(10,132,255,${glow}), rgba(10,132,255,0))`}} />
        <Img src={staticFile('icon.png')} style={{position: 'relative', width: '100%', height: '100%', filter: 'drop-shadow(0 30px 40px rgba(20,60,120,.32))'}} />
      </div>
      <div style={{marginTop: 56, fontSize: 56, fontWeight: 600, color: ACCENT, opacity: name, transform: `translateY(${(1 - name) * 30}px)`}}>LangSwitcher</div>
      <div style={{marginTop: 26, fontSize: 104, lineHeight: 1.04, fontWeight: 800, letterSpacing: -3}}>
        {title.map((l, i) => (
          <div key={l.text} style={{opacity: lines[i], transform: `translateY(${(1 - lines[i]) * 50}px)`}}>
            <span
              style={
                l.color === 'gradient'
                  ? {background: 'linear-gradient(90deg, #0a62d6, #3aa0ff)', WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent'}
                  : {color: l.color}
              }
            >
              {l.text}
            </span>
          </div>
        ))}
      </div>
      <div style={{marginTop: 34, fontSize: 40, fontWeight: 500, color: MUTED, opacity: meta, transform: `translateY(${(1 - meta) * 24}px)`}}>
        macOS 13+ · Apple Silicon и Intel
      </div>
      <div style={{marginTop: 100, opacity: keys, transform: `translateY(${(1 - keys) * 120}px)`}}>
        <Keys depth={depth} />
      </div>
    </AbsoluteFill>
  );
};

export const Promo: React.FC = () => {
  const frame = useCurrentFrame();
  const out = interpolate(frame, T.sceneSwap, [1, 0], clamp);
  const fadeIn = interpolate(frame, [0, 8], [0, 1], clamp);
  return (
    <AbsoluteFill style={{opacity: fadeIn}}>
      <Background />
      {out > 0 && (
        <AbsoluteFill style={{opacity: out, transform: `scale(${1 + (1 - out) * 0.08})`, filter: `blur(${(1 - out) * 12}px)`}}>
          <Demo />
        </AbsoluteFill>
      )}
      {frame >= T.iconIn - 2 && <Poster />}
      <Soundtrack />
    </AbsoluteFill>
  );
};

/** Frames at which a new character appears while typing (one keystroke each). */
const typingFrames = (text: string, range: readonly [number, number]) => {
  const hits: {frame: number; char: string}[] = [];
  for (let f = range[0]; f <= range[1] + 1; f++) {
    const now = typed(text, f, range);
    if (now.length > typed(text, f - 1, range).length) hits.push({frame: f, char: now[now.length - 1]});
  }
  return hits;
};

const Sfx: React.FC<{at: number; file: string; volume?: number}> = ({at, file, volume = 1}) => (
  <Sequence from={at} durationInFrames={45} layout="none">
    <Audio src={staticFile(`audio/${file}`)} volume={volume} />
  </Sequence>
);

/** Music + sound effects, timed from the same timeline as the visuals. */
const Soundtrack: React.FC = () => {
  const clicks = [...typingFrames(EN_TEXT, T.typeEn), ...typingFrames(RU_TEXT, T.typeRu)];
  const tap = (at: number) => [
    <Sfx key={`d${at}`} at={at - 4} file="keys-down.wav" volume={0.7} />,
    <Sfx key={`u${at}`} at={at + 8} file="keys-up.wav" volume={0.6} />,
  ];
  return (
    <>
      <Audio src={staticFile('audio/lofi.wav')} volume={0.75} />
      <Sfx at={0} file="pop.wav" volume={0.3} />
      {clicks.map(({frame: f, char}, i) => (
        <Sfx key={`t${f}`} at={f} file={char === ' ' ? 'space.wav' : `type${((i * 5) % 6) + 1}.wav`} volume={0.55} />
      ))}
      <Sfx at={T.keysIn} file="whoosh-soft.wav" volume={0.35} />
      {tap(T.press)}
      <Sfx at={T.press + 2} file="switch.wav" volume={0.45} />
      <Sfx at={T.sceneSwap[0]} file="whoosh.wav" volume={0.45} />
      <Sfx at={T.iconIn} file="pop.wav" volume={0.6} />
      {T.titleIn.map((f, i) => (
        <Sfx key={`p${f}`} at={f} file={`pluck${i + 1}.wav`} volume={0.3} />
      ))}
      <Sfx at={T.posterKeysIn} file="whoosh-soft.wav" volume={0.3} />
      {tap(T.posterPress)}
    </>
  );
};
