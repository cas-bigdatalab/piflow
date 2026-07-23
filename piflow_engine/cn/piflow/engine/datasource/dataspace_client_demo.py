from piflow_engine.cn.piflow.engine.datasource import DataspaceClient

if __name__ == '__main__':
    client = DataspaceClient(
        base_url="http://10.0.90.47",
        app_id="614646",
        auth_code="ZGNkMWRlMjVhZjg4NDY4OTk0MmY0MDUwNzA1NGM3ZDU=",
    )

    spaces = client.list_spaces()
    space_id = client.get_space_id_by_name("空间导入相关任务优化测试空间")
    space_info = client.get_space_info(space_id)
    result = client.list_space_directory_by_name(
        "空间导入相关任务优化测试空间",
        ftp_user="15117913512@126.com",
        ftp_password="Cc289836256&",
        ftp_subpath=""
    )
    print(result)