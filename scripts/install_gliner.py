#!/usr/bin/env python3
"""
install_gliner.py — Automate GLiNER installation in this environment.

Per CEO directive cycle 121: 'find a way to automate it in environment.'

This script:
  1. Installs GLiNER from GitHub source (no PyPI package)
  2. Installs all dependencies (torch CPU, transformers, sentencepiece, onnxruntime)
  3. Downloads the pretrained model (urchade/gliner_small)
  4. Verifies the installation works
  5. Is idempotent — safe to run multiple times

Usage:
  python3 scripts/install_gliner.py
"""
import subprocess
import sys


def run_pip_install(package, extra_args=None):
    """Install a package via pip, return success."""
    cmd = [sys.executable, "-m", "pip", "install"]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(package)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    return result.returncode == 0


def check_import(module_name):
    """Check if a module is importable."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def install_gliner():
    """Automate GLiNER installation."""
    print("=== GLiNER Installation Automation ===")
    
    # Step 1: Check/install torch (CPU version)
    if not check_import("torch"):
        print("1. Installing PyTorch (CPU)...")
        run_pip_install("torch", ["--index-url", "https://download.pytorch.org/whl/cpu"])
    else:
        print("1. PyTorch already installed.")
    
    # Step 2: Install transformers (compatible version)
    if not check_import("transformers"):
        print("2. Installing transformers...")
        run_pip_install("transformers>=4.51.3,<5.14.0")
    else:
        print("2. transformers already installed.")
    
    # Step 3: Install sentencepiece
    if not check_import("sentencepiece"):
        print("3. Installing sentencepiece...")
        run_pip_install("sentencepiece")
    else:
        print("3. sentencepiece already installed.")
    
    # Step 4: Install onnxruntime
    if not check_import("onnxruntime"):
        print("4. Installing onnxruntime...")
        run_pip_install("onnxruntime")
    else:
        print("4. onnxruntime already installed.")
    
    # Step 5: Install GLiNER from GitHub
    if not check_import("gliner"):
        print("5. Installing GLiNER from GitHub...")
        import pathlib
        gliner_dir = pathlib.Path("/tmp/GLiNER")
        if not gliner_dir.exists():
            subprocess.run(
                ["git", "clone", "--depth", "1", 
                 "https://github.com/urchade/GLiNER.git", str(gliner_dir)],
                capture_output=True, text=True, timeout=60
            )
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-deps", "-e", str(gliner_dir)],
            capture_output=True, text=True, timeout=60
        )
    else:
        print("5. GLiNER already installed.")
    
    # Step 6: Verify
    print("6. Verifying installation...")
    try:
        from gliner import GLiNER
        model = GLiNER.from_pretrained("urchade/gliner_small")
        entities = model.predict_entities(
            "Electrospinning produces nanofiber membranes.",
            ["material", "mechanism"], threshold=0.5
        )
        print(f"   GLiNER works! Extracted {len(entities)} entities.")
        for e in entities:
            print(f"     {e['label']:12s} {e['text']}")
        return True
    except Exception as e:
        print(f"   GLiNER verification failed: {e}")
        return False


if __name__ == "__main__":
    success = install_gliner()
    if success:
        print("\n✅ GLiNER is ready for use.")
        print("   Import: from gliner import GLiNER")
        print("   Model: GLiNER.from_pretrained('urchade/gliner_small')")
    else:
        print("\n❌ GLiNER installation failed.")
        sys.exit(1)
