from __future__ import annotations

import importlib.util
import io
import json
import sys
import tarfile
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "workspace"
    / "skills"
    / "numeric_metric_topn_summary"
    / "scripts"
    / "run_numeric_metric_topn_summary.py"
)
SPEC = importlib.util.spec_from_file_location("numeric_metric_topn_summary_script", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
METRIC_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = METRIC_MODULE
SPEC.loader.exec_module(METRIC_MODULE)


def test_hyphenated_corpus_property_fields_are_summarized(tmp_path: Path) -> None:
    values = ("2133 m²·g⁻¹", "402 m²·g⁻¹", "high specific surface area")
    archive_path = tmp_path / "corpus.tar"
    with tarfile.open(archive_path, "w") as archive:
        for index, value in enumerate(values, start=1):
            payload = {
                "annotation": [
                    {
                        "property": [
                            {
                                "property-name": "Surface_Area",
                                "property-value": value,
                            }
                        ]
                    }
                ]
            }
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            member = tarfile.TarInfo(f"knowledge/sample-{index}.json")
            member.size = len(encoded)
            archive.addfile(member, io.BytesIO(encoded))

    output_path = tmp_path / "summary.csv"
    result = METRIC_MODULE.summarize_numeric_metric(
        archive_path,
        output_path,
        dataset_label="supercap_electrode",
        metric="specific_surface_area",
        order="desc",
        top_n=30,
        target_unit="m2/g",
    )

    assert result["available_count"] == 2
    assert result["selected_count"] == 2
    assert result["mean_value"] == 1267.5
    assert result["min_value"] == 402.0
    assert result["max_value"] == 2133.0
    assert result["ignored_value_count"] == 1
    assert output_path.is_file()


def test_json_file_accepts_multiple_json_documents(tmp_path: Path) -> None:
    documents = (
        {
            "property-name": "Surface_Area",
            "property-value": "5 m²·g⁻¹",
        },
        {
            "property-name": "Surface_Area",
            "property-value": "3 m²·g⁻¹",
        },
    )
    input_path = tmp_path / "multiple-records.json"
    input_path.write_text(
        "\n".join(json.dumps(document, ensure_ascii=False) for document in documents),
        encoding="utf-8",
    )

    result = METRIC_MODULE.summarize_numeric_metric(
        input_path,
        tmp_path / "summary.csv",
        dataset_label="multi_document_json",
        metric="specific_surface_area",
        order="desc",
        top_n=30,
        target_unit="m2/g",
    )

    assert result["available_count"] == 2
    assert result["selected_count"] == 2
    assert result["mean_value"] == 4.0
    assert result["min_value"] == 3.0
    assert result["max_value"] == 5.0


def test_question_answer_corpus_extracts_and_deduplicates_text_metric(tmp_path: Path) -> None:
    samples = (("A", 45.41), ("B", 72.26), ("C", 10.0))
    documents = []
    for sample_name, reduced_bet in samples:
        description = (
            f"催化剂样本{sample_name}，还原后BET为{reduced_bet}平方米每克，"
            "反应后BET为999平方米每克，"
        )
        documents.extend(
            (
                {"question": description + "请问，CO转化率是多少？", "answer": "10mol%。"},
                {"question": description + "请问，产物选择性是多少？", "answer": "20mol%。"},
            )
        )

    input_path = tmp_path / "qa-corpus.json"
    input_path.write_text(
        "\n".join(json.dumps(document, ensure_ascii=False) for document in documents),
        encoding="utf-8",
    )

    result = METRIC_MODULE.summarize_numeric_metric(
        input_path,
        tmp_path / "qa-summary.csv",
        dataset_label="catalyst",
        metric="specific_surface_area",
        order="desc",
        top_n=2,
        target_unit="m2/g",
    )

    assert result["available_count"] == 3
    assert result["selected_count"] == 2
    assert round(result["mean_value"], 6) == 58.835
    assert result["min_value"] == 45.41
    assert result["max_value"] == 72.26
