# Frontend Architecture (`/extension`)

Sasayaku's frontend is a Chrome Extension that serves as the user interface for managing whisper-based subtitle generation and sending them to `asbplayer`.

## Tech Stack
- React + Typescript, Vite, Material UI (MUI)
- Chrome extension

## Key Files
- `extension/src/App.tsx`: Main application root
- `extension/src/Dashboard.tsx`: Primary videos & subtitles management view
- `extension/src/Settings.tsx`: Extension configuration & preferences view
- `extension/src/Menu.tsx`: Navigation menu
- `extension/src/services/api.ts`: API communication layer with backend server
- `extension/src/types.ts`: TypeScript interfaces for API responses and internal state
- `extension/manifest.json`: Chrome extension configuration and permissions

## Rules & Constraints
- **API Isolation**: All backend requests should go through the `services/api.ts`, never use raw `fetch()` directly inside UI components.
- **Types**: Import and reuse types from `src/types.ts` for all backend request/response payloads and component state.
- **Styling**: Use standard MUI component props and sx styling. Avoid loose CSS strings or inline styles
- **Permissions**: If adding Chrome API calls (`chrome.storage`, `chrome.tabs`, etc.), verify required permissions in `manifest.json`.
