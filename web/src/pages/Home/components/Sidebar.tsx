import type { Conversation } from "..";

type SidebarProps = {
  currentConversation: Conversation | null;
  conversations: Conversation[];
  onAddConversation: () => void;
  onSelectConversation: (conversation: Conversation) => void;
};

export default function Sidebar({
  conversations,
  currentConversation,
  onAddConversation,
  onSelectConversation,
}: SidebarProps) {
  console.log("Sidebar props:", { conversations });
  return (
    <aside className="w-[260px] flex-shrink-0 bg-gray-50 border-r border-gray-100 flex flex-col">
      <div className="p-4">
        <button
          className="w-full py-2.5 bg-black text-white text-sm font-bold flex items-center justify-center gap-2 hover:bg-gray-800 transition-colors"
          onClick={() => onAddConversation()}>
          <iconify-icon icon="ri:add-line" />
          <span>新对话</span>
        </button>
      </div>
      <div className="px-4 py-2 border-b border-gray-100 mx-4 mb-2">
        <h2 className="text-[12px] font-bold text-gray-400 uppercase tracking-widest">
          历史对话
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="px-3 space-y-1">
          {conversations.map((item) => (
            <div
              key={item.id}
              className={`p-3 text-sm cursor-pointer group transition-all ${
                currentConversation?.id === item.id
                  ? "bg-white border border-gray-200 shadow-sm"
                  : "hover:bg-white hover:border-gray-200 text-gray-500"
              }`}
              onClick={() => onSelectConversation(item)}>
              <p
                className={`font-medium truncate mb-1 ${
                  currentConversation?.id === item.id
                    ? "text-gray-900"
                    : "group-hover:text-gray-900 transition-colors"
                }`}>
                {item.title}
              </p>
              <p className="text-[11px] text-gray-400">{item.date}</p>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
