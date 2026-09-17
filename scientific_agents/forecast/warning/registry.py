"""Pure catalogue lookup. Hub-backed catalogues can populate the same Settings contract."""
from .contracts import Scenario


class WarningRegistry:
    def __init__(self, settings):
        self.settings = settings
        self.scenarios = {s.case_id: s for s in settings.warning_scenarios}
        if len(self.scenarios) != len(settings.warning_scenarios):
            raise ValueError("预警场景的case_id不能重复")
        cases = {c.id: c for source in settings.sources for c in source.cases}
        if settings.risk_standard:
            for key, case in cases.items():
                scenario = self.get(case)
                # Explicit site rules (even disabled ones) take precedence.
                if scenario.use_standard and not scenario.rules:
                    rules = settings.risk_standard.rules_for(case.target, self.timing(key)[0])
                    if rules:
                        self.scenarios[key] = scenario.model_copy(update={"rules": rules})
        for key, scenario in self.scenarios.items():
            if key not in cases:
                raise ValueError(f"预警场景引用未知案例：{key}")
            variables = {v.name: v for v in [cases[key].target, *cases[key].covariates]}
            for rule in scenario.rules:
                for condition in rule.conditions:
                    linked = cases.get(condition.case_id) if condition.case_id else None
                    variable = (linked.target if linked and linked.target.name == condition.variable else None) if condition.case_id else variables.get(condition.variable)
                    if variable is None or variable.unit != condition.unit:
                        raise ValueError(f"规则变量或单位不匹配：{rule.id}")
                    if variable.semantics == "circular_degrees":
                        raise ValueError(f"风向等环形变量须先转换为向量或适用的派生指标：{rule.id}")
                    if variable.semantics == "rolling_total" and condition.statistic == "sum":
                        raise ValueError(f"滑动累计量不能再次求和：{rule.id}")
                    if condition.statistic == "sum" and condition.input_kind == "interval_total" and variable.aggregation != "sum":
                        raise ValueError(f"累计量变量必须使用sum聚合：{rule.id}")

    def get(self, case):
        return self.scenarios.get(case.id) or Scenario(case_id=case.id, version="legacy-1", area=case.label,
                                                      hazard_type="unspecified")

    def timing(self, case_id):
        s = self.scenarios.get(case_id)
        cfg = self.settings
        frequency = (s.frequency_minutes if s else None) or cfg.frequency_minutes
        # Directory capabilities retain their list shape; old scenario white lists no longer override the global range.
        hours = list(range(1, min(cfg.max_horizon_hours, 1024 * frequency // 60) + 1))
        return (frequency,
                (s.context_steps if s else None) or cfg.context_steps,
                hours)

    def allowed_hours(self, case_ids):
        sets = [set(self.timing(i)[2]) for i in case_ids]
        return sorted(set.intersection(*sets)) if sets else list(range(1, self.settings.max_horizon_hours + 1))

    def hours_description(self, case_ids):
        maximum = self.allowed_hours(case_ids)[-1]
        text = f"支持 1～{maximum} 个整数小时，1 天为 24 小时"
        if maximum < self.settings.max_horizon_hours:
            text += "；已按所选数据的采样间隔限制为最多 1024 个预测点"
        return text

    def validate_hours(self, hours, case_ids):
        if hours not in self.allowed_hours(case_ids):
            from ..feedback import ForecastError
            raise ForecastError("invalid_parameters", "预测时长超出允许范围：" + self.hours_description(case_ids) + "。")
