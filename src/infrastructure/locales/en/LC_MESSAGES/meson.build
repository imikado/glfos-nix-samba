custom_target(
  'mo-en',
  input: 'nix-samba.po',
  output: 'nix-samba.mo',
  command: ['msgfmt', '-o', '@OUTPUT@', '@INPUT@'],
  install: true,
  install_dir: pkgdatadir / 'infrastructure' / 'locales' / 'en' / 'LC_MESSAGES',
  build_by_default: true,
)
