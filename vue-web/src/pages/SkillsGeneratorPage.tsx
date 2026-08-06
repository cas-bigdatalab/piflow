import React, { useState, useRef, useEffect } from 'react';
import './SkillsGeneratorPage.css'; // 引入样式文件

import { useNavigate } from 'react-router-dom';
import { streamChatSkill } from "../lib/api";
import { shortId } from "../lib/ids"; 



const OperatorGenerator = () => {
  const [inputValue, setInputValue] = useState('');
  const navigate = useNavigate();
    
  const initialAssistantMessage = {
    id: 'msg_welcome',
    role: 'assistant' as const,
    content: `你好！我是算子生成器 👻\n\n请描述你想要创建的算子功能，我会帮你生成标准的算子文件夹结构。\n\n例如：“帮我做一个过滤文本中 URL 链接的算子，支持白名单域名”`,
  };

  const [messages, setMessages] = useState([
    initialAssistantMessage
  ]);
  const chatAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTop = chatAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      id: 'msg_' + Date.now(),
      role: 'user' as const,
      content: inputValue.trim(),
    };

    // 先更新 UI：添加用户消息
    setMessages((prev) => [...prev, userMessage]);

    const userId = localStorage.getItem('userId') || 'u_default';
    const advisorSessionId = `t_${shortId()}`;
    // 调用 AI 接口
    streamChatSkill(
      {
        message: inputValue.trim(),
        user_id: userId,
        thread_id: advisorSessionId,
        workflow_id: "",     
        canvas_dsl: {
          additionalProp1:{}
        },       // ← 取消注释
      selected_node_id: ""
      },
      (event) => {
        if (event.type === 'delta') {
          // 可选：实时流式更新（需额外状态如 currentAssistantMessage）
        } else if (event.type === 'done') {
          const aiMessage = {
            id: 'msg_' + Date.now(),
            role: 'assistant' as const,
            content: event.content,
          };
          setMessages((prev) => [...prev, aiMessage]);
        } else if (event.type === 'error') {
          console.error('AI 错误:', event.message);
        }
      }
    ).catch((err) => {
      console.error('流式请求失败:', err);
    });

    setInputValue('');
  };

  return (
    <div className="og-container">
      {/* 顶部导航 */}
      <header className="og-header">
        <button className="og-back-link">← 返回算子库</button>
        <h1 className="og-page-title">添加算子</h1>
      </header>

      {/* 步骤条 */}
      <div className="og-stepper">
        <div className="og-step completed">
          <span className="og-step-circle">1</span>
          <span className="og-step-label">选择方式</span>
        </div>
        <div className="og-step-line"></div>
        <div className="og-step active">
          <span className="og-step-circle">2</span>
          <span className="og-step-label">算子生成器</span>
        </div>
        <div className="og-step-line"></div>
        <div className="og-step">
          <span className="og-step-circle">3</span>
          <span className="og-step-label">完成</span>
        </div>
      </div>

      {/* 主内容卡片 */}
      <main className="og-card">
        <div className="og-card-header">
          <div>
            <h2 className="og-card-title">算子生成器</h2>
            <p className="og-card-subtitle">描述算子功能需求，生成器帮你构建标准算子文件夹结构</p>
          </div>
          <button className="og-back-small"
           onClick={() => navigate('/skill/create')}
          >← 返回</button>
        </div>

        {/* 聊天/展示区域 */}
        <div className="og-chat-area" ref={chatAreaRef}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`og-message-row ${msg.role === 'user' ? 'user' : 'assistant'}`}
            >
              <div className={`og-avatar ${msg.role === 'user' ? 'user' : 'assistant'}`}>
                {msg.role === 'user' ? 'ME' : 'OP'}
              </div>
              <div className={`og-message-bubble ${msg.role === 'user' ? 'user' : 'assistant'}`}>
                {/* 支持多段落 */}
                {msg.content.split('\n\n').map((para, i) => (
                  <p key={i}>{para}</p>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* 底部操作栏 */}
        <div className="og-action-area">
          {/* 快捷标签 */}
          {/* <div className="og-chips-container">
            <button className="og-chip">+ 增加参数校验</button>
            <button className="og-chip">+ 支持正则模式</button>
          </div> */}

          {/* 输入框行 */}
          <div className="og-input-row">
            <input
              type="text"
              className="og-input"
              placeholder="描述算子功能需求..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />
            <button className="og-btn-send" onClick={handleSend}>发送</button>
          </div>

          {/* 底部次要按钮 */}
          {/* <div className="og-footer-actions">
            <button className="og-btn-preview">👁️ 预览算子</button>
          </div> */}
        </div>
      </main>
    </div>
  );
};

export default OperatorGenerator;