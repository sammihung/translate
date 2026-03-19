"""
模型下載器
自動從 HuggingFace 下載所需模型
"""

import requests
from pathlib import Path
from tqdm import tqdm
import hashlib
import json


MODELS = {
    "qwen3_asr_0.6b_int8": {
        "name": "Qwen3-ASR-0.6B INT8",
        "repo": "dseditor/Qwen3-ASR-0.6B-INT8_ASYM-OpenVINO",
        "files": [
            "openvino_model.xml",
            "openvino_model.bin",
        ],
        "output_dir": "ov_models/qwen3_asr_int8",
        "size_gb": 1.2,
    },
    "qwen3_asr_1.7b_int8": {
        "name": "Qwen3-ASR-1.7B INT8",
        "repo": "dseditor/Qwen3-ASR-1.7B-INT8_OpenVINO",
        "files": [
            "openvino_model.xml",
            "openvino_model.bin",
        ],
        "output_dir": "ov_models/qwen3_asr_1p7b_int8",
        "size_gb": 4.3,
    },
    "silero_vad": {
        "name": "Silero VAD",
        "url": "https://github.com/snakers4/silero-vad/raw/master/files/silero_vad.onnx",
        "output_dir": "ov_models",
        "filename": "silero_vad.onnx",
        "size_mb": 2,
    },
    "diarization": {
        "name": "說話者分離模型",
        "repo": "altunenes/speaker-diarization-community-1-onnx",
        "files": [
            "segmentation-community-1.onnx",
            "embedding_model.onnx",
        ],
        "output_dir": "ov_models/diarization",
        "size_mb": 32,
    },
}


def download_file(url, dest_path, expected_size=None):
    """下載檔案並顯示進度"""
    
    if Path(dest_path).exists():
        print(f"✅ 已存在：{dest_path}")
        return
    
    # 建立目錄
    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"下載：{url}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest_path, 'wb') as f, tqdm(
            desc=Path(dest_path).name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))
        
        print(f"✅ 下載完成：{dest_path}")
        
    except Exception as e:
        print(f"❌ 下載失敗：{e}")
        if Path(dest_path).exists():
            Path(dest_path).unlink()


def download_from_huggingface(repo_id, filename, output_path):
    """從 HuggingFace 下載模型檔案"""
    
    base_url = f"https://huggingface.co/{repo_id}/resolve/main"
    url = f"{base_url}/{filename}"
    
    download_file(url, output_path)


def check_model_integrity(model_name):
    """檢查模型完整性"""
    
    model_info = MODELS.get(model_name)
    if not model_info:
        return False
    
    output_dir = Path(model_info["output_dir"])
    
    if not output_dir.exists():
        return False
    
    if "files" in model_info:
        # 檢查所有檔案
        for filename in model_info["files"]:
            filepath = output_dir / filename
            if not filepath.exists():
                return False
    elif "filename" in model_info:
        # 單一檔案
        filepath = output_dir / model_info["filename"]
        if not filepath.exists():
            return False
    
    return True


def download_model(model_name):
    """下載指定模型"""
    
    model_info = MODELS.get(model_name)
    if not model_info:
        print(f"❌ 未知的模型：{model_name}")
        return False
    
    print(f"\n{'='*60}")
    print(f"下載：{model_info['name']}")
    print(f"大小：{model_info.get('size_gb', model_info.get('size_mb', '未知'))}")
    print(f"{'='*60}")
    
    output_dir = Path(model_info["output_dir"])
    
    # 檢查是否已存在
    if check_model_integrity(model_name):
        print(f"✅ 模型已存在且完整：{output_dir}")
        return True
    
    # 下載檔案
    if "url" in model_info:
        # 直接 URL
        output_path = output_dir / model_info["filename"]
        download_file(model_info["url"], output_path)
    
    elif "repo" in model_info:
        # HuggingFace repo
        repo_id = model_info["repo"]
        
        for filename in model_info.get("files", []):
            output_path = output_dir / filename
            download_from_huggingface(repo_id, filename, output_path)
    
    # 再次檢查完整性
    if check_model_integrity(model_name):
        print(f"\n✅ {model_info['name']} 下載完成")
        return True
    else:
        print(f"\n❌ {model_info['name']} 下載失敗或不完整")
        return False


def interactive_download():
    """互動式模型下載"""
    
    print("\n" + "="*60)
    print("QwenASR 模型下載器")
    print("="*60)
    
    while True:
        print("\n可用模型:")
        for i, (key, info) in enumerate(MODELS.items(), 1):
            status = "✅" if check_model_integrity(key) else "❌"
            size = info.get('size_gb', info.get('size_mb', '?'))
            unit = "GB" if 'size_gb' in info else "MB"
            print(f"  {i}. {status} {info['name']} ({size} {unit})")
        
        print("\n  0. 下載所有必需模型")
        print("  q. 退出")
        
        choice = input("\n請選擇 (輸入編號或 0/q): ").strip()
        
        if choice == 'q':
            break
        elif choice == '0':
            # 下載必需模型
            required = ["qwen3_asr_0.6b_int8", "silero_vad"]
            for model_name in required:
                download_model(model_name)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(MODELS):
                model_name = list(MODELS.keys())[idx]
                download_model(model_name)
        
        input("\n按 Enter 繼續...")
    
    print("\n✅ 模型下載完成")


if __name__ == "__main__":
    interactive_download()
