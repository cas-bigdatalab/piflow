import { useEffect, useState } from "react";
import TextInput from "./components/TextInput";
import Sidebar from "./components/Sidebar";
import { getHistory, getThreadMessages } from "../../apis/chat";
import { formatDate } from "../../utils/formatDate";
export type Message = {
  role: "user" | "assistant";
  content: string;
};

export type Conversation = {
  id: string;
  title: string;
  date: string;
  messages: Message[] | [];
};
const Slogan = () => {
  return (
    <section className="pt-24 pb-16 text-center bg-white">
      <h1 className="text-[36px] font-bold mb-6 tracking-tight">
        πFlowAgent：科研数据加工智能体
      </h1>
      <p className="text-[16px] text-[#6B7280] tracking-wide">
        专注科研数据治理，赋能科研语料构建
      </p>
    </section>
  );
};

export default function Home() {
  const [mode, setMode] = useState("newChat");
  // 历史对话列表（模拟接口返回）
  const [conversations, setConversations] = useState<Conversation[]>([]);
  // 当前对话ID
  const getNewConversationId = () =>
    ({
      // @ts-ignore
      id: Date.now().toString(),
      title: "新对话",
      date: new Date().toLocaleDateString(),
      messages: [],
    }) as Conversation;
  const [currentConversation, setCurrentConversation] =
    useState<Conversation | null>(getNewConversationId());
  // 当前对话消息

  const handleSelectConversation = async (conversation: Conversation) => {
    if (currentConversation?.id === conversation.id) return;
    // 这里可以根据conversation.id从接口获取历史消息
    // 现在使用模拟数据
    // 模拟从后端接口获取历史消息
    const res = await getThreadMessages({
      user_id: "default_user",
      thread_id: conversation.id,
      limit: 200,
    });
    setCurrentConversation({
      id: conversation.id,
      title: conversation.title,
      date: conversation.date,
      messages: res.data.messages || [],
    });
    setMode("chat");
  };

  const handleAddConversation = (message?: Message | null) => {
    const newConversation = getNewConversationId();
    if (message) {
      newConversation.messages.push(message);
      console.log("newConversation:", newConversation);
      setConversations((prev) => [newConversation, ...prev]);
      setCurrentConversation(newConversation);
    } else {
      setCurrentConversation(newConversation);
      setMode("newChat");
    }
  };

  const getSidebarHistory = async () => {
    const res = await getHistory({ user_id: "default_user" });
    const list =
      res.data.threads?.map((item: any) => ({
        id: item.thread_id,
        title: item.title,
        date: formatDate(item.updated_at),
        messages: item.messages || [],
      })) || [];

    setConversations(list);
  };

  useEffect(() => {
    getSidebarHistory();
  }, []);

  return (
    <>
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          conversations={conversations}
          currentConversation={currentConversation}
          onAddConversation={handleAddConversation}
          onSelectConversation={handleSelectConversation}
        />
        <main className="flex-1 overflow-y-auto custom-scrollbar flex flex-col">
          {/* 标题Slogan区 */}
          {mode === "newChat" && <Slogan />}

          {/* 智能对话区 */}
          <TextInput
            mode={mode}
            onModeChange={(val) => setMode(val)}
            onAddConversation={handleAddConversation}
            currentConversation={currentConversation}
          />
        </main>
      </div>
    </>
  );
}
