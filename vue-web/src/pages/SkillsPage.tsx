import { Icon } from "@iconify/react";
import { useEffect, useMemo, useState } from "react";
import { listSkills, type SkillItem } from "../lib/api";

const PAGE_SIZE = 20;

type SkillCard = {
  title: string;
  description: string;
  category: string;
  icon?: string;
  raw: SkillItem;
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

function normalizeSkill(item: SkillItem, index: number): SkillCard {
  const icon = pickString(item, ["icon"]);
  return {
    title: pickString(item, ["name", "title", "skill_name", "id"]) || `技能 ${index + 1}`,
    description:
      pickString(item, ["description", "desc", "summary"]) || "面向科研数据处理流程的可复用技能。",
    category: pickString(item, ["category", "tag", "type"]) || "未分类",
    icon: /^(https?:|data:|\/)/.test(icon) ? icon : undefined,
    raw: item,
  };
}

export function SkillsPage() {
  const [keyword, setKeyword] = useState("");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<SkillCard[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeCategory, setActiveCategory] = useState("全部技能");

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError("");

    listSkills(page, PAGE_SIZE, keyword)
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
        setTotal(response.total || cards.length);
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
  }, [keyword, page]);

  const categoryStats = useMemo(() => {
    const map = new Map<string, number>();
    for (const item of items) {
      map.set(item.category, (map.get(item.category) || 0) + 1);
    }
    const entries = Array.from(map.entries()).sort((a, b) => b[1] - a[1]);
    return [{ label: "全部技能", count: total || items.length }, ...entries.map(([label, count]) => ({ label, count }))];
  }, [items, total]);

  const visibleItems = useMemo(() => {
    if (activeCategory === "全部技能") {
      return items;
    }
    return items.filter((item) => item.category === activeCategory);
  }, [activeCategory, items]);

  const hasNextPage = page * PAGE_SIZE < total;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pageNumbers = useMemo(() => {
    const pages = new Set<number>([1, totalPages, page - 1, page, page + 1]);
    return Array.from(pages)
      .filter((value) => value >= 1 && value <= totalPages)
      .sort((left, right) => left - right);
  }, [page, totalPages]);

  useEffect(() => {
    if (activeCategory !== "全部技能" && !items.some((item) => item.category === activeCategory)) {
      setActiveCategory("全部技能");
    }
  }, [activeCategory, items]);

  return (
    <div className="w-full px-6 py-8 lg:px-8 xl:px-10">
      <div className="mb-10 flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
            Skills Hub
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-950">技能中心</h1>
          <p className="mt-3 text-sm leading-7 text-slate-500">
            浏览已注册技能，按关键词检索，并快速查看每个技能的用途说明。
          </p>
        </div>

        <div className="w-full max-w-[420px] rounded-[24px] border border-slate-200 bg-white px-4 py-3 shadow-sm">
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

      <div className="grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)] 2xl:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="h-fit rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_24px_60px_rgba(15,23,42,0.04)]">
          <p className="mb-4 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-400">分类</p>
          <ul className="space-y-2">
            {categoryStats.map((category) => {
              const active = activeCategory === category.label;
              return (
                <li key={category.label}>
                  <button
                    className={
                      active
                        ? "flex w-full items-center justify-between rounded-2xl bg-black px-3 py-3 text-left text-sm font-medium text-white"
                        : "flex w-full items-center justify-between rounded-2xl px-3 py-3 text-left text-sm font-medium text-slate-500 transition-colors hover:bg-slate-50 hover:text-slate-900"
                    }
                    onClick={() => setActiveCategory(category.label)}
                    type="button"
                  >
                    <span>{category.label}</span>
                    <span className={active ? "rounded-full bg-white/15 px-2 py-0.5 text-[10px]" : "rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-500"}>
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

          <div className="mb-6 flex items-center justify-between text-sm text-slate-500">
            <span>{loading ? "正在加载技能列表..." : `共 ${total} 个技能，每页 ${PAGE_SIZE} 个，当前显示 ${visibleItems.length} 个`}</span>
            <span>第 {page} 页</span>
          </div>

          <div className="grid justify-items-start gap-6 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {visibleItems.map((item) => (
              <article
                key={`${item.title}-${item.category}`}
                className="group relative flex min-h-[248px] w-full max-w-[320px] flex-col rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_20px_60px_rgba(15,23,42,0.04)] transition-all hover:-translate-y-1 hover:border-black"
                title="点击复制技能 JSON"
                onClick={() => {
                  navigator.clipboard?.writeText(JSON.stringify(item.raw, null, 2)).catch(() => {});
                }}
              >
                <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                  {item.icon ? (
                    <img alt={item.title} className="h-8 w-8 rounded-xl object-cover" src={item.icon} />
                  ) : (
                    <Icon icon="ri:flashlight-line" width="22" />
                  )}
                </div>

                <h3 className="text-base font-semibold leading-7 text-slate-900">{item.title}</h3>
                <p
                  className="mt-3 flex-1 overflow-hidden text-sm leading-7 text-slate-500"
                  style={{
                    display: "-webkit-box",
                    WebkitBoxOrient: "vertical",
                    WebkitLineClamp: 3,
                  }}
                  title={item.description}
                >
                  {item.description}
                </p>

                <div className="pointer-events-none absolute inset-x-5 top-[98px] z-10 hidden rounded-2xl border border-slate-200 bg-slate-950 px-4 py-3 text-xs leading-6 text-white shadow-[0_20px_50px_rgba(15,23,42,0.24)] group-hover:block">
                  {item.description}
                </div>

                <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-slate-500">
                    {item.category}
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-400 transition-colors group-hover:text-black">
                    复制配置
                    <Icon icon="ri:arrow-right-up-line" width="14" />
                  </span>
                </div>
              </article>
            ))}

            {!loading && visibleItems.length === 0 ? (
              <div className="col-span-full rounded-[28px] border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-400">
                没有匹配到技能。可以尝试更换关键词，或切换分类重新查看。
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
