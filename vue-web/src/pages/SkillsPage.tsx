import { Icon } from "@iconify/react";
import { useEffect, useMemo, useState } from "react";
import { apiBase, getSkillTypes, listSkills, type SkillItem, type SkillTypeStat } from "../lib/api";

const PAGE_SIZE = 10;
const ALL_SKILLS_LABEL = "全部技能";

type SkillCard = {
  key: string;
  title: string;
  description: string;
  category: string;
  icon?: string;
  raw: SkillItem;
};

type CategoryOption = {
  label: string;
  value: string;
  count: number;
};

function pickString(record: SkillItem, keys: string[]) {
  for (const key of keys) {
    const value = record[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }
  return "";
}

function resolveIconUrl(icon: string) {
  if (/^(https?:|data:|\/)/.test(icon)) {
    return icon;
  }
  return `${apiBase()}/${icon.replace(/^\/+/, "")}`;
}

function normalizeSkill(item: SkillItem, index: number): SkillCard {
  const icon = pickString(item, ["icon"]);
  const title = pickString(item, ["name", "title", "skill_name", "id"]) || `技能 ${index + 1}`;
  const category = pickString(item, ["category", "tag", "type"]) || "未分类";

  return {
    key: `${title}-${category}-${index}`,
    title,
    description:
      pickString(item, ["description", "desc", "summary"]) || "面向科研数据处理流程的可复用技能。",
    category,
    icon: icon ? resolveIconUrl(icon) : undefined,
    raw: item,
  };
}

function normalizeTypeStats(stats: SkillTypeStat[]): CategoryOption[] {
  const normalized = stats
    .filter((item) => item && typeof item.type === "string" && item.type.trim())
    .map((item) => ({
      label: item.type,
      value: item.type,
      count: Number(item.count) || 0,
    }))
    .sort((left, right) => right.count - left.count || left.label.localeCompare(right.label, "zh-CN"));

  const totalCount = normalized.reduce((sum, item) => sum + item.count, 0);
  return [{ label: ALL_SKILLS_LABEL, value: "", count: totalCount }, ...normalized];
}

function overlayPositionClass(index: number) {
  const isRightColumnOnTwoCol = index % 2 === 1;
  const xlColumn = index % 4;
  const opensLeftOnXl = xlColumn >= 2;

  return [
    "md:max-xl:w-[320px]",
    isRightColumnOnTwoCol ? "md:max-xl:right-[72%]" : "md:max-xl:left-[72%]",
    "xl:w-[340px]",
    opensLeftOnXl ? "xl:right-[72%]" : "xl:left-[72%]",
  ].join(" ");
}

export function SkillsPage() {
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<SkillCard[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [categoryOptions, setCategoryOptions] = useState<CategoryOption[]>([
    { label: ALL_SKILLS_LABEL, value: "", count: 0 },
  ]);
  const [categoryError, setCategoryError] = useState("");
  const [activeType, setActiveType] = useState("");
  const [copiedSkillKey, setCopiedSkillKey] = useState("");

  useEffect(() => {
    let alive = true;

    getSkillTypes()
      .then((response) => {
        if (!alive) {
          return;
        }
        if (response.code !== 200) {
          setCategoryError(response.message || "技能分类加载失败");
          return;
        }
        setCategoryOptions(normalizeTypeStats(response.data || []));
        setCategoryError("");
      })
      .catch((err: any) => {
        if (!alive) {
          return;
        }
        setCategoryError(String(err?.message || err));
      });

    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError("");

    listSkills(page, PAGE_SIZE, keyword, activeType)
      .then((response) => {
        if (!alive) {
          return;
        }
        if (response.code !== 200) {
          setError(response.message || "技能列表加载失败");
          setItems([]);
          setTotal(0);
          return;
        }

        const cards = (response.data || []).map(normalizeSkill);
        setItems(cards);
        setTotal(response.total || 0);
      })
      .catch((err: any) => {
        if (!alive) {
          return;
        }
        setError(String(err?.message || err));
        setItems([]);
        setTotal(0);
      })
      .finally(() => {
        if (!alive) {
          return;
        }
        setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [activeType, keyword, page]);

  useEffect(() => {
    if (!copiedSkillKey) {
      return;
    }
    const timer = window.setTimeout(() => setCopiedSkillKey(""), 1500);
    return () => window.clearTimeout(timer);
  }, [copiedSkillKey]);

  const hasNextPage = page * PAGE_SIZE < total;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pageNumbers = useMemo(() => {
    const pages = new Set<number>([1, totalPages, page - 1, page, page + 1]);
    return Array.from(pages)
      .filter((value) => value >= 1 && value <= totalPages)
      .sort((left, right) => left - right);
  }, [page, totalPages]);

  return (
    <div className="w-full px-4 py-8 sm:px-6 lg:px-[8vw] xl:px-[10vw]">
      <div className="mb-8 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
            Skills Hub
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-950">技能中心</h1>
          <p className="mt-3 text-sm leading-7 text-slate-500">
            浏览已注册技能，按关键词与类型检索，并快速查看每个技能的用途说明。
          </p>
        </div>

        <div className="w-full max-w-[460px] rounded-[24px] border border-slate-200 bg-white px-4 py-3 shadow-sm">
          <div className="flex items-center gap-3">
            <Icon className="text-slate-400" icon="ri:search-line" width="18" />
            <input
              className="w-full border-none bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
              onChange={(event) => {
                setKeyword(event.target.value);
                setPage(1);
              }}
              placeholder="搜索技能名、描述或标签"
              type="text"
              value={keyword}
            />
          </div>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[220px_minmax(0,1fr)] xl:grid-cols-[240px_minmax(0,1fr)]">
        <aside className="h-fit rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_24px_60px_rgba(15,23,42,0.04)]">
          <div className="mb-4 flex items-center justify-between">
            <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-slate-400">分类</p>
            {categoryError ? <span className="text-xs text-rose-500">加载失败</span> : null}
          </div>

          <ul className="space-y-2">
            {categoryOptions.map((category) => {
              const active = activeType === category.value;
              return (
                <li key={`${category.label}-${category.value || "all"}`}>
                  <button
                    className={
                      active
                        ? "flex w-full items-center justify-between rounded-2xl bg-black px-3 py-3 text-left text-sm font-medium text-white"
                        : "flex w-full items-center justify-between rounded-2xl px-3 py-3 text-left text-sm font-medium text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-900"
                    }
                    onClick={() => {
                      setActiveType(category.value);
                      setPage(1);
                    }}
                    type="button"
                  >
                    <span>{category.label}</span>
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

        <section className="min-w-0">
          {error ? (
            <div className="mb-6 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}

          <div className="mb-6 flex flex-col gap-3 rounded-[28px] border border-slate-200 bg-white px-5 py-4 shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
            <div className="text-sm text-slate-500">
              {loading ? "正在加载技能列表..." : `共 ${total} 个技能，每页 ${PAGE_SIZE} 个，当前页显示 ${items.length} 个`}
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
              <span className="rounded-full bg-slate-100 px-3 py-1">
                类型：{categoryOptions.find((item) => item.value === activeType)?.label || ALL_SKILLS_LABEL}
              </span>
              {keyword ? <span className="rounded-full bg-slate-100 px-3 py-1">关键词：{keyword}</span> : null}
              {!loading ? (
                <span className="rounded-full bg-slate-100 px-3 py-1">当前第 {page} 页</span>
              ) : null}
            </div>
          </div>

          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {items.map((item, index) => {
              const copied = copiedSkillKey === item.key;

              return (
                <article
                  key={item.key}
                  className="group/skill relative z-0 flex h-full flex-col rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_20px_60px_rgba(15,23,42,0.04)] transition-all hover:z-20 hover:-translate-y-1 hover:border-black"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                      {item.icon ? (
                        <img alt={item.title} className="h-8 w-8 rounded-xl object-cover" src={item.icon} />
                      ) : (
                        <Icon icon="ri:flashlight-line" width="22" />
                      )}
                    </div>

                    <div className="min-w-0 flex-1">
                      <h3 className="break-words text-lg font-semibold leading-7 text-slate-900">
                        {item.title}
                      </h3>
                      <div className="mt-2">
                        <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-[11px] font-medium tracking-[0.08em] text-slate-500">
                          {item.category}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="group/desc relative mt-5 flex-1 rounded-[24px] bg-slate-50 px-4 py-4">
                    <p className="line-clamp-3 text-sm leading-7 text-slate-600" title={item.description}>
                      {item.description}
                    </p>

                    <div
                      className={`pointer-events-none absolute top-1/2 z-30 hidden min-h-[168px] -translate-y-1/2 rounded-[24px] border border-slate-200 bg-slate-950 px-5 py-4 text-sm leading-7 text-white opacity-0 shadow-[0_24px_60px_rgba(15,23,42,0.28)] transition-all duration-200 md:block ${overlayPositionClass(index)} group-hover/desc:opacity-100 group-focus-within/desc:opacity-100`}
                    >
                      {item.description}
                    </div>
                  </div>

                  <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
                    <span className="text-xs text-slate-400">点击复制技能配置</span>
                    <button
                      className="inline-flex items-center gap-1 rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-black hover:text-black"
                      onClick={() => {
                        navigator.clipboard?.writeText(JSON.stringify(item.raw, null, 2)).catch(() => {});
                        setCopiedSkillKey(item.key);
                      }}
                      type="button"
                    >
                      {copied ? "已复制" : "复制配置"}
                      <Icon icon="ri:arrow-right-up-line" width="14" />
                    </button>
                  </div>
                </article>
              );
            })}

            {!loading && items.length === 0 ? (
              <div className="col-span-full rounded-[28px] border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-400">
                没有匹配到技能。可以尝试更换关键词，或切换类型重新查看。
              </div>
            ) : null}
          </div>

          <div className="mt-10 flex flex-col gap-4 border-t border-slate-200 pt-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-slate-500">
              共 {total} 条，当前第 {page} / {totalPages} 页
            </div>

            <div className="flex flex-wrap items-center justify-end gap-2">
              {pageNumbers.map((value, index) => {
                const previous = pageNumbers[index - 1];
                const showGap = previous && value - previous > 1;
                return (
                  <div key={value} className="flex items-center gap-2">
                    {showGap ? <span className="px-1 text-xs text-slate-400">...</span> : null}
                    <button
                      className={
                        value === page
                          ? "rounded-full border border-black bg-black px-3 py-1.5 text-xs font-medium text-white"
                          : "rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-black hover:text-black"
                      }
                      onClick={() => setPage(value)}
                      type="button"
                    >
                      {value}
                    </button>
                  </div>
                );
              })}

              <div className="mx-1 h-5 w-px bg-slate-200" />

              <button
                className="rounded-full border border-slate-200 px-4 py-2 text-xs font-medium text-slate-600 transition-colors hover:border-black hover:text-black disabled:cursor-not-allowed disabled:opacity-40"
                disabled={page <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                type="button"
              >
                上一页
              </button>
              <button
                className="rounded-full border border-slate-200 px-4 py-2 text-xs font-medium text-slate-600 transition-colors hover:border-black hover:text-black disabled:cursor-not-allowed disabled:opacity-40"
                disabled={loading || !hasNextPage}
                onClick={() => setPage((current) => current + 1)}
                type="button"
              >
                下一页
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
