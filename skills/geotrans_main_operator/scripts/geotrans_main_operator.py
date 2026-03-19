"""
Static operator emitter for geotrans_main.
"""


def emit_operator() -> dict:
    """
    Return the geotrans_main operator JSON fragment.
    """
    return {
        "node_type": "compute",
        "operator_name": "geotrans_main",
        "requires": [
            "榆林市地理坐标信息文件",
            "榆林市卫星遥感数据集图像分割文件",
        ],
        "produces": [
            "detect_geotrans_port",
        ],
        "stop": {
            "customizedProperties": {},
            "dataCenter": "http://124.16.184.77:7801",
            "registerId": "CSTR:33113.11.UYfFpZa2Zoi9Dl",
            "name": "geotrans_main",
            "uuid": "4761c58f9eb94de5ba96cb1d88bde279",
            "bundle": "cn.piflow.bundle.script.DockerExecute",
            "properties": {
                "outports": "detect_geotrans_port",
                "ymlContent": (
                    "version: \"3\"\\n"
                    "services:\\n"
                    "  geotrans_main-d92ffe57cc9b44d38f54d5f4ac52257f:\\n"
                    "    image: \"registry.cn-hangzhou.aliyuncs.com/bigflow/yolo:3.7.5\"\\n"
                    "    extra_hosts:bigflow_extra_hosts\\n"
                    "    hostname: geotrans_main-d92ffe57cc9b44d38f54d5f4ac52257f\\n"
                    "    container_name: geotrans_main-d92ffe57cc9b44d38f54d5f4ac52257f\\n"
                    "    environment:\\n"
                    "      - hdfs_url=bigflow_hdfs_url\\n"
                    "      - TZ=Asia/Shanghai\\n"
                    "    volumes:\\n"
                    "      - ../app:/app\\n"
                    "      - /data/nfs/:/data/nfs/\\n"
                    "      - /data1/nfs:/data1/nfs\\n"
                    "      - /data/instdb:/data/instdb\\n"
                    "    command: python3 /pythonDir/geotrans_main.py /demo.csv \\n"
                    "    network_mode: bridge\\n"
                ),
                "inports": "yolov7_port,tfw_port",
            },
        },
    }
