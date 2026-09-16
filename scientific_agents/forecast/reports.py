"""Deterministic numerical reports, with an optional evidence-bound narrative.

Figure contract: distinguish forecasts from observations and show measured errors.
Quantitative panels; shared time axis; explicit forecast boundary and interval meaning.
Exports retain source values, Beijing-time labels, editable SVG text and model/data provenance.
"""
from html import escape
from pathlib import Path
import json
import threading
import re

import numpy as np
import pandas as pd

from .schema import ForecastResult
from .feedback import DISPLAY_ZONE, local_time
from .warning.analysis import analysis_lines, context_label, note_text

_render_lock = threading.Lock()


def display_times(text, year):
    """Format explicitly zoned evidence for reports without changing saved facts."""
    text = re.sub(r"(?<![\d-])(\d{2}-\d{2} \d{2}:\d{2}) UTC\b",
                  lambda m: local_time(f"{year}-{m[1]}+00:00")[5:] + " 北京时间", text)
    return re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})",
                  lambda m: local_time(m[0]) + " 北京时间", text)

INTERVAL = "q10–q90 是模型名义 80% 分位数范围，未经覆盖率校准，不表示准确率。"


def number(value) -> str:
    return "不可计算" if value is None else format(float(value), ".6g")


def pdf_text(text: str) -> str:
    # The bundled Chinese PDF font lacks superscript glyphs; preserve unit meaning.
    return escape(text).replace("³", "<super>3</super>").replace("²", "<super>2</super>")


def export_predictions(result, directory):
    rows = [{"case_id": s.case_id, "variable": s.variable, "unit": s.unit, **p.model_dump()}
            for s in result.series for p in s.predictions]
    frame = pd.DataFrame(rows)
    frame["timestamp"] = frame["timestamp"].map(lambda value: pd.Timestamp(value).tz_convert(DISPLAY_ZONE).isoformat())
    frame.to_csv(directory / "predictions.csv", index=False, encoding="utf-8-sig")


def build_facts(result: ForecastResult) -> dict[str, str]:
    from .warning.presentation import facts as warning_facts
    modes = {s.assessment.mode for s in result.series if s.assessment}
    facts = {"task": f"预测起点 {pd.Timestamp(result.task.origin).tz_convert('UTC').isoformat()}；预测时长 {result.task.horizon_hours} 小时。",
             "interval": INTERVAL,
             "scope": ("这是当前数据评估；无未来观测时不计算回测误差。" if modes == {"current"} else
                       "包含当前评估和历史回放，请分别查看每个案例的模式。" if len(modes) > 1 else
                       "这是历史时点回放；真实观测只用于回测评价，不进入预测输入。")}
    for i, series in enumerate(result.series):
        facts.update({f"series_{i}.{k}": v for k, v in warning_facts(series).items()})
        from .warning.insights import facts as insight_facts
        facts.update({f"series_{i}.{k}": v for k, v in insight_facts(series).items()})
    for i, series in enumerate(result.series):
        summary, metrics = series.summary, series.evaluation
        prefix = f"series_{i}"
        label = f"{series.label} / {series.variable}"
        if series.quality.get(series.variable, {}).get("constant_input"):
            facts[f"{prefix}.input_quality"] = f"{label}：本次历史输入恒定，缺少变化信息；需核查传感器及缺测编码，不能据此判断环境安全。"
        alignment = series.metadata.get("data_alignment")
        if alignment:
            facts[f"{prefix}.data_alignment"] = (
                f"{label}：历史观测截止于 {alignment['history_end']}，距请求起点 {alignment['requested_origin']} "
                f"相差 {number(alignment['delay_hours'])} 小时。模型跨越此间隔后输出请求时段的预测；"
                "未将该间隔填补为真实观测。")
        window = series.history_window
        if window:
            facts[f"{prefix}.history_window"] = (f"{label}：实际使用 {number(window['actual_hours'])} 小时历史窗口，"
                f"共 {window['actual_steps']} 点，覆盖 {window['start']} 至 {window['end']}；"
                f"原计划 {number(window['requested_hours'])} 小时。{window['reason']}")
        facts[f"{prefix}.max"] = f"{label}：预测最大值 {number(summary['max'])} {series.unit}，首次出现于 {summary['max_time']}。"
        facts[f"{prefix}.min"] = f"预测最小值 {number(summary['min'])} {series.unit}，首次出现于 {summary['min_time']}。"
        facts[f"{prefix}.mean"] = f"预测均值 {number(summary['mean'])} {series.unit}。"
        facts[f"{prefix}.change"] = f"预测终点相对最后历史观测的变化量为 {number(summary['end_minus_origin'])} {series.unit}；此数值不代表全过程单调变化。"
        if metrics["available"]:
            facts[f"{prefix}.evaluation"] = (
                f"回测有效观测 {metrics['valid_points']}/{metrics['expected_points']} 点；"
                f"MAE {number(metrics['mae'])}、RMSE {number(metrics['rmse'])}、平均偏差 {number(metrics['mean_bias'])} {series.unit}。"
                f"保持最后观测值基线的 MAE 为 {number(metrics['baseline_mae'])} {series.unit}。")
            facts[f"{prefix}.coverage"] = f"本次有效观测落入 q10–q90 范围的比例为 {number(metrics['empirical_interval_coverage'] * 100)}%；小样本覆盖率不等于总体校准结果。"
        else:
            facts[f"{prefix}.evaluation"] = metrics["reason"]
    for finding in result.research.get("findings", []):
        facts[finding["id"]] = finding["text"]
    for feature in result.research.get("features", []):
        index = next(i for i, s in enumerate(result.series) if s.case_id == feature["case_id"])
        rate, ref = feature["largest_rate"], feature["reference"]
        facts[f"series_{index}.rate"] = f"预测相邻采样点间最大绝对变化速率为 {number(rate['value'])} {rate['unit']}，出现在 {rate['timestamp']}；不代表全过程趋势。"
        facts[f"series_{index}.reference"] = f"本次历史输入参考范围：{number(ref['min'])}–{number(ref['max'])} {result.series[index].unit}，覆盖 {ref['start']} 至 {ref['end']}；不是季节正常范围或风险阈值。"
    return facts


def render_reply(result: ForecastResult, fact_ids: list[str] | None = None) -> str:
    ids = fact_ids or list(result.facts)
    if any(key not in result.facts for key in ids):
        raise ValueError("解释引用了不存在的事实")
    # Label selected facts even when a follow-up asks about only one metric.
    lines, labelled = [], set()
    for key in dict.fromkeys(ids):
        if key.startswith("series_"):
            index = int(key.split(".")[0].removeprefix("series_"))
            if index not in labelled:
                series = result.series[index]
                lines.append(f"{series.label} / {series.variable}（{series.unit}）")
                labelled.add(index)
        lines.append(result.facts[key])
    if fact_ids is None:
        lines.extend(analysis_lines(result.warning_analysis))
    return "\n\n".join(lines)


def compare_results(first: ForecastResult, second: ForecastResult) -> str:
    lines = ["历史任务比较（每项统计独立计算，未对不同单位的序列合并或排名）："]
    other = {s.case_id: s for s in second.series}
    for series in first.series:
        match = other.get(series.case_id)
        if not match or (series.unit, series.variable) != (match.unit, match.variable):
            continue
        lines.append(f"{series.label}：前次预测最大值 {number(series.summary['max'])}，后次 {number(match.summary['max'])} {series.unit}。")
        same_grid = [p.timestamp for p in series.predictions] == [p.timestamp for p in match.predictions]
        same_truth = series.observations == match.observations
        if same_grid and same_truth and series.evaluation["available"] and match.evaluation["available"]:
            lines.append(f"相同评价窗口与真实观测：MAE 从 {number(series.evaluation['mae'])} 变为 {number(match.evaluation['mae'])} {series.unit}。")
        else:
            lines.append("评价窗口或真实观测不一致，不能据此判断哪个模型表现更好。")
    return "\n\n".join(lines) if len(lines) > 1 else "所选任务没有可直接比较的同变量、同单位序列。"


def _figures(result: ForecastResult, directory: Path) -> list[tuple[str, str]]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib import font_manager

    available = {f.name for f in font_manager.fontManager.ttflist}
    fonts = [f for f in ["Microsoft YaHei", "Noto Sans CJK SC", "DejaVu Sans"] if f in available]
    chinese = any(f in fonts for f in ["Microsoft YaHei", "Noto Sans CJK SC"])
    outputs = []
    with plt.rc_context({"font.family": "sans-serif", "font.sans-serif": fonts,
                         "svg.fonttype": "none", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "legend.frameon": False, "axes.unicode_minus": False}):
        for i, series in enumerate(result.series):
            hist = pd.DataFrame(series.history)
            pred = pd.DataFrame([p.model_dump() for p in series.predictions])
            x = pd.to_datetime(pred.timestamp, utc=True)
            truth = np.asarray([p.get("value") for p in series.observations], dtype=float)
            policy = bool(series.assessment and series.assessment.evidence)
            detail = policy or np.ptp(pred.prediction.to_numpy()) > max(0, np.ptp(hist.value.to_numpy()) * .05)
            fig, axes = plt.subplots(3 if policy else 2 if detail else 1, 1, figsize=(10, 5.76 if policy else 4.63 if detail else 3),
                                     gridspec_kw={"height_ratios": [1, 1, .5] if policy else [1, 1] if detail else [1]},
                                     layout="constrained")
            axes = np.atleast_1d(axes)
            recent = hist.tail(min(len(hist), len(pred)))
            axes[0].plot(pd.to_datetime(recent.timestamp, utc=True), recent.value,
                         color="#64748b", label="近期历史观测" if chinese else "Recent history", linewidth=1.2)
            for ax in axes[:2]:
                ax.fill_between(x, pred.q10.to_numpy(), pred.q90.to_numpy(), color="#1c8a9e", alpha=.18, label="q10–q90")
                ax.plot(x, pred.prediction, color="#087e91", linewidth=1.6, label="预测中位数" if chinese else "Forecast median")
                ax.set_ylabel(series.unit)
            if np.isfinite(truth).any():
                axes[0].plot(x, truth, color="#bd663f", linestyle="--", linewidth=1.4, label="回放真实观测" if chinese else "Held-out observations")
            axes[0].axvline(result.task.origin, color="#64748b", linestyle=":", linewidth=1)
            axes[0].set_title("历史与预测对照" if chinese else "History and forecast", loc="left")
            if detail:
                axes[1].set_title("预测窗口细节（独立纵轴，注意量级）" if chinese else "Forecast detail (independent y-axis; note scale)", loc="left")
            axes[0].legend(loc="upper right", fontsize=8, ncol=2)
            if detail:
                axes[1].legend(loc="upper right", fontsize=8, ncol=2)
            if policy:
                from .warning.presentation import annotate
                annotate(axes[1], axes[2], series)
            for ax in axes:
                locator = mdates.AutoDateLocator(minticks=3, maxticks=5, tz=DISPLAY_ZONE)
                ax.xaxis.set_major_locator(locator)
                ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator, tz=DISPLAY_ZONE))
                ax.grid(axis="y", alpha=.14)
                ax.set_xlabel("北京时间 (UTC+8)" if chinese else "Beijing time (UTC+8)")
            stem = f"forecast_{i + 1}"
            fig.savefig(directory / f"{stem}.png", dpi=160, facecolor="white")
            fig.savefig(directory / f"{stem}.svg", facecolor="white")
            plt.close(fig)
            outputs.append((f"{stem}.png", f"{stem}.svg"))
    return outputs


def render_report(result: ForecastResult, directory: Path):
    """Analysis first; raw points and provenance remain in downloadable CSV/JSON."""
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
    from .warning.insights import facts as insights, periods, retrospective, risk_status
    from .warning.presentation import facts as warning_facts

    directory.mkdir(parents=True, exist_ok=True)
    with _render_lock:
        existing = [(f"forecast_{i + 1}.png", f"forecast_{i + 1}.svg") for i in range(len(result.series))]
        html_path = directory / "report.html"
        local_charts = html_path.exists() and 'data-timezone="Asia/Shanghai"' in html_path.read_text(encoding="utf-8")
        figures = (existing if result.warning_analysis and local_charts and all((directory / name).is_file() for pair in existing for name in pair)
                   else _figures(result, directory))
        if "STSong-Light" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        styles = getSampleStyleSheet()
        for name in ["Normal", "Title", "Heading1", "Heading2"]:
            styles[name].fontName = "STSong-Light"
            styles[name].wordWrap = "CJK"
            styles[name].textColor = colors.HexColor("#20384b")
        styles["Normal"].fontSize, styles["Normal"].leading = 9.5, 15
        styles["Title"].fontSize, styles["Title"].leading = 24, 32
        styles["Heading2"].fontSize, styles["Heading2"].leading = 12, 19
        styles["Heading2"].keepWithNext = True
        styles["Heading2"].spaceBefore = 9
        styles.add(ParagraphStyle("Footnote", parent=styles["Normal"], fontSize=7, leading=11, textColor=colors.HexColor("#6e7a87")))
        analysis = result.warning_analysis
        from .result_view import title as result_title
        title = result_title(result, report=True)
        story = [Paragraph(pdf_text(title), styles["Title"])]
        html = [f"<header><div class='eyebrow'>科学预测智能体 · 分析报告</div><h1>{escape(title)}</h1></header>"]
        location_files, limits = [], ["时间为北京时间（UTC+8）；回放检验使用事后观测，不参与预测。q10–q90 为未经校准的模型分位数范围。"]

        def paragraph(text, kind="body"):
            text = display_times(text, pd.Timestamp(result.task.origin).year)
            story.extend([Paragraph(pdf_text(text), styles["Normal"]), Spacer(1, 5)])
            html.append(f"<p class='{kind}'>{escape(text)}</p>")

        def heading(text):
            story.append(Paragraph(pdf_text(text), styles["Heading2"]))
            html.append(f"<h3>{escape(text)}</h3>")

        cited_facts = set()

        def narrative(section_id, index):
            if not analysis:
                return False
            section = next((s for s in analysis.sections if s.id == section_id), None)
            if not section:
                return False
            notes = [n for n in section.items if any(k.startswith(f"series_{index}.") for k in n.fact_ids)
                     or index == 0 and not any(k.startswith("series_") for k in n.fact_ids)]
            if not notes:
                return False
            heading(section.title)
            for note in notes:
                text = note_text(note, analysis.facts)
                paragraph(text)
                if note.condition:
                    paragraph("成立条件：" + note.condition, "meta")
                if note.knowledge_basis == "general":
                    paragraph("分析依据：一般领域知识，需结合具体对象核实。", "meta")
                for key in note.fact_ids:
                    if (key not in cited_facts and analysis.facts[key] not in text and key.startswith(f"series_{index}.")
                            and not key.endswith(("limitations", "probability"))):
                        paragraph(analysis.facts[key], "meta")
                        cited_facts.add(key)
                for key in note.context_ids:
                    ref = analysis.contexts.get(key, {})
                    paragraph("背景依据：" + context_label(key, ref), "meta")
            return True

        objective = result.analysis_context.get("user", {}).get("objective")
        if objective:
            paragraph("研究目标：" + objective)
        for i, series in enumerate(result.series):
            if i:
                story.append(PageBreak())
            a = series.assessment
            area = a.area if a else series.label
            mode = "历史回放" if a and a.mode == "historical_replay" else "当前评估" if a else "指标预测"
            status = a.status if a else "not_assessed"
            html.append(f"<section class='case'><div class='tag'>{escape(mode)}</div><h2>{escape(series.label)}</h2>")
            story.append(Paragraph(pdf_text(series.label), styles["Heading2"]))
            paragraph(f"{local_time(result.task.origin)} 至 {local_time(series.predictions[-1].timestamp)} 北京时间 · {result.task.horizon_hours} 小时 · 单位 {series.unit}", "meta")
            location = series.metadata.get("location") or series.provenance.get(series.variable, {}).get("location")
            if location:
                from .location_map import render_location
                from .result_view import build as result_view
                heading("预测位置与概况")
                name = f"location_{i + 1}.png"
                reason = render_location(location, directory / name)
                summary = next(c for c in result_view(result)["series"] if c["case_id"] == series.case_id)
                details = ["位置 1：" + (location.get("name") or series.label),
                    "地址：" + (location.get("address") or "未提供"),
                    f"原始坐标：经度 {location.get('longitude')}，纬度 {location.get('latitude')}（{location.get('coordinate_system', '未提供')}）"
                    if location.get("longitude") is not None and location.get("latitude") is not None else "经纬度：待补充",
                    f"本次 {result.task.horizon_hours} 小时预测：",
                    *[f"{m['label']}：{number(m['value'])} {m['unit']}" for m in summary["metrics"]]]
                if reason:
                    for text in [*details, reason]:
                        paragraph(text, "meta")
                else:
                    location_files.append(name)
                    picture = Image(str(directory / name), width=290, height=290 * 4.4/7)
                    panel = Table([[picture, [Paragraph(pdf_text(t), styles["Normal"]) for t in details]]],
                                  colWidths=[302, 184], hAlign="LEFT")
                    panel.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),
                        ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 8)]))
                    story.extend([panel, Spacer(1, 6)])
                    html.append(f"<div class='location-panel'><img src='{name}' alt='中国地图：{escape(location.get('name') or series.label)}位置 1'><div>"
                                + "".join(f"<p>{escape(t)}</p>" for t in details) + "</div></div>")
                    paragraph("底图：阿里云 DataV GeoAtlas。标点为数据配置位置，仅作位置示意；指标代表对应观测序列。", "meta")
            own = insights(series)
            if not narrative("overview", i):
                heading("主要结论")
                paragraph(own["outlook"], "lead")
            heading("风险分析与预警判定")
            html.append(f"<div class='assessment {status}'>")
            if a and a.status != "not_assessed":
                paragraph(f"评估对象：{a.area}；" + ("方法：历史异常筛查。" if a.method == "historical_screening" else f"关注类型：{a.hazard_type}。"), "meta")
            paragraph(risk_status(series), "lead")
            if a and a.level:
                paragraph(f"{'历史异常关注等级' if a.method == 'historical_screening' else '登记规则研究分级'}：{a.level}")
            html.append("</div>")
            narrative("impacts", i)
            for key, value in warning_facts(series).items():
                if key.startswith("rule_"):
                    paragraph(value)
            validation = retrospective(series)
            if validation:
                heading("历史回放验证（事后实测）")
                paragraph(validation, "validation")
                paragraph(result.facts.get(f"series_{i}.evaluation", ""), "meta")
            else:
                paragraph("结果验证：" + result.facts.get(f"series_{i}.evaluation", "没有可用的历史验证结果。"), "meta")
            heading("数据走势与关键时段")
            for key in ("profile", "focus"):
                if f"series_{i}.{key}" not in cited_facts:
                    paragraph(own[key])
                    cited_facts.add(f"series_{i}.{key}")
            chart = Image(str(directory / figures[i][0]))
            image_width, image_height = chart.imageWidth, chart.imageHeight
            chart.drawWidth = 486
            chart.drawHeight = 486 * image_height / image_width
            story.append(chart)
            html.append(f"<img src='{figures[i][0]}' alt='{escape(area)}指标预测与观测对照图'>")
            heading("主要依据与关注时段")
            blocks = periods(series)
            additive = blocks[0]["total"] is not None
            table_rows = [["时段（北京时间）", f"峰值 ({series.unit})", f"{'逐点中位数合计' if additive else '均值'} ({series.unit})"]]
            for block in blocks:
                table_rows.append([f"{local_time(block['start'])[5:]}—{local_time(block['end'])[5:]}", format(block["max"], ".4g"),
                                   format(block["total"] if additive else block["mean"], ".4g")])
            cell_rows = [[Paragraph(pdf_text(str(v)), styles["Normal"]) for v in row] for row in table_rows]
            table = Table(cell_rows, colWidths=[224, 105, 157], repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9f2f4")),
                                      ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                      ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                                      ("TOPPADDING", (0, 0), (-1, -1), 6),
                                      ("LINEBELOW", (0, 0), (-1, -1), .3, colors.HexColor("#dbe4e8"))]))
            story += [table, Spacer(1, 8)]
            html.append("<table>" + "".join("<tr>" + "".join(f"<td>{escape(str(v))}</td>" for v in row) + "</tr>" for row in table_rows) + "</table>")
            for finding in result.research.get("findings", []):
                if finding["kind"] == "coincidence" and series.case_id == finding["case_ids"][0]:
                    paragraph(finding["text"])
            if analysis and analysis.source == "llm":
                narrative("evidence", i)
            if not (analysis and analysis.source == "llm" and narrative("recommendations", i)):
                heading("后续关注建议")
                paragraph(own["followup"])
            heading("数据与方法简述")
            for name, quality in series.quality.items():
                paragraph(f"{name}：历史窗口 {quality['expected_points']} 点，缺测 {quality['missing_before']} 点，填补 {quality['filled_points']} 点；单位 {quality.get('unit', '')}。", "meta")
            citations = list(dict.fromkeys(str(s.get("citation") or s.get("source_id") or "未登记") for s in series.provenance.values()))
            for citation in citations:
                paragraph("数据来源：" + citation, "meta")
            paragraph("预测方法：" + str(result.model.get("id", "未登记")) + "；根据预测起点之前的历史观测推断后续指标变化。", "meta")
            context = next((c for c in result.analysis_context.get("cases", []) if c["case_id"] == series.case_id), {})
            for ref in context.get("context", {}).get("references", []):
                paragraph(f"参考资料：{ref['title']}；来源：{ref['source']}。", "meta")
            if a:
                limits.extend(a.limitations)
            if additive:
                limits.append("时段合计是逐点中位数之和，非累计量分位数。")
            if series.postprocessing.get("adjusted_values", 0):
                limits.append("物理边界约束不代表精度提升。")
            html.append("</section>")
        if analysis and analysis.source == "llm":
            for section in analysis.sections:
                if section.id == "limitations":
                    for note in section.items:
                        if note.text != "评估边界：":
                            limits.append(note_text(note, analysis.facts))
                            if note.condition:
                                limits.append(note.condition)
        limits.append("潜在影响为条件性分析，规则触发不代表实际影响已发生，未触发或未评估不代表没有潜在风险。")
        limits.append("分析用于科研核查。")
        footnote = "分析局限性：" + " ".join(dict.fromkeys(limits))
        story += [Spacer(1, 6), Paragraph(pdf_text(footnote), styles["Footnote"])]
        html.append(f"<footer><small>{escape(display_times(footnote, pd.Timestamp(result.task.origin).year))}</small></footer>")

        def page_footer(canvas, document):
            canvas.setFont("STSong-Light", 8)
            canvas.setFillColor(colors.HexColor("#82909e"))
            canvas.drawString(48, 24, title[:50])
            canvas.drawRightString(A4[0] - 48, 24, str(document.page))

        SimpleDocTemplate(str(directory / "report.pdf.tmp"), title=title, author="Scientific Forecast Agent", pagesize=A4,
                          rightMargin=48, leftMargin=48, topMargin=35, bottomMargin=42).build(story, onFirstPage=page_footer, onLaterPages=page_footer)
        (directory / "report.pdf.tmp").replace(directory / "report.pdf")
        css = "body{font:16px/1.8 system-ui,'Microsoft YaHei',sans-serif;color:#20384b;max-width:980px;margin:40px auto;padding:0 28px;background:#fff}header{padding:20px 0 24px;border-bottom:2px solid #187e90}.eyebrow,.meta{font-size:13px;color:#697d8d}h1{font-size:34px;margin:6px 0}h2{font-size:26px;margin:8px 0}h3{font-size:18px;margin:28px 0 12px;color:#146878}.case{padding-top:24px}.tag{display:inline-block;background:#edf3f6;color:#516c7c;padding:2px 10px;font-size:12px;border-radius:4px}.assessment{background:#eff7f8;border-left:4px solid #178497;padding:12px 20px;margin:20px 0}.assessment.triggered{background:#fff3e9;border-color:#bd663f}.lead{font-size:18px;font-weight:600;margin:6px 0}img{width:100%;height:auto;margin:12px 0}table{border-collapse:collapse;width:100%;font-size:14px}td{border-bottom:1px solid #dbe4e8;padding:10px}tr:first-child{background:#e9f2f4;font-weight:600}.validation{background:#f7f5ef;padding:14px 18px}footer{border-top:1px solid #dbe4e8;padding-top:14px;margin-top:30px;color:#73818c;line-height:1.6}small{font-size:11px}@media print{body{margin:0}h2,h3{break-after:avoid}img,tr{break-inside:avoid}}"
        css += ".location-panel{display:grid;grid-template-columns:3fr 2fr;gap:20px;align-items:start;background:#f6f9fc;padding:14px;border-radius:10px;break-inside:avoid}.location-panel img{margin:0}.location-panel p{font-size:14px;margin:4px 0;overflow-wrap:anywhere}@media(max-width:620px){.location-panel{grid-template-columns:1fr}}"
        (directory / "report.html.tmp").write_text("<!doctype html><html lang='zh-CN' data-timezone=\"Asia/Shanghai\"><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>" + escape(title) + "</title><style>" + css + "</style><body>" + "".join(html) + "</body></html>", encoding="utf-8")
        (directory / "report.html.tmp").replace(directory / "report.html")
        export_predictions(result, directory)
        result.artifacts = ["report.html", "report.pdf", "predictions.csv", "result.json"] + [f for pair in figures for f in pair] + location_files
        if any(s.assessment for s in result.series):
            (directory / "assessment.json").write_text(json.dumps({s.case_id: s.assessment.model_dump(mode="json")
                for s in result.series if s.assessment}, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
            result.artifacts.append("assessment.json")
        result.report_status = "completed"
