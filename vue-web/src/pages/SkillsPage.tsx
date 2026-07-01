import { Icon } from "@iconify/react";
import { useEffect, useState } from "react";
import { apiBase, listSkills, getSkillTypes, type DagSkillInfo } from "../lib/api";

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

  return new URL(normalizedPath.replace(/^\/+/, ""), `${apiBase().replace(/\/+$/, "")}/`).toString();
}

type SkillGroup = {
  groupName: string;
  DagSkillInfoList: DagSkillInfo[];
};

export function SkillsPage() {
  const [keyword, setKeyword] = useState("");
  const [displayGroups, setDisplayGroups] = useState<SkillGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("");
  const [allCategories, setAllCategories] = useState<{ name: string; count: number }[]>([]);

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
    <div className="w-full px-4 py-4 sm:px-6 lg:px-[20px] xl:px-[20px]">
      <div className="mb-8 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          {/* <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
            Skills Hub
          </div> */}
          <h1 className="page-title">算子库</h1>
          <p className="mt-3 text-sm leading-7 text-slate-500">
            探索多样化的科学数据加工算子 
          </p>
        </div>

        <div className="w-full max-w-[460px] rounded-[24px] border border-slate-200 bg-white px-4 py-3 shadow-sm">
          <div className="flex items-center gap-3">
            <Icon className="text-slate-400" icon="ri:search-line" width="18" />
            <input
              className="w-full border-none bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="搜索算子名、描述或标签"
              type="text"
              value={keyword}
            />
          </div>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[220px_minmax(0,1fr)] xl:grid-cols-[240px_minmax(0,1fr)]">
        {/* 左侧分类 */}
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

        {/* 右侧内容 */}
        <section className="min-w-0">
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
                  <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
                    {group.DagSkillInfoList.map((skill, skillIndex) => (
                      <article
                        key={skillIndex}
                        className="group/skill relative z-0 flex h-full flex-col rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_20px_60px_rgba(15,23,42,0.04)] transition-all hover:z-20 hover:-translate-y-1 hover:border-black"
                      >
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
    </div>
  );
}
