"""Copy entry.png to the output directory after validating it.

The program runs with no network. It reads entry.png from the same
directory as this file, checks that it is a whole PNG of at most
1,048,576 bytes and exactly 1024 by 1024 pixels, then copies it to
MAKEFUN_OUTPUT_DIR (default /output) as entry.png.
"""

import os
import shutil
import struct
import sys
import zlib
from pathlib import Path

MAX_BYTES = 1048576
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def validate_png(data):
    if len(data) > MAX_BYTES:
        raise ValueError(f"entry.png is {len(data)} bytes, over {MAX_BYTES}")
    if len(data) < 8 or data[:8] != PNG_SIGNATURE:
        raise ValueError("entry.png is not a PNG file")
    offset = 8
    saw_ihdr = False
    saw_iend = False
    width = None
    height = None
    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        chunk_start = offset + 8
        chunk_end = chunk_start + length
        if chunk_end + 4 > len(data):
            raise ValueError(f"truncated PNG chunk {chunk_type!r}")
        chunk_data = data[chunk_start:chunk_end]
        stored_crc = struct.unpack(">I", data[chunk_end:chunk_end + 4])[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            raise ValueError(f"bad CRC in PNG chunk {chunk_type!r}")
        if chunk_type == b"IHDR":
            if length != 13:
                raise ValueError("bad IHDR length")
            width, height = struct.unpack(">II", chunk_data[:8])
            saw_ihdr = True
        if chunk_type == b"IEND":
            if chunk_end + 4 != len(data):
                raise ValueError("trailing data after PNG IEND chunk")
            saw_iend = True
            break
        offset = chunk_end + 4
    if not saw_ihdr:
        raise ValueError("PNG has no IHDR chunk")
    if not saw_iend:
        raise ValueError("PNG has no IEND chunk")
    if width != EXPECTED_WIDTH or height != EXPECTED_HEIGHT:
        raise ValueError(
            f"entry.png is {width}x{height}, expected "
            f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"
        )
    return width, height


def main():
    here = Path(__file__).resolve().parent
    source = here / "entry.png"
    data = source.read_bytes()
    validate_png(data)
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    destination = out_dir / "entry.png"
    shutil.copyfile(source, destination)
    print(f"wrote {destination} ({len(data)} bytes, 1024x1024)")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
