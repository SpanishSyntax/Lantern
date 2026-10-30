{
  description = "Lantern - Frost's Interactive Explainer and Simulation Dashboard Compiler";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    prism = {
      url = "github:SpanishSyntax/Prism";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    barograph = {
      url = "github:SpanishSyntax/Barograph";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.prism.follows = "prism";
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    prism,
    barograph,
  }: let
    systems = flake-utils.lib.defaultSystems;
  in
    flake-utils.lib.eachSystem systems (system: let
      pkgs = import nixpkgs {
        inherit system;
        overlays = [prism.overlays.default];
      };
      lib = pkgs.lib;

      barographPkg = barograph.packages.${system}.default;

      lanternPackage = pkgs.python3Packages.buildPythonApplication {
        pname = "lantern";
        version = "0.1.0";
        src = lib.cleanSource ./.;
        pyproject = true;

        build-system = [
          pkgs.python3Packages.setuptools
        ];

        propagatedBuildInputs = [
          pkgs.python3Packages.jinja2
          pkgs.python3Packages.markdown
          pkgs.python3Packages.watchdog
          pkgs.python3Packages.rich
          pkgs.python3Packages.prism
          pkgs.python3Packages.pyyaml
          barographPkg
        ];

        nativeCheckInputs = [
          pkgs.python3Packages.pytest
        ];

        doCheck = false;

        meta = with lib; {
          description = "Frost's Interactive Explainer and Simulation Dashboard Compiler";
          homepage = "https://github.com/SpanishSyntax/Lantern";
          license = licenses.mit;
          mainProgram = "lantern";
        };
      };
    in {
      packages = {
        default = lanternPackage;
        lantern = lanternPackage;
      };

      apps = {
        default = {
          type = "app";
          program = "${lanternPackage}/bin/lantern";
          meta.description = "Frost's Interactive Explainer and Simulation Dashboard Compiler";
        };
        lantern = {
          type = "app";
          program = "${lanternPackage}/bin/lantern";
          meta.description = "Frost's Interactive Explainer and Simulation Dashboard Compiler";
        };
      };

      devShells.default = pkgs.mkShell {
        packages = with pkgs; [
          (python3.withPackages (ps: with ps; [
            setuptools
            pytest
            jinja2
            markdown
            watchdog
            rich
            prism
            pyyaml
            numpy
            matplotlib
            plotly
          ]))
          barographPkg
          direnv
        ];
      };
    })
    // {
      overlays = {
        default = final: prev: {
          lantern = self.packages.${prev.stdenv.hostPlatform.system}.default;
        };
        lantern = self.overlays.default;
      };

      nixosModules = {
        default = self.nixosModules.lantern;
        lantern = {
          config,
          lib,
          pkgs,
          ...
        }: let
          cfg = config.programs.lantern;
          system = pkgs.stdenv.hostPlatform.system;
          defaultLantern = self.packages.${system}.default;
        in {
          options.programs.lantern = {
            enable = lib.mkEnableOption "Lantern - Interactive explainer and simulation dashboard compiler";

            package = lib.mkOption {
              type = lib.types.package;
              default = defaultLantern;
              description = "The Lantern package to use.";
            };
          };

          config = lib.mkIf cfg.enable {
            environment.systemPackages = [cfg.package];
          };
        };
      };

      homeManagerModules = {
        default = self.homeManagerModules.lantern;
        lantern = {
          config,
          lib,
          pkgs,
          ...
        }: let
          cfg = config.programs.lantern;
          tomlFormat = pkgs.formats.toml {};
          system = pkgs.stdenv.hostPlatform.system;
          defaultLantern = self.packages.${system}.default;
        in {
          options.programs.lantern = {
            enable = lib.mkEnableOption "Lantern - Interactive explainer and simulation dashboard compiler";

            package = lib.mkOption {
              type = lib.types.package;
              default = defaultLantern;
              description = "The Lantern package to use.";
            };

            settings = lib.mkOption {
              type = tomlFormat.type;
              default = {};
              description = "Configuration written to ~/.config/lantern/lantern.toml.";
            };
          };

          config = lib.mkIf cfg.enable {
            home.packages = [cfg.package];

            xdg.configFile."lantern/lantern.toml" = lib.mkIf (cfg.settings != {}) {
              source = tomlFormat.generate "lantern.toml" cfg.settings;
            };
          };
        };
      };
    };
}
