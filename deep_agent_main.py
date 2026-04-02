import uuid

from agents.agent_factory import agent,memory_agent


def build_stage_preview(user_input: str) -> list[str]:
    text = (user_input or "").strip()
    if not text:
        return []

    if "分析" in text or "判识" in text or "识别" in text:
        stages = ["正在识别分析类型并匹配技能"]
        if "淤地坝" in text:
            stages.append("正在补齐上游算子与数据源角色")
        else:
            stages.append("正在补齐算子依赖并生成检索计划")
        stages.append("随后将检索协同数据源并组装 flow")
        return stages

    if "开始执行" in text or "运行流程" in text or "执行 flow" in text or "启动流水线" in text:
        return [
            "正在定位可执行的 flow",
            "随后将调用运行接口启动流水线",
        ]

    return []


USER_ID = "user_001"  # 👉 真实场景这里从登录态来

if __name__ == "__main__":

    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": USER_ID,
        }
    }

    printed_count = 0

    print("Deep Agent interactive CLI")
    print("Input 'exit' or 'quit' to stop.")

    while True:

        user_input = input("\nYou> ").strip()
        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            break

        stage_preview = build_stage_preview(user_input)
        if stage_preview:
            print("\nAgent>")
            for stage in stage_preview:
                print(f"[stage] {stage}")

        # result = agent.invoke(
        #     {
        #         "messages": [
        #             {
        #                 "role": "user",
        #                 "content": user_input,
        #             }
        #         ]
        #     },
        #     config,
        # )

        result = memory_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_input,
                    }
                ]
            },
            config,
        )

        if not stage_preview:
            print("\nAgent>")
        messages = result["messages"]
        new_messages = messages[printed_count:]
        for message in new_messages:
            if hasattr(message, "pretty_print"):
                message.pretty_print()
            else:
                print(f"{message.type}: {message.content}")
        printed_count = len(messages)
