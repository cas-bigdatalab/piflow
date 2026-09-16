import json

from tools.excutor.json_convert_tool import convert_json_a_to_b


JSON_A = {
    "task": {
        "name": "森林每木调查数据清洗与排序",
        "description": "对上传的 CSV 文件进行空行清洗、空格清洗，并根据 fa0116 字段进行升序排序",
    },
    "nodes": [
        {
            "node_name": "输入文件",
            "skill_name": "source_stop",
            "params": {
                "file_path": "/temp/森林每木调查数据-blank-line-space.csv",
                "output": "",
            },
        },
        {
            "node_name": "空行清洗",
            "skill_name": "DC1_Blank_Line_Clean",
            "params": {
                "input": {
                    "source_node": "输入文件",
                    "source_param": "output",
                },
                "output": "",
            },
        },
        {
            "node_name": "空格清洗",
            "skill_name": "DC2_SpaceCleaning",
            "params": {
                "input_path": {
                    "source_node": "空行清洗",
                    "source_param": "output",
                },
                "output_path": "",
            },
        },
        {
            "node_name": "数据排序",
            "skill_name": "Pi_DataSorting",
            "params": {
                "input_path": {
                    "source_node": "空格清洗",
                    "source_param": "output_path",
                },
                "output_path": "",
                "id_field_name": "fa0116",
                "sort_order": "asc",
            },
        },
        {
            "node_name": "输出文件",
            "skill_name": "sink_stop",
            "params": {
                "input": {
                    "source_node": "数据排序",
                    "source_param": "output_path",
                },
                "path": "workspace/outputs/森林每木调查数据-cleaned-sorted.csv",
                "overwrite": True,
            },
        },
    ],
}
if __name__ == "__main__":
    json_b = convert_json_a_to_b(JSON_A)
    print(json.dumps(json_b, ensure_ascii=False, indent=2))
