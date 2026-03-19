"""
Static operator emitter for gully_slop.
"""


def emit_operator() -> dict:
    """
    Return the gully_slop operator JSON fragment.
    """
    return {
        "node_type": "compute",
        "operator_name": "gully_slop",
        "requires": [
            "2019年中国榆林市沟道信息",
            "2019年中国榆林市30m数字高程数据集",
        ],
        "produces": [
            "gully_slop_port",
        ],
        "stop": {
            "customizedProperties": {},
            "dataCenter": "http://210.77.77.148:7001",
            "registerId": "CSTR:33113.11.bcE2SaomXIS5s2",
            "name": "gully_slop",
            "uuid": "d3f326f448d9402180c7791040e7304e",
            "bundle": "cn.piflow.bundle.script.DockerExecute",
            "properties": {
                "outports": "gully_slop_port",
                "ymlContent": (
                    "version: \"3\"\\n"
                    "services:\\n"
                    "  gully_slop-b998d9d3872c4d34848db213fc8a8531:\\n"
                    "    image: \"registry.cn-hangzhou.aliyuncs.com/bigflow/geo_entropy.py-1672748449294:3.7.5\"\\n"
                    "    extra_hosts:bigflow_extra_hosts\\n"
                    "    hostname: gully_slop-b998d9d3872c4d34848db213fc8a8531\\n"
                    "    container_name: gully_slop-b998d9d3872c4d34848db213fc8a8531\\n"
                    "    environment:\\n"
                    "      - hdfs_url=bigflow_hdfs_url\\n"
                    "      - TZ=Asia/Shanghai\\n"
                    "    volumes:\\n"
                    "      - ../app:/app\\n"
                    "      - /data/nfs/:/data/nfs/\\n"
                    "      - /data1/nfs:/data1/nfs\\n"
                    "      - /data/instdb:/data/instdb\\n"
                    "    command: python3 /pythonDir/gully_slop.py /demo.csv \\n"
                    "    network_mode: bridge\\n"
                ),
                "inports": "recordPort,demPort",
            },
        },
    }
