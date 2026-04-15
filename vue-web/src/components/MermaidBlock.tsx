import { Icon } from "@iconify/react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

type MermaidBlockProps = {
  chart: string;
};

type SvgSize = {
  width: number;
  height: number;
};

let mermaidApiPromise: Promise<any> | null = null;

async function getMermaidApi() {
  if (!mermaidApiPromise) {
    mermaidApiPromise = import("mermaid").then(({ default: mermaid }) => {
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: "loose",
        theme: "default",
      });
      return mermaid;
    });
  }

  return mermaidApiPromise;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function readSvgSize(svgElement: SVGSVGElement): SvgSize {
  const viewBox = svgElement.viewBox?.baseVal;
  if (viewBox && viewBox.width > 0 && viewBox.height > 0) {
    return { width: viewBox.width, height: viewBox.height };
  }

  const widthAttr = Number.parseFloat(svgElement.getAttribute("width") || "");
  const heightAttr = Number.parseFloat(svgElement.getAttribute("height") || "");
  if (widthAttr > 0 && heightAttr > 0) {
    return { width: widthAttr, height: heightAttr };
  }

  const box = svgElement.getBBox();
  return {
    width: Math.max(box.width, 1),
    height: Math.max(box.height, 1),
  };
}

export function MermaidBlock({ chart }: MermaidBlockProps) {
  const reactId = useId();
  const panelRef = useRef<HTMLDivElement | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const graphRef = useRef<HTMLDivElement | null>(null);
  const manualZoomRef = useRef(false);

  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");
  const [zoom, setZoom] = useState(1);
  const [fitZoom, setFitZoom] = useState(1);
  const [svgSize, setSvgSize] = useState<SvgSize | null>(null);
  const [tab, setTab] = useState<"graph" | "code">("graph");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const source = chart.trim();
    if (!source) {
      setSvg("");
      setError("");
      return;
    }

    let active = true;
    const renderId = `mermaid-${reactId.replace(/[^a-zA-Z0-9_-]/g, "")}`;

    (async () => {
      try {
        const mermaid = await getMermaidApi();
        const { svg: renderedSvg } = await mermaid.render(renderId, source);
        if (!active) {
          return;
        }
        manualZoomRef.current = false;
        setSvg(renderedSvg);
        setError("");
      } catch (err: any) {
        if (!active) {
          return;
        }
        setSvg("");
        setError(String(err?.message || err));
      }
    })();

    return () => {
      active = false;
    };
  }, [chart, reactId]);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(document.fullscreenElement === panelRef.current);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  useEffect(() => {
    if (!copied) {
      return;
    }

    const timer = window.setTimeout(() => setCopied(false), 1600);
    return () => window.clearTimeout(timer);
  }, [copied]);

  useEffect(() => {
    if (tab !== "graph" || !svg || !graphRef.current || !viewportRef.current) {
      return;
    }

    const svgElement = graphRef.current.querySelector("svg");
    if (!(svgElement instanceof SVGSVGElement)) {
      return;
    }

    const measured = readSvgSize(svgElement);
    setSvgSize(measured);

    const updateFitZoom = () => {
      const viewportWidth = viewportRef.current?.clientWidth || measured.width;
      const nextFitZoom = clamp((viewportWidth - 48) / measured.width, 0.35, 1.25);
      setFitZoom(nextFitZoom);
      if (!manualZoomRef.current) {
        setZoom(nextFitZoom);
      }
    };

    const frame = window.requestAnimationFrame(updateFitZoom);
    window.addEventListener("resize", updateFitZoom);
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("resize", updateFitZoom);
    };
  }, [svg, isFullscreen, tab]);

  useEffect(() => {
    if (tab !== "graph" || !svg || !viewportRef.current || !svgSize) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      const viewportWidth = viewportRef.current?.clientWidth || svgSize.width;
      const nextFitZoom = clamp((viewportWidth - 48) / svgSize.width, 0.35, 1.25);
      manualZoomRef.current = false;
      setFitZoom(nextFitZoom);
      setZoom(nextFitZoom);
    });

    return () => window.cancelAnimationFrame(frame);
  }, [tab, svg, svgSize]);

  useEffect(() => {
    if (tab !== "graph" || !svgSize || !graphRef.current) {
      return;
    }

    const svgElement = graphRef.current.querySelector("svg");
    if (!(svgElement instanceof SVGSVGElement)) {
      return;
    }

    svgElement.style.width = `${Math.round(svgSize.width * zoom)}px`;
    svgElement.style.height = "auto";
    svgElement.style.maxWidth = "none";
  }, [svgSize, zoom, svg, tab]);

  const zoomLabel = useMemo(() => `${Math.round(zoom * 100)}%`, [zoom]);

  const updateZoom = (nextZoom: number, manual = true) => {
    manualZoomRef.current = manual;
    setZoom(clamp(nextZoom, 0.35, 2.5));
  };

  const handleFit = () => {
    updateZoom(fitZoom, false);
  };

  const handleDownload = () => {
    if (!svg) {
      return;
    }

    const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "diagram.svg";
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleCopyCode = async () => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(chart);
      } else {
        const input = document.createElement("textarea");
        input.value = chart;
        input.setAttribute("readonly", "true");
        input.style.position = "absolute";
        input.style.left = "-9999px";
        document.body.appendChild(input);
        input.select();
        document.execCommand("copy");
        document.body.removeChild(input);
      }
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  const handleDownloadCode = () => {
    const blob = new Blob([chart], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "diagram.mmd";
    link.click();
    URL.revokeObjectURL(url);
  };

  const toggleFullscreen = async () => {
    const node = panelRef.current;
    if (!node) {
      return;
    }

    if (document.fullscreenElement === node) {
      await document.exitFullscreen();
      return;
    }

    await node.requestFullscreen();
  };

  if (error) {
    return (
      <div className="mermaid-panel">
        <div className="mermaid-state mermaid-state-error">
          Mermaid 渲染失败，已回退为源码显示。
        </div>
        <pre className="markdown-pre">
          <code>{chart}</code>
        </pre>
      </div>
    );
  }

  if (!svg) {
    return (
      <div className="mermaid-panel">
        <div className="mermaid-state">正在渲染 Mermaid 图...</div>
        <pre className="markdown-pre">
          <code>{chart}</code>
        </pre>
      </div>
    );
  }

  return (
    <div
      className={`mermaid-panel ${isFullscreen ? "is-fullscreen" : ""} ${tab === "code" ? "is-code-mode" : "is-graph-mode"}`}
      ref={panelRef}
    >
      <div className="mermaid-toolbar">
        <div className="mermaid-tabs" role="tablist" aria-label="Mermaid view mode">
          <button
            type="button"
            className={tab === "graph" ? "mermaid-tab is-active" : "mermaid-tab"}
            onClick={() => setTab("graph")}
            aria-label="切换到图表视图"
          >
            <Icon icon="ri:flow-chart" width="16" />
            <span>图表</span>
          </button>
          <button
            type="button"
            className={tab === "code" ? "mermaid-tab is-active" : "mermaid-tab"}
            onClick={() => setTab("code")}
            aria-label="切换到代码视图"
          >
            <Icon icon="ri:code-s-slash-line" width="16" />
            <span>代码</span>
          </button>
        </div>

        {tab === "graph" ? (
          <div className="mermaid-actions">
            <button
              type="button"
              className="mermaid-action"
              onClick={() => updateZoom(zoom - 0.15)}
              aria-label="缩小图表"
              title="缩小"
            >
              <Icon icon="ri:zoom-out-line" width="16" />
            </button>
            <button
              type="button"
              className="mermaid-zoom-label"
              onClick={handleFit}
              aria-label="按容器适配缩放"
              title="按容器适配"
            >
              {zoomLabel}
            </button>
            <button
              type="button"
              className="mermaid-action"
              onClick={() => updateZoom(zoom + 0.15)}
              aria-label="放大图表"
              title="放大"
            >
              <Icon icon="ri:zoom-in-line" width="16" />
            </button>
            <button
              type="button"
              className="mermaid-action wide"
              onClick={handleFit}
              aria-label="适配容器"
              title="适配容器"
            >
              <Icon icon="ri:scan-line" width="16" />
              <span>适配</span>
            </button>
            <button
              type="button"
              className="mermaid-action wide"
              onClick={handleDownload}
              aria-label="下载 SVG"
              title="下载 SVG"
            >
              <Icon icon="ri:download-2-line" width="16" />
              <span>下载</span>
            </button>
            <button
              type="button"
              className="mermaid-action"
              onClick={toggleFullscreen}
              aria-label={isFullscreen ? "退出全屏" : "进入全屏"}
              title={isFullscreen ? "退出全屏" : "进入全屏"}
            >
              <Icon icon={isFullscreen ? "ri:fullscreen-exit-line" : "ri:fullscreen-line"} width="16" />
            </button>
          </div>
        ) : (
          <div className="mermaid-actions mermaid-actions-code">
            <button
              type="button"
              className={`mermaid-action wide ${copied ? "is-success" : ""}`}
              onClick={handleCopyCode}
              aria-label="复制 Mermaid 代码"
              title="复制 Mermaid 代码"
            >
              <Icon icon={copied ? "ri:check-line" : "ri:file-copy-line"} width="16" />
              <span>{copied ? "已复制" : "复制"}</span>
            </button>
            <button
              type="button"
              className="mermaid-action wide"
              onClick={handleDownloadCode}
              aria-label="下载 Mermaid 代码"
              title="下载 Mermaid 代码"
            >
              <Icon icon="ri:download-2-line" width="16" />
              <span>下载</span>
            </button>
            <button
              type="button"
              className="mermaid-action wide"
              onClick={toggleFullscreen}
              aria-label={isFullscreen ? "退出全屏" : "进入全屏"}
              title={isFullscreen ? "退出全屏" : "进入全屏"}
            >
              <Icon icon={isFullscreen ? "ri:fullscreen-exit-line" : "ri:fullscreen-line"} width="16" />
              <span>{isFullscreen ? "退出全屏" : "全屏"}</span>
            </button>
          </div>
        )}
      </div>

      {tab === "graph" ? (
        <div className="mermaid-viewport custom-scrollbar" ref={viewportRef}>
          <div className="mermaid-canvas">
            <div className="mermaid-graph" ref={graphRef} dangerouslySetInnerHTML={{ __html: svg }} />
          </div>
        </div>
      ) : (
        <div className="mermaid-code-wrap">
          <div className="mermaid-code-surface">
            <pre className="markdown-pre mermaid-code-block">
              <code>{chart}</code>
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
