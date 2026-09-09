import json

from chemical import schedule_chemical_dag_file
from chemical import ChemicalConfig

chemical_config = ChemicalConfig.from_file("/Users/renhao/PycharmProjects/flow-deepagents-0408/chemical/config.example.yaml")
plan = schedule_chemical_dag_file(
    "/Users/renhao/PycharmProjects/flow-deepagents-0408/chemical/乙酸分子量子化学计算与波函数分析流水线.json",
    config=chemical_config,
)
json_str = json.dumps(plan.dag_definition, ensure_ascii=False)

scheduled_dag = plan.dag_definition