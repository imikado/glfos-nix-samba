# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Permissions

Claude is allowed to:
- Run shell commands without confirmation
- Write and edit files without confirmation

## Project Overview

GTK4/Libadwaita GUI application for managing Samba (CIFS) mount configurations on NixOS. It allows users to add/edit/delete remote share mount points, create credentials files, and rebuild the NixOS configuration.

## Commands

```bash
# Run the application
python src/main.py

# Using Nix development shell (recommended on NixOS)
nix develop
python src/main.py

# Using Docker
./buildDocker.sh    # Build once
./runWithDocker.sh  # Run

# Extract translation strings
xgettext -d base -o src/infrastructure/locales/nix-samba.pot src/main.py
```

## Architecture

Clean Architecture with three layers:

```
src/
├── main.py                    # Entry point (i18n setup via gettext)
├── domain/                    # Business logic
│   ├── entity/               # RemoteShare data model
│   ├── contract/             # Interface abstractions (dependency injection)
│   ├── repository/           # In-memory data management
│   ├── remote_domain.py      # Core logic for managing remotes
│   └── credentials_file_domain.py
└── infrastructure/
    ├── api/                  # System implementations
    │   ├── nix_file_api.py  # Parse/generate Nix expressions using `nix eval`
    │   ├── samba_file_api.py # Orchestrates Nix file operations
    │   └── system_api.py    # File I/O, sudo operations, NixOS rebuild
    └── ui/                   # GTK4/Adw pages
        ├── app_window.py    # Main window, navigation, config checks
        ├── remote_list_page.py
        ├── remote_add_page.py
        ├── remote_edit_page.py
        └── create_creds_file_page.py
```

## Key Patterns

- **Dependency Injection**: Domain classes receive infrastructure implementations via constructor (e.g., `RemoteDomain(system_api, samba_file_api)`)
- **Repository Pattern**: `RemoteShareRepository` manages in-memory list with lazy loading from disk
- **State Tracking**: `_need_to_save` flag prevents data loss; UI warns on close if unsaved
- **Gettext i18n**: `_()` function installed globally in main.py; translations in `infrastructure/locales/`

## Important Files

- **NixOS config read/written**: `/etc/nixos/customConfig/samba.nix`
- **Config validation checks**: `/etc/nixos/customConfig/default.nix` (for samba.nix import and cifs-utils)
- **Credentials files**: User-specified paths with `chmod 600`

## UI Conventions

- Uses `Adw.NavigationView` for in-window navigation (push/pop pages)
- `Adw.PreferencesPage/Group/Row` for settings-style forms
- `Adw.AlertDialog` for confirmations and errors
- `Adw.Toast` for notifications
- Signal handlers: `Gtk.Button` uses `'clicked'`, `Adw.ButtonRow` uses `'activated'`

## GTK4/Python Notes

- Import order matters: `gi.require_version()` must come before importing from `gi.repository`
- FileDialog in GTK4 doesn't support `show_hidden`; use GSettings `org.gtk.gtk4.Settings.FileChooser` instead
- The `_` variable in for loops conflicts with gettext `_()` function due to Python scoping; use named variables instead

## Validation Rules

- Mount path: must be absolute (`/...`)
- Remote address: must match `//host/share` pattern
- Timeouts: numeric with optional suffix (`s`, `m`, `h`)
