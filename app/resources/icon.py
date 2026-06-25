import struct
import zlib
from pathlib import Path


def _create_png(width: int, height: int, pixels: bytes) -> bytes:
    """Create a PNG from raw RGBA pixel data."""
    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    raw_data = b""
    for y in range(height):
        raw_data += b"\x00"  # filter byte
        raw_data += pixels[y * width * 4 : (y + 1) * width * 4]

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw_data))
        + chunk(b"IEND", b"")
    )


def generate_icon(size: int = 512) -> bytes:
    """Generate a modern gradient 'Q' app icon."""
    pixels = bytearray(size * size * 4)
    cx, cy = size / 2, size / 2
    radius = size * 0.42

    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            dx, dy = x - cx, y - cy
            dist = (dx * dx + dy * dy) ** 0.5

            # Circular mask with soft edge
            edge = 8
            if dist > radius + edge:
                alpha = 0
            elif dist > radius - edge:
                alpha = int(255 * (radius + edge - dist) / (2 * edge))
            else:
                alpha = 255

            if alpha == 0:
                continue

            # Gradient from top-left to bottom-right
            frac = (x / size + y / size) / 2
            r = int(40 + 80 * frac)
            g = int(60 + 100 * frac)
            b = int(180 + 75 * (1 - frac))

            # Draw letter "Q" - a circle with a tail
            if dist < radius * 0.75:
                # Inner circle - white/transparent for the letter hollow
                inner_frac = max(0, (dist / (radius * 0.75)))
                # Draw a diagonal stroke for the Q tail
                tail_angle = 0.7  # radians
                tx, ty = cx + radius * 0.5, cy + radius * 0.5
                tail_dist = ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5
                if tail_dist < radius * 0.25:
                    r, g, b = 255, 255, 255
                    alpha = min(255, int(alpha * 1.2))
                elif inner_frac > 0.85:
                    # Ring highlight
                    r = min(255, r + 40)
                    g = min(255, g + 40)
                    b = min(255, b + 40)
                else:
                    # Outer ring area - keep gradient
                    pass

            # White highlight at top
            if y < size * 0.15 and dist < radius * 0.5:
                highlight = 1 - (y / (size * 0.15))
                r = min(255, r + int(60 * highlight))
                g = min(255, g + int(60 * highlight))
                b = min(255, b + int(60 * highlight))

            pixels[idx] = max(0, min(255, r))
            pixels[idx + 1] = max(0, min(255, g))
            pixels[idx + 2] = max(0, min(255, b))
            pixels[idx + 3] = max(0, min(255, alpha))

    return _create_png(size, size, bytes(pixels))


def save_icons():
    """Generate and save app icons at various sizes."""
    out = Path(__file__).parent
    # Main icon
    png_data = generate_icon(512)
    (out / "icon.png").write_bytes(png_data)
    # Smaller version for tray
    png_data_small = generate_icon(64)
    (out / "icon_small.png").write_bytes(png_data_small)
    print(f"Icons saved to {out}")


def get_icon_path() -> str:
    """Get path to the app icon PNG."""
    out = Path(__file__).parent / "icon.png"
    if not out.exists():
        save_icons()
    return str(out)


def get_small_icon_path() -> str:
    """Get path to the small app icon PNG."""
    out = Path(__file__).parent / "icon_small.png"
    if not out.exists():
        save_icons()
    return str(out)


if __name__ == "__main__":
    save_icons()
