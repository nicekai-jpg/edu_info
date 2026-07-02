import os
import shutil
from pathlib import Path

def reorganize():
    data_dir = Path("data")
    raw_2025_dir = data_dir / "raw" / "2025"
    
    if not raw_2025_dir.exists():
        print("data/raw/2025 folder does not exist. Nothing to reorganize.")
        return
        
    print("====== Starting Data Directory Reorganization ======")
    
    # 1. 创建目标目录
    for year in ["2022", "2023", "2024", "2025"]:
        (data_dir / "raw" / year).mkdir(parents=True, exist_ok=True)
    (data_dir / "processed").mkdir(parents=True, exist_ok=True)
    
    # 2. 移动历年原始文件
    for year in ["2022", "2023", "2024"]:
        dest_raw_dir = data_dir / "raw" / year
        
        # 物理类
        for ext in [".xlsx", ".zip"]:
            phys_file = raw_2025_dir / f"physics_{year}_raw{ext}"
            if phys_file.exists():
                shutil.move(str(phys_file), str(dest_raw_dir / f"physics_{year}_raw{ext}"))
                print(f"Moved {phys_file.name} to raw/{year}/")
                
        # 历史类
        for ext in [".xlsx", ".zip"]:
            hist_file = raw_2025_dir / f"history_{year}_raw{ext}"
            if hist_file.exists():
                shutil.move(str(hist_file), str(dest_raw_dir / f"history_{year}_raw{ext}"))
                print(f"Moved {hist_file.name} to raw/{year}/")
                
    # 3. 移动已处理的活动 JSON 数据库文件
    processed_dir = data_dir / "processed"
    db_files = [
        "universities_2025.json",
        "universities_2025_backup.json",
        "majors_2025.json",
        "scores_2025.json"
    ]
    for db_file in db_files:
        src_path = raw_2025_dir / db_file
        if src_path.exists():
            shutil.move(str(src_path), str(processed_dir / db_file))
            print(f"Moved {db_file} to processed/")
            
    print("====== Reorganization Completed successfully! ======")

if __name__ == "__main__":
    reorganize()
