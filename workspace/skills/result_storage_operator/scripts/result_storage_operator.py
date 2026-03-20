"""
Static operator emitter for result_storage.
"""


def emit_operator() -> dict:
    """
    Return the result storage operator JSON fragment.
    """
    return {
        "node_type": "sink",
        "operator_name": "结果存储",
        "requires": [
            "overlap_dam_select",
        ],
        "produces": [],
        "stop": {
            "customizedProperties": {},
            "dataCenter": "http://210.77.77.148:7001",
            "name": "结果存储",
            "uuid": "692a4287218e407784549dad16d34904",
            "bundle": "cn.piflow.bundle.csv.CsvSave",
            "properties": {
                "csvSavePath": "/work/ncdc/out/result/",
                "saveMode": "append",
                "partition": "1",
                "delimiter": ",",
                "header": "false",
            },
        },
    }
