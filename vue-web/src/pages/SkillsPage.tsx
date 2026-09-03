// src/pages/SkillsPage.tsx
import { Icon } from "@iconify/react";
import { useEffect, useState, useCallback } from "react";
import { apiBase, iconBase,listSkills, getSkillTypes, type DagSkillInfo,removeLocalSkill,enableLocalSkill } from "../lib/api";
import { useNavigate, useSearchParams } from 'react-router-dom';

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

export function SkillsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [keyword, setKeyword] = useState("");
  const [displayGroups, setDisplayGroups] = useState<SkillGroup[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>("");
  const [allCategories, setAllCategories] = useState<{ name: string; count: number }[]>([]);
  // 初始页签支持通过 URL 参数 tab 指定（例如从算子生成器返回时定位到“我的空间”）
  const [activeTab, setActiveTab] = useState<"社区生态" | "我的空间">(
    searchParams.get("tab") === "我的空间" ? "我的空间" : "社区生态"
  );
  
  // === 新增状态（不影响原有逻辑）===
  const [batchMode, setBatchMode] = useState(false);
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);
  const [showSpecPanel, setShowSpecPanel] = useState(false);// 1. 新增：用于控制“共享到社区”模态框的显示
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  // 2. 新增：用于存储当前要共享的算子信息
  const [currentSkill, setCurrentSkill] = useState<DagSkillInfo | null>(null);
  // 👇 添加这一行
  const [skillEnabledMap, setSkillEnabledMap] = useState<Record<string, boolean>>({});
  // ===========================
  const [data, setData] = useState<OperatorData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const loadMySkills = useCallback(() => {
    const skill_type = activeCategory === "全部算子" ? "" : activeCategory;
    setLoading(true);
    setError("");

    // 根据当前所在页签决定请求的 publisher，避免删除后刷新错拿到社区数据
    const publisher = activeTab === "社区生态" ? "COMMUNITY" : "PRIVATE";
    listSkills(1, 200, keyword, skill_type, publisher)
      .then((response) => {
        if (response.code !== 200) {
          setError(response.message || "我的算子列表加载失败");
          setDisplayGroups([]);
          return;
        }
        const responseData = (response as any).result?.data;
        setDisplayGroups(Array.isArray(responseData) ? responseData : []);
        const initialEnabledMap: Record<string, boolean> = {};
        if (Array.isArray(responseData)) {
          responseData.forEach((group: SkillGroup) => {
            group.DagSkillInfoList.forEach(skill => {
              const isEnabled = skill.is_deleted === 0 || skill.is_deleted == null;
              initialEnabledMap[skill.skill_name!] = isEnabled;
            });
          });
        }
        setSkillEnabledMap(initialEnabledMap);
      })
      .catch((err: any) => {
        console.error("加载我的算子失败:", err);
        setError(String(err?.message || err));
        setDisplayGroups([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [activeCategory, keyword, activeTab]);
  // 加载分类列表（完全保留你的原始逻辑）
  useEffect(() => {
    let alive = true;
    
    getSkillTypes()
      .then((response) => {
        if (!alive) return;
        
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
  // 加载算子列表（完全保留你的原始逻辑，仅社区生态）
  useEffect(() => {
    if (!activeCategory) return;

    let alive = true;
    setLoading(true);
    setError("");

    const loadCommunitySkills = () => {
      const skill_type = activeCategory === "全部算子" ? "" : activeCategory;
      const publisher = activeTab === "社区生态" ? "COMMUNITY" : "PRIVATE";
      listSkills(1, 200, keyword, skill_type,publisher)
        .then((response) => {
          if (!alive) return;
          if (response.code !== 200) {
            setError(response.message || "算子列表加载失败");
            setDisplayGroups([]);
            return;
          }
          const responseData = (response as any).result?.data;
          setDisplayGroups(Array.isArray(responseData) ? responseData : []);
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
    };

    const loadMySkills = () => {
      const skill_type = activeCategory === "全部算子" ? "" : activeCategory;
      listSkills(1, 200, keyword, skill_type, "PRIVATE") // 注意：publisher = "PRIVATE"
        .then((response) => {
          if (!alive) return;
          if (response.code !== 200) {
            setError(response.message || "我的算子列表加载失败");
            setDisplayGroups([]);
            return;
          }
          const responseData = (response as any).result?.data;
          setDisplayGroups(Array.isArray(responseData) ? responseData : []);
          const initialEnabledMap: Record<string, boolean> = {};
          if (Array.isArray(responseData)) {
            responseData.forEach((group: SkillGroup) => {
              group.DagSkillInfoList.forEach(skill => {
                // 社区生态：默认启用（is_deleted 不存在或为 0）
                const isEnabled = skill.is_deleted === 0 || skill.is_deleted == null;
                initialEnabledMap[skill.skill_name!] = isEnabled;
              });
            });
          }
          setSkillEnabledMap(initialEnabledMap);
        })
        .catch((err: any) => {
          if (!alive) return;
          console.error("加载我的算子失败:", err);
          setError(String(err?.message || err));
          setDisplayGroups([]);
        })
        .finally(() => {
          if (!alive) return;
          setLoading(false);
        });
    };

    if (activeTab === "社区生态") {
      loadCommunitySkills();
    } else if (activeTab === "我的空间") {
      loadMySkills();
    }

    return () => { alive = false; };
  }, [activeCategory, keyword, activeTab]);


  // 计算总算子数（根据当前 Tab）
  const totalSkills = activeTab === "社区生态" 
    ? displayGroups.reduce((sum, group) => sum + group.DagSkillInfoList.length, 0)
    : 0; // 我的空间暂时无数据（暂时也走社区生态的数据）

  // === 新增函数（不影响原有逻辑）===
  const toggleSelection = useCallback((skillName: string, checked: boolean) => {
    setSelectedSkillIds(prev => {
      if (checked) {
        return prev.includes(skillName) ? prev : [...prev, skillName];
      } else {
        return prev.filter(id => id !== skillName);
      }
    });
  }, []);

  // 新增：处理标记逻辑
  const handleMark = (skill: DagSkillInfo) => {
    setCurrentSkill(skill);       // 保存当前算子信息
    setIsShareModalOpen(true);    // 打开模态框
  };
  // 4. 新增：关闭模态框的函数
  const closeShareModal = () => {
    setIsShareModalOpen(false);
    setCurrentSkill(null);
  };
  const handleDelete = async (skill: DagSkillInfo) => {
    if (!window.confirm(`确定要删除算子 "${skill.name_zh || skill.skill_name}" 吗？此操作不可恢复。`)) {
      return;
    }

    removeLocalSkill(String(skill.skill_id))
      .then(res => {
        if (res.code === 200) {
          // 刷新列表或更新状态
          loadMySkills(); // 或使用更细粒度的状态更新
        } else {
          alert("删除失败：" + (res.message || ""));
        }
      })
      .catch(err => {
        console.error("删除出错:", err);
        alert("删除过程中发生错误，请重试。");
    });
  };

  const handleShare = (skill: DagSkillInfo) => {
    alert("共享功能待实现");
  };
  // ===========================

  return (
    <div className="max-w-[1440px] mx-auto px-4 py-4 sm:px-6 lg:px-[40px] xl:px-[40px] pt-[40px] pb-[56px]">
      <div className="mb-5 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="page-title">算子库</h1>
          <p className="mt-3 text-sm leading-7 text-slate-500">
            探索多样化的科学数据加工算子，管理并共享你的自定义算子 · 优秀的算子欢迎共享到社区，让更多人受益
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
                  setSelectedSkillIds([]);
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
              placeholder={activeTab === "社区生态" ? "搜索算子名、描述或标签" : "搜索我的算子"}
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
        ) : null}
      
      </div>
        {/* //  : batchMode ? (
        //   <div className="ml-4 flex items-center gap-2">
        //     <span className="text-sm text-slate-600">已选择 {selectedSkillIds.length} 个</span>
        //     <button
        //       className="px-3 py-2 text-sm border border-slate-300 rounded-md hover:bg-slate-50"
        //       onClick={() => setBatchMode(false)}
        //     >
        //       取消
        //     </button>
        //   </div>
        // ) 
        // : (
        //   <button
        //     className="ml-4 px-3 py-2 text-sm border border-slate-300 rounded-md hover:bg-slate-50"
        //     onClick={() => setBatchMode(true)}
        //   >
        //     批量管理
        //   </button>
        // )} */}

      {/* Batch Bar */}
      {batchMode && activeTab === "社区生态" && (
        <div className="mb-4 p-3 bg-slate-100 rounded-lg flex justify-between items-center">
          <span>已选择 {selectedSkillIds.length} 个算子</span>
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

      <div className="grid gap-8 lg:grid-cols-[220px_minmax(0,1fr)] xl:grid-cols-[200px_minmax(0,1fr)]">
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

        {activeTab === "我的空间" && (
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


          {error && activeTab === "我的空间" ? (
            <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}
        
          <div className="space-y-8">
            {displayGroups.map((group, groupIndex) => (
              <div key={groupIndex}>
                <h2 className="mb-4 text-xl font-semibold font-size-[14px] font-weight-[600]">
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
                        navigate(
                          `/skill/detail?id=${skill.skill_id}&name=${skill.name_zh}`
                        ); 
                      }}
                      className="group/skill relative z-0 flex h-full w-[280px] flex-col rounded-[14px] border border-slate-200 bg-white shadow-[0_20px_60px_rgba(15,23,42,0.04)] transition-all hover:z-20 hover:-translate-y-1 hover:border-black px-[18px] py-[18px]"
                    >
                      {/* “我的空间”始终显示操作图标；“社区生态”仅在批量模式下显示复选框 */}
                      {activeTab === '我的空间' ? (
                        <div className="absolute top-3 right-3 flex items-center">
                          {/* 标记图标 */}
                          {/* <button
                            className="p-1.5 rounded-full hover:bg-yellow-100 text-slate-400 hover:text-yellow-500 transition-colors"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleMark(skill);
                            }}
                            title="标记"
                          >
                            ↗
                          </button> */}
                          {/* 删除图标 */}
                          <button
                            className="p-1.5 rounded-full hover:bg-rose-100 text-slate-400 hover:text-rose-600 transition-colors"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(skill);
                            }}
                            title="删除"
                          >
                            <Icon icon="ri:delete-bin-line" width="20" />
                          </button>
                        </div>
                      ) : batchMode ? (
                        <div className="absolute top-3 right-3">
                          <input
                            type="checkbox"
                            className="batch-checkbox w-5 h-5 rounded border-slate-300"
                            checked={selectedSkillIds.includes(skill.skill_name)}
                            onChange={(e) => toggleSelection(skill.skill_name, e.target.checked)}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                      ) : null}

                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-4 min-w-0 flex-1">
                          <div className="flex h-[38px] w-[38px] flex-shrink-0 items-center justify-center rounded-[10px] bg-[#e5e7eb] text-slate-700">
                            {skill.icon_path ? (
                              <img
                                alt={(skill as any).name_zh || skill.skill_name || "算子图标"}
                                className="h-[30px] w-[30px] rounded-xl object-cover"
                                src={resolveIconUrl(skill.icon_path)}
                              />
                            ) : (
                              <Icon icon="ri:flashlight-line" width="22" />
                            )}
                          </div>

                          <div className="min-w-0 flex-1">
                            <div className="max-w-[120px] truncate font-semibold text-slate-900 text-[14px]">
                              {(skill as any).name_zh || skill.skill_name || "未命名算子"}
                            </div>
                            <div className="mt-[-5px]">
                              <span className="inline-flex rounded-[4px] bg-slate-100 px-[6px] text-[13px] font-medium tracking-[0.08em] text-slate-500">
                                {skill.skill_type || "未分类"}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* 开关图标 - 新增部分 */}
                        {/* Switch 开关组件 - 仅在“我的空间”显示 */}
                        {activeTab === '社区生态' && (
                          <div className="flex items-center">
                              <button
                                type="button"
                                role="switch"
                                aria-checked={skill.is_deleted === 0}
                                className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                                  skill.is_deleted === 0 ? 'bg-[#111827]' : 'bg-[#cad4e0]'
                                }`}
                                onClick={async (e) => {
                                  e.stopPropagation();
                                  const currentlyEnabled = skill.is_deleted === 0;
                                  const newEnabled = !currentlyEnabled;

                                  // 乐观更新 UI（可选，但建议保留）
                                  setSkillEnabledMap(prev => ({
                                    ...prev,
                                    [skill.skill_name]: newEnabled,
                                  }));

                                  try {
                                    if (newEnabled) {
                                      // 恢复算子（设 is_deleted = 0）
                                      let id = String(skill.skill_id)
                                      const res = await enableLocalSkill(id);
                                      if (res.code === 200){
                                       loadMySkills();
                                      }
                                      console.log(`算子 ${skill.skill_name} 已被恢复`);
                                    } else {
                                      let id = String(skill.skill_id)
                                      console.log(id)
                                      // 禁用/移除算子（设 is_deleted = 1）
                                      const res = await removeLocalSkill(id);
                                      if (res.code === 200){
                                       loadMySkills();
                                      }
                                      console.log(`算子 ${skill.skill_name} 已被移除`);
                                    }

                                    // 可选：刷新列表或更新 skill 对象的 is_deleted 字段
                                    // 当前实现依赖下次重新加载，若需即时反馈，应更新 displayGroups 中的 skill.is_deleted
                                  } catch (err) {
                                    console.error("操作失败:", err);
                                    setError("操作失败，请重试");
                                    // 回滚 UI
                                    setSkillEnabledMap(prev => ({
                                      ...prev,
                                      [skill.skill_name]: currentlyEnabled,
                                    }));
                                  }
                                }}
                              >
                                <span
                                  aria-hidden="true"
                                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition-transform duration-200 ease-in-out ${
                                    (skillEnabledMap[skill.skill_name] ?? (skill.is_deleted === 0)) ? 'translate-x-4' : 'translate-x-0'
                                  }`}
                                />
                              </button>
                          </div>
                        )}
                      </div>

                      <div className="mt-[10px] flex-1">
                        <p className="line-clamp-3 text-sm text-slate-600" title={skill.description}>
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
        </section>
      </div>

      {/* 开发规范面板（简化版）*/}
      {showSpecPanel && (
        <>
          {/* 遮罩层 */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-30 z-40"
            onClick={() => setShowSpecPanel(false)}
          />
          
          {/* 侧边栏面板 */}
          <div className="fixed top-0 right-0 w-full max-w-[540px] h-screen bg-white shadow-lg z-50 overflow-y-auto">
            {/* 标题栏 */}
            <div className="flex justify-between items-center mb-6 border-b p-6 sticky top-0 bg-white z-10">
              <h2 className="text-xl font-semibold">📖 算子开发规范</h2>
              <button 
                onClick={() => setShowSpecPanel(false)}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-6 p-6 pb-12">
              {/* 概述 */}
              <section>
                <p className="text-sm text-slate-600 leading-relaxed">
                  算子本质上是一个标准文件夹结构，包含描述文件、配置清单、执行脚本和资源文件。以下为完整规范说明。
                </p>
              </section>

              {/* 文件夹结构 */}
              <section>
                <h3 className="text-base font-semibold mb-3 flex items-center gap-2">
                  📂 算子文件夹结构
                </h3>
                <div className="bg-[#f8f9fa] border border-gray-200 rounded-lg p-4 font-mono text-sm space-y-2">
                  <div className="pl-0">📁 my-operator/</div>
                  <div className="pl-4 text-gray-600">├── skill.md - 算子功能描述与使用说明</div>
                  <div className="pl-4 text-gray-600">├── skill.json - 算子元数据配置（名称、参数、版本等）</div>
                  <div className="pl-4 text-gray-600">├── scripts/</div>
                  <div className="pl-8 text-gray-600">│   └── main.py - 算子执行入口脚本</div>
                  <div className="pl-4 text-gray-600">├── requirements.txt - Python 依赖包列表</div>
                  <div className="pl-4 text-gray-600">└── assets/</div>
                  <div className="pl-8 text-gray-600">    └── icon.svg - 算子图标（建议 64×64px）</div>
                </div>
              </section>

              {/* skill.json 配置说明 */}
              <section>
                <h3 className="text-base font-semibold mb-3 flex items-center gap-2">
                  ⚙️ skill.json 配置说明
                </h3>
                <p className="text-sm text-slate-600 mb-3">
                  skill.json 是算子的核心配置文件，必须包含以下字段：
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="border border-gray-200 px-4 py-2 text-left font-medium">字段</th>
                        <th className="border border-gray-200 px-4 py-2 text-left font-medium">类型</th>
                        <th className="border border-gray-200 px-4 py-2 text-left font-medium">说明</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td className="border border-gray-200 px-4 py-2"><code>name</code></td>
                        <td className="border border-gray-200 px-4 py-2">string</td>
                        <td className="border border-gray-200 px-4 py-2">算子唯一标识，英文小写+连字符</td>
                      </tr>
                      <tr className="bg-gray-50/50">
                        <td className="border border-gray-200 px-4 py-2"><code>label</code></td>
                        <td className="border border-gray-200 px-4 py-2">string</td>
                        <td className="border border-gray-200 px-4 py-2">算子显示名称</td>
                      </tr>
                      <tr>
                        <td className="border border-gray-200 px-4 py-2"><code>version</code></td>
                        <td className="border border-gray-200 px-4 py-2">string</td>
                        <td className="border border-gray-200 px-4 py-2">版本号，遵循语义化版本</td>
                      </tr>
                      <tr className="bg-gray-50/50">
                        <td className="border border-gray-200 px-4 py-2"><code>description</code></td>
                        <td className="border border-gray-200 px-4 py-2">string</td>
                        <td className="border border-gray-200 px-4 py-2">算子功能描述（100字内）</td>
                      </tr>
                      <tr>
                        <td className="border border-gray-200 px-4 py-2"><code>author</code></td>
                        <td className="border border-gray-200 px-4 py-2">string</td>
                        <td className="border border-gray-200 px-4 py-2">作者名称或团队</td>
                      </tr>
                      <tr className="bg-gray-50/50">
                        <td className="border border-gray-200 px-4 py-2"><code>inputs</code></td>
                        <td className="border border-gray-200 px-4 py-2">array</td>
                        <td className="border border-gray-200 px-4 py-2">输入参数列表，包含 name、type、required</td>
                      </tr>
                      <tr>
                        <td className="border border-gray-200 px-4 py-2"><code>outputs</code></td>
                        <td className="border border-gray-200 px-4 py-2">array</td>
                        <td className="border border-gray-200 px-4 py-2">输出参数列表，格式同 inputs</td>
                      </tr>
                      <tr className="bg-gray-50/50">
                        <td className="border border-gray-200 px-4 py-2"><code>tags</code></td>
                        <td className="border border-gray-200 px-4 py-2">array</td>
                        <td className="border border-gray-200 px-4 py-2">分类标签，如 ["过滤", "文本"]</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              {/* skill.md 编写规范 */}
              <section>
                <h3 className="text-base font-semibold mb-3 flex items-center gap-2">
                  📝 skill.md 编写规范
                </h3>
                <p className="text-sm text-slate-600 mb-3">
                  skill.md 使用 Markdown 格式，建议包含以下章节：
                </p>
                
                <div className="space-y-3">
                  <div className="border-l-4 border-blue-500 pl-4">
                    <h4 className="font-medium"># 算子名称</h4>
                    <p className="text-sm text-slate-600 mt-1">清晰简洁地说明算子用途和适用场景。</p>
                  </div>
                  
                  <div className="border-l-4 border-green-500 pl-4">
                    <h4 className="font-medium">## 参数说明</h4>
                    <div className="mt-2 bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-xs overflow-x-auto">
                      <pre>{`| 参数名称 | 类型 | 是否必填 | 说明 |

      |----------|------|----------|------|
      | input    | str  | 是       | 输入文本 |

      \\\\ V \\\\
      const result = operator.run({input: "待处理输入"})
      \\\\ ^ \\\\`}</pre>
                    </div>
                  </div>
                  
                  <div className="border-l-4 border-yellow-500 pl-4">
                    <h4 className="font-medium">## 注意事项</h4>
                    <ul className="text-sm text-slate-600 list-disc pl-5 mt-1 space-y-1">
                      <li>需要 Python 3.8+</li>
                      <li>输入数据量建议不超过 1MB</li>
                    </ul>
                  </div>
                </div>
              </section>

              {/* 示例算子 */}
              <section>
                <h3 className="text-base font-semibold mb-3 flex items-center gap-2">
                  💡 示例算子
                </h3>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-800 mb-2">示例：utf-filter-operator</h4>
                  <p className="text-sm text-slate-700 mb-3">
                    功能：过滤文本中的特殊字符，支持白名单/黑名单配置。<br/>
                    包含完整的配置文件和脚本，可作为开发模板参考。
                  </p>
                  <button className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors">
                    <span>⬇️</span>
                    <span>下载示例算子.zip</span>
                  </button>
                </div>
              </section>

              {/* 发布前检查清单 */}
              <section>
                <h3 className="text-base font-semibold mb-3 flex items-center gap-2">
                  ✅ 发布前检查清单
                </h3>
                <p className="text-sm text-slate-600 mb-3">发布前请逐项确认：</p>
                <div className="space-y-2">
                  {[
                    'skill.json 中心字段完整无缺',
                    'skill.md 包含功能描述和使用示例',
                    'scripts/ 中包含可执行的入口脚本',
                    'assets/icon.svg 存在且清晰可识别',
                    '已在本地测试通过',
                    '无敏感信息或硬编码密钥'
                  ].map((item, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <div className="w-5 h-5 rounded border border-gray-300 flex-shrink-0 mt-0.5"></div>
                      <span className="text-sm text-slate-700">{item}</span>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </div>
        </>
      )}


      {/* 共享社区的弹框内容 */}
    <div className="w-full px-4 py-4 sm:px-6 lg:px-[40px] xl:px-[40px]">
      {/* ... 页面其他内容 ... */}

      {/* 5. 在页面底部渲染模态框 */}
      <ShareToCommunityModal
        isOpen={isShareModalOpen}
        onClose={closeShareModal}
        skill={currentSkill}
      />
    </div>
    </div>
  );

  
}

// --- 新增：共享到社区模态框组件 ---
interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  skill: DagSkillInfo | null;
}


const ShareToCommunityModal: React.FC<ShareModalProps> = ({ isOpen, onClose, skill }) => {
  if (!isOpen || !skill) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl p-6 relative animate-in fade-in zoom-in duration-200">
        {/* 标题栏 */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900">共享到社区</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        {/* 表单内容区 */}
        <div className="space-y-4">
          {/* 算子名称 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">算子名称 <span className="text-red-500">*</span></label>
            <input
              type="text"
              defaultValue={skill.skill_name}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-green-500 focus:border-green-500"
            />
          </div>

          {/* 描述 */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="block text-sm font-medium text-gray-700">描述 <span className="text-red-500">*</span></label>
              <button className="text-xs text-blue-600 hover:underline">从 skill.md 抓取</button>
            </div>
            <textarea
              rows={4}
              placeholder="简要描述算子的功能、适用场景与使用方式"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-green-500 focus:border-green-500"
            ></textarea>
          </div>

          {/* 图标选择 (简化版示意) */}
          <div>
             <label className="block text-sm font-medium text-gray-700 mb-2">图标 <span className="text-red-500">*</span></label>
             <div className="grid grid-cols-6 gap-2 p-3 border rounded-md bg-gray-50">
                {[1,2,3,4,5,6].map(i => (
                    <div key={i} className="w-8 h-8 bg-white border rounded cursor-pointer hover:border-green-500 flex items-center justify-center">📷</div>
                ))}
             </div>
          </div>

          {/* 机构与作者 */}
          <div className="grid grid-cols-2 gap-4">
             <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">机构 <span className="text-red-500">*</span></label>
                <input type="text" placeholder="例如：中国科学院计算技术研究所" className="w-full border border-gray-300 rounded-md px-3 py-2" />
             </div>
             <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">作者 <span className="text-red-500">*</span></label>
                <input type="text" placeholder="姓名" className="w-full border border-gray-300 rounded-md px-3 py-2" />
             </div>
          </div>

           <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">邮箱 <span className="text-red-500">*</span></label>
                <input type="email" placeholder="name@example.com" className="w-full border border-gray-300 rounded-md px-3 py-2" />
           </div>

           {/* 提示信息 */}
           <div className="bg-yellow-50 text-yellow-800 text-xs p-3 rounded border border-yellow-100">
             ⓘ 提交后将发送至官网进行审核，审核通过后将在社区生态中公开展示。审核结果（通过或拒绝）将通过邮件通知您，请确保邮箱地址正确。
           </div>
        </div>

        {/* 底部按钮 */}
        <div className="flex justify-end gap-3 mt-8">
          <button onClick={onClose} className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">取消</button>
          <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">提交审核</button>
        </div>
      </div>
    </div>
  );
};