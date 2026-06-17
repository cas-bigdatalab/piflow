import os
import time
import uuid
import requests
from pathlib import Path


class MineruException(Exception):
    pass


class MineruClient:
    """
    MinerU API Client

    https://mineru.net
    """

    BASE_URL = "https://mineru.net/api/v4"

    def __init__(
        self,
        api_key: str,
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.timeout = timeout

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ==========================================================
    # URL解析
    # ==========================================================

    def parse_url(
        self,
        file_url: str,
        model_version: str = "vlm",
        language: str = "ch",
        enable_formula: bool = True,
        enable_table: bool = True,
        is_ocr: bool = False,
        page_ranges: str | None = None,
        callback: str | None = None,
        data_id: str | None = None,
    ):
        payload = {
            "url": file_url,
            "model_version": model_version,
            "language": language,
            "enable_formula": enable_formula,
            "enable_table": enable_table,
            "is_ocr": is_ocr,
        }

        if page_ranges:
            payload["page_ranges"] = page_ranges

        if callback:
            payload["callback"] = callback

        if data_id:
            payload["data_id"] = data_id

        resp = requests.post(
            f"{self.BASE_URL}/extract/task",
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )

        self._check_response(resp)

        return resp.json()

    # ==========================================================
    # 上传文件
    # ==========================================================

    def parse_file(
        self,
        file_path: str,
        model_version: str = "vlm",
        data_id: str | None = None,
    ):
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(file_path)

        if data_id is None:
            data_id = uuid.uuid4().hex

        upload_info = self.create_upload_url(
            file_name=file_path.name,
            model_version=model_version,
            data_id=data_id,
        )

        upload_url = upload_info["data"]["file_urls"][0]

        with open(file_path, "rb") as f:
            upload_resp = requests.put(
                upload_url,
                data=f,
                timeout=600,
            )

        upload_resp.raise_for_status()

        return upload_info

    # ==========================================================
    # 获取上传地址
    # ==========================================================

    def create_upload_url(
        self,
        file_name: str,
        data_id: str,
        model_version: str = "vlm",
    ):
        payload = {
            "files": [
                {
                    "name": file_name,
                    "data_id": data_id,
                }
            ],
            "model_version": model_version,
        }

        resp = requests.post(
            f"{self.BASE_URL}/file-urls/batch",
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )

        self._check_response(resp)

        return resp.json()

    # ==========================================================
    # 批量解析
    # ==========================================================

    def batch_parse(
        self,
        files: list[dict],
        model_version: str = "vlm",
    ):
        payload = {
            "files": files,
            "model_version": model_version,
        }

        resp = requests.post(
            f"{self.BASE_URL}/extract/task/batch",
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )

        self._check_response(resp)

        return resp.json()

    # ==========================================================
    # 查询任务
    # ==========================================================

    def get_task(self, task_id: str):
        resp = requests.get(
            f"{self.BASE_URL}/extract/task/{task_id}",
            headers=self.headers,
            timeout=self.timeout,
        )

        self._check_response(resp)

        return resp.json()

    # ==========================================================
    # 等待任务完成
    # ==========================================================

    def wait_task(
        self,
        task_id: str,
        interval: int = 5,
        timeout: int = 1800,
    ):
        start = time.time()

        while True:
            result = self.get_task(task_id)

            status = (
                result.get("data", {})
                .get("status")
            )

            if status in [
                "success",
                "completed",
                "finished",
            ]:
                return result

            if status in [
                "failed",
                "error",
            ]:
                raise MineruException(
                    f"task failed: {task_id}"
                )

            if time.time() - start > timeout:
                raise TimeoutError(
                    f"task timeout: {task_id}"
                )

            time.sleep(interval)

    # ==========================================================
    # 下载结果
    # ==========================================================

    def download_result(
        self,
        download_url: str,
        save_path: str,
    ):
        save_path = Path(save_path)

        resp = requests.get(
            download_url,
            stream=True,
            timeout=600,
        )

        resp.raise_for_status()

        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                if chunk:
                    f.write(chunk)

        return str(save_path)

    # ==========================================================
    # 一键解析
    # ==========================================================

    def parse_and_wait(
        self,
        file_url: str,
        **kwargs,
    ):
        task = self.parse_url(
            file_url=file_url,
            **kwargs,
        )

        task_id = (
            task["data"]["task_id"]
        )

        return self.wait_task(task_id)

    # ==========================================================
    # 工具函数
    # ==========================================================

    @staticmethod
    def _check_response(resp):
        try:
            resp.raise_for_status()
        except Exception as e:
            raise MineruException(
                f"http error: {e}"
            )

        try:
            data = resp.json()
        except Exception:
            return

        if isinstance(data, dict):
            code = data.get("code")

            if code not in (0, 200, None):
                raise MineruException(
                    data.get("msg", "unknown error")
                )