{
  description = "IMAP activation development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true; # Simplified from allowUnfreePredicate
      };

      python = pkgs.python313;

      pythonOverridden = python.override {
        packageOverrides = self: super: {
          # pyairtable is the only custom override needed now
          pyairtable = super.buildPythonPackage rec {
            pname = "pyairtable";
            version = "3.1.1";
            format = "setuptools";
            src = super.fetchPypi {
              inherit pname version;
              sha256 = "sha256-sYX+8SEZ8kng5wSrTksVopCA/Ikq1NVRoQU6G7YJ7y4=";
            };
            propagatedBuildInputs = with super; [requests inflection pydantic];
            doCheck = false;
          };
        };
      };

      # 🐍 Minimal list of required Python packages
      nixpkgspythondepnames = [
        "playwright"
        "pytest-playwright" # Good for testing playwright scripts
        "python-dotenv"
        "requests"
        "inflection"
        "pydantic"
        "packaging"
        "pip"
        "setuptools"
      ];

      pythonEnv = pythonOverridden.withPackages (
        ps:
          (map (name: ps.${name}) nixpkgspythondepnames)
          ++ [ps.pyairtable] # Add the custom pyairtable package
      );
    in {
      devShells.default = pkgs.mkShell {
        packages = [
          pythonEnv
          pkgs.playwright-driver.browsers # Still needed for Playwright

          # 👇 System dependencies required by Playwright
          pkgs.glib
          pkgs.nss
          pkgs.nspr
          pkgs.dbus
          pkgs.atk
          pkgs.at-spi2-core
          pkgs.cups
          pkgs.gtk3
          pkgs.xorg.libX11
          pkgs.xorg.libXcomposite
          pkgs.xorg.libXdamage
          pkgs.xorg.libXext
          pkgs.xorg.libXfixes
          pkgs.xorg.libXrandr
          pkgs.libxkbcommon
          pkgs.pango
          pkgs.cairo
          pkgs.udev
          pkgs.alsa-lib
        ];

        shellHook = ''
          echo "---------------------------------------------------------------------"
          echo "✅ nix dev shell for IMAP Activator is ready."
          echo "   Python environment (3.13) is active with Playwright & Airtable deps."
          echo "   python: $(which python) ($($(which python) --version 2>&1))"
          echo ""

          # Path for Playwright's browsers
          export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
          export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true

          echo "---------------------------------------------------------------------"
        '';
      };
    });
}
