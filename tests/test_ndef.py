from scripts.make_tag import main, ndef_uri_record, tlv_wrap, uri_payload


def test_uri_prefix_compression():
    assert uri_payload("https://cards.test/c/x") == b"\x04cards.test/c/x"
    assert uri_payload("https://www.a.io") == b"\x02a.io"
    assert uri_payload("ftp://x") == b"\x00ftp://x"


def test_short_record_layout():
    rec = ndef_uri_record("https://cards.test/c/rehan?src=nfc")
    payload = b"\x04cards.test/c/rehan?src=nfc"
    assert rec[0] == 0xD1 and rec[1] == 1 and rec[2] == len(payload) and rec[3:4] == b"U"
    assert rec[4:] == payload


def test_long_record_layout():
    rec = ndef_uri_record("https://x.io/" + "a" * 300)
    assert rec[0] == 0xC1 and int.from_bytes(rec[2:6], "big") == len(rec) - 7


def test_tlv_wrap():
    t = tlv_wrap(b"\x01\x02")
    assert t == b"\x03\x02\x01\x02\xfe"


def test_cli_writes_files(tmp_path):
    main(["rehan", "--base-url", "https://cards.test", "--out", str(tmp_path)])
    assert (tmp_path / "rehan.ndef").read_bytes() == ndef_uri_record("https://cards.test/c/rehan?src=nfc")
    assert (tmp_path / "rehan.tlv.hex").read_text().startswith("03 ")
    assert (tmp_path / "rehan-qr.png").read_bytes()[:4] == b"\x89PNG"
