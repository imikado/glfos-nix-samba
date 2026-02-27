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

# Install pre-compiled .mo translation files
foreach lang : ['en', 'fr']
  install_data(
    'infrastructure/locales' / lang / 'LC_MESSAGES' / 'nix-samba.mo',
    install_dir: pkgdatadir / 'infrastructure' / 'locales' / lang / 'LC_MESSAGES',
  )
endforeach
