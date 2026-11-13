"""Actual MCP catalogue discovery and scope bindings, without external I/O."""
import asyncio

import pytest

from ..capabilities import inputs, profile
from ..contracts import Server
from ..mcp import MCPGateway


@pytest.mark.parametrize("query,expected", [
    ("我想找化学化工相关的数据集", "search_corpus_datasets"),
    ("查看这个数据集的来源和作者详情", "get_corpus_dataset_detail"),
    ("查看这个数据集的目录结构和文件列表", "get_corpus_dataset_directory"),
    ("从数据集随机采样十条数据", "sample_corpus_dataset"),
    ("查看measurements.jsonl文件的schema", "get_corpus_file_schema"),
    ("查看已选文件的字段结构和类型", "get_corpus_file_schema"),
    ("读取另一个文件observations.json的样例记录", "read_corpus_file_records"),
])
def test_relevant_tool_is_loaded_from_real_descriptions_on_cold_and_warm_start(query, expected):
    from mcp_servers.corpus_mcp import mcp

    async def run():
        gateway = MCPGateway({"piflow-corpus": Server(mcp)})
        for _ in range(2):
            async with gateway.session() as tools:
                await tools.prepare(query)
                assert expected in {tool.name for tool in tools.loaded.values()}
                assert not tools.definition_errors.get("piflow-corpus")
                tool = next(tool for tool in tools.loaded.values() if tool.name==expected)
                from ..capabilities import profile
                contract = profile(tool).result
                description = tool.definition()["function"]["description"]
                assert description.startswith(tool.description + "\nQA outcome kind: " + (contract.kind if contract else tool.name))
                assert "Supported operations: " + ", ".join(profile(tool).routing.operations) in description
    asyncio.run(run())


def test_six_tools_keep_schema_and_record_inputs_separate():
    from mcp_servers.corpus_mcp import mcp

    async def run():
        async with MCPGateway({"piflow-corpus": Server(mcp)}).session() as tools:
            catalogue = {tool.name: tool for tool in await tools.tools("piflow-corpus")}
            assert set(catalogue)=={"search_corpus_datasets", "get_corpus_dataset_detail", "get_corpus_dataset_directory",
                "sample_corpus_dataset", "get_corpus_file_schema", "read_corpus_file_records",
                "query_pubchem_compounds", "export_dataset"}
            schema = catalogue["get_corpus_file_schema"]
            records = catalogue["read_corpus_file_records"]
            assert profile(schema).target_kind==profile(records).target_kind=="file"
            source = {"downloadUrl": "https://example.invalid/records.jsonl"}
            assert inputs(schema, {}, source)=={"download_url": source["downloadUrl"]}
            assert inputs(records, {}, source)=={
                "download_url": "https://example.invalid/records.jsonl", "size": 5}
            assert "size" not in schema.schema["properties"]
            assert schema.schema["required"]==records.schema["required"]==["download_url"]
    asyncio.run(run())
