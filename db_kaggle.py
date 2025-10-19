import kagglehub
from pathlib import Path
import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '', 
    'database': 'db_dtck'
}

CLASS_NAMES = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'other']

def main():
    print(">>> 1. Đang tải dữ liệu từ Kaggle...")
    try:
        download_path = Path(kagglehub.dataset_download("farzadnekouei/trash-type-image-dataset"))
        original_data_path = next(p for p in download_path.iterdir() if p.is_dir())
        print(f"INFO: Dữ liệu đã tải về tại: {original_data_path}")
    except Exception as e:
        print(f"LỖI: Không thể tải dataset. Lỗi: {e}"); return

    print("\n>>> 2. Đang kết nối tới MySQL và chèn dữ liệu...")
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
    except mysql.connector.Error as err:
        print(f"LỖI: Không thể kết nối MySQL. Lỗi: {err}"); return

    total_inserted = 0
    for class_name in CLASS_NAMES:
        class_path = original_data_path / class_name
        if not class_path.exists(): continue
        
        images = list(class_path.glob("*.jpg"))
        for img_path in images:
            absolute_path = str(img_path.resolve())
            sql = "INSERT IGNORE INTO training_data (image_path, class_name) VALUES (%s, %s)"
            cursor.execute(sql, (absolute_path, class_name))
            total_inserted += cursor.rowcount

    conn.commit()
    cursor.close()
    conn.close()
    print(f"\n>>> Hoàn tất! Đã chèn {total_inserted} ảnh mới vào bảng 'training_data'.")

if __name__ == "__main__":
    main()