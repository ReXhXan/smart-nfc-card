"""Generate the NFC payload (NDEF URI record) and a QR-code fallback for a card URL.

Usage:
    python -m scripts.make_tag rehan --base-url https://cards.example.com --out out/

Writes:
    <slug>.ndef      raw NDEF message (import into NFC Tools / write with any NTAG213/215/216 writer)
    <slug>.tlv.hex   NDEF wrapped in a Type 2 tag TLV, hex, for raw writers
    <slug>-qr.png    QR code pointing at the same card (fallback for phones without NFC)
"""
import argparse
from pathlib import Path

# NFC Forum URI Record Type Definition, abbreviation table (subset, longest match first)
URI_PREFIXES = {
    0x04: "https://", 0x03: "http://", 0x02: "https://www.", 0x01: "http://www.",
}


def uri_payload(url: str) -> bytes:
    for code, prefix in sorted(URI_PREFIXES.items(), key=lambda kv: -len(kv[1])):
        if url.startswith(prefix):
            return bytes([code]) + url[len(prefix):].encode("utf-8")
    return b"\x00" + url.encode("utf-8")


def ndef_uri_record(url: str) -> bytes:
    """Single well-known 'U' record. Uses the short-record (SR) form when payload < 256 bytes."""
    payload = uri_payload(url)
    tnf_well_known = 0x01
    flags = 0x80 | 0x40  # MB | ME
    if len(payload) < 256:
        header = bytes([flags | 0x10 | tnf_well_known, 1, len(payload)])
    else:
        header = bytes([flags | tnf_well_known, 1]) + len(payload).to_bytes(4, "big")
    return header + b"U" + payload


def tlv_wrap(ndef: bytes) -> bytes:
    """Type 2 tag TLV: 0x03 <len> <ndef> 0xFE (3-byte length form for >= 255 bytes)."""
    length = bytes([len(ndef)]) if len(ndef) < 0xFF else b"\xff" + len(ndef).to_bytes(2, "big")
    return b"\x03" + length + ndef + b"\xfe"


def card_url(base_url: str, slug: str, source: str) -> str:
    return f"{base_url.rstrip('/')}/c/{slug}?src={source}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--base-url", default=None, help="defaults to PUBLIC_BASE_URL from .env")
    ap.add_argument("--out", default="out")
    ap.add_argument("--no-qr", action="store_true")
    a = ap.parse_args(argv)
    if a.base_url is None:
        from app.config import get_settings
        a.base_url = get_settings().public_base_url

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    nfc_url = card_url(a.base_url, a.slug, "nfc")
    ndef = ndef_uri_record(nfc_url)
    (out / f"{a.slug}.ndef").write_bytes(ndef)
    (out / f"{a.slug}.tlv.hex").write_text(tlv_wrap(ndef).hex(" "))
    print(f"NFC URL : {nfc_url}\nNDEF    : {len(ndef)} bytes -> {out / (a.slug + '.ndef')}")

    if not a.no_qr:
        import qrcode
        qr_url = card_url(a.base_url, a.slug, "qr")
        qrcode.make(qr_url).save(out / f"{a.slug}-qr.png")
        print(f"QR      : {qr_url} -> {out / (a.slug + '-qr.png')}")


if __name__ == "__main__":
    main()
