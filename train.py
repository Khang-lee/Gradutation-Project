from ultralytics import YOLO
import os
import torch
import time
import glob

#--cấu hình--
DATASET_DIR = 'D:/DTKL/XAYDUNGHETHONGPHANLOAIRAC/database/Train'
MODEL_NAME = 'yolov8n-cls.pt'
IMAGE_SIZE = 224
EPOCHS = 50
BATCH_SIZE = 5
PROJECT_NAME = 'train/classify_trash'
EXPERIMENT_NAME = 'testtrainning'
DEVICE = 'cpu'
# các mô hình huấn luyện của yolov8 dựa trên yêu cầu của người train
#YOLOv8n (Nano)
#YOLOv8s (Small)
#YOLOv8m (Medium)
#YOLOv8l (Large)
#YOLOv8x (Extra Large)
#Tính thời gian train
# Bắt đầu với giá trị này cho yolov8n-cls, imgsz=224, batch=8 trên CPU trung bình.
ESTIMATED_SECONDS_PER_BATCH = 10 #huấn luyện theo lô ( 1 lô / bao nhiêu ảnh bạn muốn )

def count_images(directory):
    """Đếm tổng số file ảnh trong thư mục dataset (đã là thư mục train)."""
    count = 0
    print(f"Đang tìm ảnh trong: {directory}") #thêm dòng kiểm tra
    # Tìm tất cả file ảnh jpg, png, jpeg trong thư mục dataset và các thư mục con
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        # Bỏ phần 'train' ra khỏi đường dẫn tìm kiếm
        search_path = os.path.join(directory, '**', ext)
        found_files = glob.glob(search_path, recursive=True)
        print(f"Tìm thấy {len(found_files)} file {ext}")
        count += len(found_files)
    print(f"Tổng số ảnh tìm thấy: {count}")
    return count

#--tính thời gian train--
def format_time(seconds):
    #đổi thành giờ/phút/giây
    if seconds < 0:
        return "N/A"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

#ước tính thời gian huấn luyện dựa trên batchsize ( số lượng ảnh 1 lô huấn luyện), epochs ( số lần đọc tất cả ảnh train )
def estimate_training_time():
    try:
        num_train_images = count_images(DATASET_DIR)
        if num_train_images == 0:
            print("(!) Không tìm thấy ảnh trong thư mục train để ước tính thời gian.")
            return -1

        batches_per_epoch = (num_train_images + BATCH_SIZE - 1) // BATCH_SIZE #Làm tròn lên
        time_per_epoch_seconds = batches_per_epoch * ESTIMATED_SECONDS_PER_BATCH
        total_time_seconds = time_per_epoch_seconds * EPOCHS
        print(f"Ước tính dựa trên {num_train_images} ảnh huấn luyện:")
        print(f" - Khoảng {batches_per_epoch} batch mỗi epoch.")
        print(f" - Thời gian ước tính cho mỗi epoch: ~{format_time(time_per_epoch_seconds)}")
        print(f" - TỔNG THỜI GIAN HUẤN LUYỆN ƯỚC TÍNH ({EPOCHS} epochs): ~{format_time(total_time_seconds)}")
        return total_time_seconds
    except Exception as e:
        print(f"(!) Lỗi khi ước tính thời gian: {e}")
        return -1

def main():
    print("--- Bắt đầu quá trình huấn luyện YOLOv8 Classification trên CPU ---")
    print(f"Dataset: {DATASET_DIR}")
    print(f"Model: {MODEL_NAME}")
    print(f"Thiết bị: {DEVICE}")

    #hàm gọi ước tính thời gian
    estimated_time = estimate_training_time()
    print("-" * 30)

    # Tải model train về ( trong file dữ liệu Train tải từ kaggle về)
    model = YOLO(MODEL_NAME)

    #Bắt đầu huấn luyện
    start_time = time.time() #ghi lại thời gian bắt đầu thực tế
    try:
        results = model.train(
            data=DATASET_DIR,
            imgsz=IMAGE_SIZE,
            epochs=EPOCHS,
            batch=BATCH_SIZE,
            device=DEVICE,
            project=PROJECT_NAME,
            name=EXPERIMENT_NAME,
            exist_ok=True
        )
        end_time = time.time() #ghi lại thời gian kết thúc thực tế
        actual_duration_seconds = end_time - start_time

        print("--- Huấn luyện hoàn tất ---")
        print(f"Kết quả và model tốt nhất được lưu tại: {os.path.join(PROJECT_NAME, EXPERIMENT_NAME)}")
        print(f"THỜI GIAN HUẤN LUYỆN THỰC TẾ: {format_time(actual_duration_seconds)}")
        if estimated_time > 0:
             print(f"(Thời gian ước tính ban đầu: ~{format_time(estimated_time)})")


    except Exception as e:
        print(f"\n--- Đã xảy ra lỗi trong quá trình huấn luyện ---")
        print(e)

if __name__ == '__main__':
    main()