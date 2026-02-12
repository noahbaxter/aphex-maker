import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d


def synthesize(
    image: np.ndarray,
    duration: float,
    sample_rate: int,
    freq_min: float,
    freq_max: float,
    log_freq: bool = True,
    random_phase: bool = True,
    stereo_spread: float = 0.0,
    stereo_seed: int = 42,
) -> np.ndarray:
    num_bins, num_cols = image.shape
    num_samples = int(duration * sample_rate)
    t = np.arange(num_samples, dtype=np.float64) / sample_rate

    if log_freq:
        freqs = np.logspace(
            np.log10(freq_min), np.log10(freq_max), num_bins
        )
    else:
        freqs = np.linspace(freq_min, freq_max, num_bins)

    col_times = np.linspace(0, duration, num_cols)

    stereo = stereo_spread > 0
    if stereo:
        signal_l = np.zeros(num_samples, dtype=np.float64)
        signal_r = np.zeros(num_samples, dtype=np.float64)
    else:
        signal = np.zeros(num_samples, dtype=np.float64)

    rng = np.random.default_rng(stereo_seed)

    for i in range(num_bins):
        row = image[num_bins - 1 - i, :]

        if np.max(row) == 0:
            continue

        if num_cols >= 4:
            interp = interp1d(col_times, row, kind="cubic", fill_value="extrapolate")
        else:
            interp = interp1d(col_times, row, kind="linear", fill_value="extrapolate")
        envelope = interp(t)
        envelope = np.clip(envelope, 0, 1)

        phase = rng.uniform(0, 2 * np.pi) if random_phase else 0.0
        tone = envelope * np.sin(2 * np.pi * freqs[i] * t + phase)

        if stereo:
            # Random pan: 0 = full left, 1 = full right, 0.5 = center
            # stereo_spread controls how far from center pans can go
            pan = 0.5 + rng.uniform(-0.5, 0.5) * stereo_spread
            signal_l += tone * np.sqrt(1 - pan)
            signal_r += tone * np.sqrt(pan)
        else:
            signal += tone

        print(f"\r  synthesizing: {i + 1}/{num_bins} frequency bins", end="", file=sys.stderr)

    print(file=sys.stderr)

    if stereo:
        peak = max(np.max(np.abs(signal_l)), np.max(np.abs(signal_r)))
        if peak > 0:
            signal_l /= peak
            signal_r /= peak
        return np.column_stack([signal_l, signal_r])
    else:
        peak = np.max(np.abs(signal))
        if peak > 0:
            signal /= peak
        return signal


def save_wav(signal: np.ndarray, path: str, sample_rate: int) -> None:
    import wave

    if signal.ndim == 2:
        nchannels = 2
        num_samples = signal.shape[0]
        # Explicitly interleave: [L0, R0, L1, R1, ...]
        interleaved = np.empty(num_samples * 2, dtype=np.float64)
        interleaved[0::2] = signal[:, 0]
        interleaved[1::2] = signal[:, 1]
        pcm = np.clip(interleaved * 32767, -32768, 32767).astype(np.int16)
    else:
        nchannels = 1
        pcm = np.clip(signal * 32767, -32768, 32767).astype(np.int16)

    with wave.open(path, "wb") as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def save_spectrogram(
    signal: np.ndarray,
    path: str,
    sample_rate: int,
    freq_min: float,
    freq_max: float,
    log_freq: bool = True,
) -> None:
    # Mix to mono for spectrogram if stereo
    if signal.ndim == 2:
        mono = signal.mean(axis=1)
    else:
        mono = signal

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")

    nfft = 2048
    ax.specgram(
        mono,
        NFFT=nfft,
        Fs=sample_rate,
        noverlap=nfft * 3 // 4,
        cmap="inferno",
        scale="dB",
        vmin=-120,
        vmax=0,
    )

    if log_freq:
        ax.set_yscale("log")

    ax.set_ylim(freq_min, freq_max)
    ax.set_xlim(0, len(mono) / sample_rate)
    ax.axis("off")

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(path, dpi=150, bbox_inches="tight", pad_inches=0, facecolor="black")
    plt.close(fig)
