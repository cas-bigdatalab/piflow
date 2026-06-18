import argparse
import json
import os
import time
import requests

import sys
from pathlib import Path

# 获取当前脚本所在文件夹的上级（项目根目录）
root_path = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(root_path))

from infra.config_loader import get_settings

mineru_settings = get_settings()
api_key = mineru_settings.mineru.api_key

def download_file(url: str, output_path: str):
    resp = requests.get(
        url,
        stream=True,
        timeout=600
    )
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            if chunk:
                f.write(chunk)


def run_mineru_url_parse(
    url: str,
    output_zip: str,
    model_version: str = "vlm",
    poll_interval: int = 5,
    timeout: int = 1800,
):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    submit_resp = requests.post(
        "https://mineru.net/api/v4/extract/task",
        headers=headers,
        json={
            "url": url,
            "model_version": model_version,
        },
        timeout=60,
    )

    submit_resp.raise_for_status()

    submit_data = submit_resp.json()

    if submit_data.get("code") != 0:
        raise RuntimeError(
            f"submit failed: {submit_data}"
        )

    task_id = submit_data["data"]["task_id"]

    print(f"task_id={task_id}")

    start_time = time.time()

    while True:

        query_resp = requests.get(
            f"https://mineru.net/api/v4/extract/task/{task_id}",
            headers=headers,
            timeout=60,
        )

        query_resp.raise_for_status()

        result = query_resp.json()

        if result.get("code") != 0:
            raise RuntimeError(
                f"query failed: {result}"
            )

        data = result["data"]

        state = data["state"]

        print(f"state={state}")

        if state == "done":
            full_zip_url = data["full_zip_url"]

            os.makedirs(
                os.path.dirname(
                    os.path.abspath(output_zip)
                ),
                exist_ok=True
            )

            download_file(
                full_zip_url,
                output_zip
            )

            return {
                "task_id": task_id,
                "state": state,
                "zip_file": output_zip,
            }

        if state == "failed":
            raise RuntimeError(
                data.get(
                    "err_msg",
                    "mineru parse failed"
                )
            )

        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"task timeout: {task_id}"
            )

        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(
        description="MinerU URL Parse"
    )

    parser.add_argument(
        "--url",
        required=True,
        help="Document URL"
    )

    parser.add_argument(
        "--output_zip",
        required=True,
        help="Output zip path"
    )

    parser.add_argument(
        "--model_version",
        default="vlm"
    )

    parser.add_argument(
        "--poll_interval",
        type=int,
        default=5
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=1800
    )

    args = parser.parse_args()

    try:
        result = run_mineru_url_parse(
            url=args.url,
            output_zip=args.output_zip,
            model_version=args.model_version,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
        )

        print("__PYTHON_SUCCESS__")
        print(
            json.dumps(
                result,
                ensure_ascii=False
            )
        )

    except Exception as e:
        print("__PYTHON_ERROR__")
        print(str(e))
        raise


if __name__ == "__main__":
    main()