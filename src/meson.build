# Install all Python sources to pkgdatadir (preserving directory structure)
# .mo files are excluded here — they are compiled fresh by the targets below
install_subdir(
  '.',
  install_dir: pkgdatadir,
  exclude_files: [
    'infrastructure/locales/en/LC_MESSAGES/nix-samba.mo',
    'infrastructure/locales/fr/LC_MESSAGES/nix-samba.mo',
  ],
  exclude_directories: ['__pycache__'],
)

# Compile .po → .mo at build time and install alongside the Python sources
foreach lang : ['en', 'fr']
  custom_target(
    'mo-' + lang,
    input: files('infrastructure/locales' / lang / 'LC_MESSAGES' / 'nix-samba.po'),
    output: lang + '-nix-samba.mo',
    command: ['msgfmt', '-o', '@OUTPUT@', '@INPUT@'],
    install: true,
    install_dir: pkgdatadir / 'infrastructure' / 'locales' / lang / 'LC_MESSAGES',
    install_rename: 'nix-samba.mo',
    build_by_default: true,
  )
endforeach
