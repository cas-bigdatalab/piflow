import { getSkills } from "@/apis/chat";
import { useRequest } from "@/hooks/useRequest";
import { useMemo, useState } from "react";

const categories = [
  { name: "全部分类", count: 24, active: true },
  { name: "数据清洗", count: 8 },
  { name: "实体抽取", count: 5 },
  { name: "格式转换", count: 6 },
  { name: "翻译与校对", count: 3 },
  { name: "知识对齐", count: 2 },
];

// const skills = [
//   {
//     icon: "ri:file-shred-line",
//     title: "PDF文本高精度清洗",
//     desc: "去除PDF导出的冗余页眉页脚及乱码字符。",
//     tag: "数据清洗",
//   },
//   {
//     icon: "ri:microscope-line",
//     title: "医学术语自动识别",
//     desc: "基于LLM的医学专有名词标准化抽取。",
//     tag: "实体抽取",
//   },
//   {
//     icon: "ri:translate-2",
//     title: "学术论文摘要翻译",
//     desc: "保留专业术语的英中双语对照翻译。",
//     tag: "翻译",
//   },
// ];

export default function SkillsPage() {
  const [search, setSearch] = useState("");
  const { data: skills } = useRequest(getSkills, {
    defaultData: [],
  });

  const filteredSkills = useMemo(() => {
    return skills.filter((skill) => skill.name.includes(search));
  }, [skills, search]);

  return (
    <main className="flex-1 py-12">
      <div className="w-[1200px] mx-auto">
        {/* 页面标题与搜索 */}
        <div className="flex justify-between items-end mb-12">
          <div>
            <h1 className="text-2xl font-bold mb-2">技能中心</h1>
            <p className="text-sm text-[#6B7280]">
              探索多样化的科研数据加工技能
            </p>
          </div>
          <div className="w-[300px] relative">
            <input
              className="w-full border-b-2 border-gray-200 py-2 pl-2 pr-10 text-sm focus:border-black outline-none transition-colors"
              placeholder="搜索加工技能..."
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <iconify-icon
              className="absolute right-2 top-2.5 text-gray-400"
              icon="ri:search-line"
            />
          </div>
        </div>

        <div className="flex gap-10">
          {/* 左侧分类 */}
          <aside className="w-48">
            <ul className="space-y-4 text-sm font-medium">
              {categories.map((cat) => (
                <li
                  key={cat.name}
                  className={`flex items-center justify-between cursor-pointer transition-colors ${
                    cat.active ? "text-black" : "text-gray-400 hover:text-black"
                  }`}>
                  <span>{cat.name}</span>
                  <span
                    className={`text-[10px] px-1.5 rounded ${
                      cat.active ? "bg-gray-100" : "bg-gray-50"
                    }`}>
                    {cat.count}
                  </span>
                </li>
              ))}
            </ul>
          </aside>

          {/* 技能网格区 */}
          <div className="flex-1 grid grid-cols-3 gap-6">
            {filteredSkills.map((skill: FT.Object) => (
              <div
                key={skill.name}
                className="border border-[#E5E7EB] p-5 hover:bg-[#F9FAFB] transition-colors cursor-pointer">
                <div className="w-10 h-10 bg-gray-100 flex items-center justify-center rounded mb-4">
                  <img src={skill.icon} alt={skill.name} className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-bold mb-1">{skill.name}</h3>
                <p className="text-xs text-[#6B7280] mb-4">
                  {skill.description}
                </p>
                <div className="flex items-center justify-between pt-4 border-t border-gray-50">
                  <span className="text-[10px] uppercase tracking-tighter text-gray-400">
                    {/* {skill.tag} */}
                  </span>
                  <iconify-icon
                    className="text-gray-300"
                    icon="ri:arrow-right-up-line"
                  />
                </div>
              </div>
            ))}
            {/* 更多占位卡片 */}
            <div className="border border-dashed border-gray-200 p-5 flex flex-col items-center justify-center text-gray-300">
              <iconify-icon
                className="mb-2 opacity-30"
                icon="ri:add-circle-line"
                width="32"
              />
              <span className="text-xs">更多技能持续更新</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
