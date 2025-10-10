# SETUP_GUIDE.md Needs Update

This file still references the old master setup.py approach and needs a comprehensive rewrite.

## Issues Found:

1. References to root `python3 setup.py` (no longer exists)
2. References to `--setup frontend`, `--setup backend`, `--setup both` flags (no longer exist)
3. References to `start_frontend.py` and `start_backend.py` (no longer exist)
4. Old SSH tunnel commands using `-R 8888:localhost:8888` instead of `-R 8888:0.0.0.0:8888`

## Should Be Replaced With:

**Setup:**
- `cd backend && python3 setup.py` (for backend)
- `cd frontend && python3 setup.py` (for frontend)

**Start:**
- `cd backend && docker compose up -d` (for backend)
- `cd frontend && docker compose up -d` (for frontend & image server)

**SSH Tunnel:**
- `ssh -L 8000:localhost:8000 -R 8888:0.0.0.0:8888 user@server`

## Recommendation:

This file is comprehensive but outdated. Consider:
1. Using QUICK_START.md for quick setup
2. Using REMOTE_BACKEND_SETUP.md for remote setup
3. Using WORKING_CONFIG.md for configuration reference
4. Rewriting SETUP_GUIDE.md from scratch based on the new simplified approach

Or simply deprecate/archive this file and point users to the newer, simpler guides.
