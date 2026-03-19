"""
Setup Checker - Check system environment readiness
"""
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("ERROR: Python 3.10 or higher required")
        return False
    else:
        print("Python version OK")
        return True

def check_packages():
    """Check required Python packages"""
    required_packages = [
        "customtkinter",
        "numpy",
        "onnxruntime",
        "pyaudio",
        "librosa",
        "soundfile",
        "transformers",
        "requests",
        "tqdm"
    ]
    
    # Optional packages (don't fail if missing)
    optional_packages = [
        "openvino",
        "openvino-dev",
        "silero-vad"
    ]
    
    missing = []
    installed = []
    optional_missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            installed.append(package)
        except ImportError:
            missing.append(package)
    
    for package in optional_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            optional_missing.append(package)
    
    print(f"\nInstalled packages ({len(installed)}/{len(required_packages)}):")
    for pkg in installed:
        print(f"  [OK] {pkg}")
    
    if missing:
        print(f"\nMissing required packages:")
        for pkg in missing:
            print(f"  [MISSING] {pkg}")
        print(f"\nInstall with: pip install -r requirements.txt")
        return False
    else:
        print("\nAll required packages installed")
        
        if optional_missing:
            print(f"\nOptional packages not installed (can run without):")
            for pkg in optional_missing:
                print(f"  [OPTIONAL] {pkg}")
        
        return True

def check_models():
    """Check model files"""
    print("\nChecking model files:")
    
    model_paths = {
        "ASR Model (0.6B)": "ov_models/qwen3_asr_int8",
        "VAD Model": "ov_models/silero_vad.onnx",
    }
    
    all_exist = True
    for name, path in model_paths.items():
        if Path(path).exists():
            print(f"  [OK] {name}")
        else:
            print(f"  [MISSING] {name} - needs download")
            all_exist = False
    
    if not all_exist:
        print(f"\nDownload models with: python downloader.py")
    
    return all_exist

def check_audio_device():
    """Check audio devices"""
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        input_devices = []
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    input_devices.append(info['name'])
            except:
                pass
        
        p.terminate()
        
        if input_devices:
            print(f"\nFound {len(input_devices)} audio input device(s)")
            return True
        else:
            print(f"\nNo audio input devices found")
            return False
            
    except Exception as e:
        print(f"\nCannot check audio devices: {e}")
        return False

def main():
    """Main checker"""
    print("=" * 60)
    print("QwenASR Translate - System Check")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version()),
        ("Python Packages", check_packages()),
        ("Model Files", check_models()),
        ("Audio Devices", check_audio_device()),
    ]
    
    print("\n" + "=" * 60)
    print("Summary:")
    
    all_passed = True
    for name, passed in checks:
        status = "[OK]" if passed else "[ISSUE]"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\nSystem ready! Run: python app.py")
        return 0
    else:
        print("\nSome items need attention. See above for details.")
        print("\nQuick install steps:")
        print("  1. python -m venv .venv")
        print("  2. .venv\\Scripts\\activate")
        print("  3. pip install -r requirements.txt")
        print("  4. python downloader.py")
        print("  5. python app.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
