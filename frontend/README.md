# Broadlink Manager v2 - Frontend

Vue 3 frontend for Broadlink Manager.

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **Vite** - Next generation frontend tooling
- **Pinia** - State management
- **Axios** - HTTP client

## Development

### Prerequisites

- Node.js 18+ and npm

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

Opens at http://localhost:5173 with hot-reload.

API calls are proxied to Flask backend at http://localhost:8099.

### Build for Production

```bash
npm run build
```

Builds to `../app/static/` directory.

## Project Structure

```
src/
├── assets/
│   └── styles/
│       └── main.css          # Global styles
├── components/               # Reusable components
├── services/
│   └── api.js               # Axios API client
├── stores/
│   └── app.js               # Pinia stores
├── views/
│   └── Dashboard.vue        # Page components
├── App.vue                  # Root component
└── main.js                  # Entry point
```

## Development Workflow

1. **Run Flask backend** (Terminal 1):
   ```bash
   cd ../app
   python main.py
   ```

2. **Run Vue dev server** (Terminal 2):
   ```bash
   npm run dev
   ```

3. **Make changes** - Hot reload updates automatically

4. **Build for production** when ready:
   ```bash
   npm run build
   ```

## Environment Variables

Create `.env` file for custom configuration:

```
VITE_API_BASE_URL=http://localhost:8099
```

## Home Assistant Theme

The UI uses Home Assistant's design system:
- Material Design Icons (MDI)
- HA color variables
- Dark mode support
- Consistent spacing and typography
