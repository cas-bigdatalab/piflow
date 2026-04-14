import { useContext, useEffect, useRef, useState } from "react";
import type { Conversation, Message } from "..";
import Examples from "./Skills";
import { GlobalContext } from "@/context";

type TextInputProps = {
  mode: string;
  onModeChange: (val: string) => void;
  onAddConversation: (message: Message) => void;
  currentConversation: Conversation | null;
};
const TextInput = ({
  mode,
  onModeChange,
  onAddConversation,
  currentConversation,
}: TextInputProps) => {
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [typedContent, setTypedContent] = useState("");
  const [currentMessages, setCurrentMessages] = useState(
    currentConversation?.messages || [],
  );
  const lastConversationId = useRef<string>("");
  const { userId } = useContext(GlobalContext);

  const onSend = async () => {
    if (input.trim()) {
      const newMessage = { role: "user" as const, content: input };
      if (!lastConversationId.current) {
        onAddConversation(newMessage);
      }
      setCurrentMessages((prev) => [...prev, newMessage]);
      onModeChange("chat");
      setInput("");

      setIsTyping(true);
      setTypedContent("");

      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: input,
          thread_id: currentConversation?.id || "",
          user_id: userId,
          attachments: [],
        }),
      });

      if (res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let aiResponse = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            setIsTyping(false);
            // 处理剩余缓冲区内容
            if (buffer) {
              const lines = buffer.split("\n");
              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  const data = line.slice(6);
                  if (data && data !== "[DONE]") {
                    try {
                      const parsed = JSON.parse(data);
                      if (parsed.type === "message_delta" && parsed.delta) {
                        aiResponse += parsed.delta;
                      }
                    } catch {
                      // 忽略解析错误
                    }
                  }
                }
              }
            }

            // 确保有内容且没有重复的AI回复
            if (aiResponse) {
              setCurrentMessages((prev) => {
                // 检查最后一条消息是否是AI回复，避免重复
                const lastMessage = prev[prev.length - 1];
                if (lastMessage && lastMessage.role === "assistant") {
                  return prev;
                }
                return [
                  ...prev,
                  { role: "assistant" as const, content: aiResponse },
                ];
              });
            }

            // 清空打字内容，为下一次回复做准备
            setTypedContent("");
            break;
          }

          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;

          // 处理完整的行
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // 保留不完整的行

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data && data !== "[DONE]") {
                try {
                  const parsed = JSON.parse(data);
                  if (parsed.type === "message_delta" && parsed.delta) {
                    aiResponse += parsed.delta;
                    // 实时更新打字内容
                    setTypedContent(aiResponse);
                  }
                } catch {
                  // 忽略解析错误
                }
              }
            }
          }
        }
      }
      // 模拟AI回复
      // simulateStreamResponse();
    }
  };

  useEffect(() => {
    if (currentConversation?.id !== lastConversationId.current) {
      setCurrentMessages(currentConversation?.messages || []);
      // 当切换对话或消息更新时，重置打字机状态
      setIsTyping(false);
      setTypedContent("");
    }
    lastConversationId.current = currentConversation?.id || "";
  }, [currentConversation]);

  return (
    <div className="flex flex-col h-full">
      {/* 对话区域 */}
      {mode === "chat" && (
        <section className="px-8 py-6 flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto flex flex-col h-full">
            <div className="flex-1 overflow-y-auto custom-scrollbar mb-4">
              {currentMessages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} mb-4`}>
                  <div
                    className={`max-w-[80%] p-3 rounded-lg ${message.role === "user" ? "bg-gray-100" : "bg-white border border-gray-200"} overflow-x-auto`}>
                    <p className="text-sm whitespace-pre-wrap">
                      {message.content}
                    </p>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start mb-4">
                  <div className="max-w-[80%] p-3 rounded-lg bg-white border border-gray-200">
                    <div className="flex items-center">
                      <div className="flex space-x-1 mr-2">
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0ms" }}></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "150ms" }}></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "300ms" }}></div>
                      </div>
                      <p className="text-sm">
                        {typedContent}
                        <span className="animate-pulse">|</span>
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* 输入区域 */}
      <section className="px-8 pb-10 flex-shrink-0">
        <div className="max-w-4xl mx-auto flex flex-col">
          <div className="border border-gray-200 rounded-xl bg-white shadow-sm overflow-hidden flex flex-col">
            <div className="p-4 relative">
              <textarea
                className="w-full p-2 pb-12 text-sm bg-transparent resize-none min-h-[100px] focus:outline-none"
                placeholder={"输入您的科研数据加工需求..."}
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <div className="absolute bottom-6 left-6 flex gap-4">
                <button
                  className="text-gray-400 hover:text-black transition-colors flex items-center cursor-pointer"
                  title="上传附件">
                  <iconify-icon icon="ri:attachment-2" width="20" />
                </button>
                <button
                  className="text-gray-400 hover:text-black transition-colors flex items-center cursor-pointer"
                  title="使用插件">
                  <iconify-icon icon="ri:plug-2-line" width="20" />
                </button>
              </div>
              <div className="absolute bottom-6 right-6">
                <button
                  className="px-6 py-2 bg-black text-white text-xs font-bold rounded flex items-center gap-2 hover:bg-gray-800 transition-all shadow-sm"
                  onClick={onSend}>
                  <span>{mode === "newChat" ? "开始加工" : "发送"}</span>
                  <iconify-icon icon="ri:send-plane-fill" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
      {mode === "newChat" && <Examples />}
    </div>
  );
};

export default TextInput;
