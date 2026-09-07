import {
  AppBar,
  Box,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import DashboardIcon from "@mui/icons-material/Dashboard";
import SendIcon from "@mui/icons-material/Send";
import SettingsIcon from "@mui/icons-material/Settings";
import { useState } from "react";

interface MenuProps {
  onNavigate: (view: "dashboard" | "send" | "settings") => void;
  currentView: string;
}

export function Menu({ onNavigate, currentView }: MenuProps) {
  const [open, setOpen] = useState(false);

  const toggleDrawer = () => setOpen((prev) => !prev);

  const handleNav = (view: "dashboard" | "send" | "settings") => {
    onNavigate(view);
    setOpen(false);
  };

  const menuItems = [
    { id: "dashboard" as const, label: "Dashboard", icon: <DashboardIcon /> },
    //{ id: "send" as const, label: "Send Video", icon: <SendIcon /> },
    { id: "settings" as const, label: "Settings", icon: <SettingsIcon /> },
  ];

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={toggleDrawer}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Sasayaku
          </Typography>
        </Toolbar>
      </AppBar>

      <Drawer anchor="left" open={open} onClose={toggleDrawer}>
        <Box sx={{ width: 250 }} role="presentation">
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.id} disablePadding>
                <ListItemButton
                  selected={currentView === item.id}
                  onClick={() => handleNav(item.id)}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
    </>
  );
}
