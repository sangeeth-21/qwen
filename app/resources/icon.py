import struct
import zlib
from pathlib import Path


def _create_png(width: int, height: int, pixels: bytes) -> bytes:
    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    raw_data = b""
    for y in range(height):
        raw_data += b"\x00"
        raw_data += pixels[y * width * 4 : (y + 1) * width * 4]

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw_data))
        + chunk(b"IEND", b"")
    )


def generate_icon(size: int = 512) -> bytes:
    pixels = bytearray(size * size * 4)
    cx, cy = size / 2, size / 2
    radius = size * 0.42

    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            dx, dy = x - cx, y - cy
            dist = (dx * dx + dy * dy) ** 0.5

            edge = 12
            if dist > radius + edge:
                alpha = 0
            elif dist > radius - edge:
                alpha = int(255 * (radius + edge - dist) / (2 * edge))
            else:
                alpha = 255

            if alpha == 0:
                continue

            frac = (x / size + y / size) / 2
            r = int(35 + 90 * frac)
            g = int(55 + 110 * frac)
            b = int(200 + 55 * (1 - frac))

            inner_frac = dist / (radius * 0.75) if dist < radius * 0.75 else 1.0

            tx, ty = cx + radius * 0.45 * 0.707, cy + radius * 0.45 * 0.707
            tail_dist = ((x - tx) ** 2 + (y - ty) ** 2) ** 0.5

            if dist < radius * 0.75:
                if tail_dist < radius * 0.2 and dx > 0 and dy > 0:
                    r, g, b = min(255, r + 60), min(255, g + 60), min(255, b + 60)
                    alpha = min(255, alpha)
                elif inner_frac > 0.7:
                    r = min(255, int(r * 0.85))
                    g = min(255, int(g * 0.85))
                    b = min(255, int(b * 0.85))

            if y < size * 0.12 and dist < radius * 0.5:
                hl = 1 - (y / (size * 0.12))
                r = min(255, r + int(80 * hl))
                g = min(255, g + int(80 * hl))
                b = min(255, b + int(80 * hl))

            glow = max(0, 1 - dist / radius)
            if glow > 0.8:
                extra = int((glow - 0.8) * 200)
                r = min(255, r + extra)
                g = min(255, g + extra)
                b = min(255, b + extra)

            pixels[idx] = max(0, min(255, r))
            pixels[idx + 1] = max(0, min(255, g))
            pixels[idx + 2] = max(0, min(255, b))
            pixels[idx + 3] = max(0, min(255, alpha))

    return _create_png(size, size, bytes(pixels))


def save_icons():
    out = Path(__file__).parent
    for name, s in [("icon.png", 512), ("icon_small.png", 64)]:
        (out / name).write_bytes(generate_icon(s))
    print(f"Icons saved to {out}")


def get_icon_path() -> str:
    p = Path(__file__).parent / "icon.png"
    if not p.exists():
        save_icons()
    return str(p)


def get_small_icon_path() -> str:
    p = Path(__file__).parent / "icon_small.png"
    if not p.exists():
        save_icons()
    return str(p)


if __name__ == "__main__":
    save_icons()
