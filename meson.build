project(
  'glfos-nix-samba',
  version: '1.0.0',
  meson_version: '>= 0.64.0',
  license: 'GPL-3.0-or-later',
)

python = import('python').find_installation('python3')

pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()

conf = configuration_data()
conf.set('PYTHON', python.full_path())
conf.set('pkgdatadir', pkgdatadir)
conf.set('VERSION', meson.project_version())

configure_file(
  input: 'bin' / 'glfos-nix-samba.in',
  output: 'glfos-nix-samba',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

subdir('data')
subdir('src')
