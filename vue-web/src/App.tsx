import { Navigate, Route, Routes, useSearchParams } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { HomePage } from "./pages/HomePage";
import { SkillsPage } from "./pages/SkillsPage";
import { WorkLibPage } from "./pages/WorkLibPage";
import { RunHistoryPage } from "./pages/RunHistoryPage";
import { TaskManagePage } from "./pages/TaskManagePage";
import { TaskDrawPage } from "./pages/TaskDrawPage";
import RunDetails from "./components/RunDetails";

import SkillsDetailsPage from "./pages/SkillsDetailsPage"; // 注意：默认导出，不用大括号
import SkillsCreatePage from "./pages/SkillsCreatePage";
import SkillsGeneratorPage from "./pages/SkillsGeneratorPage";
import DataManPage from "./pages/DataManPage";
import DataManConnectionsPage from "./pages/DataManConnectionsPage"; // 确保文件名完全匹配

function TaskDrawPageWrapper() {
  const [searchParams] = useSearchParams();
  const descriptionParam = searchParams.get('description');
  return (
    <TaskDrawPage
      taskId={searchParams.get('taskId') || ''}
      taskName={searchParams.get('taskName') || ''}
      description={descriptionParam === 'null' ? '' : descriptionParam || ''}
      isEdit={searchParams.get('isEdit') === 'true'}
    />
  );
}
function SkillsDetailsPageWrapper() {
  const [searchParams] = useSearchParams();
  const id = searchParams.get('id');
  const name = searchParams.get('name');
  return (
    <SkillsDetailsPage
      id={searchParams.get('id') || ''}
      name={searchParams.get('name') || ''}
    />
  );
}

function RunDetailsWrapper() {
  const [searchParams] = useSearchParams();
  const processId = searchParams.get('processId') || '';
  return <RunDetails processId={processId} />;
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/skills" element={<SkillsPage />} />
        <Route path="/workLib" element={<WorkLibPage />} />
        {/* 新增算子详情页面和添加算子 */}
        <Route path="/skill/detail" element={<SkillsDetailsPageWrapper />} />
        <Route path="/skill/create" element={<SkillsCreatePage />} />
        {/* 算子生成器 */}
        <Route path="/skill/generator" element={<SkillsGeneratorPage />} />
        {/* 新增数据管理页面 */}
        <Route path="/dataMan" element={<DataManPage />} />
        <Route path="/dataMan-connections" element={<DataManConnectionsPage />} />
        <Route path="/run-history" element={<RunHistoryPage />} />
        <Route path="/run-details" element={<RunDetailsWrapper />} />
        <Route path="/editTask" element={<TaskManagePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
      <Route path="/task-draw" element={<TaskDrawPageWrapper />} />
    </Routes>
  );
}
