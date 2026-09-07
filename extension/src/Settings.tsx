import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Stack,
  Alert,
  Tooltip,
} from "@mui/material";
import SyncIcon from "@mui/icons-material/Sync";
import RotateLeft from "@mui/icons-material/RotateLeft";
import { useState } from "react";
import { ping } from "./services/api";

export function Settings() {
  const [serverUrl, setServerUrl] = useState("http://localhost:8000");
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<boolean | null>(null);

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);

    const success = await ping(serverUrl);

    setTestResult(success);
    setIsTesting(false);
  };

  // Determine the MUI color prop based on the test result
  const buttonColor = testResult === true ? "success" : testResult === false ? "error" : "primary";

  return (
    <Box sx={{ p: 1, width: 400 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Settings
      </Typography>

      <Card>
        <CardContent>
          <Stack spacing={2}>
            <Stack direction="row" spacing={1} alignItems="center">
              <TextField
                label="Server URL"
                placeholder="http://localhost:8000"
                size="small"
                sx={{ flex: 1 }}
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
              />
              <Tooltip title="Test Connection">
                <Button
                  variant="contained"
                  color={buttonColor}
                  startIcon={isTesting ? <RotateLeft /> : <SyncIcon />}
                  size="small"
                  disabled={isTesting}
                  onClick={handleTestConnection}
                  sx={{
                    minWidth: 'auto',
                    px: 1,
                    "&:disabled": {
                      opacity: 0.7,
                    }
                  }}
                />
              </Tooltip>
            </Stack>
            {testResult !== null && (
              <Alert
                severity={testResult ? "success" : "error"}
                variant="outlined"
              >
                {testResult ? "Connection successful!" : "Connection failed."}
              </Alert>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
