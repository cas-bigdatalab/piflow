from enum import Enum


class TemplatePublisher(str, Enum):
    """workflow_template.publisher 来源"""

    PERSONAL = "个人创建"
    ORG_SHARED = "组织共享"
    OFFICIAL_COMMUNITY = "官方社区"


class TemplateTag(str, Enum):
    """workflow_template.tags 标签"""

    COLLECTION = "采集"
    FILTERING = "过滤"
    SCREENING = "筛选"
    VALIDATION = "校验"
    ENHANCEMENT = "增强"
    COMPUTATION = "计算"
    STATISTICS = "统计"
    ANNOTATION = "标注"
    STANDARDIZATION = "标准化"
    DEDUPLICATION = "去重"
    QUALITY_INSPECTION = "质检"
    PROOFREADING = "校对"
    QUALITY_CONTROL = "质控"
    FUSION = "融合"
    SPLITTING = "切分"
    REPORT_GENERATION = "报告生成"


TEMPLATE_PUBLISHER_VALUES = [item.value for item in TemplatePublisher]
TEMPLATE_TAG_VALUES = [item.value for item in TemplateTag]


def validate_tags(tags: list) -> bool:
    if not tags:
        return True
    return all(tag in TEMPLATE_TAG_VALUES for tag in tags)
