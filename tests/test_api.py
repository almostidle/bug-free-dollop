import io
from app.services.demo_service import get_sample_presets


def test_health_and_demo_seed(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    seed = client.post("/api/demo/seed?reset=true")
    assert seed.status_code == 200
    assert seed.json()["total_documents"] == 4

    samples = client.get("/api/demo/samples")
    assert samples.status_code == 200
    assert len(samples.json()) == 4


def test_analyze_detects_patchwork_plagiarism_and_highlights_spans(client):
    client.post("/api/demo/seed?reset=true")
    presets = {p["id"]: p for p in get_sample_presets()}
    patchwork = presets["patchwork_plagiarism"]

    res = client.post(
        "/api/documents/analyze",
        data={
            "title": patchwork["title"],
            "text": patchwork["content"],
            "save_to_corpus": "true",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["saved"] is True
    assert body["plagiarism"]["is_plagiarized"] is True
    assert body["plagiarism"]["coverage_ratio"] > 0.4
    assert len(body["plagiarism"]["matches"]) >= 2
    assert len(body["plagiarism"]["highlight_spans"]) >= 2

    first_span = body["plagiarism"]["highlight_spans"][0]
    sliced = body["content"][first_span["start"]:first_span["end"]]
    assert len(sliced) > 20


def test_draft_mode_does_not_persist_document(client):
    client.post("/api/demo/seed?reset=true")
    before = len(client.get("/api/documents/history").json())

    presets = {p["id"]: p for p in get_sample_presets()}
    human = presets["original_human"]

    res = client.post(
        "/api/documents/analyze",
        data={
            "title": "Draft Essay",
            "text": human["content"],
            "save_to_corpus": "false",
        },
    )
    assert res.status_code == 200
    assert res.json()["saved"] is False
    assert res.json()["id"] == 0

    after = len(client.get("/api/documents/history").json())
    assert after == before


def test_file_upload_and_validation_errors(client):
    short_res = client.post("/api/documents/analyze", data={"text": "Too short."})
    assert short_res.status_code == 400

    bad_ext = client.post(
        "/api/documents/analyze",
        files={"file": ("essay.pdf", io.BytesIO(b"x" * 100), "application/pdf")},
    )
    assert bad_ext.status_code == 400

    valid_content = (
        "Distributed consensus algorithms require a majority quorum of replicas to agree "
        "on ordering before committing state machine transitions safely to disk."
    ).encode("utf-8")
    ok_upload = client.post(
        "/api/documents/analyze",
        files={"file": ("notes.md", io.BytesIO(valid_content), "text/markdown")},
    )
    assert ok_upload.status_code == 200
    assert ok_upload.json()["title"] == "notes.md"


def test_pairwise_compare_and_document_lifecycle(client):
    cmp_res = client.post(
        "/api/documents/compare",
        json={
            "source_text": (
                "Relational database management systems rely on B+Tree indexes to maintain "
                "sorted keys and support logarithmic point lookups and range scans."
            ),
            "suspect_text": (
                "In modern systems, relational database management systems rely on B+Tree "
                "indexes to maintain sorted keys and support logarithmic point lookups."
            ),
        },
    )
    assert cmp_res.status_code == 200
    assert cmp_res.json()["is_plagiarized"] is True
    assert len(cmp_res.json()["highlight_spans"]) >= 1

    created = client.post(
        "/api/documents/analyze",
        data={
            "title": "Temporary Doc",
            "text": (
                "Operating systems virtualize physical memory using multi-level page tables "
                "and translation lookaside buffers to accelerate address translation."
            ),
        },
    ).json()

    doc_id = created["id"]
    detail = client.get(f"/api/documents/{doc_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Temporary Doc"

    deleted = client.delete(f"/api/documents/{doc_id}")
    assert deleted.status_code == 200
    assert client.get(f"/api/documents/{doc_id}").status_code == 404


def test_config_update_validation_and_reset(client):
    configs = client.get("/api/config")
    assert configs.status_code == 200
    assert len(configs.json()) == 12

    updated = client.put("/api/config/shingle_size", json={"value": "6"})
    assert updated.status_code == 200
    assert updated.json()["value"] == "6"

    invalid = client.put("/api/config/shingle_size", json={"value": "not-an-int"})
    assert invalid.status_code == 400

    out_of_bounds = client.put("/api/config/plagiarism_threshold", json={"value": "2.5"})
    assert out_of_bounds.status_code == 400

    missing = client.put("/api/config/non_existent_key", json={"value": "1"})
    assert missing.status_code == 404

    reset = client.post("/api/config/reset")
    assert reset.status_code == 200
    shingle_cfg = next(c for c in reset.json() if c["key"] == "shingle_size")
    assert shingle_cfg["value"] == "5"
