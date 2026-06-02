import React, { useCallback, useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Database, Filter, Square, Download, ArrowLeft, Check, Play, X } from 'lucide-react';
import { getExecutionDetail, stopDAGTask, downloadWorkspaceUrl2 } from '../lib/api';

interface StopInfo {
  stop_name: string;
  status: string;
  job_id: string;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  progress?: number;
  processed_records?: number;
  total_records?: number;
}

interface ExecutionDetail {
  process_id: string;
  flow_uuid: string | null;
  flow_name: string;
  status: string;
  progress: number | null;
  total_stop_count: number;
  success_stop_count: number;
  failed_stop_count: number;
  skipped_stop_count: number;
  workspace_path: string | null;
  log_path: string | null;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  stops: StopInfo[];
  final_output_paths: string[];
}

interface LogEntry {
  time: string;
  node: string;
  message: string;
}

const statusConfig: Record<string, { label: string; color: string; bgColor: string; borderColor: string }> = {
  SUCCESS: { label: '已完成', color: '#22c55e', bgColor: '#dcfce7', borderColor: '#22c55e' },
  RUNNING: { label: '执行中', color: '#1f2937', bgColor: '#ffffff', borderColor: '#1f2937' },
  FAILED: { label: '执行失败', color: '#ef4444', bgColor: '#fee2e2', borderColor: '#ef4444' },
  SUBMITTED: { label: '已提交', color: '#f59e0b', bgColor: '#fef3c7', borderColor: '#f59e0b' },
  PENDING: { label: '等待执行', color: '#9ca3af', bgColor: '#f9fafb', borderColor: '#d1d5db' },
};

const getStatusInfo = (status: string) => {
  return statusConfig[status] || { label: status, color: '#6b7280', bgColor: '#f3f4f6', borderColor: '#d1d5db' };
};

const getNodeIcon = (nodeName: string) => {
  const name = nodeName.toLowerCase();
  if (name.includes('source') || name.includes('mysql') || name.includes('database')) return Database;
  if (name.includes('filter') || name.includes('clean') || name.includes('process')) return Filter;
  return Square;
};

const calculateDuration = (startTime: string | null, endTime: string | null): string => {
  if (!startTime) return '-';
  const start = new Date(startTime).getTime();
  const end = endTime ? new Date(endTime).getTime() : Date.now();
  const duration = Math.floor((end - start) / 1000);
  if (duration < 60) return `${duration}s`;
  if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
  return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
};

const RunDetails: React.FC<{ processId: string }> = ({ processId }) => {
  const navigate = useNavigate();
  const [executionData, setExecutionData] = useState<ExecutionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const handleBack = () => navigate('/run-history');
  const loadingRef = useRef(false);

  const loadExecutionDetail = useCallback(async () => {
    if (loadingRef.current) return;
    loadingRef.current = true;
    try {
      const response = await getExecutionDetail(processId);
      if (response.code === 200 && response.result) {
        setExecutionData(response.result);
        const newLogs: LogEntry[] = response.result.stops.map((stop: StopInfo) => {
          const startTime = stop.started_at ? new Date(stop.started_at) : null;
          const timeStr = startTime ? startTime.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';
          if (stop.status === 'SUCCESS') {
            return { time: timeStr, node: stop.stop_name, message: `Done: ${stop.processed_records || stop.total_records || 'N/A'} recs` };
          } else if (stop.status === 'RUNNING') {
            return { time: timeStr, node: stop.stop_name, message: `Progress updated: ${stop.processed_records || 0} recs.` };
          } else if (stop.status === 'FAILED') {
            return { time: timeStr, node: stop.stop_name, message: `Error: ${stop.error_message || 'Unknown error'}` };
          }
          return null;
        }).filter((log): log is LogEntry => log !== null);
        setLogs(newLogs);
        if (response.result.status === 'RUNNING' || response.result.status === 'SUBMITTED') {
          pollingRef.current = setTimeout(() => {
            loadingRef.current = false;
            loadExecutionDetail();
          }, 5000);
          return;
        }
      }
    } catch (error) {
      console.error('加载执行详情失败:', error);
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  }, [processId]);

  useEffect(() => {
    loadExecutionDetail();
    return () => {
      if (pollingRef.current) clearTimeout(pollingRef.current);
      loadingRef.current = false;
    };
  }, [loadExecutionDetail]);

  useEffect(() => {
    if (logContainerRef.current) logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
  }, [logs]);

  const handleStopExecution = async () => {
    if (!window.confirm('确定要停止执行吗？')) return;
    try {
      await stopDAGTask(processId);
      alert('已停止执行');
      loadExecutionDetail();
    } catch (error) {
      console.error('停止执行失败:', error);
      alert('停止执行失败');
    }
  };

  if (loading) {
    return (
      <div style={{ height: '100vh', background: '#f5f7fa', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px', height: '40px',
            border: '3px solid #f3f3f3',
            borderTop: '3px solid #3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }} />
          <span style={{ color: '#64748b', fontSize: '14px' }}>加载中...</span>
        </div>
      </div>
    );
  }

  if (!executionData) {
    return (
      <div style={{ height: '100vh', background: '#f5f7fa', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: '#64748b', fontSize: '14px' }}>无法获取执行详情</span>
      </div>
    );
  }

  const statusInfo = getStatusInfo(executionData.status);
  const isRunning = executionData.status === 'RUNNING';

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', padding: '20px', boxSizing: 'border-box' }}>
      <style>{`
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes rdWaterFlowLine {
          0% { stroke-dashoffset: 24; }
          100% { stroke-dashoffset: 0; }
        }
        @keyframes rdLineFlow {
          0% { stroke-dashoffset: 36; }
          100% { stroke-dashoffset: 0; }
        }
        @keyframes rdShadowExpand {
          0% { 
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); 
          }
          100% { 
            box-shadow: 0 0 0 18px rgba(16, 185, 129, 0); 
          }
        }
        .rdGridBg {
          background-image: radial-gradient(circle, #d1d5db 1px, transparent 1px);
          background-size: 20px 20px;
        }
        .rdAnimatedShadow {
          animation: rdShadowExpand 1.5s ease-out infinite;
        }
      `}</style>

      <div style={{ height: '64px', background: '#ffffff', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 16px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>RUN_{processId}</span>
            <span style={{
              fontSize: '13px', fontWeight: 600, padding: '4px 14px', borderRadius: '20px',
              backgroundColor: statusInfo.bgColor, color: statusInfo.color,
              boxShadow: `0 2px 8px ${statusInfo.color}20`
            }}>{statusInfo.label}</span>
          </div>
          <div style={{ display: 'flex', gap: '24px' }}>
            <span style={{ fontSize: '12px', color: '#64748b' }}>所属流水线: {executionData.flow_name || '-'}</span>
            <span style={{ fontSize: '12px', color: '#64748b' }}>开始时间: {executionData.started_at ? new Date(executionData.started_at).toLocaleString('zh-CN') : '-'}</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button onClick={handleBack} style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '8px 16px', border: 'none', borderRadius: '10px',
            fontSize: '13px', fontWeight: 500, cursor: 'pointer',
            background: '#f8fafc', color: '#475569',
            transition: 'all 0.2s ease',
            boxShadow: '0 2px 4px rgba(0,0,0,0.04)'
          }}>
            <ArrowLeft size={14} />
            <span>返回历史进程列表</span>
          </button>
          {isRunning && (
            <button onClick={handleStopExecution} style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '8px 16px', border: 'none', borderRadius: '10px',
              fontSize: '13px', fontWeight: 500, cursor: 'pointer',
              background: '#fef2f2', color: '#dc2626',
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 8px rgba(220, 38, 38, 0.15)'
            }}>
              <Square size={14} fill="currentColor" />
              <span>停止执行</span>
            </button>
          )}
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', gap: '20px', overflow: 'hidden' }}>
        <div style={{ flex: 1, background: '#f5f7fa', borderRadius: '16px', padding: '24px', boxShadow: '0 8px 32px rgba(0,0,0,0.06)', overflow: 'auto' }} className="rdGridBg">
          <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
            {executionData.stops.map((stop: StopInfo, index: number) => {
              const NodeIcon = getNodeIcon(stop.stop_name);
              const stopStatus = getStatusInfo(stop.status);
              const isCompleted = stop.status === 'SUCCESS';
              const isRunningStop = stop.status === 'RUNNING';
              const isFailed = stop.status === 'FAILED';
              const isPending = stop.status === 'PENDING';
              const progress = stop.progress || (isCompleted ? 100 : 0);

              return (
                <React.Fragment key={index}>
                  <div
                    className={(isCompleted || isRunningStop) ? 'rdAnimatedShadow' : ''}
                    style={{
                      display: 'flex', flexDirection: 'column', gap: '8px',
                      padding: '20px',
                      background: '#ffffff',
                      border: `2px solid ${stopStatus.borderColor}`,
                      borderRadius: '12px',
                      minWidth: '200px',
                      position: 'relative',
                      boxShadow: isCompleted ? `0 4px 16px ${stopStatus.color}25` : isRunningStop ? '0 4px 16px rgba(0,0,0,0.1)' : '0 4px 16px rgba(0,0,0,0.06)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <span style={{ fontSize: '15px', fontWeight: 600, color: '#0f172a' }}>{stop.stop_name}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      {(stop.processed_records != null || stop.total_records != null) ? (
                        <span style={{
                          fontSize: '12px', fontStyle: 'italic',
                          color: isCompleted ? '#22c55e' : isRunningStop ? '#1f2937' : isFailed ? '#ef4444' : '#9ca3af'
                        }}>
                          {isCompleted ? `Done: ${stop.processed_records || stop.total_records} recs` :
                           isRunningStop ? `Proc: ${stop.processed_records || 0} recs` :
                           isFailed ? '执行失败' : '等待执行'}
                        </span>
                      ) : (
                        <div></div>
                      )}
                      <span style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b' }}>{progress}%</span>
                    </div>
                    <div style={{
                      position: 'absolute', top: '-12px', right: '-12px',
                      width: '24px', height: '24px',
                      borderRadius: '50%',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      backgroundColor: isPending ? '#9CA3AF' : '#10B981',
                      border: '2px solid #ffffff',
                      boxShadow: isPending ? '0 2px 8px rgba(156, 163, 175, 0.4)' : '0 2px 8px rgba(16, 185, 129, 0.4)',
                    }}>
                      {isCompleted && <Check size={12} style={{ color: '#ffffff' }} />}
                      {isRunningStop && <Play size={12} style={{ color: '#ffffff' }} />}
                      {isFailed && <X size={12} style={{ color: '#ffffff' }} />}
                      {isPending && <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#ffffff' }} />}
                    </div>
                  </div>

                  {index < executionData.stops.length - 1 && (
                    <div style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      width: '80px', height: '48px', position: 'relative',
                      opacity: isPending ? '0.3' : '1'
                    }}>
                      <svg width="80" height="24" viewBox="0 0 80 24">
                        <line
                          x1="0" y1="12" x2="55" y2="12"
                          stroke="#E2E8F0" strokeWidth="2"
                        />
                        <line
                          x1="0" y1="12" x2="55" y2="12"
                          stroke={isCompleted || isRunningStop ? '#0F172A' : '#9CA3AF'}
                          strokeWidth={isCompleted || isRunningStop ? '3' : '2'}
                          strokeDasharray="10 8"
                          fill="none"
                          style={{ animation: 'rdLineFlow 1.2s linear infinite' }}
                        />
                        <polygon
                          points="75,12 60,6 60,18"
                          fill={isCompleted || isRunningStop ? '#0F172A' : '#9CA3AF'}
                        />
                      </svg>
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        <div style={{
          width: '440px', background: '#0f172a', borderRadius: '16px',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
          flexShrink: 0,
          boxShadow: '0 8px 32px rgba(0,0,0,0.15)'
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '20px 24px', background: '#1e293b', borderBottom: '1px solid #334155'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#22c55e', boxShadow: '0 0 8px #22c55e' }} />
              <span style={{ fontSize: '15px', fontWeight: 600, color: '#f1f5f9' }}>运行日志</span>
            </div>
            {isRunning && <span style={{ fontSize: '12px', color: '#22c55e', fontWeight: 500 }}>实时同步中...</span>}
          </div>
          <div ref={logContainerRef} style={{ flex: 1, overflowY: 'auto', padding: '20px 24px' }}>
            {logs.length > 0 ? (
              logs.map((log, index) => (
                <div key={index} style={{
                  display: 'flex', flexWrap: 'wrap', gap: '10px',
                  padding: '12px 16px', marginBottom: '8px',
                  background: '#1e293b', borderRadius: '8px',
                  fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace", fontSize: '12px', lineHeight: 1.6
                }}>
                  <span style={{ color: '#94a3b8', fontWeight: 500 }}>[{log.time}]</span>
                  <span style={{ color: '#38bdf8', fontWeight: 500 }}>[{log.node}]</span>
                  <span style={{ color: '#e2e8f0', wordBreak: 'break-word' }}>{log.message}</span>
                </div>
              ))
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569' }}>
                <span>暂无日志信息</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div style={{
        padding: '16px 20px', background: '#ffffff', borderTop: '1px solid #e2e8f0',
        display: 'flex', flexDirection: 'column', gap: '16px',
        marginTop: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 500 }}>节点总数</span>
            <span style={{ fontSize: '20px', fontWeight: 700, color: '#0f172a' }}>{executionData.total_stop_count}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 500 }}>成功</span>
            <span style={{ fontSize: '20px', fontWeight: 700, color: '#16a34a' }}>{executionData.success_stop_count}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 500 }}>失败</span>
            <span style={{ fontSize: '20px', fontWeight: 700, color: '#dc2626' }}>{executionData.failed_stop_count}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 500 }}>跳过</span>
            <span style={{ fontSize: '20px', fontWeight: 700, color: '#f59e0b' }}>{executionData.skipped_stop_count}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', paddingLeft: '24px', borderLeft: '1px solid #e2e8f0' }}>
            <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 500 }}>执行时长</span>
            <span style={{ fontSize: '18px', fontWeight: 600, color: '#334155' }}>{calculateDuration(executionData.started_at, executionData.finished_at)}</span>
          </div>
        </div>
        
        {executionData.final_output_paths && executionData.final_output_paths.length > 0 && (
          <div style={{
            padding: '16px', background: '#f8fafc',
            borderRadius: '10px', border: '1px solid #e2e8f0'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <Download size={16} style={{ color: '#2563eb' }} />
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>结果文件</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {executionData.final_output_paths.map((file: string, index: number) => (
                <a key={index} href={downloadWorkspaceUrl2(file)} target="_blank" rel="noopener noreferrer" style={{
                  display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 14px',
                  background: '#ffffff', color: '#2563eb', textDecoration: 'none',
                  borderRadius: '8px', fontSize: '13px', fontWeight: 500,
                  border: '1px solid #dbeafe',
                  boxShadow: '0 2px 8px rgba(37, 99, 235, 0.08)',
                  transition: 'all 0.2s ease'
                }}>
                  <Download size={14} />
                  <span>{file.split('/').pop() || file}</span>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RunDetails;
