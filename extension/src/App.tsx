import { Box } from "@mui/material";
import { useState } from "react";
import { Menu } from "./Menu";
import { Dashboard } from "./Dashboard";
import { Settings } from "./Settings";

export default function App() {
  const [currentView, setCurrentView] = useState<"dashboard" | "send" | "settings">("dashboard");

  const handleNavigate = (view: "dashboard" | "send" | "settings") => {
    setCurrentView(view);
  };

  return (
    <Box sx={{ width: "100%" }}>
			<Menu onNavigate={handleNavigate} currentView={currentView} />
			{currentView === "dashboard" && <Dashboard />}
			{currentView === "settings" && <Settings />}
    </Box>
  );
}
