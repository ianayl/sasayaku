{
  description = "Sasayaku -- Youtube Whisper subtitles for asbplayer";

  inputs = {
    #nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    nixpkgs.url = "github:nixos/nixpkgs/26.05";
  };

  nixConfig = {
    extra-substituters = [
      "https://cuda-maintainers.cachix.org"
      "https://nix-community.cachix.org"
      "https://cache.nixos-cuda.org"
    ];
    extra-trusted-public-keys = [
      "cuda-maintainers.cachix.org-1:0dq3bujKpuEPMCX6U4WylrUDZ9JyUG0VpVZa7CNfq5E="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
      "cache.nixos-cuda.org:74DUi4Ye579gUqzH4ziL9IyiJBlDpMRn9MBN8oNan9M="
    ];
  };

  outputs = { self, nixpkgs }: {
    devShells.x86_64-linux.default = let
      # Packages from pkgs should be fetched from e.g. cachix:
      pkgs = import nixpkgs {
        system = "x86_64-linux";
        config.allowUnfree = true;
      };

      # Packages from pkgsCuda are rebuilt since cudaSupport forces rebuilds:
      pkgsCuda = import nixpkgs {
        system = "x86_64-linux";
        config = {
          allowUnfree = true;
          cudaSupport = true;
        };
      };

      python = pkgs.python3.withPackages (ps: [
        ps.flask
        ps.flask-cors
        ps.srt
        # CTranslate2 needs to be compiled locally with cuda support
        pkgsCuda.python3Packages.ctranslate2
        pkgsCuda.python3Packages.faster-whisper
        pkgsCuda.python3Packages.whisperx
        pkgsCuda.python3Packages.torch
        #ps.whisperx
      ]);

    in pkgs.mkShell {
      buildInputs = [
        pkgs.ffmpeg
        pkgs.cudaPackages.cuda_nvcc
        pkgs.cudaPackages.cudnn
        python
      ];

      shellHook = ''
        export LD_LIBRARY_PATH="/run/opengl-driver/lib:${pkgs.cudaPackages.cudnn}/lib:${pkgs.cudaPackages.cuda_cudart}/lib:$LD_LIBRARY_PATH"
        export CUDA_PATH="${pkgs.cudaPackages.cuda_nvcc}"

        nvcc --version
        echo ""
      '';
    };
  };
}
