def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_create_and_read(client, sample):
    r = client.post("/api/cards", json=sample)
    assert r.status_code == 201 and r.json()["url"] == "https://cards.test/c/rehan"
    card = client.get("/api/cards/rehan").json()
    assert card["full_name"] == "Rehan Khan" and card["taps"] == 0


def test_invalid_slug(client, sample):
    assert client.post("/api/cards", json=sample | {"slug": "Bad Slug!"}).status_code == 422


def test_missing_card_404(client):
    assert client.get("/api/cards/nobody").status_code == 404
    assert client.post("/api/cards/nobody/ask", json={"question": "hi"}).status_code == 404


def test_bio_generation_saves(client, sample):
    client.post("/api/cards", json=sample)
    r = client.post("/api/cards/rehan/bio", json={"max_words": 30})
    assert r.status_code == 200 and r.json()["bio"]
    assert client.get("/api/cards/rehan").json()["bio"] == r.json()["bio"]


def test_ask(client, sample):
    client.post("/api/cards", json=sample)
    r = client.post("/api/cards/rehan/ask", json={"question": "What skills does he have?"})
    assert "LangChain" in r.json()["answer"]


def test_vcard_download(client, sample):
    client.post("/api/cards", json=sample)
    r = client.get("/api/cards/rehan/vcard")
    assert r.headers["content-type"].startswith("text/vcard")
    assert "rehan.vcf" in r.headers["content-disposition"] and "FN:Rehan Khan" in r.text


def test_public_page_records_taps(client, sample):
    client.post("/api/cards", json=sample)
    r = client.get("/c/rehan?src=nfc", headers={"user-agent": "iPhone"})
    assert r.status_code == 200 and "Rehan Khan" in r.text
    client.get("/c/rehan?src=qr")
    client.get("/c/rehan?src=<script>")
    stats = client.get("/api/cards/rehan/analytics").json()
    assert stats["total"] == 3 and stats["by_source"] == {"nfc": 1, "qr": 1, "link": 1}
    assert client.get("/api/cards/rehan").json()["taps"] == 3


def test_html_escaped(client, sample):
    client.post("/api/cards", json=sample | {"full_name": "<b>x</b>"})
    assert "<b>x</b>" not in client.get("/c/rehan").text


def test_delete(client, sample):
    client.post("/api/cards", json=sample)
    assert client.delete("/api/cards/rehan").status_code == 204
    assert client.get("/api/cards/rehan").status_code == 404
