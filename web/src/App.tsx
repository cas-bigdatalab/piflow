import { Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import SkillsPage from "./pages/SkillsPage";
import Home from "./pages/Home";
import { GlobalContext } from "./context";
function App() {
  return (
    <GlobalContext.Provider
      value={{
        userId: "default_user",
      }}>
      <Routes>
        <Route
          path="/"
          element={
            <div className="h-screen flex flex-col overflow-hidden">
              <Header />
              <Home />
            </div>
          }
        />
        <Route
          path="/skills"
          element={
            <div className="min-h-screen flex flex-col">
              <Header />
              <SkillsPage />
            </div>
          }
        />
      </Routes>
    </GlobalContext.Provider>
  );
}

export default App;
