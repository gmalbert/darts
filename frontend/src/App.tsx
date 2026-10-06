import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Shell } from "./components/layout/Shell";
import { useTheme } from "./theme/ThemeProvider";
import HomePage from "./pages/HomePage";
import PlayersPage from "./pages/PlayersPage";
import MatchesPage from "./pages/MatchesPage";
import TournamentsPage from "./pages/TournamentsPage";
import OddsPage from "./pages/OddsPage";
import ToolsPage from "./pages/ToolsPage";

export default function App() {
  useTheme();
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Shell />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/players" element={<PlayersPage />} />
          <Route path="/matches" element={<MatchesPage />} />
          <Route path="/tournaments" element={<TournamentsPage />} />
          <Route path="/odds" element={<OddsPage />} />
          <Route path="/tools" element={<ToolsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
