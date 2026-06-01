import { Navigate, Route, Routes, useSearchParams } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { HomePage } from "./pages/HomePage";
import { SkillsPage } from "./pages/SkillsPage";
import { RunHistoryPage } from "./pages/RunHistoryPage";
import { TaskManagePage } from "./pages/TaskManagePage";
import { TaskDrawPage } from "./pages/TaskDrawPage";

function TaskDrawPageWrapper() {
  const [searchParams] = useSearchParams();
  return (
    <TaskDrawPage
      taskId={searchParams.get('taskId') || ''}
      taskName={searchParams.get('taskName') || ''}
      isEdit={searchParams.get('isEdit') === 'true'}
    />
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/skills" element={<SkillsPage />} />
        <Route path="/run-history" element={<RunHistoryPage />} />
        <Route path="/editTask" element={<TaskManagePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
      <Route path="/task-draw" element={<TaskDrawPageWrapper />} />
    </Routes>
  );
}
