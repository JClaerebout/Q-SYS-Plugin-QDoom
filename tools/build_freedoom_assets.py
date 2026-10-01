"""Embed selected Freedoom 0.13.0 artwork in QDoom.qplug.

Usage: python3 tools/build_freedoom_assets.py /path/to/freedoom1.wad
Requires Pillow. Keep Freedoom's COPYING.txt and CREDITS.txt with distributions.
"""
from __future__ import annotations

import base64
import io
import pathlib
import struct
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
START = "-- BEGIN GENERATED FREEDOOM ASSETS\n"
END = "-- END GENERATED FREEDOOM ASSETS\n"
WALL_NAMES = ("STARTAN2", "STARG1", "TEKWALL1", "REDWALL1")
SPRITE_NAMES = ("TROOA1", "TROOB1", "TROOE1")
GUN_NAMES = ("SHTGA0", "SHTGB0")
CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUV"


def read_wad(path: pathlib.Path):
    data = path.read_bytes()
    tag, count, offset = struct.unpack_from("<4sii", data)
    if tag != b"IWAD":
        raise ValueError("Expected an IWAD")
    lumps = {}
    for i in range(count):
        position, length, raw_name = struct.unpack_from("<ii8s", data, offset + 16 * i)
        lumps[raw_name.rstrip(b"\0").decode("ascii")] = data[position : position + length]
    return lumps


def decode_patch(raw: bytes, palette):
    width, height, _, _ = struct.unpack_from("<hhhh", raw)
    if not 0 < width <= 1024 or not 0 < height <= 1024:
        raise ValueError("Invalid patch dimensions")
    image = Image.new("RGBA", (width, height))
    pixels = image.load()
    offsets = struct.unpack_from("<" + "I" * width, raw, 8)
    for x, position in enumerate(offsets):
        while raw[position] != 255:
            top, count = raw[position], raw[position + 1]
            position += 3
            for dy in range(count):
                if top + dy < height:
                    pixels[x, top + dy] = (*palette[raw[position + dy]], 255)
            position += count + 1
    return image


def decode_textures(raw: bytes, names, lumps, palette):
    count = struct.unpack_from("<I", raw)[0]
    offsets = struct.unpack_from("<" + "I" * count, raw, 4)
    found = {}
    for offset in offsets:
        name = raw[offset : offset + 8].rstrip(b"\0").decode("ascii")
        if name not in WALL_NAMES:
            continue
        width, height = struct.unpack_from("<hh", raw, offset + 12)
        patches = struct.unpack_from("<h", raw, offset + 20)[0]
        image = Image.new("RGBA", (width, height))
        for j in range(patches):
            x, y, patch_index, _, _ = struct.unpack_from("<hhhhh", raw, offset + 22 + j * 10)
            patch = decode_patch(lumps[names[patch_index]], palette)
            image.paste(patch, (x, y), patch)
        found[name] = image
    return found


def png_base64(image: Image.Image):
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return base64.b64encode(stream.getvalue()).decode("ascii")


def wall_data(image: Image.Image):
    resized = image.convert("RGB").resize((32, 32), Image.Resampling.BILINEAR)
    indexed = resized.quantize(colors=24, method=Image.Quantize.MEDIANCUT)
    raw_palette = indexed.getpalette()
    palette = []
    for i in range(24):
        r, g, b = raw_palette[i * 3 : i * 3 + 3]
        palette.append(f"#{r:02x}{g:02x}{b:02x}")
    rows = []
    for y in range(32):
        rows.append("".join(CHARS[indexed.getpixel((x, y))] for x in range(32)))
    return palette, rows


def generate(wad_path: pathlib.Path):
    lumps = read_wad(wad_path)
    palette = [tuple(lumps["PLAYPAL"][i : i + 3]) for i in range(0, 768, 3)]
    pnames_raw = lumps["PNAMES"]
    count = struct.unpack_from("<I", pnames_raw)[0]
    pnames = [pnames_raw[4 + 8 * i : 12 + 8 * i].rstrip(b"\0").decode("ascii") for i in range(count)]
    textures = {}
    for lump in ("TEXTURE1", "TEXTURE2"):
        if lump in lumps:
            textures.update(decode_textures(lumps[lump], pnames, lumps, palette))
    lines = [START.rstrip(), "-- Freedoom 0.13.0 derived graphics. See FREEDOOM-COPYING.txt and FREEDOOM-CREDITS.txt.", "local WALL_ART={"]
    for name in WALL_NAMES:
        colors, rows = wall_data(textures[name])
        lines.append("  {name=%r,palette={%s},rows={" % (name, ",".join('"' + color + '"' for color in colors)))
        lines.extend('    "' + row + '",' for row in rows)
        lines.append("  }},")
    lines.append("}")
    for table_name, names in (("MONSTER_ART", SPRITE_NAMES), ("GUN_ART", GUN_NAMES)):
        lines.append("local " + table_name + "={")
        for name in names:
            image = decode_patch(lumps[name], palette)
            lines.append('  {name="%s",w=%d,h=%d,png="%s"},' % (name, image.width, image.height, png_base64(image)))
        lines.append("}")
    lines.append(END.rstrip())
    block = "\n".join(lines) + "\n"
    plugin_path = ROOT / "QDoom.qplug"
    source = plugin_path.read_text()
    if START in source:
        before, rest = source.split(START, 1)
        _, after = rest.split(END, 1)
        source = before + block + after
    else:
        source = source.replace("if Controls then\n", block + "\nif Controls then\n", 1)
    plugin_path.write_text(source)
    print("Embedded", len(WALL_NAMES), "wall textures,", len(SPRITE_NAMES), "monster frames,", len(GUN_NAMES), "weapon frames;", len(block), "source bytes")


if __name__ == "__main__":
    generate(pathlib.Path(sys.argv[1]))
