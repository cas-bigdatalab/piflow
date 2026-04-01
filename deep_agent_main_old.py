import os
import uuid
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from deepagents.backends.filesystem import FilesystemBackend

from infra.config_loader import get_settings


WORKSPACE_PATH = "workspace"


@tool
def exec_shell(command: str):
    """
    执行终端命令
    :param command:
    :return:
    """
    import subprocess
    import shlex
    import os

    root_dir = os.path.abspath(WORKSPACE_PATH)

    def convert_path(p: str):
        if p.startswith(f"/{WORKSPACE_PATH}"):
            rel = p.replace(f"/{WORKSPACE_PATH}", "").lstrip("/")
            return os.path.normpath(os.path.join(root_dir, rel))
        return p

    print(f"[exec_shell] {command}")

    # -------------------------
    # 1. 解析 cd && 结构
    # -------------------------
    cwd = None

    if "&&" in command:
        left, right = command.split("&&", 1)

        left_parts = shlex.split(left.strip())
        right_parts = shlex.split(right.strip())

        # 处理 cd
        if left_parts[0] == "cd":
            cwd = convert_path(left_parts[1])

        parts = right_parts
    else:
        parts = shlex.split(command)

    # -------------------------
    # 2. 路径转换
    # -------------------------
    parts = [convert_path(p) for p in parts]

    # -------------------------
    # 3. 自动 cwd（兜底）
    # -------------------------
    if cwd is None and parts[0] == "python" and len(parts) > 1:
        script_path = parts[1]
        cwd = os.path.dirname(script_path)

    print(f"[exec_shell] -> parts={parts}")
    print(f"[exec_shell] -> cwd={cwd}")

    # -------------------------
    # 4. 执行
    # -------------------------
    result = subprocess.run(
        parts,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=120
    )

    return f"""
    命令: {' '.join(parts)}
    cwd: {cwd}

    stdout:
    {result.stdout}

    stderr:
    {result.stderr}

    returncode: {result.returncode}
    """

# -----------------------------
# 3. 创建Deep Agent（核心：自动扫描Skills）
# -----------------------------
# 项目根目录
root_dir = os.path.abspath(".")
# 创建FilesystemBackend
# backend = LocalShellBackend(root_dir=root_dir,virtual_mode=True)
backend = FilesystemBackend(root_dir=root_dir,virtual_mode=True)
# Skill根目录（绝对路径）
# skills_root = os.path.abspath("skills")
skills_root = "/workspace/skills/"
# 初始化Checkpointer（Deep Agent必需）
checkpointer = InMemorySaver()

settings = get_settings()

llm_cfg = settings.llm
provider_name = llm_cfg.provider

provider_cfg = getattr(settings.providers, provider_name, None)

if provider_cfg is None:
    raise ValueError(f"Provider config not found: {provider_name}")

# -----------------------------
# 读取 API Key
# -----------------------------

api_key = None

if provider_cfg.api_key_env:
    api_key = os.getenv(provider_cfg.api_key_env)

if not api_key:
    api_key = os.getenv("LLM_API_KEY")

if not api_key:
    raise ValueError(
        f"Missing API key for provider '{provider_name}'. "
        f"Set {provider_cfg.api_key_env} or LLM_API_KEY."
    )

# -----------------------------
# 创建 LLM
# -----------------------------

model = ChatOpenAI(
    model=llm_cfg.model,
    temperature=llm_cfg.temperature,
    api_key=api_key,
    base_url=provider_cfg.base_url,
    max_retries=5,
    model_kwargs={
        "parallel_tool_calls": True
    }
)

agent = create_deep_agent(
    model=model,
    system_prompt=(
        "你是一个AI智能助手，你会根据用户输入的问题进行分析，并调用skill来辅助你完成具体的任务，优先匹配注册的skills\n\n"
        "如果 tool 报路径错误，你必须立即修正路径并重新调用 tool，而不是停止\n"
        "【文件规则】\n"
        "1. 输入文件默认在 /workspace/temp/\n"
        "2. 输出文件也必须输出到 /workspace/下\n"
        "3. 默认输出的文件不覆盖原文件"
    ),
    backend=backend,
    skills=[skills_root],
    tools=[exec_shell],
    interrupt_on={
        "write_file": False,  # Default: approve, edit, reject
        "read_file": False,  # No interrupts needed
        "edit_file": True    # Default: approve, edit, reject
    },
    checkpointer=checkpointer,  # Required!
    debug=True  # 开启详细日志，便于调试
)



# Example usage
if __name__ == "__main__":
    # Configuration for this conversation thread
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Ask for a SQL query
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "我想先对temp/森林每木调查数据-blank-line-space文件先进行空行清洗，再进行空格清洗，最终清洗完的文件输出到原文件同目录下（不要覆盖原文件）",
                }
            ]
        },
        config,
    )

    # Print the conversation
    for message in result["messages"]:
        if hasattr(message, 'pretty_print'):
            message.pretty_print()
        else:
            print(f"{message.type}: {message.content}")