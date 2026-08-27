import { useEffect, useState, useCallback } from 'react';
import { Icon } from '@iconify/react';
import { toast } from '../components/Toast';
import {
  listWorkflowTemplates,
  getWorkflowTemplateFields,
  getWorkflowTemplateTags,
  createWorkflowTemplate,
  deleteWorkflowTemplate,
  runWorkflowTemplate,
  getTasks,
  WorkflowTemplateInfo,
  Task,
} from '../lib/api';

const DEFAULT_TEMPLATE_ICON = 'ri:flow-chart';

const PUBLISHER_PERSONAL = '个人创建';
const PUBLISHER_ORG_SHARED = '组织共享';
const PUBLISHER_OFFICIAL_COMMUNITY = '官方社区';

function getPublisherBadgeClass(publisher?: string): string {
  switch (publisher) {
    case PUBLISHER_PERSONAL:
      return 'bg-blue-50 text-blue-700 border border-blue-200';
    case PUBLISHER_ORG_SHARED:
      return 'bg-amber-50 text-amber-700 border border-amber-200';
    case PUBLISHER_OFFICIAL_COMMUNITY:
      return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
    default:
      return 'bg-slate-50 text-slate-600 border border-slate-200';
  }
}

function getPublisherIcon(publisher?: string): string {
  switch (publisher) {
    case PUBLISHER_PERSONAL:
      return 'ri:user-line';
    case PUBLISHER_ORG_SHARED:
      return 'ri:team-line';
    case PUBLISHER_OFFICIAL_COMMUNITY:
      return 'ri:community-line';
    default:
      return 'ri:user-line';
  }
}

function formatDateTime(dateStr?: string): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const h = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${day} ${h}:${min}`;
  } catch {
    return dateStr;
  }
}

type TemplateGroup = {
  disciplinary_field: string;
  templateList: WorkflowTemplateInfo[];
};

export function WorkLibPage() {
  const [keyword, setKeyword] = useState('');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [activeField, setActiveField] = useState<string>('');
  const [allFields, setAllFields] = useState<{ name: string; count: number }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [templateGroups, setTemplateGroups] = useState<TemplateGroup[]>([]);
  const [totalCount, setTotalCount] = useState(0);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showTaskPickerModal, setShowTaskPickerModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<{ template: WorkflowTemplateInfo | null }>({ template: null });

  const [showRunSuccessModal, setShowRunSuccessModal] = useState(false);
  const [runSuccessInfo, setRunSuccessInfo] = useState<{ templateName: string; processId: string; templateId: string } | null>(null);
  const [showRunErrorModal, setShowRunErrorModal] = useState(false);
  const [runErrorInfo, setRunErrorInfo] = useState<{ templateName: string; message: string } | null>(null);

  const [tags, setTags] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  const [createForm, setCreateForm] = useState({
    template_name: '',
    description: '',
    disciplinary_field: '',
    tags: [] as string[],
    version: '1.0.0',
    dag_task_id: '',
    dag_task_name: '',
  });

  const [editForm, setEditForm] = useState<{
    template: WorkflowTemplateInfo | null;
    template_name: string;
    description: string;
    disciplinary_field: string;
    tags: string[];
    version: string;
  }>({
    template: null,
    template_name: '',
    description: '',
    disciplinary_field: '',
    tags: [],
    version: '',
  });

  const loadTemplates = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const publisherParam = sourceFilter === 'all' ? '' : sourceFilter;
      const fieldParam = activeField && activeField !== '全部领域' ? activeField : '';
      const res = await listWorkflowTemplates(undefined, undefined, keyword || '', fieldParam, publisherParam);
      if (res.code === 200 && res.data) {
        const resultData = (res.data as any).data || [];
        const total = (res.data as any).total || 0;
        setTemplateGroups(resultData);
        setTotalCount(total);
      } else {
        setError(res.message || '加载工作流列表失败');
        setTemplateGroups([]);
      }
    } catch (err: any) {
      setError(err?.message || '加载工作流列表失败');
      setTemplateGroups([]);
    } finally {
      setLoading(false);
    }
  }, [keyword, sourceFilter, activeField]);

  const loadFields = useCallback(async () => {
    try {
      const res = await getWorkflowTemplateFields();
      if (res.code === 200 && res.data) {
        const fieldData = res.data;
        const withTotal = [{ name: '全部领域', count: totalCount }, ...fieldData.map((f: any) => ({ name: f.disciplinary_field || '基础', count: f.count }))];
        setAllFields(withTotal);
        if (!activeField) {
          setActiveField('全部领域');
        }
      }
    } catch (err) {
      console.error('加载领域列表失败:', err);
    }
  }, [totalCount, activeField]);

  const loadTags = useCallback(async () => {
    try {
      const res = await getWorkflowTemplateTags();
      if (res.code === 200 && res.data) {
        setTags(res.data);
      }
    } catch (err) {
      console.error('加载标签列表失败:', err);
    }
  }, []);

  useEffect(() => {
    loadTags();
  }, [loadTags]);

  useEffect(() => {
    loadFields();
  }, [loadFields]);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const totalTemplates = templateGroups.reduce(
    (sum, g) => sum + (g.templateList?.length || 0),
    0
  );

  const handleSourceFilterChange = (val: string) => {
    setSourceFilter(val);
  };

  const handleFieldClick = (field: string) => {
    setActiveField(field);
  };

  const handleSearch = (val: string) => {
    setKeyword(val);
  };

  const openCreateModal = () => {
    setCreateForm({
      template_name: '',
      description: '',
      disciplinary_field: '',
      tags: [],
      version: '1.0.0',
      dag_task_id: '',
      dag_task_name: '',
    });
    setShowCreateModal(true);
  };

  const closeCreateModal = () => {
    setShowCreateModal(false);
    setShowTaskPickerModal(false);
  };

  const openEditModal = (template: WorkflowTemplateInfo) => {
    setEditForm({
      template,
      template_name: template.template_name,
      description: template.description || '',
      disciplinary_field: template.disciplinary_field || '',
      tags: template.tags || [],
      version: template.version || '1.0.0',
    });
    setShowEditModal(true);
  };

  const closeEditModal = () => {
    setShowEditModal(false);
    setEditForm({
      template: null,
      template_name: '',
      description: '',
      disciplinary_field: '',
      tags: [],
      version: '',
    });
  };

  const toggleTag = (tag: string) => {
    setCreateForm((prev) => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter((t) => t !== tag)
        : [...prev.tags, tag],
    }));
  };

  const toggleEditTag = (tag: string) => {
    setEditForm((prev) => ({
      ...prev,
      tags: prev.tags.includes(tag)
        ? prev.tags.filter((t) => t !== tag)
        : [...prev.tags, tag],
    }));
  };

  const handleSelectTask = (task: Task) => {
    setCreateForm((prev) => ({
      ...prev,
      dag_task_id: task.dag_task_id,
      dag_task_name: task.dag_task_name,
    }));
    setShowTaskPickerModal(false);
  };

  const handleRemoveSelectedTask = () => {
    setCreateForm((prev) => ({
      ...prev,
      dag_task_id: '',
      dag_task_name: '',
    }));
  };

  const handleCreateSubmit = async () => {
    if (!createForm.template_name.trim()) {
      toast.error('请填写工作流模板名称');
      return;
    }
    if (!createForm.dag_task_id) {
      toast.error('请选择模板来源任务');
      return;
    }
    setSubmitting(true);
    try {
      const res = await createWorkflowTemplate({
        template_name: createForm.template_name.trim(),
        description: createForm.description,
        dag_task_id: createForm.dag_task_id,
        template_json: {},
        disciplinary_field: createForm.disciplinary_field || undefined,
        tags: createForm.tags,
        version: createForm.version,
      });
      if (res.code === 200) {
        toast.success('工作流模板创建成功');
        closeCreateModal();
        loadTemplates();
        loadFields();
      } else {
        toast.error(res.message || '创建失败');
      }
    } catch (err: any) {
      toast.error('创建失败: ' + (err?.message || '未知错误'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditSubmit = async () => {
    const template = editForm.template;
    if (!template) return;
    setSubmitting(true);
    try {
      const res = await createWorkflowTemplate({
        template_name: editForm.template_name,
        description: editForm.description,
        template_json: {},
        disciplinary_field: editForm.disciplinary_field || undefined,
        tags: editForm.tags,
        version: editForm.version,
        db_id: template.id,
      });
      if (res.code === 200) {
        toast.success('工作流模板更新成功');
        closeEditModal();
        loadTemplates();
        loadFields();
      } else {
        toast.error(res.message || '更新失败');
      }
    } catch (err: any) {
      toast.error('更新失败: ' + (err?.message || '未知错误'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteTemplate = async () => {
    const template = showDeleteConfirm.template;
    if (!template) return;
    try {
      const res = await deleteWorkflowTemplate(template.template_id);
      if (res.code === 200 && res.data?.deleted) {
        toast.success('删除成功');
        setShowDeleteConfirm({ template: null });
        loadTemplates();
        loadFields();
      } else {
        toast.error(res.message || '删除失败');
      }
    } catch (err: any) {
      toast.error('删除失败: ' + (err?.message || '未知错误'));
    }
  };

  const handleRunTemplate = async (template: WorkflowTemplateInfo) => {
    try {
      const res = await runWorkflowTemplate(template.template_id);
      if (res.code === 200 && res.result) {
        setRunSuccessInfo({
          templateName: template.template_name,
          templateId: template.template_id,
          processId: res.result.process_id,
        });
        setShowRunSuccessModal(true);
      } else {
        setRunErrorInfo({
          templateName: template.template_name,
          message: res.message || '运行失败',
        });
        setShowRunErrorModal(true);
      }
    } catch (err: any) {
      setRunErrorInfo({
        templateName: template.template_name,
        message: err?.message || '未知错误',
      });
      setShowRunErrorModal(true);
    }
  };

  return (
    <div className="w-full px-6 py-6">
      <div className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">工作流库</h1>
          <p className="mt-2 text-sm text-slate-500">
            将重复性强的标准化流程固化为工作流模板，供自己或团队复用。优秀的工作流欢迎共享，让更多人受益。
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700"
        >
          <Icon icon="ri:add-line" width="18" />
          添加工作流
        </button>
      </div>

      {/* Toolbar */}
      <div className="mb-5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Icon
              icon="ri:search-line"
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              width="18"
            />
            <input
              type="text"
              placeholder="搜索我的工作流"
              value={keyword}
              onChange={(e) => handleSearch(e.target.value)}
              className="h-10 w-[320px] rounded-lg border border-slate-200 bg-white pl-10 pr-4 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
          <select
            value={sourceFilter}
            onChange={(e) => handleSourceFilterChange(e.target.value)}
            className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          >
            <option value="all">全部来源</option>
            <option value={PUBLISHER_PERSONAL}>个人创建</option>
            <option value={PUBLISHER_ORG_SHARED}>组织共享</option>
            <option value={PUBLISHER_OFFICIAL_COMMUNITY}>官方社区</option>
          </select>
        </div>
      </div>

      <div className="flex gap-6">
        {/* 左侧学科领域 */}
        <aside className="w-[200px] flex-shrink-0">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="mb-3 text-[11px] font-bold uppercase tracking-widest text-slate-400">
              学科领域
            </p>
            <ul className="space-y-1">
              {allFields.map((field) => {
                const isActive = activeField === field.name;
                return (
                  <li key={field.name}>
                    <button
                      onClick={() => handleFieldClick(field.name)}
                      className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-[13px] font-medium transition ${
                        isActive
                          ? 'bg-slate-900 text-white'
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                      }`}
                    >
                      <span>{field.name}</span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-[11px] ${
                          isActive
                            ? 'bg-white/20 text-white'
                            : 'bg-slate-100 text-slate-500'
                        }`}
                      >
                        {field.count}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        </aside>

        {/* 右侧工作流列表 */}
        <main className="min-w-0 flex-1">
          {error && (
            <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          )}

          <div className="mb-3 text-sm text-slate-500">
            {loading ? '加载中...' : `共 ${totalTemplates} 个工作流`}
          </div>

          {loading ? (
            <div className="rounded-xl border border-dashed border-slate-200 bg-white p-12 text-center text-sm text-slate-400">
              加载中...
            </div>
          ) : totalTemplates === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 bg-white p-12 text-center text-sm text-slate-400">
              暂无工作流，点击右上角「添加工作流」创建
            </div>
          ) : (
            <div className="space-y-8">
              {templateGroups.map((group) => (
                <div key={group.disciplinary_field}>
                  <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-900">
                    {group.disciplinary_field}
                    <span className="text-sm font-normal text-slate-400">
                      ({group.templateList.length} 个)
                    </span>
                  </h2>
                  <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                    {group.templateList.map((template) => (
                      <TemplateCard
                        key={template.template_id}
                        template={template}
                        onDelete={() => setShowDeleteConfirm({ template })}
                        onRun={() => handleRunTemplate(template)}
                        onEdit={() => openEditModal(template)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>

      {/* 创建工作流 Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="max-h-[90vh] w-[560px] max-w-[90vw] overflow-auto rounded-xl bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <h3 className="text-base font-semibold text-slate-900">添加工作流</h3>
              <button
                onClick={closeCreateModal}
                className="text-xl text-slate-400 transition hover:text-slate-900"
              >
                ×
              </button>
            </div>
            <div className="space-y-4 px-6 py-4">
              <div>
                <label className="mb-1.5 block text-sm text-slate-600">
                  工作流模板名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={createForm.template_name}
                  onChange={(e) => setCreateForm({ ...createForm, template_name: e.target.value })}
                  placeholder="例如：文本数据清洗流水线"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm text-slate-600">描述</label>
                <textarea
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="简要描述工作流的功能、适用场景"
                  className="min-h-[80px] w-full resize-y rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm text-slate-600">学科领域</label>
                <input
                  type="text"
                  value={createForm.disciplinary_field}
                  onChange={(e) => setCreateForm({ ...createForm, disciplinary_field: e.target.value })}
                  placeholder="例如：信息科学"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm text-slate-600">标签</label>
                <div className="flex flex-wrap gap-2 rounded-lg border border-slate-200 p-2">
                  {tags.length === 0 && (
                    <span className="text-sm text-slate-400">加载中...</span>
                  )}
                  {tags.map((tag) => {
                    const isSelected = createForm.tags.includes(tag);
                    return (
                      <button
                        key={tag}
                        type="button"
                        onClick={() => toggleTag(tag)}
                        className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                          isSelected
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {tag}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-sm text-slate-600">版本号</label>
                <input
                  type="text"
                  value={createForm.version}
                  onChange={(e) => setCreateForm({ ...createForm, version: e.target.value })}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm text-slate-600">
                  模板来源任务 <span className="text-red-500">*</span>
                </label>
                {createForm.dag_task_id ? (
                  <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                    <div className="flex items-center gap-2">
                      <Icon icon="ri:task-line" className="text-blue-500" width="18" />
                      <span className="text-sm text-slate-700">
                        {createForm.dag_task_name || createForm.dag_task_id}
                      </span>
                    </div>
                    <button
                      onClick={handleRemoveSelectedTask}
                      className="text-xs text-slate-400 transition hover:text-red-500"
                    >
                      移除
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setShowTaskPickerModal(true)}
                    className="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-slate-300 bg-slate-50 px-3 py-6 text-sm text-slate-500 transition hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600"
                  >
                    <Icon icon="ri:add-line" width="18" />
                    选择任务
                  </button>
                )}
              </div>
            </div>
            <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
              <button
                onClick={closeCreateModal}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 transition hover:bg-slate-50"
              >
                取消
              </button>
              <button
                onClick={handleCreateSubmit}
                disabled={submitting}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? '创建中...' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑工作流 Modal */}
      {showEditModal && editForm.template && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="max-h-[90vh] w-[560px] max-w-[90vw] overflow-auto rounded-xl bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <h3 className="text-base font-semibold text-slate-900">编辑工作流</h3>
              <button
                onClick={closeEditModal}
                className="text-xl text-slate-400 transition hover:text-slate-900"
              >
                ×
              </button>
            </div>
            <div className="space-y-4 px-6 py-4">
              <div>
                <label className="mb-1.5 block text-sm text-slate-600">工作流模板名称</label>
                <input
                  type="text"
                  value={editForm.template_name}
                  onChange={(e) => setEditForm({ ...editForm, template_name: e.target.value })}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm text-slate-600">描述</label>
                <textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  placeholder="简要描述工作流的功能、适用场景"
                  className="min-h-[80px] w-full resize-y rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm text-slate-600">学科领域</label>
                <input
                  type="text"
                  value={editForm.disciplinary_field}
                  onChange={(e) => setEditForm({ ...editForm, disciplinary_field: e.target.value })}
                  placeholder="例如：信息科学"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm text-slate-600">标签</label>
                <div className="flex flex-wrap gap-2 rounded-lg border border-slate-200 p-2">
                  {tags.length === 0 && (
                    <span className="text-sm text-slate-400">加载中...</span>
                  )}
                  {tags.map((tag) => {
                    const isSelected = editForm.tags.includes(tag);
                    return (
                      <button
                        key={tag}
                        type="button"
                        onClick={() => toggleEditTag(tag)}
                        className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                          isSelected
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {tag}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-sm text-slate-600">版本号</label>
                <input
                  type="text"
                  value={editForm.version}
                  onChange={(e) => setEditForm({ ...editForm, version: e.target.value })}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
              <button
                onClick={closeEditModal}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 transition hover:bg-slate-50"
              >
                取消
              </button>
              <button
                onClick={handleEditSubmit}
                disabled={submitting}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 任务选择 Modal */}
      {showTaskPickerModal && (
        <TaskPickerModal
          onClose={() => setShowTaskPickerModal(false)}
          onSelect={handleSelectTask}
        />
      )}

      {/* 删除确认 Modal */}
      {showDeleteConfirm.template && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-[420px] rounded-xl bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <h3 className="text-base font-semibold text-slate-900">确认删除</h3>
              <button
                onClick={() => setShowDeleteConfirm({ template: null })}
                className="text-xl text-slate-400 transition hover:text-slate-900"
              >
                ×
              </button>
            </div>
            <div className="px-6 py-4">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-red-50 text-red-500">
                  <Icon icon="ri:alert-line" width="22" />
                </div>
                <div>
                  <p className="mb-1 text-sm font-semibold text-slate-900">
                    确定要删除该工作流吗？
                  </p>
                  <p className="text-sm text-slate-500">
                    工作流「
                    <span className="font-medium text-slate-700">
                      {showDeleteConfirm.template.template_name}
                    </span>
                    」将被永久删除，此操作不可撤销。
                  </p>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
              <button
                onClick={() => setShowDeleteConfirm({ template: null })}
                className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 transition hover:bg-slate-50"
              >
                取消
              </button>
              <button
                onClick={handleDeleteTemplate}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-700"
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 运行成功 Modal */}
      {showRunSuccessModal && runSuccessInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-[480px] rounded-xl bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <h3 className="text-base font-semibold text-slate-900">工作流提交成功</h3>
              <button
                onClick={() => setShowRunSuccessModal(false)}
                className="text-xl text-slate-400 transition hover:text-slate-900"
              >
                ×
              </button>
            </div>
            <div className="px-6 py-4">
              <p className="text-sm text-slate-700">
                工作流「<strong>{runSuccessInfo.templateName}</strong>」已提交运行，请前往【运行历史】查看执行状态。
              </p>
              <div className="mt-3 space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-slate-500">工作流模板ID：</span>
                  <code className="rounded bg-slate-100 px-2 py-0.5 font-mono text-xs text-slate-700">
                    {runSuccessInfo.templateId}
                  </code>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-slate-500">执行实例ID：</span>
                  <code className="rounded bg-slate-100 px-2 py-0.5 font-mono text-xs text-slate-700">
                    {runSuccessInfo.processId}
                  </code>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
              <button
                onClick={() => setShowRunSuccessModal(false)}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
              >
                确定
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 运行失败 Modal */}
      {showRunErrorModal && runErrorInfo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-[480px] rounded-xl bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
              <h3 className="text-base font-semibold text-red-600">工作流运行失败</h3>
              <button
                onClick={() => setShowRunErrorModal(false)}
                className="text-xl text-slate-400 transition hover:text-slate-900"
              >
                ×
              </button>
            </div>
            <div className="px-6 py-4">
              <p className="text-sm text-slate-700">
                工作流「<strong>{runErrorInfo.templateName}</strong>」提交失败：
              </p>
              <p className="mt-2 text-sm text-red-600">
                <strong>错误信息：</strong>{runErrorInfo.message}
              </p>
            </div>
            <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4">
              <button
                onClick={() => setShowRunErrorModal(false)}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-700"
              >
                确定
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function TemplateCard({
  template,
  onDelete,
  onRun,
  onEdit,
}: {
  template: WorkflowTemplateInfo;
  onDelete: () => void;
  onRun: () => void;
  onEdit: () => void;
}) {
  const isPersonal = template.publisher === PUBLISHER_PERSONAL;

  return (
    <article className="group relative flex flex-col rounded-xl border border-slate-200 bg-white p-5 transition-all hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md">
      {/* Header */}
      <div className="mb-3 flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
            <Icon icon={DEFAULT_TEMPLATE_ICON} width="22" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="truncate text-base font-semibold text-slate-900">
              {template.template_name}
            </h3>
            <div className="mt-1 flex flex-wrap items-center gap-1.5">
              {template.disciplinary_field && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
                  {template.disciplinary_field}
                </span>
              )}
              {template.publisher && (
                <span
                  className={`inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[11px] font-medium ${getPublisherBadgeClass(template.publisher)}`}
                >
                  <Icon icon={getPublisherIcon(template.publisher)} width="10" />
                  {template.publisher}
                </span>
              )}
            </div>
          </div>
        </div>
        {/* Actions */}
        <div className="flex items-center gap-1">
          {isPersonal && (
            <>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit();
                }}
                title="编辑"
                className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-slate-400 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-500"
              >
                <Icon icon="ri:edit-line" width="16" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                title="删除"
                className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-slate-400 transition hover:border-red-200 hover:bg-red-50 hover:text-red-500"
              >
                <Icon icon="ri:delete-bin-line" width="16" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Tags */}
      {template.tags && template.tags.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1.5">
          {template.tags.map((tag, i) => (
            <span
              key={i}
              className="rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Description */}
      <p className="mb-4 line-clamp-3 flex-1 rounded-lg bg-slate-50 px-3 py-3 text-sm leading-6 text-slate-600">
        {template.description || '暂无描述'}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between border-t border-slate-100 pt-3">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          {template.author_name && (
            <div className="flex items-center gap-1">
              <div className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-200 text-[10px] font-bold text-slate-600">
                {template.author_name.slice(0, 1)}
              </div>
              <span className="text-slate-500">{template.author_name}</span>
            </div>
          )}
          {template.version && (
            <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[10px] text-slate-500">
              v{template.version}
            </span>
          )}
        </div>
        <button
          onClick={onRun}
          className="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 transition hover:bg-emerald-100"
        >
          <Icon icon="ri:play-line" width="12" />
          运行
        </button>
      </div>
    </article>
  );
}

function TaskPickerModal({
  onClose,
  onSelect,
}: {
  onClose: () => void;
  onSelect: (task: Task) => void;
}) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [keyword, setKeyword] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const loadTasks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getTasks(page, pageSize, keyword || undefined);
      if (res.code === 200 && res.result) {
        setTasks(res.result.data || []);
        setTotal(res.result.total || 0);
      } else {
        setTasks([]);
      }
    } catch (err) {
      console.error('加载任务列表失败:', err);
      setTasks([]);
    } finally {
      setLoading(false);
    }
  }, [page, keyword]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="max-h-[80vh] w-[520px] max-w-[90vw] overflow-hidden rounded-xl bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
          <h3 className="text-base font-semibold text-slate-900">选择模板来源任务</h3>
          <button
            onClick={onClose}
            className="text-xl text-slate-400 transition hover:text-slate-900"
          >
            ×
          </button>
        </div>
        <div className="border-b border-slate-100 px-5 py-3">
          <div className="relative">
            <Icon
              icon="ri:search-line"
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              width="18"
            />
            <input
              type="text"
              placeholder="搜索任务名称"
              value={keyword}
              onChange={(e) => {
                setKeyword(e.target.value);
                setPage(1);
              }}
              className="h-9 w-full rounded-lg border border-slate-200 pl-10 pr-3 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
        </div>
        <div className="max-h-[400px] overflow-auto px-5 py-3">
          {loading ? (
            <div className="py-12 text-center text-sm text-slate-400">加载中...</div>
          ) : tasks.length === 0 ? (
            <div className="py-12 text-center text-sm text-slate-400">暂无任务</div>
          ) : (
            <div className="space-y-2">
              {tasks.map((task) => (
                <button
                  key={task.dag_task_id}
                  onClick={() => onSelect(task)}
                  className="flex w-full items-start gap-3 rounded-lg border border-slate-200 px-4 py-3 text-left transition hover:border-blue-300 hover:bg-blue-50"
                >
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                    <Icon icon="ri:task-line" width="16" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-slate-900">
                      {task.dag_task_name || '未命名任务'}
                    </div>
                    <div className="mt-0.5 truncate text-xs text-slate-500">
                      {task.description || '暂无描述'}
                    </div>
                    <div className="mt-1 text-[11px] text-slate-400">
                      创建时间：{formatDateTime(task.create_time)}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
        {total > pageSize && (
          <div className="flex items-center justify-between border-t border-slate-200 px-5 py-3">
            <span className="text-xs text-slate-400">
              共 {total} 个任务
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="rounded border border-slate-200 px-2 py-1 text-xs text-slate-600 transition hover:bg-slate-50 disabled:opacity-40"
              >
                上一页
              </button>
              <span className="text-xs text-slate-500">{page}</span>
              <button
                disabled={page * pageSize >= total}
                onClick={() => setPage((p) => p + 1)}
                className="rounded border border-slate-200 px-2 py-1 text-xs text-slate-600 transition hover:bg-slate-50 disabled:opacity-40"
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
