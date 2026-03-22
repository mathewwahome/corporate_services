# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a **Frappe/ERPNext customization app** (`corporate_services`) for IntelliSOFT Consulting's HR and corporate management workflows. It extends ERPNext with custom doctypes, Python APIs, and React-based admin pages.

## Build Commands

### Survey Manager Admin UI (desk page)
```bash
cd corporate_services/icl_corporate_services/page/survey_manager
npm run dev    # watch mode (Vite)
npm run build  # production build → outputs to ../../public/js/survey_admin.js
```

### Public Survey Form (website page)
```bash
cd corporate_services/public/ts
npm run dev    # watch mode
npm run build  # production build → outputs to ../js/survey_public.js
```

Both Vite configs output **IIFE bundles** to `corporate_services/public/js/`. The compiled JS must be committed alongside TSX source changes.

## Architecture

### Backend (Frappe/Python)
- **`corporate_services/api/`** — Whitelisted Python methods callable from the frontend via `frappe.call()`. Organized by domain: `survey.py`, `timesheet/`, `notification/`, `candidates/`, etc.
- **`corporate_services/icl_corporate_services/doctype/`** — Custom ERPNext DocType definitions (JSON + Python controllers). ~106 doctypes.
- **`corporate_services/icl_corporate_services/custom/`** — Property setter overrides for standard ERPNext fields.
- **`hooks.py`** — Central Frappe configuration: registers page JS bundles, doc event handlers, scheduled tasks, and fixtures.

### Frontend (React/TypeScript)
- **`page/survey_manager/components/`** — Admin UI for survey CRUD and analytics. Entry point: `components/index.tsx`. State managed via `hooks/useSurveys.ts`.
- **`public/ts/survey_public.tsx`** — Public-facing survey submission form (loaded on all website pages via `web_include_js` in hooks.py).
- **`public/ts/survey_admin.tsx`** — Legacy/simpler survey admin (kept alongside the new survey_manager app).

### How Frappe Loads Frontend Code
1. Compiled JS bundles land in `corporate_services/public/js/`
2. `hooks.py` maps page slugs to bundles via `page_js` (for desk pages) or `web_include_js` (for public site)
3. Bundles expose a global init function (e.g. `window.initSurveyManager()`) that mounts the React app into a Frappe page container

### Frontend ↔ Backend Communication
Frontend calls Python via `window.frappe.call({ method: "corporate_services.api.survey.get_surveys", ... })`. All callable methods must be decorated with `@frappe.whitelist()`. Guest-accessible methods use `@frappe.whitelist(allow_guest=True)`.

### Doc Events
Document lifecycle hooks (on_update, after_insert, validate, before_delete, etc.) are registered in `hooks.py` via the `doc_events` dict built from `generate_doc_events()`. Add new handlers there.

### Fixtures
`hooks.py` declares which DocTypes are exported as fixtures (JSON files in `corporate_services/fixtures/`). Run `bench export-fixtures` inside the Frappe bench to regenerate them after changing Workflows, Roles, Email Templates, etc.

## Key Conventions

- **API module path** follows `corporate_services.api.<domain>.<module>.<function>` — match the file system path exactly.
- **New React pages** follow the pattern in `page/survey_manager/`: a `vite.config.js` that outputs an IIFE to `public/js/`, registered in `hooks.py` under `page_js`.
- TypeScript source lives in `page/<name>/components/` or `public/ts/`; compiled output lives in `public/js/` — both are committed.
- Frappe CSS variables (e.g. `var(--primary)`) are used for theming in the React apps; see `ui/GlobalStyles.tsx`.


Dont add any new features unless explicitly told so