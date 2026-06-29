from __future__ import annotations

import json

import pytest

from cn.piflow.core.flow import FlowImpl
from cn.piflow.core.flow_bean import FlowBean
from cn.piflow.core.runner import Runner
from tests.support.test_stops import (
    MockForkStop,
    MockMergeStop,
    MockSinkStop,
    MockSourceStop,
    MockTransformStop,
)


def test_flow_bean_from_json_constructs_flow() -> None:
    flow_data = {
        "flow": {
            "uuid": "flow-001",
            "name": "demo-flow",
            "runMode": "RUN",
            "stops": [
                {
                    "uuid": "stop-001",
                    "name": "Source",
                    "bundle": "tests.support.test_stops.MockSourceStop",
                    "properties": {
                        "path": "${input_path}/users.csv",
                        "format": "csv",
                    },
                    "customizedProperties": {"owner": "qa"},
                },
                {
                    "uuid": "stop-002",
                    "name": "Sink",
                    "bundle": "tests.support.test_stops.MockSinkStop",
                    "properties": {
                        "output_path": "${output_path}/result.json",
                    },
                },
            ],
            "paths": [
                {
                    "from": "Source",
                    "outport": "",
                    "inport": "",
                    "to": "Sink",
                }
            ],
            "environmentVariable": {
                "${input_path}": "/tmp/input",
                "${output_path}": "/tmp/output",
            },
        }
    }

    flow_bean = FlowBean.from_dict(flow_data)

    assert flow_bean.uuid == "flow-001"
    assert flow_bean.name == "demo-flow"
    assert len(flow_bean.stops) == 2
    assert len(flow_bean.paths) == 1
    assert flow_bean.stops[0].properties["path"] == "/tmp/input/users.csv"
    assert flow_bean.stops[1].properties["output_path"] == "/tmp/output/result.json"

    flow = flow_bean.construct_flow()

    assert isinstance(flow, FlowImpl)
    assert flow.name == "demo-flow"
    assert flow.uuid == "flow-001"
    assert set(flow.get_stop_names()) == {"stop-001", "stop-002"}
    assert len(flow.edges) == 1
    assert flow.edges[0].stop_from == "stop-001"
    assert flow.edges[0].stop_to == "stop-002"
    assert flow.edges[0].out_port == ""
    assert flow.edges[0].in_port == ""

    source_stop = flow.get_stop("Source")
    sink_stop = flow.get_stop("Sink")

    assert isinstance(source_stop, MockSourceStop)
    assert isinstance(sink_stop, MockSinkStop)
    assert source_stop.path == "/tmp/input/users.csv"
    assert source_stop.format == "csv"
    assert source_stop.customized_properties == {"owner": "qa"}
    assert sink_stop.output_path == "/tmp/output/result.json"


def test_flow_bean_routes_paths_internally_by_stop_uuid() -> None:
    flow_data = {
        "flow": {
            "uuid": "flow-001",
            "name": "demo-flow",
            "runMode": "RUN",
            "stops": [
                {
                    "uuid": "source-uuid",
                    "name": "Source",
                    "bundle": "tests.support.test_stops.MockSourceStop",
                    "properties": {
                        "path": "source.csv",
                        "format": "csv",
                    },
                },
                {
                    "uuid": "sink-uuid",
                    "name": "Sink",
                    "bundle": "tests.support.test_stops.MockSinkStop",
                    "properties": {
                        "output_path": "result.csv",
                    },
                },
            ],
            "paths": [
                {
                    "from": "Source",
                    "outport": "",
                    "inport": "",
                    "to": "Sink",
                }
            ],
        }
    }

    flow = FlowBean.from_dict(flow_data).construct_flow()

    assert flow.get_stop_names() == ["source-uuid", "sink-uuid"]
    assert len(flow.edges) == 1
    assert flow.edges[0].stop_from == "source-uuid"
    assert flow.edges[0].stop_to == "sink-uuid"


def test_flow_bean_from_complex_json_runs_flow_and_routes_artifacts(capsys) -> None:
    flow_json = """
    {
        "flow": {
            "name": "Example",
            "uuid": "8a80d63f720cdd2301723a4e679e2457",
            "paths": [
                {"inport": "", "from": "8a80d63f720cdd2301723a4e67a7246d", "to": "8a80d63f720cdd2301723a4e67aa2477", "outport": ""},
                {"inport": "", "from": "8a80d63f720cdd2301723a4e67a42465", "to": "8a80d63f720cdd2301723a4e67a52467", "outport": "out1"},
                {"inport": "data2", "from": "8a80d63f720cdd2301723a4e67aa2477", "to": "8a80d63f720cdd2301723a4e67a92475", "outport": ""},
                {"inport": "", "from": "8a80d63f720cdd2301723a4e67a92475", "to": "8a80d63f720cdd2301723a4e67a42465", "outport": ""},
                {"inport": "data1", "from": "8a80d63f720cdd2301723a4e67a82470", "to": "8a80d63f720cdd2301723a4e67a92475", "outport": ""},
                {"inport": "", "from": "8a80d63f720cdd2301723a4e67a42465", "to": "8a80d63f720cdd2301723a4e67a1245f", "outport": "out3"},
                {"inport": "", "from": "8a80d63f720cdd2301723a4e67a42465", "to": "8a80d63f720cdd2301723a4e67a22461", "outport": "out2"}
            ],
            "stops": [
                {
                    "name": "CsvSave",
                    "bundle": "tests.support.test_stops.MockSinkStop",
                    "uuid": "8a80d63f720cdd2301723a4e67a52467",
                    "properties": {
                        "output_path": "csv-result"
                    },
                    "customizedProperties": {}
                },
                {
                    "name": "PutHiveMode",
                    "bundle": "tests.support.test_stops.MockSinkStop",
                    "uuid": "8a80d63f720cdd2301723a4e67a22461",
                    "properties": {
                        "output_path": "hive-result"
                    },
                    "customizedProperties": {}
                },
                {
                    "name": "CsvParser",
                    "bundle": "tests.support.test_stops.MockSourceStop",
                    "uuid": "8a80d63f720cdd2301723a4e67a82470",
                    "properties": {
                        "path": "csv-source",
                        "format": "csv"
                    },
                    "customizedProperties": {}
                },
                {
                    "name": "JsonSave",
                    "bundle": "tests.support.test_stops.MockSinkStop",
                    "uuid": "8a80d63f720cdd2301723a4e67a1245f",
                    "properties": {
                        "output_path": "json-result"
                    },
                    "customizedProperties": {}
                },
                {
                    "name": "XmlParser",
                    "bundle": "tests.support.test_stops.MockSourceStop",
                    "uuid": "8a80d63f720cdd2301723a4e67a7246d",
                    "properties": {
                        "path": "xml-source",
                        "format": "xml"
                    },
                    "customizedProperties": {}
                },
                {
                    "name": "SelectField",
                    "bundle": "tests.support.test_stops.MockTransformStop",
                    "uuid": "8a80d63f720cdd2301723a4e67aa2477",
                    "properties": {
                        "tag": "select"
                    },
                    "customizedProperties": {}
                },
                {
                    "name": "Merge",
                    "bundle": "tests.support.test_stops.MockMergeStop",
                    "uuid": "8a80d63f720cdd2301723a4e67a92475",
                    "properties": {
                        "inports": "data1,data2"
                    },
                    "customizedProperties": {}
                },
                {
                    "name": "Fork",
                    "bundle": "tests.support.test_stops.MockForkStop",
                    "uuid": "8a80d63f720cdd2301723a4e67a42465",
                    "properties": {
                        "outports": "out1,out3,out2"
                    },
                    "customizedProperties": {}
                }
            ]
        }
    }
    """

    flow_data = json.loads(flow_json)
    flow_bean = FlowBean.from_dict(flow_data)
    flow = flow_bean.construct_flow()

    with capsys.disabled():
        process = Runner.create().start(flow)
        process.await_termination()

    xml_parser = flow.get_stop("XmlParser")
    csv_parser = flow.get_stop("CsvParser")
    select_field = flow.get_stop("SelectField")
    merge = flow.get_stop("Merge")
    fork = flow.get_stop("Fork")
    csv_save = flow.get_stop("CsvSave")
    json_save = flow.get_stop("JsonSave")
    hive_save = flow.get_stop("PutHiveMode")

    assert xml_parser.last_output == "source::xml-source::xml"
    assert csv_parser.last_output == "source::csv-source::csv"
    assert select_field.last_output.startswith("select::")
    assert merge.last_output.startswith("merge::")
    assert len(fork.last_output) == 3
    assert any(item.startswith("fork::out1::") for item in fork.last_output)
    assert any(item.startswith("fork::out2::") for item in fork.last_output)
    assert any(item.startswith("fork::out3::") for item in fork.last_output)
    assert csv_save.last_input is not None
    assert json_save.last_input is not None
    assert hive_save.last_input is not None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
