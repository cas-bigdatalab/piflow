"""
Static operator emitter for overlap_dam_select.
"""


def emit_operator() -> dict:
    """
    Return the overlap_dam_select operator JSON fragment.
    """
    return {
        "node_type": "compute",
        "operator_name": "overlap_dam_select",
        "requires": [
            "geotrans_main",
            "hydro_susceptibility",
        ],
        "produces": [
            "damDetect_port",
        ],
        "stop": {
            "customizedProperties": {},
            "dataCenter": "http://210.77.77.148:7001",
            "registerId": "CSTR:33113.11.YIox6ZS4Ab4IUT",
            "name": "overlap_dam_select",
            "uuid": "25bfa4e81907497a97b7372ed94a18ce",
            "bundle": "cn.piflow.bundle.script.DockerExecute",
            "properties": {
                "outports": "damDetect_port",
                "ymlContent": (
                    "version: \"3\"\\n"
                    "services:\\n"
                    "  overlap_dam_select-20535db5a4db48d79d9334b4901d0152:\\n"
                    "    image: \"registry.cn-hangzhou.aliyuncs.com/bigflow/geo_entropy.py-1672748449294:3.7.5\"\\n"
                    "    extra_hosts:bigflow_extra_hosts\\n"
                    "    hostname: overlap_dam_select-20535db5a4db48d79d9334b4901d0152\\n"
                    "    container_name: overlap_dam_select-20535db5a4db48d79d9334b4901d0152\\n"
                    "    environment:\\n"
                    "      - hdfs_url=bigflow_hdfs_url\\n"
                    "      - TZ=Asia/Shanghai\\n"
                    "    volumes:\\n"
                    "      - ../app:/app\\n"
                    "      - /data/nfs/:/data/nfs/\\n"
                    "      - /data1/nfs:/data1/nfs\\n"
                    "      - /data/instdb:/data/instdb\\n"
                    "    command: python3 /pythonDir/overlap_dam_select.py /demo.csv \\n"
                    "    network_mode: bridge\\n"
                ),
                "inports": "suscep_hdyro_port,label_port",
            },
        },
    }

