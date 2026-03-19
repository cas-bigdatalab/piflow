import requests

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64


def aes_encrypt(plain_text):

    KEY = "ABCDEFGHIJKL_key"
    # IV偏移量 (需与前端/后端一致)
    IV = "ABCDEFGHIJKLM_iv"

    if not plain_text:
        return None

    # 创建cipher对象
    cipher = AES.new(
        key=KEY.encode('utf-8'),
        mode=AES.MODE_CBC,
        iv=IV.encode('utf-8')
    )

    # 加密并添加填充
    encrypted = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))

    # Base64编码
    return base64.b64encode(encrypted).decode('utf-8')


def loginIn(username, password):
    url = "http://conet.rdcn.link/piflow-web/jwtLogin"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh",
        "Authorization": "Bearer false",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "http://conet.rdcn.link",
        "Referer": "http://conet.rdcn.link/login",
        "User-Agent": "Mozilla/5.0"
    }

    data = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)

        if response.status_code != 200:
            raise Exception(f"登录失败，HTTP状态码: {response.status_code}")

        result = response.json()

        # 判断业务是否成功
        if result.get("code") == 200:
            token = result.get("token")
            if not token:
                raise Exception("登录成功但未返回token")
            return token
        else:
            raise Exception(f"登录失败: {result.get('errorMsg')}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"请求异常: {e}")


def run_flow(token, flow_json):
    url = "http://conet.rdcn.link/piflow-web/flow/startFlowByFlowJson"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh",
        "Authorization": f"Bearer {token}",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "flowJson": flow_json
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            verify=False,
            timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"调用 runFlow 失败，HTTP状态码: {response.status_code}")

        result = response.json()

        # 根据实际接口返回判断（有的接口没有 code，需要你确认）
        if result.get("code") == 200 or "success" in str(result).lower():
            return result
        else:
            raise Exception(f"运行 flow 失败: {result}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"请求异常: {e}")


if __name__ == "__main__":

    username = "netuser1"
    password = "cnic$@Nzlh1"

    flow_json = r'''
{
  "flow" : {
    "executorNumber" : "1",
    "driverMemory" : "1g",
    "executorMemory" : "1g",
    "executorCores" : "1",
    "paths" : [ {
      "inport" : "tfw_port",
      "from" : "榆林市地理坐标信息文件",
      "to" : "geotrans_main",
      "outport" : ""
    }, {
      "inport" : "gully_slop_port",
      "from" : "gully_slop",
      "to" : "hydro_susceptibility",
      "outport" : "gully_slop_port"
    }, {
      "inport" : "label_port",
      "from" : "geotrans_main",
      "to" : "overlap_dam_select",
      "outport" : "detect_geotrans_port"
    }, {
      "inport" : "suscep_hdyro_port",
      "from" : "hydro_susceptibility",
      "to" : "overlap_dam_select",
      "outport" : "suscep_hdyro_port"
    }, {
      "inport" : "demPort",
      "from" : "2019年中国榆林市30m数字高程数据集",
      "to" : "gully_slop",
      "outport" : ""
    }, {
      "inport" : "yolov7_port",
      "from" : "榆林市卫星遥感数据集图像分割文件",
      "to" : "geotrans_main",
      "outport" : ""
    }, {
      "inport" : "recordPort",
      "from" : "2019年中国榆林市沟道信息",
      "to" : "gully_slop",
      "outport" : ""
    }, {
      "inport" : "",
      "from" : "overlap_dam_select",
      "to" : "结果存储",
      "outport" : "damDetect_port"
    }, {
      "inport" : "geoentropy_port",
      "from" : "地貌信息熵",
      "to" : "hydro_susceptibility",
      "outport" : ""
    } ],
    "name" : "协同智能编排",
    "stops" : [ {
      "customizedProperties" : { },
      "dataCenter" : "http://210.77.77.148:7001",
      "name" : "结果存储",
      "uuid" : "b9a4ff9213804cfa84017349cff681c5",
      "bundle" : "cn.piflow.bundle.csv.CsvSave",
      "properties" : {
        "csvSavePath" : "/work/ncdc/out/result/",
        "saveMode" : "append",
        "partition" : "1",
        "delimiter" : ",",
        "header" : "false"
      }
    }, {
      "customizedProperties" : { },
      "dataSourceId" : "b60d8e7d3b6fba85a12ad4d5251d08ea",
      "dataCenter" : "http://210.77.77.148:7001",
      "registerId" : "CSTR:33113.11.KNoAEF5k2vZJW7",
      "sourceType" : "COLLABORATIVE_NETWORK",
      "webAddress" : "http://210.77.77.148:7001",
      "name" : "地貌信息熵",
      "uuid" : "c12f9dae027f4c63b54d936d73382279",
      "bundle" : "cn.piflow.bundle.csv.CsvParser",
      "properties" : { }
    }, {
      "customizedProperties" : { },
      "dataCenter" : "http://210.77.77.148:7001",
      "registerId" : "CSTR:33113.11.bcE2SaomXIS5s2",
      "name" : "gully_slop",
      "uuid" : "7f494083465b4e819b58a2d79002bd29",
      "bundle" : "cn.piflow.bundle.script.DockerExecute",
      "properties" : {
        "outports" : "gully_slop_port",
        "ymlContent" : "version: \"3\"\nservices:\n  gully_slop-53826edfc71f4685bb88d6c59f620a55:\n    image: \"registry.cn-hangzhou.aliyuncs.com/bigflow/geo_entropy.py-1672748449294:3.7.5\"\n    extra_hosts:bigflow_extra_hosts\n    hostname: gully_slop-53826edfc71f4685bb88d6c59f620a55\n    container_name: gully_slop-53826edfc71f4685bb88d6c59f620a55\n    environment:\n      - hdfs_url=bigflow_hdfs_url\n      - TZ=Asia/Shanghai\n    volumes:\n      - ../app:/app\n      - /data/nfs/:/data/nfs/\n      - /data1/nfs:/data1/nfs\n      - /data/instdb:/data/instdb\n    command: python3 /pythonDir/gully_slop.py /demo.csv \n    network_mode: bridge\n",
        "inports" : "recordPort,demPort"
      }
    }, {
      "customizedProperties" : { },
      "dataCenter" : "http://210.77.77.148:7001",
      "registerId" : "CSTR:33113.11.kR1thvZQvEOF8f",
      "name" : "hydro_susceptibility",
      "uuid" : "81ad7c684f6a42308059e36758134e9b",
      "bundle" : "cn.piflow.bundle.script.DockerExecute",
      "properties" : {
        "outports" : "suscep_hdyro_port",
        "ymlContent" : "version: \"3\"\nservices:\n  hydro_susceptibility-e6523ad41cb94446a70a8bca0698a44f:\n    image: \"registry.cn-hangzhou.aliyuncs.com/bigflow/geo_entropy.py-1672748449294:3.7.5\"\n    extra_hosts:bigflow_extra_hosts\n    hostname: hydro_susceptibility-e6523ad41cb94446a70a8bca0698a44f\n    container_name: hydro_susceptibility-e6523ad41cb94446a70a8bca0698a44f\n    environment:\n      - hdfs_url=bigflow_hdfs_url\n      - TZ=Asia/Shanghai\n    volumes:\n      - ../app:/app\n      - /data/nfs/:/data/nfs/\n      - /data1/nfs:/data1/nfs\n      - /data/instdb:/data/instdb\n    command: python3 /pythonDir/hydro_susceptibility.py /demo.csv \n    network_mode: bridge\n",
        "inports" : "gully_slop_port,geoentropy_port"
      }
    }, {
      "customizedProperties" : { },
      "dataSourceId" : "ba6150401be0165ec5e775965f6cb864",
      "dataCenter" : "http://124.16.184.77:7801",
      "registerId" : "CSTR:33113.11.qAVho1T4uVUzIC",
      "sourceType" : "COLLABORATIVE_NETWORK",
      "webAddress" : "http://124.16.184.77:7801",
      "name" : "榆林市地理坐标信息文件",
      "uuid" : "7ea0197cddd9445bad49e94e476e2a32",
      "bundle" : "cn.piflow.bundle.hdfs.HdfsPathToDf",
      "properties" : { }
    }, {
      "customizedProperties" : { },
      "dataSourceId" : "eeddd7533316dbe26146565c18c95505",
      "dataCenter" : "http://124.16.184.77:7801",
      "registerId" : "CSTR:33113.11.ZYlk4iEw9sxvKs",
      "sourceType" : "COLLABORATIVE_NETWORK",
      "webAddress" : "http://124.16.184.77:7801",
      "name" : "榆林市卫星遥感数据集图像分割文件",
      "uuid" : "c66d0303493f4968a4b696892fddf311",
      "bundle" : "cn.piflow.bundle.hdfs.HdfsPathToDf",
      "properties" : { }
    }, {
      "customizedProperties" : { },
      "dataCenter" : "http://124.16.184.77:7801",
      "registerId" : "CSTR:33113.11.UYfFpZa2Zoi9Dl",
      "name" : "geotrans_main",
      "uuid" : "0dd2af2f8aea43a9ab4be8b652b4b1aa",
      "bundle" : "cn.piflow.bundle.script.DockerExecute",
      "properties" : {
        "outports" : "detect_geotrans_port",
        "ymlContent" : "version: \"3\"\nservices:\n  geotrans_main-bd952e03da7947e3afc0e63ac8b32b75:\n    image: \"registry.cn-hangzhou.aliyuncs.com/bigflow/yolo:3.7.5\"\n    extra_hosts:bigflow_extra_hosts\n    hostname: geotrans_main-bd952e03da7947e3afc0e63ac8b32b75\n    container_name: geotrans_main-bd952e03da7947e3afc0e63ac8b32b75\n    environment:\n      - hdfs_url=bigflow_hdfs_url\n      - TZ=Asia/Shanghai\n    volumes:\n      - ../app:/app\n      - /data/nfs/:/data/nfs/\n      - /data1/nfs:/data1/nfs\n      - /data/instdb:/data/instdb\n    command: python3 /pythonDir/geotrans_main.py /demo.csv \n    network_mode: bridge\n",
        "inports" : "yolov7_port,tfw_port"
      }
    }, {
      "customizedProperties" : { },
      "dataSourceId" : "f03b9904530bb9a2a785f86eea032b5f",
      "dataCenter" : "http://210.77.77.148:7001",
      "registerId" : "CSTR:33113.11.iXX5KpqKwJzDLs",
      "sourceType" : "COLLABORATIVE_NETWORK",
      "webAddress" : "http://210.77.77.148:7001",
      "name" : "2019年中国榆林市沟道信息",
      "uuid" : "91688b4287084d7c8227cd266b583b9f",
      "bundle" : "cn.piflow.bundle.hdfs.HdfsPathToDf",
      "properties" : { }
    }, {
      "customizedProperties" : { },
      "dataCenter" : "http://210.77.77.148:7001",
      "registerId" : "CSTR:33113.11.YIox6ZS4Ab4IUT",
      "name" : "overlap_dam_select",
      "uuid" : "4894d94dcaa4493d8f35aca1110c9be8",
      "bundle" : "cn.piflow.bundle.script.DockerExecute",
      "properties" : {
        "outports" : "damDetect_port",
        "ymlContent" : "version: \"3\"\nservices:\n  overlap_dam_select-87e39f3cfb3f41debeb016c8a219567d:\n    image: \"registry.cn-hangzhou.aliyuncs.com/bigflow/geo_entropy.py-1672748449294:3.7.5\"\n    extra_hosts:bigflow_extra_hosts\n    hostname: overlap_dam_select-87e39f3cfb3f41debeb016c8a219567d\n    container_name: overlap_dam_select-87e39f3cfb3f41debeb016c8a219567d\n    environment:\n      - hdfs_url=bigflow_hdfs_url\n      - TZ=Asia/Shanghai\n    volumes:\n      - ../app:/app\n      - /data/nfs/:/data/nfs/\n      - /data1/nfs:/data1/nfs\n      - /data/instdb:/data/instdb\n    command: python3 /pythonDir/overlap_dam_select.py /demo.csv \n    network_mode: bridge\n",
        "inports" : "suscep_hdyro_port,label_port"
      }
    }, {
      "customizedProperties" : { },
      "dataSourceId" : "ed398be641d7aebeafe55128669b3915",
      "dataCenter" : "http://210.77.77.148:7001",
      "registerId" : "CSTR:33113.11.H4YNfhqKWY1WwG",
      "sourceType" : "COLLABORATIVE_NETWORK",
      "webAddress" : "http://210.77.77.148:7001",
      "name" : "2019年中国榆林市30m数字高程数据集",
      "uuid" : "e4d35e0a10e7449387d22ddafbc77b25",
      "bundle" : "cn.piflow.bundle.hdfs.HdfsPathToDf",
      "properties" : { }
    } ],
    "uuid" : "1f42db93dc094914b3fd4aece6f3990a"
  }
}
'''

    try:
        result = aes_encrypt(password)
        print(f"加密结果: {result}")
    except Exception as e:
        print(f"加密失败: {e}")

    token = loginIn(username,result)

    print(token)

    print(run_flow(token,flow_json))

