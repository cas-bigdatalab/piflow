import { Icon } from "@iconify/react";
import { useEffect, useState } from "react";
import { apiBase, listSkills, getSkillTypes, type DagSkillInfo,iconBase } from "../lib/api";

import { useNavigate } from 'react-router-dom';

const DEFAULT_SKILL_ICON = "/storage/common/common.png";
function resolveIconUrl(icon?: string) {
  const rawIcon = (icon || "").trim();
  const normalizeStoragePath = (path: string) => {
    const normalized = `/${path.replace(/^\/+/, "")}`;
    if (
      normalized.startsWith("/storage/") &&
      !normalized.startsWith("/storage/skill/") &&
      !normalized.startsWith("/storage/skills/") &&
      !normalized.startsWith("/storage/common/")
    ) {
      return normalized.replace("/storage/", "/storage/skills/");
    }
    return normalized;
  };

  const normalizedPath = !rawIcon
    ? DEFAULT_SKILL_ICON
    : rawIcon.startsWith("/storage/")
      ? normalizeStoragePath(rawIcon)
      : rawIcon.startsWith("storage/")
        ? normalizeStoragePath(rawIcon)
        : `/storage/skills/${rawIcon.replace(/^\/+/, "")}`;

  if (/^(https?:|data:)/.test(rawIcon)) {
    return rawIcon;
  }

  const base = (iconBase() || "").trim().replace(/\/+$/, "");
  if (!base) {
    return normalizedPath;
  }

  return new URL(normalizedPath.replace(/^\/+/, ""), `${base}/`).toString();
}

type SkillGroup = {
  groupName: string;
  DagSkillInfoList: DagSkillInfo[];
};

export function WorkLibPage() {
  const navigate = useNavigate();
  const [keyword, setKeyword] = useState("");
  const [displayGroups, setDisplayGroups] = useState<SkillGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("");
  const [allCategories, setAllCategories] = useState<{ name: string; count: number }[]>([]);

  const [showSpecPanel, setShowSpecPanel] = useState(false);
  const [activeTab, setActiveTab] = useState<"社区生态" | "我的空间">("社区生态");
  const [batchMode, setBatchMode] = useState(false);
  const [selectedSkillIds, setSelectedSkillIds] = useState<Set<string>>(new Set());
  // 加载分类列表
  useEffect(() => {
    let alive = true;
    
    getSkillTypes()
      .then((response) => {
        if (!alive) return;
        
        // 从 data 获取数据
        const typeData = response.data;
        console.log("分类列表数据:", typeData);
        
        const categories = (Array.isArray(typeData) ? typeData : []).map((item: any) => ({
          name: item.type || item.name || "未分类",
          count: item.count || 0,
        }));
        
        const totalCount = categories.reduce((sum, c) => sum + c.count, 0);
        setAllCategories([
          { name: "全部算子", count: totalCount },
          ...categories,
        ]);
        
        setActiveCategory("全部算子");
      })
      .catch((err) => {
        console.error("加载分类失败:", err);
      });
    
    return () => { alive = false; };
  }, []);

  // 加载算子列表 - 当分类或关键词变化时
  useEffect(() => {
    if (!activeCategory) return; // 等待分类加载
    
    let alive = true;
    setLoading(true);
    setError("");
    
    const skill_type = activeCategory === "全部算子" ? "" : activeCategory;
    
    listSkills(1, 200, keyword, skill_type)
      .then((response) => {
        if (!alive) return;
        if (response.code !== 200) {
          setError(response.message || "算子列表加载失败");
          setDisplayGroups([]);
          return;
        }
        
        // 获取实际数据 - 在 result.data 中，是分组结构
        const responseData = (response as any).result?.data;
        console.log("接口返回数据:", responseData);
        
        if (Array.isArray(responseData)) {
          setDisplayGroups(responseData);
        } else {
          setDisplayGroups([]);
        }
      })
      .catch((err: any) => {
        if (!alive) return;
        console.error("加载失败:", err);
        setError(String(err?.message || err));
        setDisplayGroups([]);
      })
      .finally(() => {
        if (!alive) return;
        setLoading(false);
      });
    
    return () => { alive = false; };
  }, [activeCategory, keyword]);

  // 计算总算子数
  const totalSkills = displayGroups.reduce((sum, group) => sum + group.DagSkillInfoList.length, 0);



return (
  <div className="w-full px-4 py-4 sm:px-6 lg:px-[40px] xl:px-[40px]">
    <div className="mb-5 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
      <div>
        <h1 className="page-title">工作流库</h1>
        <p className="mt-3 text-sm leading-7 text-slate-500">
          将重复性强的标准化流程和反复打磨的最佳实践固化为工作流模版，供自己或团队复用，优秀的工作流欢迎共享到社区，让更多人受益
        </p>
      </div>
      <button
        className="text-sm text-slate-600 hover:text-slate-900 flex items-center gap-1 whitespace-nowrap"
        onClick={() => setShowSpecPanel(true)}
      >
        📖 开发规范
      </button>
    </div>
    {/* Tabs */}
    <div className="mb-6">
      <div className="inline-flex rounded-lg bg-slate-100 p-1">
        {(['社区生态', '我的空间'] as const).map((tab) => {
          const isActive = activeTab === tab;
          return (
            <button
              key={tab}
              className={`flex-1 px-6 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-slate-700 hover:text-slate-900'
              }`}
              type="button"
              onClick={() => {
                setActiveTab(tab);
                setSelectedSkillIds(new Set());
                setBatchMode(false);
              }}
            >
              {tab}
            </button>
          );
        })}
      </div>
    </div>
    {/* Toolbar */}
    <div className="flex items-center justify-between mb-3">
      <div className="w-full max-w-[290px] rounded-[15px] border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <div className="flex items-center gap-3">
          <Icon className="text-slate-400" icon="ri:search-line" width="18" />
          <input
            className="w-full border-none bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
            onChange={(event) => setKeyword(event.target.value)}
            placeholder={activeTab === "社区生态" ? "搜索工作流名、描述或标签" : "搜索我的工作流"}
            type="text"
            value={keyword}
          />
        </div>
      </div>
      
      {activeTab === "我的空间" ? (
        <button
          className="ml-4 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors whitespace-nowrap"
          onClick={() => navigate('/skill/create')}
        >
          + 添加算子
        </button>
      ) : batchMode ? (
        <div className="ml-4 flex items-center gap-2">
          <span className="text-sm text-slate-600">已选择 {selectedSkillIds.size} 个</span>
          <button
            className="px-3 py-2 text-sm border border-slate-300 rounded-md hover:bg-slate-50"
            onClick={() => setBatchMode(false)}
          >
            取消
          </button>
        </div>
      ) : (
        <button
          className="ml-4 px-3 py-2 text-sm border border-slate-300 rounded-md hover:bg-slate-50"
          onClick={() => setBatchMode(true)}
        >
          批量管理
        </button>
      )}
    </div>
    
    {/* Batch Bar */}
    {batchMode && activeTab === "社区生态" && (
      <div className="mb-4 p-3 bg-slate-100 rounded-lg flex justify-between items-center">
        <span>已选择 {selectedSkillIds.size} 个算子</span>
        <div className="space-x-2">
          <button 
            className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md disabled:opacity-50"
            disabled={selectedSkillIds.size === 0}
          >
            同步到本地
          </button>
          <button 
            className="px-3 py-1.5 text-sm bg-rose-600 text-white rounded-md disabled:opacity-50"
            disabled={selectedSkillIds.size === 0}
          >
            移除
          </button>
        </div>
      </div>
    )}

    <div className="grid gap-8 lg:grid-cols-[220px_minmax(0,1fr)] xl:grid-cols-[240px_minmax(0,1fr)]">
      {/* 左侧分类（仅社区生态显示）*/}
      {activeTab === "社区生态" && (
        <aside className="h-fit rounded-[28px] border border-slate-200 bg-white p-3.5 shadow-[0_24px_60px_rgba(15,23,42,0.04)]">
          <div className="mb-4 flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-400">分类</p>
            {error ? <span className="text-xs text-rose-500">加载失败</span> : null}
          </div>

          <ul className="space-y-1">
            {allCategories.map((category) => {
              const active = activeCategory === category.name;
              return (
                <li key={category.name}>
                  <button
                    className={
                      active
                        ? "flex w-full items-center justify-between rounded-2xl bg-black px-3 py-2 text-left text-[13px] font-medium text-white"
                        : "flex w-full items-center justify-between rounded-2xl px-3 py-2 text-left text-[13px] font-medium text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-900"
                    }
                    onClick={() => setActiveCategory(category.name)}
                    type="button"
                  >
                    <span>{category.name}</span>
                    <span
                      className={
                        active
                          ? "rounded-full bg-white/15 px-2 py-0.5 text-[10px]"
                          : "rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-500"
                      }
                    >
                      {category.count}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>
      )}

      {/* 右侧内容 */}
      <section className="min-w-0">
        {error && activeTab === "社区生态" ? (
          <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="mb-4 text-sm text-slate-500">
          {loading && activeTab === "社区生态" 
            ? "正在加载算子列表..." 
            : `共 ${totalSkills} 个算子`}
        </div>

        {activeTab === "我的空间" ? (
          <div className="rounded-[28px] border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-400">
            我的空间功能开发中...
          </div>
        ) : !loading && displayGroups.length === 0 ? (
          <div className="rounded-[28px] border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-400">
            没有匹配到算子。可以尝试更换关键词重新查看。
          </div>
        ) : (
          <div className="space-y-8">
            {displayGroups.map((group, groupIndex) => (
              <div key={groupIndex}>
                <h2 className="mb-4 text-xl font-semibold text-slate-900">
                  {group.groupName}
                  <span className="ml-2 text-sm font-normal text-slate-400">
                    ({group.DagSkillInfoList.length} 个)
                  </span>
                </h2>
                <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
                  {group.DagSkillInfoList.map((skill, skillIndex) => (
                    <article
                      key={`${skill.skill_name}-${skillIndex}`}
                      onClick={(e) => {
                        // 阻止复选框点击时跳转
                        if ((e.target as HTMLElement).closest('.batch-checkbox')) return;
                        navigate(`/skill/detail/${encodeURIComponent(skill.skill_name)}`);
                      }}
                      className="group/skill relative z-0 flex h-full flex-col rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_20px_60px_rgba(15,23,42,0.04)] transition-all hover:z-20 hover:-translate-y-1 hover:border-black"
                    >
                      {/* 批量选择复选框 */}
                      {batchMode && (
                        <input
                          type="checkbox"
                          className="batch-checkbox absolute top-3 right-3 w-5 h-5 rounded border-slate-300"
                          checked={selectedSkillIds.has(skill.skill_name)}
                          onChange={(e) => toggleSelection(skill.skill_name, e.target.checked)}
                          onClick={(e) => e.stopPropagation()}
                        />
                      )}

                      <div className="flex items-start gap-4">
                        <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                          {skill.icon_path ? (
                            <img
                              alt={(skill as any).name_zh || skill.skill_name || "算子图标"}
                              className="h-8 w-8 rounded-xl object-cover"
                              src={resolveIconUrl(skill.icon_path)}
                            />
                          ) : (
                            <Icon icon="ri:flashlight-line" width="22" />
                          )}
                        </div>

                        <div className="min-w-0 flex-1">
                          <h3 className="break-words text-lg font-semibold leading-7 text-slate-900">
                            {(skill as any).name_zh || skill.skill_name || "未命名算子"}
                          </h3>
                          <div className="mt-2">
                            <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-[11px] font-medium tracking-[0.08em] text-slate-500">
                              {skill.skill_type || "未分类"}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="mt-4 flex-1 rounded-[24px] bg-slate-50 px-4 py-3.5">
                        <p className="line-clamp-4 text-sm leading-7 text-slate-600" title={skill.description}>
                          {skill.description || "面向科研数据处理流程的可复用算子。"}
                        </p>
                      </div>

                      {skill.version && (
                        <div className="mt-3 text-xs text-slate-400">
                          版本: {skill.version}
                        </div>
                      )}
                    </article>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>

    {/* 2. 主体网格布局 (左侧分类 + 右侧内容) */}
    <div className="grid gap-8 lg:grid-cols-[220px_minmax(0,1fr)] xl:grid-cols-[240px_minmax(0,1fr)]">
      
      {/* --- 左侧分类 Sidebar --- */}
      <aside className="h-fit rounded-[28px] border border-slate-200 bg-white p-3.5 shadow-[0_24px_60px_rgba(15,23,42,0.04)]">
        <div className="mb-4 flex items-center justify-between">
          <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-400">分类</p>
          {error ? <span className="text-xs text-rose-500">加载失败</span> : null}
        </div>

        <ul className="space-y-1">
          {allCategories.map((category) => {
            const active = activeCategory === category.name;
            return (
              <li key={category.name}>
                <button
                  className={
                    active
                      ? "flex w-full items-center justify-between rounded-2xl bg-black px-3 py-2 text-left text-[13px] font-medium text-white"
                      : "flex w-full items-center justify-between rounded-2xl px-3 py-2 text-left text-[13px] font-medium text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-900"
                  }
                  onClick={() => setActiveCategory(category.name)}
                  type="button"
                >
                  <span>{category.name}</span>
                  <span
                    className={
                      active
                        ? "rounded-full bg-white/15 px-2 py-0.5 text-[10px]"
                        : "rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-500"
                    }
                  >
                    {category.count}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </aside>

      {/* --- 右侧内容 Main Content --- */}
      <section className="min-w-0">
        
        {/* 2.2 状态提示 (错误/加载/空数据) */}
        {error ? (
          <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="mb-4 text-sm text-slate-500">
          {loading ? "正在加载算子列表..." : `共 ${totalSkills} 个算子`}
        </div>

        {!loading && displayGroups.length === 0 ? (
          <div className="rounded-[28px] border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-400">
            没有匹配到算子。可以尝试更换关键词重新查看。
          </div>
        ) : (
          <div className="space-y-8">
            {displayGroups.map((group, groupIndex) => (
              <div key={groupIndex}>
                <h2 className="mb-4 text-xl font-semibold text-slate-900">
                  {group.groupName}
                  <span className="ml-2 text-sm font-normal text-slate-400">
                    ({group.DagSkillInfoList.length} 个)
                  </span>
                </h2>
                
                {/* 卡片网格 */}
                <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
                  {group.DagSkillInfoList.map((skill, skillIndex) => (
                    <article
                      key={skillIndex}
                      onClick={() => navigate(`/skill/detail/${encodeURIComponent(skill.skill_name)}`)}
                      className="group/skill relative z-0 flex h-full flex-col rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_20px_60px_rgba(15,23,42,0.04)] transition-all hover:z-20 hover:-translate-y-1 hover:border-black"
                    >
                      {/* --- 卡片头部: 图标 + 标题 + 开关 --- */}
                      <div className="flex items-start gap-4">
                        {/* 统一的文件夹图标 (还原截图风格) */}
                        <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                         <Icon icon="ri:folder-3-line" width="24" />
                        </div>

                        <div className="min-w-0 flex-1">
                          {/* 标题 */}
                          <h3 className="break-words text-lg font-semibold leading-7 text-slate-900">
                            {(skill as any).name_zh || skill.skill_name || "未命名工作流"}
                          </h3>
                          
                          {/* 开关 Toggle (还原截图) */}
                          <div className="mt-3">
                            <label className="inline-flex items-center cursor-pointer">
                              <input type="checkbox" className="sr-only peer" defaultChecked />
                              <div className="relative w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
                            </label>
                          </div>
                        </div>
                      </div>

                      {/* --- 标签 Tags (还原截图) --- */}
                      <div className="mt-3 flex flex-wrap gap-2">
                        {/* 假设 skill.tags 是一个数组，如果字段名不同请替换 */}
                        {/* 这里演示两个示例标签 */}
                        <span className="px-2.5 py-1 text-xs font-medium text-blue-800 bg-blue-100 rounded-full">数据处理</span>
                        <span className="px-2.5 py-1 text-xs font-medium text-purple-800 bg-purple-100 rounded-full">ETL</span>
                      </div>

                      {/* --- 描述 --- */}
                      <div className="mt-4 flex-1 rounded-[24px] bg-slate-50 px-4 py-3.5">
                        <p className="line-clamp-4 text-sm leading-7 text-slate-600" title={skill.description}>
                          {skill.description || "这是一个优秀的工作流模版，旨在提高数据处理效率。"}
                        </p>
                      </div>

                      {/* --- 底部信息: 作者/下载 + 版本 --- */}
                      <div className="mt-3 flex items-center justify-between text-xs text-slate-400 pt-3 border-t border-slate-100">
                        <div className="flex items-center gap-2">
                          {/* 这里假设有一个 author 字段，如果没有可以用 skill.skill_name 代替 */}
                          <span>作者: {(skill as any).author || "社区用户"}</span>
                          <span>·</span>
                          <span>下载: {skill.version ? skill.version.split('').length : 123}k</span>
                        </div>
                        <div>
                          版本: {skill.version || "v1.0"}
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  </div>
);
}
