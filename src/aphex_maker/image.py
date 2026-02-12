import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage import gaussian_filter


def load_image(
    path: str,
    height: int | None = None,
    width: int | None = None,
    blur: float = 0.0,
    noise_floor_db: float = -80.0,
    gamma: float = 1.0,
    noise_knee: float = 2.0,
    top_n: int | None = None,
    quantize: int | None = None,
) -> np.ndarray:
    img = ImageOps.exif_transpose(Image.open(path))

    # Extract alpha before converting to grayscale
    alpha = None
    if img.mode == "RGBA":
        alpha = np.array(img.split()[3], dtype=np.float64) / 255.0
    elif img.mode == "LA":
        alpha = np.array(img.split()[1], dtype=np.float64) / 255.0

    gray = np.array(img.convert("L"), dtype=np.float64) / 255.0

    if alpha is not None:
        gray *= alpha

    # Resize if requested
    if height is not None or width is not None:
        h = height or gray.shape[0]
        w = width or gray.shape[1]
        resized = Image.fromarray((gray * 255).astype(np.uint8))
        resized = resized.resize((w, h), Image.LANCZOS)
        gray = np.array(resized, dtype=np.float64) / 255.0

    if blur > 0:
        gray = gaussian_filter(gray, sigma=blur)

    # Gamma curve — values >1 push mid-tones toward silence
    if gamma != 1.0:
        gray = np.power(gray, gamma)

    # Soft noise floor — values below the threshold decay rapidly toward zero
    # instead of a hard cut. Uses a sigmoid-like curve centered at the threshold.
    floor = 10 ** (noise_floor_db / 20.0)
    mask = gray < floor
    gray[mask] *= (gray[mask] / floor) ** noise_knee

    # Quantize amplitudes to N discrete levels
    if quantize is not None and quantize > 1:
        gray = np.round(gray * (quantize - 1)) / (quantize - 1)

    # Keep only the N loudest frequency bins per time column
    if top_n is not None and top_n < gray.shape[0]:
        for col in range(gray.shape[1]):
            column = gray[:, col]
            if np.count_nonzero(column) > top_n:
                threshold = np.sort(column)[-top_n]
                column[column < threshold] = 0.0

    return gray
