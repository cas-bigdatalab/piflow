// BatchRunPage.tsx
import React, { useState, useRef, useEffect } from 'react';
import './BatchRunPage.css';

interface FileItem {
  key: string;
  name: string;
  type: string;
  size: string;
  modified: string;
  source: string;
  validation?: string;
}

interface BatchFileState {
  ok: boolean;
  text: string;
}

// Mock data
const mockFiles: FileItem[] = Array.from({ length: 20 }, (_, i) => {
  const n = i + 1;
  if (n === 18) {
    return {
      key: `raw:ethanol_018.csv`,
      name: 'ethanol_018.csv',
      type: 'CSV',
      size: '3.0 KB',
      modified: '2026-08-21 09:27:00',
      source: '我的数据',
      validation: 'type'
    };
  }
  if (n === 20) {
    return {
      key: `raw:ethanol_020.smi`,
      name: 'ethanol_020.smi',
      type: 'SMI',
      size: '2.9 KB',
      modified: '2026-08-21 09:29:00',
      source: '我的数据',
      validation: 'access'
    };
  }
  return {
    key: `raw:ethanol_${String(n).padStart(3, '0')}.smi`,
    name: `ethanol_${String(n).padStart(3, '0')}.smi`,
    type: 'SMI',
    size: `${(2.1 + n * 0.04).toFixed(1)} KB`,
    modified: `2026-08-21 09:${String(9 + n).padStart(2, '0')}:00`,
    source: '我的数据'
  };
});

const BatchRunPage: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<FileItem[]>([]);
  const [filesExpanded, setFilesExpanded] = useState(false);
  const [concurrency, setConcurrency] = useState(10);
  const [retryCount, setRetryCount] = useState('2 次');
  const [failPolicy, setFailPolicy] = useState<'continue' | 'stop'>('continue');
  const [renamePolicy, setRenamePolicy] = useState<'rename' | 'overwrite'>('rename');
  const [resultPath, setResultPath] = useState('我的数据 / 分子计算 / 计算结果');
  const [method, setMethod] = useState('');
  const [basis, setBasis] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitProgress, setSubmitProgress] = useState(0);
  const [showProgress, setShowProgress] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropzoneRef = useRef<HTMLDivElement>(null);

  const getFileState = (file: FileItem): BatchFileState => {
    if (file.validation === 'type') {
      return { ok: false, text: '输入类型不匹配' };
    }
    if (file.validation === 'access') {
      return { ok: false, text: '文件不可访问' };
    }
    return { ok: true, text: '可运行' };
  };

  const handleFileUpload = (files: FileList | null) => {
    if (!files || !files.length) return;
    const now = '2026-08-21 16:59:00';
    const incoming: FileItem[] = Array.from(files).map((f) => {
      const type = (f.name.split('.').pop() || 'FILE').toUpperCase();
      return {
        key: `local:${f.name}`,
        name: f.name,
        type,
        size: `${(f.size / 1024).toFixed(1)} KB`,
        modified: now,
        source: '本地上传',
        validation: type === 'SMI' ? undefined : 'type'
      };
    });
    const merged = [...selectedFiles];
    incoming.forEach((f) => {
      if (!merged.some((x) => x.key === f.key)) {
        merged.push(f);
      }
    });
    setSelectedFiles(merged);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    handleFileUpload(e.dataTransfer.files);
  };

  const removeFile = (key: string) => {
    setSelectedFiles(selectedFiles.filter((f) => f.key !== key));
  };

  const clearFiles = () => {
    setSelectedFiles([]);
    setFilesExpanded(false);
  };

  const toggleFilesExpanded = () => {
    setFilesExpanded(!filesExpanded);
  };

  const changeConcurrency = (delta: number) => {
    setConcurrency(Math.max(1, Math.min(99, concurrency + delta)));
  };

  const normalizeConcurrency = () => {
    setConcurrency(Math.max(1, Math.min(99, concurrency)));
  };

  const getValidCount = () => {
    return selectedFiles.filter((f) => getFileState(f).ok).length;
  };

  const getInvalidCount = () => {
    return selectedFiles.filter((f) => !getFileState(f).ok).length;
  };

  const isReady = () => {
    return (
      selectedFiles.length > 0 &&
      getInvalidCount() === 0 &&
      !!resultPath &&
      concurrency >= 1 &&
      concurrency <= 99
    );
  };

  const handleSubmit = () => {
    if (!isReady()) return;
    setIsSubmitting(true);
    setShowProgress(true);
    setSubmitProgress(0);

    const total = selectedFiles.length;
    let created = 0;
    const timer = setInterval(() => {
      created = Math.min(total, created + Math.max(1, Math.ceil(total / 8)));
      setSubmitProgress((created / total) * 100);
      if (created >= total) {
        clearInterval(timer);
        setTimeout(() => {
          setIsSubmitting(false);
          setShowProgress(false);
          setSubmitProgress(0);
          // 模拟跳转
          alert(`已创建 ${total} 条运行实例`);
        }, 550);
      }
    }, 140);
  };

  const scrollToSection = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  const visibleFiles = filesExpanded ? selectedFiles : selectedFiles.slice(0, 6);

  return (
    <div className="batch-page">
      <div className="page-inner">
        {/* Header */}
        <div className="page-header">
          <div className="page-title">
            <div className="kicker">
              <a href="#" onClick={(e) => { e.preventDefault(); }}>← 返回任务管理</a>
            </div>
            <h1>批量运行</h1>
            <p>分子结构优化与波函数分析</p>
            <div className="batch-context">
              <span>v1.4</span>
              <span>·</span>
              <span>5 个节点</span>
              <span>·</span>
              <span>最近修改 2026-08-21 14:42:18</span>
            </div>
          </div>
        </div>

        <div className="batch-layout">
          {/* Main Surface */}
          <div className="batch-surface">
            {/* Input Section */}
            <div className="batch-section" id="batchInputSection">
              <div className="batch-heading">
                <h3>输入数据</h3>
                <span className="batch-status-text">
                  {selectedFiles.length > 0 ? `已选择 ${selectedFiles.length} 项` : '尚未选择输入数据'}
                </span>
              </div>

              {selectedFiles.length === 0 ? (
                <div className="batch-input-surface empty">
                  <div
                    className="dropzone"
                    ref={dropzoneRef}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleDrop}
                  >
                    <div className="drop-icon">
                      <svg className="icon" viewBox="0 0 24 24">
                        <path d="M12 16V4M7 9l5-5 5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M5 20h14a2 2 0 0 0 2-2v-3M3 15v3a2 2 0 0 0 2 2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                    <b>拖拽数据文件到此处</b>
                    <div className="hint">也可以上传本地文件，或从"我的数据"选择已有数据。</div>
                    <div style={{ marginTop: 13, display: 'flex', justifyContent: 'center', gap: 8 }}>
                      <button className="btn sm" onClick={() => fileInputRef.current?.click()}>
                        <svg className="icon sm" viewBox="0 0 24 24">
                          <path d="M12 16V4M7 9l5-5 5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                          <path d="M5 20h14a2 2 0 0 0 2-2v-3M3 15v3a2 2 0 0 0 2 2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        上传文件
                      </button>
                      <button className="btn sm">
                        <svg className="icon sm" viewBox="0 0 24 24">
                          <path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        从我的数据选择
                      </button>
                      <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        style={{ display: 'none' }}
                        onChange={(e) => handleFileUpload(e.target.files)}
                      />
                    </div>
                    <div className="hint" style={{ marginTop: 10 }}>
                      每个输入数据项将创建一条独立运行实例（Workflow Run）。
                    </div>
                  </div>
                </div>
              ) : (
                <div className="batch-input-surface">
                  <div className="batch-file-head">
                    <div className="batch-file-meta">
                      <b>已选择 {selectedFiles.length} 项</b>
                      <span className={`tag ${getInvalidCount() > 0 ? 'amber' : 'green'}`}>
                        {getInvalidCount() > 0 ? '需处理' : '已校验'}
                      </span>
                    </div>
                    <div className="batch-file-actions">
                      <div className="batch-add-wrap">
                        <button className="btn sm">
                          <svg className="icon sm" viewBox="0 0 24 24">
                            <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          添加数据 ▾
                        </button>
                      </div>
                      <button className="btn sm" onClick={clearFiles}>清空</button>
                    </div>
                  </div>
                  <div className={`batch-file-list ${filesExpanded ? 'expanded' : ''}`}>
                    {visibleFiles.map((file) => {
                      const state = getFileState(file);
                      return (
                        <div className="batch-file-row" key={file.key}>
                          <div className="batch-file-name">
                            <span className="batch-file-icon">
                              <svg className="icon sm" viewBox="0 0 24 24">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M14 2v6h6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                            </span>
                            <span title={file.name}>{file.name}</span>
                          </div>
                          <div>{file.type}</div>
                          <div>{file.size}</div>
                          <div className={state.ok ? 'batch-file-ok' : 'batch-file-error'}>
                            {state.ok ? '✓' : '!'} {state.text}
                          </div>
                          <button className="icon-btn" title="移除" onClick={() => removeFile(file.key)}>×</button>
                        </div>
                      );
                    })}
                    {selectedFiles.length > 6 && (
                      <div className="batch-file-more" onClick={toggleFilesExpanded}>
                        {filesExpanded ? '收起 ↑' : `查看全部 ${selectedFiles.length} 项 ↓`}
                      </div>
                    )}
                  </div>
                  <div className={`batch-validation ${getInvalidCount() > 0 ? 'error' : ''}`}>
                    {getInvalidCount() > 0 ? (
                      <>
                        <span>!</span>
                        <span>{getValidCount()} 个可以运行，{getInvalidCount()} 个存在问题</span>
                      </>
                    ) : (
                      <>
                        <span>✓</span>
                        <span>{getValidCount()} 个数据项可以运行</span>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Runtime Parameters */}
            <div className="batch-section" id="batchRuntimeSection">
              <div className="batch-heading">
                <h3>运行参数</h3>
              </div>
              <div className="runtime-note">
                可在此调整本次运行参数；留空或未展示的参数均沿用当前任务配置。
              </div>
              <div className="runtime-param-row">
                <div className="runtime-param-name">逐条输入</div>
                <div className="muted small">
                  {selectedFiles.length > 0
                    ? `已绑定所选 ${selectedFiles.length} 个输入数据`
                    : '等待选择输入数据'}
                </div>
                <div className="runtime-param-scope dynamic">随数据项变化</div>
              </div>
              <div className="runtime-param-row" data-runtime-editable="true">
                <div className="runtime-param-name">计算方法</div>
                <div className="runtime-param-control">
                  <input
                    className="input"
                    value={method}
                    placeholder="请输入计算方法，例如 B3LYP"
                    onChange={(e) => setMethod(e.target.value)}
                  />
                  <div className="runtime-param-default">
                    任务默认值：<b>B3LYP</b> · 留空则沿用任务默认配置
                  </div>
                </div>
                <div className="runtime-param-scope">全部运行共用</div>
              </div>
              <div className="runtime-param-row" data-runtime-editable="true">
                <div className="runtime-param-name">基组</div>
                <div className="runtime-param-control">
                  <input
                    className="input"
                    value={basis}
                    placeholder="请输入基组，例如 6-31G(d)"
                    onChange={(e) => setBasis(e.target.value)}
                  />
                  <div className="runtime-param-default">
                    任务默认值：<b>6-31G(d)</b> · 留空则沿用任务默认配置
                  </div>
                </div>
                <div className="runtime-param-scope">全部运行共用</div>
              </div>
              <div className="task-config-link">
                <svg className="icon sm" viewBox="0 0 24 24">
                  <path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                查看当前任务配置
              </div>
            </div>

            {/* Run Settings */}
            <div className="batch-section">
              <div className="batch-heading">
                <h3>运行设置</h3>
              </div>
              <div className="settings-grid">
                <div className="field">
                  <div className="label">最大并行运行数</div>
                  <div className="counter">
                    <button onClick={() => changeConcurrency(-1)}>−</button>
                    <input
                      type="number"
                      min={1}
                      max={99}
                      value={concurrency}
                      onChange={(e) => setConcurrency(Math.max(1, Math.min(99, parseInt(e.target.value) || 1)))}
                      onBlur={normalizeConcurrency}
                    />
                    <button onClick={() => changeConcurrency(1)}>+</button>
                  </div>
                  <div className="hint" id="batchConcurrencyHint">
                    最多同时推进 {concurrency} 条运行实例，超出部分将自动排队。
                  </div>
                </div>
                <div className="field">
                  <div className="label">失败自动重试</div>
                  <select
                    className="select"
                    style={{ width: 150 }}
                    value={retryCount}
                    onChange={(e) => setRetryCount(e.target.value)}
                  >
                    <option>0 次</option>
                    <option>1 次</option>
                    <option>2 次</option>
                    <option>3 次</option>
                  </select>
                </div>
                <div className="field fail-policy">
                  <div className="label">单条运行失败后</div>
                  <div className="radio-stack">
                    <label>
                      <input
                        type="radio"
                        name="batchFailPolicy"
                        value="continue"
                        checked={failPolicy === 'continue'}
                        onChange={() => setFailPolicy('continue')}
                      />
                      继续执行其他运行
                    </label>
                    <label>
                      <input
                        type="radio"
                        name="batchFailPolicy"
                        value="stop"
                        checked={failPolicy === 'stop'}
                        onChange={() => setFailPolicy('stop')}
                      />
                      停止尚未开始的运行
                    </label>
                  </div>
                </div>
              </div>
              <div className="resource-scheduler-note">
                <span>ⓘ</span>
                <span>实际并行执行数量还会受可用计算资源影响，平台将自动完成资源分配与调度。</span>
              </div>
            </div>

            {/* Result Save */}
            <div className="batch-section">
              <div className="batch-heading">
                <h3>结果保存</h3>
              </div>
              <div className="result-grid">
                <div className="field">
                  <div className="label">保存到</div>
                  <div className="result-path-row">
                    <input
                      className="input result-path"
                      value={resultPath}
                      title={resultPath}
                      readOnly
                    />
                    <button className="btn">选择目录</button>
                  </div>
                  <div className="result-save-note">
                    每条运行结果将按输入数据分别保存。
                  </div>
                </div>
                <div className="field">
                  <div className="label">文件重名时</div>
                  <div className="radio-stack">
                    <label>
                      <input
                        type="radio"
                        name="batchRename"
                        value="rename"
                        checked={renamePolicy === 'rename'}
                        onChange={() => setRenamePolicy('rename')}
                      />
                      自动重命名
                    </label>
                    <label>
                      <input
                        type="radio"
                        name="batchRename"
                        value="overwrite"
                        checked={renamePolicy === 'overwrite'}
                        onChange={() => setRenamePolicy('overwrite')}
                      />
                      覆盖已有文件
                    </label>
                  </div>
                  <div className={`overwrite-warning ${renamePolicy === 'overwrite' ? 'show' : ''}`}>
                    同名结果文件可能被替换，请确认保存目录中已有数据无需保留。
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Summary Card */}
          <div className="surface summary-card" id="batchReadinessCard">
            <div className="readiness-title">
              <div className="section-title" style={{ margin: 0 }}>运行准备</div>
              <span className={`ready-badge ${isReady() ? '' : 'not-ready-badge'}`}>
                {isReady() ? '已就绪' : '待完成'}
              </span>
            </div>

            <div className={`readiness-item ${selectedFiles.length > 0 && getInvalidCount() === 0 ? 'ready' : 'warn'}`}
                 onClick={() => scrollToSection('batchInputSection')}>
              <div className="readiness-line">
                <span className="state-icon">
                  {selectedFiles.length > 0 && getInvalidCount() === 0 ? '✓' : '!'}
                </span>
                <span>输入数据</span>
              </div>
              <div className="readiness-sub">
                {selectedFiles.length === 0
                  ? '尚未选择输入数据'
                  : getInvalidCount() > 0
                  ? `${getValidCount()} 个可运行，${getInvalidCount()} 个存在问题`
                  : `${selectedFiles.length} 个数据项已校验，可运行`}
              </div>
            </div>

            <div className="readiness-item ready" onClick={() => scrollToSection('batchRuntimeSection')}>
              <div className="readiness-line">
                <span className="state-icon">✓</span>
                <span>运行参数</span>
              </div>
              <div className="readiness-sub">
                {method || basis
                  ? `已调整 ${[method, basis].filter(Boolean).length} 个参数，其他参数沿用任务配置`
                  : '2 个可修改参数，当前均沿用任务默认配置'}
              </div>
            </div>

            <div className="readiness-item ready">
              <div className="readiness-line">
                <span className="state-icon">✓</span>
                <span>运行策略</span>
              </div>
              <div className="readiness-sub">
                最大并行 {concurrency} · 重试 {retryCount}
                <br />
                {failPolicy === 'stop' ? '失败后停止尚未开始的运行' : '失败后继续其他运行'}
              </div>
            </div>

            <div className="readiness-item ready">
              <div className="readiness-line">
                <span className="state-icon">✓</span>
                <span>结果位置</span>
              </div>
              <div className="readiness-sub">{resultPath}</div>
            </div>

            <div className="readiness-cta">
              <div className="small muted">将创建</div>
              <div>
                <span className="readiness-number">{selectedFiles.length}</span>
                <span className="small muted"> 条运行实例</span>
              </div>
              <div className="small muted" style={{ marginTop: 4 }}>
                最大同时运行 <b>{concurrency}</b> 条
              </div>
              <div style={{ margin: '12px 0 10px' }}>
                <span className={`ready-badge ${isReady() ? '' : 'not-ready-badge'}`}>
                  {isReady()
                    ? '✓ 已准备就绪'
                    : selectedFiles.length === 0
                    ? '还需选择输入数据'
                    : getInvalidCount() > 0
                    ? '请先处理输入数据问题'
                    : '请完成运行配置'}
                </span>
              </div>
              <button
                className="btn primary batch-submit"
                style={{ width: '100%', height: 42 }}
                onClick={handleSubmit}
                disabled={!isReady() || isSubmitting}
              >
                {isSubmitting ? '正在创建运行实例…' : '开始批量运行'}
              </button>
              <div className={`batch-progress ${showProgress ? 'show' : ''}`}>
                <div className="batch-progress-track">
                  <div className="batch-progress-fill" style={{ width: `${submitProgress}%` }} />
                </div>
                <div className="batch-progress-text">
                  正在创建 {selectedFiles.length} 条运行实例 · {Math.round(submitProgress / 100 * selectedFiles.length)} / {selectedFiles.length}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BatchRunPage;