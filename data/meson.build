# Desktop file
install_data(
  'glfos-nix-samba.desktop',
  install_dir: get_option('datadir') / 'applications',
)

# Icons
icon_sizes = ['16x16', '32x32', '48x48', '64x64', '128x128', '256x256']

foreach size : icon_sizes
  install_data(
    'icons/nix-samba-' + size + '.png',
    install_dir: get_option('datadir') / 'icons' / 'hicolor' / size / 'apps',
    rename: 'nix-samba.png',
  )
endforeach

install_data(
  'icons/nix-samba.webp',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'scalable' / 'apps',
  rename: 'nix-samba.webp',
)
