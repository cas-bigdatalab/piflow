import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { HomePage } from "./pages/HomePage";
import { SkillsPage } from "./pages/SkillsPage";
import { DialoguePage } from "./pages/DialoguePage";
import { RunHistoryPage } from "./pages/RunHistoryPage";
import { TaskManagePage } from "./pages/TaskManagePage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/skills" element={<SkillsPage />} />
        <Route path="/dialogue" element={<DialoguePage />} />
        <Route path="/run-history" element={<RunHistoryPage />} />
        <Route path="/editTask" element={<TaskManagePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
