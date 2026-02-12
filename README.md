# aphex-maker

Embed an image into audio so it's visible in a spectrogram. Inspired by the Aphex Twin "Equation" technique.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

### 1. Prep an image (optional)

If your image has a busy background (e.g. a photo), strip it first:

```bash
aphex-prep photo.jpeg
```

This removes the background, crops to the subject, and outputs `photo_prep.png` with transparency. First run downloads the U2-Net model (~170MB).

Options:

```
aphex-prep photo.jpeg -o clean.png    # custom output path
aphex-prep photo.jpeg --padding 20    # more space around subject (default: 10)
aphex-prep photo.jpeg --no-crop       # keep original dimensions
```

### 2. Generate audio

```bash
aphex-maker photo_prep.png -o output.wav
```

This synthesizes a WAV file where the image is embedded in the frequency spectrum, and saves a spectrogram preview (`output_spectrogram.png`) so you can verify the result.

Options:

```
aphex-maker input.png -o out.wav --duration 5         # 5 second clip (default: 10)
aphex-maker input.png --freq-min 200 --freq-max 8000  # narrower freq range
aphex-maker input.png --freq-scale linear             # linear frequency mapping (default: log)
aphex-maker input.png --blur 1.5                      # anti-alias pixel boundaries
aphex-maker input.png --height 256 --width 512        # resize image before synthesis
aphex-maker input.png --noise-floor -60               # kill quiet pixels more aggressively (default: -80)
aphex-maker input.png --no-preview                    # skip spectrogram image
aphex-maker input.png --preview-path spec.png         # custom spectrogram path
aphex-maker input.png --sample-rate 48000             # custom sample rate (default: 44100)
```

### Full pipeline example

```bash
aphex-prep images/dog.jpeg
aphex-maker images/dog_prep.png -o dog.wav --duration 8 --blur 1
# check dog_spectrogram.png, then open dog.wav in Audacity/Spek
```

## How it works

- Image is converted to grayscale (alpha channel controls transparency → silence)
- Each row of pixels maps to a sine wave at a specific frequency (bottom = low, top = high)
- Each column maps to a point in time
- Pixel brightness = amplitude of that frequency at that time
- All sinusoids are summed together with random phases to avoid interference artifacts
- Result is normalized and written as 16-bit WAV

## Tips

- **Simpler images work better** — high-contrast silhouettes and line art produce the clearest spectrograms
- **Fewer frequency bins** (`--height 128`) = cleaner separation between tones
- **Log scale** (default) matches how most spectrogram viewers display, giving more detail in lower frequencies
- **Blur** helps smooth out pixel boundaries that can look jagged in the spectrogram
- Use a spectrogram viewer like [Spek](https://www.spek.cc/) or Audacity for the best verification
