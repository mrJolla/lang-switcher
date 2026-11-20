"""Synthesize the promo soundtrack: a muffled lo-fi loop + UI sound effects.

Everything is generated from scratch (no samples), so there are no licensing questions.
Run:  uv run --with numpy python scripts/make_audio.py
Writes WAV files (44.1 kHz, 16-bit stereo) to public/audio/.
"""
import pathlib
import wave

import numpy as np

SR = 44100
OUT = pathlib.Path(__file__).resolve().parent.parent / "public" / "audio"
rng = np.random.default_rng(7)


# ---------- helpers ----------
def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def band(x, lo=None, hi=None, slope=2.0):
    """Soft FFT band-pass (lo/hi in Hz, either may be None)."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-9
    g = np.ones_like(f)
    if hi:
        g /= np.sqrt(1 + (f / hi) ** (2 * slope))
    if lo:
        g /= np.sqrt(1 + (lo / f) ** (2 * slope))
    return np.fft.irfft(spec * g, len(x))


def env_ad(n, attack, decay_tau):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / decay_tau)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(buf, clip, at_sec, gain=1.0):
    i = int(at_sec * SR)
    j = min(len(buf), i + len(clip))
    if i < len(buf):
        buf[i:j] += clip[: j - i] * gain


def write(name, left, right=None, peak=0.9):
    right = left if right is None else right
    st = np.stack([left, right], axis=1)
    m = np.abs(st).max()
    if m > 0:
        st = st / m * peak
    pcm = (st * 32767).astype("<i2")
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", OUT / name)


# ---------- music ----------
BPM = 80
BEAT = 60 / BPM  # 0.75 s
LENGTH = 9.6  # a bit longer than the 9 s video, Remotion trims it


def epiano(freq, dur, vel=1.0):
    """Rhodes-ish electric piano: a few harmonics, bell attack, tremolo, tape wobble."""
    t = t_axis(dur)
    wob = 1 + 0.0025 * np.sin(2 * np.pi * 0.7 * t + rng.uniform(0, 6))
    ph = 2 * np.pi * freq * np.cumsum(wob) / SR
    tone = (
        np.sin(ph)
        + 0.35 * np.sin(2 * ph) * np.exp(-t / 0.25)
        + 0.12 * np.sin(3 * ph) * np.exp(-t / 0.12)
        + 0.06 * np.sin(7.1 * ph) * np.exp(-t / 0.03)  # tine "bark"
    )
    trem = 1 - 0.18 * (0.5 + 0.5 * np.sin(2 * np.pi * 4.2 * t))
    rel = np.clip((dur - t) / 0.35, 0, 1)
    return tone * trem * (0.35 + 0.65 * env_ad(len(t), 0.008, 1.4)) * np.clip(t / 0.008, 0, 1) * rel * vel


def kick(vel=1.0):
    t = t_axis(0.45)
    f = 45 + 75 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.002, 0.16) * vel


def snare(vel=1.0):
    n = int(0.35 * SR)
    noise = band(rng.standard_normal(n), 900, 4500) * env_ad(n, 0.002, 0.09)
    t = t_axis(0.35)
    body = np.sin(2 * np.pi * 185 * t) * env_ad(n, 0.002, 0.05)
    return (noise * 0.9 + body * 0.5) * vel


def hat(vel=1.0):
    n = int(0.08 * SR)
    return band(rng.standard_normal(n), 6000, 11000) * env_ad(n, 0.001, 0.018) * vel


def music():
    n = int(LENGTH * SR)
    L = np.zeros(n)
    R = np.zeros(n)

    # Fmaj9 -> Em7 -> Dm9 -> Cmaj9 (the last one rings out over the poster)
    chords = [
        (0 * BEAT, 4 * BEAT, [53, 57, 60, 64, 67]),  # F A C E G
        (4 * BEAT, 4 * BEAT, [52, 55, 59, 62, 66]),  # E G B D F#
        (8 * BEAT, 2 * BEAT, [50, 53, 57, 60, 64]),  # D F A C E
        (10 * BEAT, LENGTH - 10 * BEAT, [48, 55, 59, 62, 64]),  # C G B D E
    ]
    for start, dur, notes in chords:
        for k, m in enumerate(notes):
            strum = k * 0.018
            v = epiano(midi(m), dur - strum + 0.45, 0.55 if k else 0.7)  # overlap into next chord
            pan = 0.5 + (k - 2) * 0.12
            place(L, v, start + strum, 1 - pan * 0.6)
            place(R, v, start + strum, 0.4 + pan * 0.6)
        # bass: root, an octave down
        b = epiano(midi(notes[0] - 12), dur + 0.3, 0.9)
        place(L, b, start)
        place(R, b, start)
    # small melody on top (pentatonic-ish), sparse
    for at, m in [(1.5, 72), (2.25, 74), (3.75, 76), (4.5, 74), (5.25, 72), (6.75, 71), (7.5, 72), (8.25, 76)]:
        v = epiano(midi(m), 1.1, 0.32)
        place(L, v, at, 0.8)
        place(R, v, at, 1.0)

    # drums: lazy swung pattern, stops before the last chord so the ending breathes
    drums = np.zeros(n)
    swing = 0.06
    for bar in range(3):
        b0 = bar * 4 * BEAT
        for beat, inst in [(0, "k"), (1, "s"), (2.5, "k"), (3, "s")]:
            clip = kick(0.9) if inst == "k" else snare(0.45)
            place(drums, clip, b0 + beat * BEAT)
        for e in range(8):
            place(drums, hat(0.22 if e % 2 else 0.3), b0 + e * BEAT / 2 + (swing if e % 2 else 0))
    place(drums, kick(0.8), 12 * BEAT)
    L += drums * 0.55
    R += drums * 0.55

    # vinyl: soft hiss + sparse crackles
    hiss = band(rng.standard_normal(n), 1500, 6000) * 0.012
    crack = np.zeros(n)
    for i in rng.integers(0, n - 200, 140):
        crack[i : i + 60] += rng.uniform(-1, 1) * np.exp(-np.arange(60) / 8) * rng.uniform(0.05, 0.25)
    crack = band(crack, 1200, 8000)
    L += hiss + crack
    R += hiss + np.roll(crack, 37)

    # muffle: warm low-pass, then fade in/out
    L = band(L, 35, 2400, 1.5)
    R = band(R, 35, 2400, 1.5)
    fade = np.ones(n)
    fi, fo = int(0.4 * SR), int(1.4 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
    write("lofi.wav", L * fade, R * fade, peak=0.85)


# ---------- sound effects ----------
# Keyboard sounds use modal synthesis: a very short excitation (the impact) is run
# through a bank of damped resonators (keycap plastic + chassis), like a real key.
krng = np.random.default_rng(11)


def resonate(excitation, modes, dur):
    """Convolve an excitation with damped sinusoids: modes = [(freq, decay_s, gain), ...]."""
    t = t_axis(dur)
    ir = np.zeros_like(t)
    for f, tau, g in modes:
        ir += g * np.sin(2 * np.pi * f * t + krng.uniform(0, 6)) * np.exp(-t / tau)
    return np.convolve(excitation, ir)[: len(t)]


def impact(ms=0.6, hard=1.0):
    """Short raised-cosine noise burst: the moment plastic hits plastic."""
    n = max(4, int(ms / 1000 * SR))
    return krng.standard_normal(n) * np.hanning(n) * hard


def room(x, amount=0.18):
    """Tiny desk/room: a few early reflections, slightly darker each time."""
    out = x.copy()
    for d_ms, g in [(6.5, 0.55), (11.3, 0.4), (17.9, 0.3), (26.0, 0.2), (37.0, 0.12)]:
        d = int(d_ms / 1000 * SR)
        out[d:] += band(x, 120, 5000)[: len(x) - d] * g * amount
    return out


def key_stroke(size=1.0, seed=0, up_after=0.085, level_up=0.45):
    """One key: switch tick -> bottom-out -> release clack, ~0.25 s total.

    size > 1 = bigger key (space, shift): lower modes, longer decays, a little rattle."""
    global krng
    krng = np.random.default_rng(100 + seed)
    dur = 0.28
    n = int(dur * SR)
    jit = lambda: krng.uniform(0.94, 1.06)

    # keycap / switch housing: many dense, heavily damped modes (real plastic is noisy, not tonal)
    freqs = np.exp(krng.uniform(np.log(900), np.log(7500), 12)) / size ** 0.7
    cap = [(f, krng.uniform(0.0012, 0.0045) * size ** 0.5, (1000 / f) ** 0.4 * krng.uniform(0.5, 1)) for f in freqs]
    body = [  # chassis / desk: short, quiet thump
        (220 / size ** 0.5 * jit(), 0.010 * size ** 0.5, 0.35),
        (560 * jit(), 0.006, 0.25),
    ]
    out = np.zeros(n)

    # 1) light switch tick a few ms before bottom-out
    tick = band(resonate(impact(0.25, 0.25), [(5200 * jit(), 0.0015, 1), (7600 * jit(), 0.001, 0.6)], 0.02), 3000, None)
    place(out, tick, 0.0)
    # 2) bottom-out: bright cap modes + body thump
    t0 = krng.uniform(0.004, 0.007)
    hit = resonate(impact(0.5, 1.0), cap, 0.12) + resonate(impact(1.2, 0.9), body, 0.12)
    hn = int(0.012 * SR)
    hit[:hn] += band(krng.standard_normal(hn), 1500, 9000) * env_ad(hn, 0.0003, 0.0018) * 0.35
    if size > 1.3:  # stabilizer wire rattle on big keys
        rattle = band(krng.standard_normal(int(0.03 * SR)), 2500, 7000) * env_ad(int(0.03 * SR), 0.001, 0.008) * 0.08
        place(hit, rattle, 0.003)
    place(out, hit, t0)
    # 3) release: the key springs back, lighter and higher
    up_cap = [(f * 1.12, tau * 0.7, g) for f, tau, g in cap]
    up = resonate(impact(0.35, 0.7), up_cap, 0.06) + resonate(impact(0.8, 0.35), body[:1], 0.06)
    place(out, up, t0 + up_after * krng.uniform(0.85, 1.15), level_up)

    out = band(out, 90, 9000, 1.0)  # mic-ish band limit
    out = room(out)
    fade = np.clip((dur - t_axis(dur)) / 0.04, 0, 1)
    return out * fade


def modifier_chord():
    """Cmd + Shift pressed together: two bigger keys with a tiny flam, no release."""
    a = key_stroke(1.25, seed=40, up_after=5)  # up_after beyond length = no release here
    b = key_stroke(1.5, seed=41, up_after=5)
    out = np.zeros(len(a) + int(0.02 * SR))
    place(out, a, 0.0)
    place(out, b, 0.011, 0.9)
    return out


def modifier_release():
    """Both modifiers springing back up (separate file, timed with the animation)."""
    global krng
    out = np.zeros(int(0.15 * SR))
    for i, (size, at) in enumerate([(1.25, 0.0), (1.5, 0.014)]):
        krng = np.random.default_rng(60 + i)
        cap = [(1500 / size * 1.12, 0.007, 1.0), (2400 / size * 1.12, 0.005, 0.7), (3400 / size, 0.004, 0.4)]
        body = [(230 / size ** 0.5, 0.015, 0.4)]
        clip = resonate(impact(0.35, 0.7), cap, 0.06) + resonate(impact(0.9, 0.4), body, 0.06)
        place(out, clip, at)
    return room(band(out, 90, 9000, 1.0))


def bell(notes, gap, dur=0.9):
    """Soft two-note chime for the EN -> RU switch."""
    n = int((dur + gap * len(notes)) * SR)
    out = np.zeros(n)
    for i, m in enumerate(notes):
        t = t_axis(dur)
        f = midi(m)
        tone = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.15)
        place(out, tone * env_ad(len(t), 0.003, 0.28), i * gap)
    return out


def whoosh(dur=0.7, lo=300, hi=3000):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    # sweep by cross-fading two bands
    a = band(noise, lo, lo * 3)
    b = band(noise, hi / 3, hi)
    x = np.linspace(0, 1, n)
    swept = a * (1 - x) + b * x
    shape = np.sin(np.pi * x) ** 2
    return swept * shape


def pop(f0=520, f1=180):
    t = t_axis(0.25)
    f = f1 + (f0 - f1) * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.002, 0.06)


def pluck(m):
    t = t_axis(0.5)
    f = midi(m)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * env_ad(len(t), 0.002, 0.09)


def sfx():
    for i in range(6):  # six slightly different letter keys, used round-robin
        write(f"type{i + 1}.wav", key_stroke(1.0, seed=i), peak=0.8)
    write("space.wav", key_stroke(1.8, seed=20), peak=0.85)
    write("keys-down.wav", modifier_chord(), peak=0.9)
    write("keys-up.wav", modifier_release(), peak=0.6)
    write("switch.wav", bell([81, 88], 0.09), peak=0.6)  # A5 -> E6
    write("whoosh.wav", whoosh(), peak=0.7)
    write("whoosh-soft.wav", whoosh(0.45, 400, 2200), peak=0.5)
    write("pop.wav", pop(), peak=0.8)
    for i, m in enumerate([72, 76, 79]):  # C E G for the title lines
        write(f"pluck{i + 1}.wav", pluck(m), peak=0.5)


if __name__ == "__main__":
    music()
    sfx()
