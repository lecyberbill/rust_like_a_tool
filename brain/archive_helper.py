# [WFGY] Zone: SAFE | λ: 0.1 | Action: Archive zip/unzip helper functions
import sys
import os
import zipfile
from pathlib import Path

def zip_dir_or_file(source: str, destination: str):
    src_path = Path(source)
    dest_path = Path(destination)
    
    if not src_path.exists():
        print(f"Error: Source '{source}' does not exist.")
        sys.exit(2)
        
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        if src_path.is_file():
            zip_file.write(src_path, src_path.name)
        else:
            for root, dirs, files in os.walk(src_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(src_path)
                    zip_file.write(file_path, arcname)
                    
    print(f"Successfully zipped '{source}' to '{destination}'.")

def unzip_file(source: str, destination: str):
    src_path = Path(source)
    dest_path = Path(destination)
    
    if not src_path.exists():
        print(f"Error: Zip file '{source}' does not exist.")
        sys.exit(2)
        
    dest_path.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(src_path, 'r') as zip_ref:
        zip_ref.extractall(dest_path)
        
    print(f"Successfully unzipped '{source}' to '{destination}'.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python archive_helper.py <zip|unzip> <source> <destination>")
        sys.exit(1)
        
    mode = sys.argv[1]
    src = sys.argv[2]
    dst = sys.argv[3]
    
    if mode == "zip":
        zip_dir_or_file(src, dst)
    elif mode == "unzip":
        unzip_file(src, dst)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
