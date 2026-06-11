import { Icon } from "@iconify/react";
import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { runDAGTask, saveDrawInfo, getDrawInfoBymegId, getAllSkills } from "../lib/api";
import { generateUUID } from "../lib/ids";
import { toast } from "./Toast";

interface PipelineNode {
  node_name: string;
  skill_name?: string;
  skill_id?: string;
  skill?: { skill_id?: string };
  params?: Record<string, unknown>;
}

interface PipelineTask {
  name: string;
  description?: string;
  nodes?: PipelineNode[];
}

export interface PipelineData {
  task: PipelineTask;
  nodes: PipelineNode[];
}

interface ExtractionResult {
  data: PipelineData | null;
  cleanedText: string;
}

function tryParseAsPipeline(obj: unknown): PipelineData | null {
  if (!obj || typeof obj !== "object") return null;
  const record = obj as Record<string, unknown>;
  
  let task = record.task;
  if (!task || typeof task !== "object") {
    // 如果没有task，尝试直接从顶层找nodes
    if (Array.isArray(record.nodes) && record.nodes.length > 0) {
      return { 
        task: { name: "Pipeline" }, 
        nodes: record.nodes as PipelineNode[] 
      };
    }
    return null;
  }
  
  const taskRecord = task as Record<string, unknown>;
  const taskName = typeof taskRecord.name === "string" ? taskRecord.name : "Pipeline";
  
  let nodes: unknown[] | undefined;
  if (Array.isArray(record.nodes) && record.nodes.length > 0) {
    nodes = record.nodes;
  } else if (Array.isArray(taskRecord.nodes) && taskRecord.nodes.length > 0) {
    nodes = taskRecord.nodes;
  }
  
  if (!nodes) {
    // 尝试在其他可能的字段名
    if (Array.isArray(record.steps) && record.steps.length > 0) {
      nodes = record.steps;
    } else if (Array.isArray(taskRecord.steps) && taskRecord.steps.length > 0) {
      nodes = taskRecord.steps;
    }
  }
  
  if (!nodes) return null;
  return { task: { name: taskName, ...taskRecord } as PipelineData, nodes: nodes as PipelineNode[] };
}

export function extractPipelineJson(text: string): PipelineData | null {
  if (!text || typeof text !== "string") {
    return null;
  }
  
  const trimmed = text.trim();
  
  try {
    const parsed = JSON.parse(trimmed);
    return tryParseAsPipeline(parsed);
  } catch {}
  
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
    try {
      const inner = JSON.parse(trimmed) as string;
      if (typeof inner === "string") {
        return tryParseAsPipeline(JSON.parse(inner));
      }
    } catch {}
  }
  
  const codeBlockRegex = /```[\s\S]*?\n?([\s\S]*?)```/g;
  let match;
  let lastValidMatch: { match: RegExpExecArray; parsed: PipelineData } | null = null;
  
  while ((match = codeBlockRegex.exec(text)) !== null) {
    try {
      const parsed = JSON.parse(match[1].trim());
      const result = tryParseAsPipeline(parsed);
      if (result) {
        lastValidMatch = { match, parsed: result };
      }
    } catch {}
  }
  
  return lastValidMatch?.parsed || null;
}

export function extractAndCleanPipelineJson(text: string): ExtractionResult {
  if (!text || typeof text !== "string") {
    return { data: null, cleanedText: text || '' };
  }
  
  const trimmed = text.trim();
  
  try {
    const parsed = JSON.parse(trimmed);
    const result = tryParseAsPipeline(parsed);
    if (result) {
      return { data: result, cleanedText: '' };
    }
  } catch {}
  
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
    try {
      const inner = JSON.parse(trimmed) as string;
      if (typeof inner === "string") {
        const innerParsed = JSON.parse(inner);
        const result = tryParseAsPipeline(innerParsed);
        if (result) {
          return { data: result, cleanedText: '' };
        }
      }
    } catch {}
  }
  
  // 更通用的代码块匹配，支持任何语言标识
  const codeBlockRegex = /```[^\n]*\n?([\s\S]*?)```/g;
  let match;
  let lastValidMatch: { match: RegExpExecArray; parsed: PipelineData } | null = null;
  
  while ((match = codeBlockRegex.exec(text)) !== null) {
    try {
      const jsonContent = match[1].trim();
      // 尝试解析
      const parsed = JSON.parse(jsonContent);
      const result = tryParseAsPipeline(parsed);
      if (result) {
        lastValidMatch = { match, parsed: result };
      }
    } catch {}
  }
  
  if (lastValidMatch) {
    const { match: matched, parsed } = lastValidMatch;
    const before = text.substring(0, matched.index);
    const after = text.substring(matched.index + matched[0].length);
    return { 
      data: parsed, 
      cleanedText: (before + after).trim() 
    };
  }
  
  return { data: null, cleanedText: text };
}



interface PipelinePreviewProps {
  data: PipelineData;
  threadId: string;
  onOpenCanvas?: (data: PipelineData, messageId?: string) => void;
  messageId?: number;
}

// 边类型定义（仅用于 UI 显示）
interface PipelineEdge {
  id: string;
  source: string;
  target: string;
}

// 从nodes生成边（仅用于 UI 显示，根据参数引用关系生成）
function generateEdges(nodes: PipelineNode[]): PipelineEdge[] {
  const edges: PipelineEdge[] = [];
  const nodeNameToIdMap: Record<string, string> = {};
  
  // 先构建节点名称到ID的映射
  nodes.forEach((node, index) => {
    nodeNameToIdMap[node.node_name] = `node-${index + 1}`;
  });
  
  // 遍历每个节点，查找参数中的引用关系
  nodes.forEach((node, targetIndex) => {
    const targetNodeId = `node-${targetIndex + 1}`;
    const params = node.params || {};
    
    Object.values(params).forEach((paramValue: any) => {
      if (typeof paramValue === 'object' && paramValue !== null && 'source_node' in paramValue) {
        const sourceNodeName = paramValue.source_node;
        const sourceNodeId = nodeNameToIdMap[sourceNodeName];
        
        if (sourceNodeId && sourceNodeId !== targetNodeId) {
          // 检查边是否已存在
          const edgeExists = edges.some(
            e => e.source === sourceNodeId && e.target === targetNodeId
          );
          
          if (!edgeExists) {
            edges.push({
              id: `e${sourceNodeId}-${targetNodeId}`,
              source: sourceNodeId,
              target: targetNodeId,
            });
          }
        }
      }
    });
  });
  
  // 如果没有找到任何引用关系，回退到顺序连接
  if (edges.length === 0) {
    for (let i = 0; i < nodes.length - 1; i++) {
      edges.push({
        id: `e${i + 1}-${i + 2}`,
        source: `node-${i + 1}`,
        target: `node-${i + 2}`,
      });
    }
  }
  
  return edges;
}

export default function PipelinePreview({ data, threadId, onOpenCanvas, messageId }: PipelinePreviewProps) {
  const navigate = useNavigate();
  const { task, nodes } = data;

  // 仅用于 UI 显示的边
  const edges = useMemo(() => generateEdges(nodes), [nodes]);

  const handleRun = async () => {
    console.log('点击一键运行');
    console.log('会话返回的任务数据:', data);
    
    try {
      let drawData: any;
      
      // 缓存：按 skill_name 缓存算子查询结果
      const skillsCache: Record<string, any> = {};
      
      // 根据 skill_name 获取算子信息（带缓存）
      const getSkillInfoByName = async (skillName: string): Promise<any | null> => {
        if (skillsCache[skillName]) {
          return skillsCache[skillName];
        }
        
        try {
          const res = await getAllSkills(skillName);
          console.log(`根据 skill_name="${skillName}" 查询算子:`, res);
          skillsCache[skillName] = res;
          return res;
        } catch (error) {
          console.error(`获取算子 ${skillName} 失败`, error);
          skillsCache[skillName] = null;
          return null;
        }
      };
      
      // 优先从已保存的画板获取数据
      if (messageId) {
        console.log('调用 getDrawInfoBymegId 获取已保存的画板信息');
        const savedResponse = await getDrawInfoBymegId(String(messageId));
        console.log('已保存画板数据:', savedResponse);
        
        if (savedResponse.code === 200 && savedResponse.result) {
          const savedResult = savedResponse.result as any;
          console.log('savedResult 完整数据:', savedResult);
          console.log('savedResult.nodes:', savedResult.nodes);
          if (savedResult.nodes && savedResult.nodes.length > 0) {
            // 处理已保存的节点数据，尝试获取 skill_id
            const processedSavedNodes = [];
            for (const node of savedResult.nodes) {
              console.log('单个已保存节点数据:', node);
              
              let skillId = node.skill?.skill_id || node.skill_id || '';
              let iconPath = node.icon_path || '';
              let skillNameToSearch = '';
              
              // 如果已有 skill_id，直接使用
              if (skillId) {
                console.log('已保存节点已有 skill_id:', skillId);
              } else {
                // 从原始会话数据中查找对应的节点，获取 skill_name
                const originalNode = nodes.find((n: any) => n.node_name === node.node_name);
                if (originalNode && originalNode.skill_name) {
                  skillNameToSearch = originalNode.skill_name;
                  console.log('从原始数据中找到 skill_name:', skillNameToSearch);
                }
                
                // 处理特殊算子名称，写死 skill_id
                if (skillNameToSearch === 'source_stop') {
                  skillId = 'cn.piflow.engine.local.source_file_stop.SourceFileStop';
                } else if (skillNameToSearch === 'sink_stop') {
                  skillId = 'cn.piflow.engine.local.file_save_stop.FileSaveStop';
                } else if (skillNameToSearch) {
                  // 根据 skill_name 去查询算子信息
                  const skillRes = await getSkillInfoByName(skillNameToSearch);
                  if (skillRes && skillRes.result.data && skillRes.result.data.length > 0) {
                    for (const group of skillRes.result.data) {
                      if (group.DagSkillInfoList && group.DagSkillInfoList.length > 0) {
                        for (const skillInfo of group.DagSkillInfoList) {
                          if (skillInfo.skill_name === skillNameToSearch || skillInfo.name_zh === node.node_name) {
                            skillId = skillInfo.skill_id || '';
                            iconPath = skillInfo.icon_path || '';
                            console.log('为已保存节点找到 skill_id:', skillId);
                            break;
                          }
                        }
                      }
                      if (skillId) break;
                    }
                  }
                }
              }
              
              // 获取算子详情来获取 output_params（如果没有的话）
              let outParams = [];
              if (skillId && (!node.out_params || node.out_params.length === 0)) {
                // 从已查询过的算子信息中查找（通过遍历缓存）
                for (const cachedSkillName of Object.keys(skillsCache)) {
                  const cachedResult = skillsCache[cachedSkillName];
                  if (cachedResult && cachedResult.result.data && cachedResult.result.data.length > 0) {
                    for (const group of cachedResult.result.data) {
                      if (group.DagSkillInfoList && group.DagSkillInfoList.length > 0) {
                        for (const skillInfo of group.DagSkillInfoList) {
                          if (skillInfo.skill_id === skillId) {
                            const outputParams = skillInfo.output_params?.params || [];
                            outParams = outputParams.map((p: any) => ({
                              param_name: p.name || p.param_name || '',
                              param_type: p.type || p.param_type || 'string'
                            }));
                            break;
                          }
                        }
                      }
                      if (outParams.length > 0) break;
                    }
                  }
                  if (outParams.length > 0) break;
                }
              } else if (node.out_params) {
                outParams = (node.out_params.params || node.out_params).map((p: any) => ({
                  param_name: p.param_name || p.name || '',
                  param_type: p.param_type || p.type || 'string'
                }));
              }
              
              // 处理 input_params
              let inputParams = [];
              if (node.input_params?.params) {
                inputParams = node.input_params.params.map((p: any) => ({
                  param_name: p.name || p.param_name || '',
                  param_value: p.value || p.param_value || '',
                  value_mode: p._refType === 'reference' ? 'reference' : (p.value_mode || 'manual'),
                  binding_id: p.binding_id || ''
                }));
              } else if (node.input_params && Array.isArray(node.input_params)) {
                inputParams = node.input_params.map((p: any) => ({
                  param_name: p.name || p.param_name || '',
                  param_value: p.value || p.param_value || '',
                  value_mode: p._refType === 'reference' ? 'reference' : (p.value_mode || 'manual'),
                  binding_id: p.binding_id || ''
                }));
              }
              
              processedSavedNodes.push({
                node_id: node.node_id || node.id,
                node_name: node.node_name,
                node_type: 'default',
                icon_path: iconPath,
                skill: {
                  skill_id: skillId,
                  version: '1.0'
                },
                position: node.position || { x: 0, y: 0 },
                input_params: inputParams,
                out_params: outParams
              });
            }
            
            // 使用已保存的画板数据
            drawData = {
              dsl_version: "1.0",
              task: {
                dag_task_id: savedResult.task?.dag_task_id || '',
                dag_task_name: savedResult.task?.dag_task_name || task.name,
                description: savedResult.task?.description || task.description || '',
                message_id: messageId ? String(messageId) : ''
              },
              nodes: processedSavedNodes,
              edges: (savedResult.edges || []).map((e: any) => ({
                edge_id: e.edge_id || e.id,
                from_node_id: e.from_node_id || e.source,
                to_node_id: e.to_node_id || e.target
              })),
              bindings: savedResult.bindings || []
            };
            console.log('使用已保存的画板数据，处理后的节点:', processedSavedNodes);
          }
        }
      }
      
      // 如果没有已保存的画板数据，使用会话JSON信息
      if (!drawData) {
        console.log('没有已保存的画板数据，使用会话JSON信息');
        console.log('节点原始数据:', nodes);
        
        // 节点名称到节点ID的映射
        const nodeNameToIdMap: Record<string, string> = {};
        
        // 先处理所有节点，通过 skill_name 查找 skill_id
        const processedNodes = [];
        for (let index = 0; index < nodes.length; index++) {
          const node = nodes[index] as any;
          console.log(`第 ${index} 个节点数据:`, node);
          
          let skillId = '';
          let iconPath = '';
          
          // 尝试通过 skill_name 查找 skill_id
          let skillName = node.skill_name || '';
          
          // 处理特殊算子名称，写死 skill_id
          if (skillName === 'source_stop') {
            skillId = 'cn.piflow.engine.local.source_file_stop.SourceFileStop';
          } else if (skillName === 'sink_stop') {
            skillId = 'cn.piflow.engine.local.file_save_stop.FileSaveStop';
          } else if (skillName) {
            // 根据 skill_name 去查询算子信息（带缓存）
            const skillRes = await getSkillInfoByName(skillName);
            if (skillRes && skillRes.result.data && skillRes.result.data.length > 0) {
              for (const group of skillRes.result.data) {
                if (group.DagSkillInfoList && group.DagSkillInfoList.length > 0) {
                  for (const skillInfo of group.DagSkillInfoList) {
                    if (skillInfo.skill_name === skillName || skillInfo.name_zh === skillName) {
                      skillId = skillInfo.skill_id || '';
                      iconPath = skillInfo.icon_path || '';
                      console.log(`找到匹配的算子:`, skillInfo);
                      break;
                    }
                  }
                }
                if (skillId) break;
              }
            }
          }
          
          console.log(`节点 ${index} 获取到的 skill_id:`, skillId, `skill_name:`, skillName);
          
          // 获取算子 input_params 和 output_params
          let inputParams: any[] = [];
          let outputParams: any[] = [];
          
          // 对于 source_stop 和 sink_stop 特殊算子，直接使用会话返回的参数，不调用接口
          let mergedInputParams: any[] = [];
          let outParams: any[] = [];
          
          if (skillName === 'source_stop' || skillName === 'sink_stop') {
            // 特殊算子，直接使用会话返回的参数
            const nodeParams = node.params || {};
            mergedInputParams = Object.entries(nodeParams).map(([paramName, paramValue]: any) => {
              if (typeof paramValue === 'object' && paramValue !== null && 'source_node' in paramValue) {
                // 引用类型
                return {
                  param_name: paramName,
                  param_value: paramValue.source_param || '',
                  value_mode: 'reference',
                  binding_id: ''
                };
              } else {
                // 手动类型
                return {
                  param_name: paramName,
                  param_value: String(paramValue),
                  value_mode: 'manual',
                  binding_id: ''
                };
              }
            });
            
            // source_stop 有输出参数，sink_stop 没有输出参数
            if (skillName === 'source_stop') {
              outParams = [{
                param_name: 'output',
                param_type: 'string'
              }];
            } else {
              outParams = [];
            }
            
            console.log(`节点 ${index}: 特殊算子，直接使用会话返回的参数:`, { mergedInputParams, outParams });
          } else {
            // 普通算子，调用接口获取参数信息并合并
            if (skillName) {
              // 使用 getAllSkills 接口获取算子信息（带缓存）
              const skillRes = await getSkillInfoByName(skillName);
              if (skillRes && skillRes.result.data && skillRes.result.data.length > 0) {
                for (const group of skillRes.result.data) {
                  if (group.DagSkillInfoList && group.DagSkillInfoList.length > 0) {
                    for (const skillInfo of group.DagSkillInfoList) {
                      // 使用 skill_name 匹配，因为接口返回的 skill_id 和写死的格式不同
                      if (skillInfo.skill_name === skillName || skillInfo.name_zh === skillName) {
                        inputParams = skillInfo.input_params?.params || [];
                        outputParams = skillInfo.output_params?.params || [];
                        console.log(`节点 ${index}: 从 getAllSkills 获取参数信息:`, { inputParams, outputParams });
                        break;
                      }
                    }
                  }
                  if (inputParams.length > 0) break;
                }
              }
            }
            
            // 合并节点参数到 input_params，处理引用类型
            mergedInputParams = inputParams.map((paramDef: any) => {
              const paramName = paramDef.name || paramDef.param_name;
              const paramValue = (node.params || {})[paramName];
              
              if (paramValue !== undefined) {
                if (typeof paramValue === 'object' && paramValue !== null && 'source_node' in paramValue) {
                  // 引用类型
                  return {
                    param_name: paramName,
                    param_value: paramValue.source_param || '',
                    value_mode: 'reference',
                    binding_id: ''
                  };
                } else {
                  // 手动类型
                  return {
                    param_name: paramName,
                    param_value: String(paramValue),
                    value_mode: 'manual',
                    binding_id: ''
                  };
                }
              }
              
              return {
                param_name: paramName,
                param_value: paramDef.param_value || '',
                value_mode: 'manual',
                binding_id: ''
              };
            });
            
            // 转换 output_params 格式
            outParams = outputParams.map((p: any) => ({
              param_name: p.name || p.param_name || '',
              param_type: p.type || p.param_type || 'string'
            }));
          }
          
          // 节点ID从 node-1 开始，与 Draw.tsx 保持一致
          const nodeId = `node-${index + 1}`;
          processedNodes.push({
            node_id: nodeId,
            node_name: node.node_name,
            node_type: 'default',
            icon_path: iconPath,
            skill: {
              skill_id: skillId,
              version: '1.0'
            },
            position: { x: 100 + index * 200, y: 200 },
            input_params: mergedInputParams,
            out_params: outParams
          });
          
          // 构建节点名称到ID的映射
          nodeNameToIdMap[node.node_name] = nodeId;
        }
        
        // 生成 edges 和 bindings：根据原始节点的 params 中的 source_node 引用关系
        const generatedEdges: any[] = [];
        const generatedBindings: any[] = [];
        
        processedNodes.forEach((node, index) => {
          const originalNode = nodes[index];
          const dagParams = originalNode.params || {};
          
          // 遍历节点的每个参数，查找引用关系
          Object.entries(dagParams).forEach(([paramName, paramValue]: any) => {
            if (typeof paramValue === 'object' && paramValue !== null && 'source_node' in paramValue) {
              const sourceNodeName = paramValue.source_node;
              const sourceParamName = paramValue.source_param;
              const sourceNodeId = nodeNameToIdMap[sourceNodeName];
              
              if (sourceNodeId && sourceNodeId !== node.node_id) {
                // 生成边（避免重复）
                const edgeExists = generatedEdges.some(
                  e => e.from_node_id === sourceNodeId && e.to_node_id === node.node_id
                );
                if (!edgeExists) {
                  generatedEdges.push({
                    edge_id: `edge-${sourceNodeId}-${node.node_id}`,
                    from_node_id: sourceNodeId,
                    to_node_id: node.node_id
                  });
                }
                
                // 生成 binding
                generatedBindings.push({
                  binding_id: generateUUID(),
                  from_node_id: sourceNodeId,
                  from_param_name: sourceParamName,
                  to_node_id: node.node_id,
                  to_param_name: paramName
                });
              }
            }
          });
        });
        
        console.log('生成的 edges:', generatedEdges);
        console.log('生成的 bindings:', generatedBindings);
        
        drawData = {
          dsl_version: "1.0",
          task: {
            dag_task_id: '',
            dag_task_name: task.name,
            description: task.description || '',
            message_id: messageId ? String(messageId) : ''
          },
          nodes: processedNodes,
          edges: generatedEdges,
          bindings: generatedBindings
        };
      }
      
      // 检查是否已经有 dag_task_id
      const hasExistingTaskId = drawData.task.dag_task_id && drawData.task.dag_task_id !== '';
      
      // 保存画板
      console.log('保存画板数据:', drawData);
      let saveResponse = await saveDrawInfo(drawData);
      console.log('保存画板返回:', saveResponse);
      
      // 从保存响应中获取 task_id
      let taskId = '';
      if (saveResponse.code === 200 && saveResponse.result) {
        taskId = saveResponse.result.task_id || saveResponse.result.dag_task_id || saveResponse.result.task?.dag_task_id || saveResponse.result.task?.task_id || '';
      }
      
      if (!taskId) {
        throw new Error('保存画板未返回任务ID');
      }
      
      console.log('获取到任务ID:', taskId);
      
      // 如果原来没有 dag_task_id，才需要第二次保存
      if (!hasExistingTaskId) {
        // 第二次保存，带上任务ID
        drawData.task.dag_task_id = taskId;
        console.log('第二次保存画板数据:', drawData);
        saveResponse = await saveDrawInfo(drawData);
        console.log('第二次保存画板返回:', saveResponse);
      } else {
        console.log('已有 dag_task_id，跳过第二次保存');
      }
      
      // 调用运行接口
      const response = await runDAGTask(taskId);
      console.log('运行 DAG 返回结果:', response);
      if (response.code === 200 && response.result) {
        const processId = response.result.process_id;
        toast.success(`任务已提交运行，请前往【运行历史】查看执行状态。执行实例ID：${processId}`);
        return;
      } else {
        console.error('运行 DAG 失败:', response.message);
        toast.error('运行失败: ' + (response.message || '未知错误'));
        return;
      }
    } catch (error) {
      console.error('操作失败:', error);
      toast.error('操作失败: ' + (error instanceof Error ? error.message : '未知错误'));
      return;
    }
  };

  const handleEdit = () => {
    // 调用回调打开画板，而不是跳转页面
    if (onOpenCanvas) {
      onOpenCanvas(data, messageId);
    }
  };

  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <style>{`
        @keyframes pipelineFadeIn {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pipelineSlideIn {
          from { opacity: 0; transform: translateY(16px) scale(0.95); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes pipelineArrowIn {
          from { opacity: 0; transform: scaleY(0); }
          to { opacity: 1; transform: scaleY(1); }
        }
        @keyframes pipelineStaggerIn {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .pipeline-container {
          animation: pipelineFadeIn 0.4s ease-out both;
        }
        .pipeline-title {
          animation: pipelineFadeIn 0.3s ease-out 0.1s both;
        }
        .pipeline-level {
          animation: pipelineSlideIn 0.45s ease-out both;
        }
        .pipeline-arrow {
          animation: pipelineArrowIn 0.3s ease-out both;
          transform-origin: top center;
        }
        .pipeline-buttons {
          animation: pipelineFadeIn 0.5s ease-out both;
        }
      `}</style>
      {/* 标题和状态 */}
      <div className="mb-3 flex items-center justify-between pipeline-title">
        <div className="flex items-center gap-2">
          <Icon icon="ri:flow-chart" className="text-blue-600" width={20} />
          <span className="font-medium text-slate-900">{task.name}</span>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <Icon icon="ri:node" width={14} />
            {nodes.length} 节点
          </span>
          <span className="flex items-center gap-1">
            <Icon icon="ri:arrow-right-line" width={14} />
            {edges.length} 边
          </span>
          <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-600">
            <Icon icon="ri:check-line" width={12} />
            验证通过
          </span>
        </div>
      </div>

      {/* 简易DAG图 - 拓扑分层显示，每个节点只出现一次 */}
      <div className="mb-4 overflow-x-auto rounded-lg bg-slate-50 p-3">
        {(() => {
          // 解析节点引用关系，构建图结构
          const nodeNameToIndexMap: Record<string, number> = {};
          nodes.forEach((node, index) => {
            nodeNameToIndexMap[node.node_name] = index;
          });
          
          const inDegree: number[] = new Array(nodes.length).fill(0);
          const nodeOutEdges: number[][] = new Array(nodes.length).fill(null).map(() => []);
          
          nodes.forEach((pNode, targetIndex) => {
            const dagParams = pNode.params || {};
            Object.values(dagParams).forEach((paramValue: any) => {
              if (typeof paramValue === 'object' && paramValue !== null && 'source_node' in paramValue) {
                const sourceNodeName = paramValue.source_node;
                const sourceIndex = nodeNameToIndexMap[sourceNodeName];
                
                if (sourceIndex !== undefined && sourceIndex !== targetIndex) {
                  const edgeAlreadyExists = nodeOutEdges[sourceIndex].includes(targetIndex);
                  if (!edgeAlreadyExists) {
                    inDegree[targetIndex]++;
                    nodeOutEdges[sourceIndex].push(targetIndex);
                  }
                }
              }
            });
          });
          
          if (nodeOutEdges.every(edges => edges.length === 0)) {
            for (let i = 0; i < nodes.length - 1; i++) {
              nodeOutEdges[i].push(i + 1);
            }
          }
          
          // 拓扑排序分层
          const levels: number[][] = [];
          const tempInDegree = [...inDegree];
          const processed = new Set<number>();
          
          let currentLevel: number[] = [];
          for (let i = 0; i < nodes.length; i++) {
            if (tempInDegree[i] === 0 && !processed.has(i)) {
              currentLevel.push(i);
              processed.add(i);
            }
          }
          
          while (currentLevel.length > 0) {
            levels.push(currentLevel);
            const nextLevel: number[] = [];
            currentLevel.forEach(index => {
              nodeOutEdges[index].forEach(targetIndex => {
                if (!processed.has(targetIndex)) {
                  tempInDegree[targetIndex]--;
                  if (tempInDegree[targetIndex] === 0) {
                    nextLevel.push(targetIndex);
                    processed.add(targetIndex);
                  }
                }
              });
            });
            currentLevel = nextLevel;
          }
          
          if (processed.size < nodes.length) {
            for (let i = 0; i < nodes.length; i++) {
              if (!processed.has(i)) {
                levels.push([i]);
              }
            }
          }
          
          // 设置每个level的最大宽度，让所有节点居中
          const maxNodesInLevel = Math.max(...levels.map(l => l.length));
          
          // 颜色配置 - 根据节点索引分配不同颜色
          const nodeColors = [
            { bg: '#f3e8ff', border: '#a855f7', dot: '#c084fc' },  // 紫色
            { bg: '#e0f2fe', border: '#0ea5e9', dot: '#38bdf8' },  // 青色
            { bg: '#fef3c7', border: '#f59e0b', dot: '#fbbf24' },  // 橙色
            { bg: '#dcfce7', border: '#22c55e', dot: '#4ade80' },  // 绿色
            { bg: '#fce7f3', border: '#ec4899', dot: '#f472b6' },  // 粉色
            { bg: '#e0e7ff', border: '#6366f1', dot: '#818cf8' },  // 靛蓝
            { bg: '#fed7aa', border: '#f97316', dot: '#fb923c' },  // 琥珀色
            { bg: '#d1fae5', border: '#10b981', dot: '#34d399' },  // 翡翠色
          ];
          
          const getNodeColor = (index: number) => {
            return nodeColors[index % nodeColors.length];
          };
          
          // 判断是否为分支节点
          const isForkNode = (node: PipelineNode) => {
            return node.skill_name?.toLowerCase().includes('fork') || 
                   node.node_name?.toLowerCase().includes('分支');
          };
          
          const isMergeNode = (node: PipelineNode) => {
            return node.skill_name?.toLowerCase().includes('merge') || 
                   node.node_name?.toLowerCase().includes('合并');
          };
          
          // 渲染
          return (
            <div className="flex flex-col items-center gap-2 pipeline-container">
              {levels.map((level, levelIndex) => (
                <div key={levelIndex} className="flex flex-col items-center w-full">
                  {/* 当前层节点 */}
                  <div className="flex gap-6 justify-center items-center pipeline-level" style={{ animationDelay: `${0.15 + levelIndex * 0.2}s` }}>
                    {level.map((nodeIndex) => {
                      const node = nodes[nodeIndex];
                      const color = getNodeColor(nodeIndex);
                      const fork = isForkNode(node);
                      const merge = isMergeNode(node);
                      
                      return (
                        <div key={nodeIndex} className="flex flex-col items-center">
                          {/* 菱形节点 - Fork/Merge */}
                          {fork || merge ? (
                            <div 
                              className="flex items-center justify-center p-2"
                              style={{ 
                                width: '90px', 
                                height: '50px',
                                backgroundColor: '#fef3c7',
                                border: `2px solid #f59e0b`,
                                clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'
                              }}
                            >
                              <div className="text-xs font-bold text-orange-600 text-center">
                                {fork ? '分支' : '合并'}
                              </div>
                            </div>
                          ) : (
                            // 圆角矩形节点
                            <div 
                              className="flex items-center gap-2 px-4 py-2 rounded-full"
                              style={{ 
                                backgroundColor: color.bg,
                                border: `2px solid ${color.border}`,
                                minWidth: '120px'
                              }}
                            >
                              {/* 小圆点 */}
                              <div 
                                className="w-3 h-3 rounded-full flex-shrink-0"
                                style={{ backgroundColor: color.dot }}
                              />
                              {/* 节点名称 */}
                              <div className="text-sm font-medium text-slate-700 whitespace-nowrap">
                                {node.node_name}
                              </div>
                            </div>
                          )}
                          {/* 技能名称 */}
                          {node.skill_name && !fork && !merge && (
                            <div className="mt-1 text-xs text-slate-400">
                              {node.skill_name}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  
                  {/* 层级之间的连接箭头 */}
                  {levelIndex < levels.length - 1 && (
                    <div className="flex justify-center items-center py-2 pipeline-arrow" style={{ minHeight: '32px', animationDelay: `${0.35 + levelIndex * 0.2}s` }}>
                      {level.map((nodeIndex) => {
                        const targets = nodeOutEdges[nodeIndex];
                        if (targets.length === 0) return null;
                        return (
                          <div key={nodeIndex} className="flex items-center justify-center" style={{ width: '136px' }}>
                            <div className="relative">
                              {/* 箭头线 */}
                              <div className="w-px h-6 bg-slate-300 mx-auto"></div>
                              {/* 箭头 */}
                              <svg 
                                width="16" 
                                height="16" 
                                viewBox="0 0 24 24" 
                                fill="none" 
                                className="absolute left-1/2 -translate-x-1/2 -translate-y-1"
                              >
                                <path 
                                  d="M12 19V5M8 11l4 4 4-4" 
                                  stroke="#9ca3af" 
                                  strokeWidth="2" 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round"
                                />
                              </svg>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          );
        })()}
      </div>

      {/* 按钮组 */}
      <div className="flex gap-2 pipeline-buttons" style={{ animationDelay: `1.2s` }}>
        <button
          onClick={handleRun}
          className="flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800"
        >
          <Icon icon="ri:play-fill" width={16} />
          一键运行
        </button>
        <button
          onClick={handleEdit}
          className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
        >
          <Icon icon="ri:edit-line" width={16} />
          打开画板编辑
        </button>
        <button
          onClick={() => {
            if (data) {
              const jsonStr = JSON.stringify(data, null, 2);
              const blob = new Blob([jsonStr], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const link = document.createElement('a');
              link.href = url;
              link.download = `${task.name || 'dag'}_${Date.now()}.json`;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              URL.revokeObjectURL(url);
            } else {
              alert('没有可导出的JSON数据');
            }
          }}
          className="flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-600"
        >
          <Icon icon="ri:download-line" width={16} />
          导出JSON
        </button>
      </div>
    </div>
  );
}
