"""
Static operator emitter for hydro_susceptibility.
"""


def emit_operator() -> dict:
    """
    Return the hydro_susceptibility operator JSON fragment.
    """
    return {
        "node_type": "compute",
        "operator_name": "hydro_susceptibility",
        "requires": [
            "gully_slop",
            "地貌信息熵",
        ],
        "produces": [
            "suscep_hdyro_port",
        ],
        "stop": {
            "customizedProperties": {},
            "dataCenter": "http://210.77.77.148:7001",
            "registerId": "CSTR:33113.11.kR1thvZQvEOF8f",
            "name": "hydro_susceptibility",
            "uuid": "248e7954472d4e6cbad9620dc374df58",
            "bundle": "cn.piflow.bundle.script.DockerExecute",
            "properties": {
                "outports": "suscep_hdyro_port",
                "ymlContent": (
                    "version: \"3\"\\n"
                    "services:\\n"
                    "  hydro_susceptibility-990a63aa384d4d1a850b81e765153995:\\n"
                    "    image: \"registry.cn-hangzhou.aliyuncs.com/bigflow/geo_entropy.py-1672748449294:3.7.5\"\\n"
                    "    extra_hosts:bigflow_extra_hosts\\n"
                    "    hostname: hydro_susceptibility-990a63aa384d4d1a850b81e765153995\\n"
                    "    container_name: hydro_susceptibility-990a63aa384d4d1a850b81e765153995\\n"
                    "    environment:\\n"
                    "      - hdfs_url=bigflow_hdfs_url\\n"
                    "      - TZ=Asia/Shanghai\\n"
                    "    volumes:\\n"
                    "      - ../app:/app\\n"
                    "      - /data/nfs/:/data/nfs/\\n"
                    "      - /data1/nfs:/data1/nfs\\n"
                    "      - /data/instdb:/data/instdb\\n"
                    "    command: python3 /pythonDir/hydro_susceptibility.py /demo.csv \\n"
                    "    network_mode: bridge\\n"
                ),
                "inports": "gully_slop_port,geoentropy_port",
            },
        },
    }
