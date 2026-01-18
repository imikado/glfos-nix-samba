{
  description = "Python GTK4/Libadwaita development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        pythonPackages = python.pkgs;
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            pythonPackages.pygobject3

            pkgs.gtk4
            pkgs.libadwaita
            pkgs.gobject-introspection
          ];

          shellHook = ''
            echo "Python GTK4/Libadwaita development environment"
            echo "Python version: $(python --version)"
          '';
        };
      }
    );
}
