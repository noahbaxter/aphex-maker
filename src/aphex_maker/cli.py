import argparse
import sys
from pathlib import Path

from aphex_maker.config import get_synth_config
from aphex_maker.image import load_image
from aphex_maker.synth import synthesize, save_wav, save_spectrogram


def process_one(input_path: Path, output_path: Path, preview_path: Path | None, args):
    print(f"loading image: {input_path}", file=sys.stderr)
    image = load_image(
        str(input_path),
        height=args.height,
        width=args.width,
        blur=args.blur,
        noise_floor_db=args.noise_floor,
        gamma=args.gamma,
        noise_knee=args.noise_knee,
        top_n=args.top_n,
        quantize=args.quantize,
        invert=args.invert,
    )
    print(f"  image size: {image.shape[1]}x{image.shape[0]} (width x height)", file=sys.stderr)

    log_freq = not args.linear_freq
    print(f"  synthesizing audio: {args.duration}s @ {args.sample_rate}Hz", file=sys.stderr)
    print(f"  frequency range: {args.freq_min}-{args.freq_max}Hz ({'log' if log_freq else 'linear'})", file=sys.stderr)
    signal = synthesize(
        image,
        duration=args.duration,
        sample_rate=args.sample_rate,
        freq_min=args.freq_min,
        freq_max=args.freq_max,
        log_freq=log_freq,
        random_phase=args.random_phase,
        stereo_spread=args.stereo_spread,
        stereo_seed=args.stereo_seed,
    )

    print(f"  saving WAV: {output_path}", file=sys.stderr)
    save_wav(signal, str(output_path), args.sample_rate)

    if preview_path:
        print(f"  saving spectrogram: {preview_path}", file=sys.stderr)
        save_spectrogram(
            signal,
            str(preview_path),
            sample_rate=args.sample_rate,
            freq_min=args.freq_min,
            freq_max=args.freq_max,
            log_freq=log_freq,
        )


def main():
    cfg = get_synth_config()

    parser = argparse.ArgumentParser(
        prog="aphex-maker",
        description="Embed an image into audio so it's visible in a spectrogram.",
    )
    parser.add_argument("inputs", nargs="+", help="Input image(s) (PNG, JPEG, etc.)")
    parser.add_argument("-o", "--output", help="Output WAV path (only valid with single input)")
    parser.add_argument("--duration", type=float, default=cfg.get("duration", 10))
    parser.add_argument("--sample-rate", type=int, default=cfg.get("sample_rate", 44100))
    parser.add_argument("--freq-min", type=float, default=cfg.get("freq_min", 20))
    parser.add_argument("--freq-max", type=float, default=cfg.get("freq_max", 20000))
    parser.add_argument("--linear-freq", action="store_true", default=not cfg.get("log_freq", True))
    parser.add_argument("--blur", type=float, default=cfg.get("blur", 0))
    parser.add_argument("--noise-floor", type=float, default=cfg.get("noise_floor", -80))
    parser.add_argument("--gamma", type=float, default=cfg.get("gamma", 1.0))
    parser.add_argument("--noise-knee", type=float, default=cfg.get("noise_knee", 2.0))
    parser.add_argument("--top-n", type=int, default=cfg.get("top_n"))
    parser.add_argument("--quantize", type=int, default=cfg.get("quantize"))
    parser.add_argument("--invert", action=argparse.BooleanOptionalAction, default=cfg.get("invert", False))
    parser.add_argument("--height", type=int, default=cfg.get("height"))
    parser.add_argument("--width", type=int, default=cfg.get("width"))
    parser.add_argument("--random-phase", action=argparse.BooleanOptionalAction, default=cfg.get("random_phase", True))
    parser.add_argument("--stereo-spread", type=float, default=cfg.get("stereo_spread", 0.0))
    parser.add_argument("--stereo-seed", type=int, default=cfg.get("stereo_seed", 42))
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("--preview-path", help="Preview image path (only valid with single input)")

    args = parser.parse_args()

    if len(args.inputs) > 1 and (args.output or args.preview_path):
        print("error: -o/--output and --preview-path can only be used with a single input file", file=sys.stderr)
        sys.exit(1)

    for input_str in args.inputs:
        input_path = Path(input_str)
        if not input_path.exists():
            print(f"error: input file not found: {input_path}", file=sys.stderr)
            sys.exit(1)

        if args.output:
            output_path = Path(args.output)
        else:
            out_dir = input_path.parent / "out"
            out_dir.mkdir(exist_ok=True)
            output_path = out_dir / (input_path.stem + ".wav")
        preview_path = None
        if not args.no_preview:
            preview_path = Path(args.preview_path) if args.preview_path else output_path.with_name(output_path.stem + "_spectrogram.png")

        process_one(input_path, output_path, preview_path, args)

    print("done.", file=sys.stderr)
