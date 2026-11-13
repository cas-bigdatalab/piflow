"""Public links are derived from structured evidence, not model-authored text."""
from copy import deepcopy
import html

import pytest

from ..responses import delivery_links, delivery_link_suffix


def card(data, view="url", **extra):
    return {"result_id": "result-1", "title": "已交付结果", "view_type": view, "data": data, **extra}


@pytest.mark.parametrize("data", [
    "https://files.example/sample.csv",
    {"url": "https://files.example/sample.csv"},
    {"code": 200, "data": {"items": [{"downloadUrl": "https://files.example/sample.csv"}]}},
    {"resource": {"name": "sample.csv", "download_url": "https://files.example/sample.csv"}},
    {"links": [{"href": "https://files.example/sample.csv"}]},
])
def test_common_envelopes_and_link_fields(data):
    original = deepcopy(data)
    suffix = delivery_link_suffix("已取得结果。", [card(data)])
    assert "https://files.example/sample.csv" in suffix
    assert suffix.startswith("\n\n结果链接：\n\n- [")
    assert data == original


def test_explicit_links_and_standard_file_blocks_do_not_require_url_view():
    cards = [card({"download_url": "http://172.31.3.81:8086/file.csv"}, "table"),
        card({"previewUrl": "https://files.example/preview"}, "data"),
        card({}, "tool_result", content=[{"type": "file", "name": "file.txt", "url": "https://files.example/file.txt"},
            {"type": "resource_link", "name": "record", "uri": "https://files.example/record"}])]
    suffix = delivery_link_suffix("", cards)
    for url in ["http://172.31.3.81:8086/file.csv", "https://files.example/preview",
                "https://files.example/file.txt", "https://files.example/record"]:
        assert suffix.count(url) == 1


def test_unrelated_nested_data_and_private_fields_are_not_promoted_to_links():
    url = "https://files.example/result.csv"
    data = {"downloadUrl": url, "resource": {"downloadUrl": url},
        "data": [{"url": "https://source.example/row"}],
        "records": [{"downloadUrl": "https://source.example/record"}],
        "description": "See https://source.example/prose",
        "schema": {"downloadUrl": "https://source.example/schema"},
        "provenance": {"url": "https://source.example/provenance"},
        "secret": {"downloadUrl": "https://source.example/secret"},
        "serviceUrl": "https://source.example/internal"}
    suffix = delivery_link_suffix("已取得结果。", [card(data)])
    assert suffix.count(url) == 1 and "source.example" not in suffix
    assert delivery_link_suffix("已取得结果。", [card({"url": "https://source.example"}, "table")]) == ""


@pytest.mark.parametrize("url", [None, 123, "", "/files/result.csv", "file:///tmp/result.csv",
    "javascript:alert(1)", "data:text/plain,test", "https:///path", "http://user:secret@files.example/a",
    "http://@files.example/a", "https://files.example:65536/a", "https://files.example:bad/a",
    "https://files.example:0/a", "https://files.example/a\n", "https://files.example/a b",
    "https://files.example/<a>", "https://files.example/`a`", "https://files.example/\\a"])
def test_invalid_destinations_are_not_presented(url):
    assert delivery_link_suffix("已有说明。", [card({"downloadUrl": url})]) == ""


def test_signed_urls_are_preserved_and_labels_cannot_inject_markdown():
    url = "https://files.example/file(1).csv?signature=abc&copy=1&x=a%2Fb"
    cards = [card({"downloadUrl": url, "fileName": "[点击](javascript:evil)\n<script>x</script>"})]
    suffix = delivery_link_suffix("", cards)
    assert f"(<{html.escape(url, quote=False)}>)" in suffix
    assert "<script>" not in suffix and "\\[点击\\]" in suffix
    assert delivery_link_suffix(suffix, cards) == ""


@pytest.mark.parametrize("reply", [
    "下载：https://files.example/a.csv?token=abc",
    "[下载](https://files.example/a.csv?token=abc)",
    "[下载](<https://files.example/a.csv?token=abc>)",
    "https://files.example/a.csv?token=abc。",
])
def test_complete_existing_links_are_not_repeated(reply):
    assert delivery_link_suffix(reply, [card({"downloadUrl": "https://files.example/a.csv?token=abc"})]) == ""


def test_url_prefix_and_truncated_model_link_do_not_suppress_the_real_link():
    url = "https://files.example/a.csv?token=abc"
    for message in (f"[其他链接]({url}def)", "https://files.example/a.csv?token=ab…"):
        assert url in delivery_link_suffix(message, [card({"downloadUrl": url})])


def test_large_result_lists_keep_reply_bounded_without_truncating_urls():
    data = {"items": [{"name": f"file-{i}.csv", "downloadUrl": f"https://files.example/{i}.csv"}
                      for i in range(3000)]}
    suffix = delivery_link_suffix("", [card(data)])
    assert suffix.count("https://files.example/") == 20
    assert "更多链接请查看下方结果。" in suffix
    assert len(suffix)<12000


@pytest.mark.parametrize("fence", ["```", "~~~~", "````"])
@pytest.mark.parametrize("closed", [False, True])
def test_fenced_examples_do_not_hide_clickable_links_and_open_fences_are_closed(fence, closed):
    url = "https://files.example/result.csv"
    message = f"结果：\n{fence}text\n{url}"+(f"\n{fence}" if closed else "")
    suffix = delivery_link_suffix(message, [card({"downloadUrl": url})])
    assert f"(<{url}>)" in suffix
    if closed:
        assert suffix.startswith("\n\n结果链接：")
    else:
        assert suffix.startswith(f"\n{fence}\n\n结果链接：")
    assert delivery_link_suffix(message+suffix, [card({"downloadUrl": url})]) == ""


@pytest.mark.parametrize("message", [
    "[下载](https://files.example/result.csv",
    "[下载](<https://files.example/result.csv>",
    "[下载](<https://files.example/result.csv",
    "[下载](\nhttps://files.example/result.csv",
    "[下载](\n<https://files.example/result.csv>",
    "`https://files.example/result.csv`",
    "``https://files.example/result.csv``",
    "    https://files.example/result.csv",
])
def test_incomplete_links_and_code_do_not_suppress_a_clickable_delivery(message):
    url = "https://files.example/result.csv"
    suffix = delivery_link_suffix(message, [card({"downloadUrl": url})])
    assert f"(<{url}>)" in suffix
    assert delivery_link_suffix(message+suffix, [card({"downloadUrl": url})]) == ""
    # Independently verify rendered destinations with the CommonMark parser
    # available in the test environment; production has no parser dependency.
    parser = pytest.importorskip("markdown_it").MarkdownIt()
    links = [child.attrGet("href") for token in parser.parse(message+suffix)
             for child in (token.children or []) if child.type=="link_open"]
    assert url in links


def test_parent_and_resource_names_are_bound_to_their_own_urls_and_facts():
    first, second = "https://files.example/a.jsonl", "https://files.example/b.csv"
    values = delivery_links([card({"downloadUrl": first, "name": "a.jsonl", "format": "jsonl", "record_count": 10,
        "resource": {"downloadUrl": second, "name": "b.csv", "format": "csv", "record_count": 3}})])
    by_url = {item["url"]: item for item in values}
    assert by_url[first] == {"result_id": "result-1", "url": first, "label": "a.jsonl", "action": "下载",
                             "format": "jsonl", "record_count": 10}
    assert by_url[second] == {"result_id": "result-1", "url": second, "label": "b.csv", "action": "下载",
                              "format": "csv", "record_count": 3}


def test_mirrored_url_uses_the_resource_filename_once_instead_of_the_wrapper_title():
    url = "https://files.example/a.csv"
    values = delivery_links([card({"title": "导出结果", "downloadUrl": url,
        "resource": {"name": "a.csv", "downloadUrl": url, "format": "csv", "record_count": 2}})])
    assert len(values) == 1 and values[0]["label"] == "a.csv"
    assert values[0]["format"] == "csv" and values[0]["record_count"] == 2


@pytest.mark.parametrize("titles", [("条件一", "条件二"), ("导出文件", "导出文件")])
def test_identically_named_files_get_stable_labels_shared_by_the_reply(titles):
    cards = [card({"resource": {"downloadUrl": f"https://files.example/{i}.csv", "name": "dataset.csv"}},
        result_id=f"result-{i}", title=title) for i, title in enumerate(titles)]
    values = delivery_links(cards)
    assert len({item["label"] for item in values}) == 2
    assert [item["result_id"] for item in values] == ["result-0", "result-1"]
    suffix = delivery_link_suffix("已取得两个结果。", cards)
    assert all(item["label"] in suffix and item["url"] in suffix for item in values)
    assert "result-0" not in suffix and "result-1" not in suffix


def test_another_url_query_containing_the_destination_is_not_the_destination_itself():
    url = "https://files.example/result.csv"
    assert url in delivery_link_suffix(f"https://redirect.example/?next={url}", [card({"downloadUrl": url})])
