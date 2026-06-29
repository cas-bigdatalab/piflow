from pathlib import Path


PIPELINE_PREVIEW = Path(__file__).resolve().parents[1] / "vue-web" / "src" / "components" / "PipelinePreview.tsx"


def test_pipeline_preview_has_mixed_text_json_extraction_support():
    text = PIPELINE_PREVIEW.read_text(encoding="utf-8")

    assert "function extractLastPipelineJsonFromMixedText" in text
    assert "不要先输出“先核对相关技能的参数定义”" not in text
    assert "for (let start = text.indexOf('{'); start !== -1; start = text.indexOf('{', start + 1))" in text
    assert "return { data: extracted.data, cleanedText: extracted.cleanedText.trim() };" in text
