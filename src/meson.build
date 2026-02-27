# Install all Python sources to pkgdatadir (preserving directory structure)
# .mo files are excluded here and installed separately below to avoid conflicts
install_subdir(
  '.',
  install_dir: pkgdatadir,
  exclude_directories: ['__pycache__'],
  exclude_files: [
    'infrastructure/locales/en/LC_MESSAGES/nix-samba.mo',
    'infrastructure/locales/fr/LC_MESSAGES/nix-samba.mo',
  ],
)

# Compile .po → .mo at build time (each in its own subdir to avoid naming conflicts)
subdir('infrastructure/locales/en/LC_MESSAGES')
subdir('infrastructure/locales/fr/LC_MESSAGES')
