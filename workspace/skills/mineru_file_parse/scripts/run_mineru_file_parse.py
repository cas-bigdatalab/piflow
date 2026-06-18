import argparse
import json
import os
import time
import uuid
from pathlib import Path

import requests

from infra.config_loader import get_settings

mineru_settings = get_settings()
api_key = mineru_settings.mineru.api_key

def download_file(url: str, output_path: str):
    resp = requests.get(
        url,
        stream=True,
        timeout=600,
    )
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            if chunk:
                f.write(chunk)


def run_mineru_file_parse(
    file_path: str,
    output_zip: str,
    model_version: str = "vlm",
    poll_interval: int = 5,
    timeout: int = 1800,
):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            str(file_path)
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data_id = uuid.uuid4().hex

    create_resp = requests.post(
        "https://mineru.net/api/v4/file-urls/batch",
        headers=headers,
        json={
            "files": [
                {
                    "name": file_path.name,
                    "data_id": data_id,
                }
            ],
            "model_version": model_version,
        },
        timeout=60,
    )

    create_resp.raise_for_status()

    create_data = create_resp.json()

    if create_data.get("code") != 0:
        raise RuntimeError(
            f"create batch failed: {create_data}"
        )

    batch_id = create_data["data"]["batch_id"]

    upload_url = (
        create_data["data"]["file_urls"][0]
    )

    with open(file_path, "rb") as f:
        upload_resp = requests.put(
            upload_url,
            data=f,
            timeout=600,
        )

    upload_resp.raise_for_status()

    print(
        f"upload success, batch_id={batch_id}"
    )

    start_time = time.time()

    while True:

        query_resp = requests.get(
            f"https://mineru.net/api/v4/extract-results/batch/{batch_id}",
            headers={
                "Authorization": f"Bearer {api_key}"
            },
            timeout=60,
        )

        query_resp.raise_for_status()

        result = query_resp.json()

        if result.get("code") != 0:
            raise RuntimeError(
                f"query failed: {result}"
            )

        extract_result = (
            result["data"]["extract_result"]
        )

        if not extract_result:
            time.sleep(poll_interval)
            continue

        item = extract_result[0]

        state = item["state"]

        print(f"state={state}")

        if state == "done":

            full_zip_url = item["full_zip_url"]

            os.makedirs(
                os.path.dirname(
                    os.path.abspath(output_zip)
                ),
                exist_ok=True
            )

            download_file(
                full_zip_url,
                output_zip,
            )

            return {
                "batch_id": batch_id,
                "state": state,
                "zip_file": output_zip,
            }

        if state == "failed":
            raise RuntimeError(
                item.get(
                    "err_msg",
                    "mineru parse failed"
                )
            )

        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"batch timeout: {batch_id}"
            )

        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(
        description="MinerU File Parse"
    )

    parser.add_argument(
        "--file_path",
        required=True,
    )

    parser.add_argument(
        "--output_zip",
        required=True,
    )

    parser.add_argument(
        "--model_version",
        default="vlm",
    )

    parser.add_argument(
        "--poll_interval",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
    )

    args = parser.parse_args()

    try:
        result = run_mineru_file_parse(
            file_path=args.file_path,
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