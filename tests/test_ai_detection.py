from app.services.ai_detection_service import _split_sentences, detect_ai_content
from app.services.demo_service import get_sample_presets


def test_split_sentences_handles_abbreviations_and_decimals():
    text = (
        "Dr. Smith et al. reported a 98.4% F1 score in Fig. 2 (e.g., on benchmark tasks). "
        "However, latency increased by 1.5x under load! Why did that happen?"
    )
    sentences = _split_sentences(text)
    assert len(sentences) == 3
    assert sentences[0].startswith("Dr. Smith et al.")
    assert "98.4%" in sentences[0]


def test_human_vs_ai_preset_separation(db_session):
    presets = {p["id"]: p for p in get_sample_presets()}

    human_res = detect_ai_content(presets["original_human"]["content"], db_session)
    ai_res = detect_ai_content(presets["ai_generated"]["content"], db_session)

    assert human_res["is_ai_generated"] is False
    assert ai_res["is_ai_generated"] is True
    assert ai_res["overall_score"] > human_res["overall_score"] + 0.35
    assert len(ai_res["sentences"]) >= 5
    assert set(ai_res["metrics"].keys()) == {
        "burstiness",
        "lexical_diversity",
        "repeated_ngrams",
        "avg_sentence_length",
        "punctuation_patterns",
    }
