# train.py

from ultralytics import YOLO
from pathlib import Path
import shutil
import os
import db_handler
from tensorflow.keras.preprocessing.image import ImageDataGenerator


TEMP_DATASET_DIR = Path("./temp_yolo_dataset_from_db")
FINAL_MODEL_PATH = Path("./best.pt")
IMAGE_SIZE = 224  # Kích thước ảnh đầu vào
BATCH_SIZE = 8    # Số ảnh xử lý mỗi lần, giảm xuống 4 nếu máy yếu

# <<< SỬA LỖI 3: Đơn giản hóa hàm, không cần truyền đối tượng 'db' >>>
def prepare_dataset_from_db(only_new=False):
    """Lấy dữ liệu từ CSDL và chuẩn bị thư mục cho việc huấn luyện."""
    print(f"\n>>> Chuẩn bị dữ liệu từ CSDL (Chỉ dữ liệu mới: {only_new})...")
    if TEMP_DATASET_DIR.exists():
        shutil.rmtree(TEMP_DATASET_DIR)
    
    # Gọi trực tiếp các hàm từ module db_handler
    images_to_process = db_handler.get_training_images(only_new=only_new)
    if not images_to_process:
        return []

    train_dir = TEMP_DATASET_DIR / "train"
    val_dir = TEMP_DATASET_DIR / "val"
    class_names = db_handler.get_class_names_from_db()

    for name in class_names:
        (train_dir / name).mkdir(parents=True, exist_ok=True)
        (val_dir / name).mkdir(parents=True, exist_ok=True)

    prepared_image_ids = []
    for i, (img_id, img_path, class_name) in enumerate(images_to_process):
        if not os.path.exists(img_path):
            print(f"CẢNH BÁO: Không tìm thấy file ảnh '{img_path}'. Bỏ qua.")
            continue
        
        destination_folder = val_dir if i % 5 == 0 else train_dir
        shutil.copy(img_path, destination_folder / os.path.basename(img_path))
        prepared_image_ids.append(img_id)

    print(f">>> Hoàn tất chuẩn bị. {len(prepared_image_ids)} ảnh đã sẵn sàng.")
    return prepared_image_ids

def run_training():
    """Hàm chính để chạy toàn bộ quá trình huấn luyện."""
    # Xác định chế độ huấn luyện
    if FINAL_MODEL_PATH.exists():
        print(">>> Chế độ: Fine-tuning trên dữ liệu mới...")
        model_to_load, only_new_data, epochs = FINAL_MODEL_PATH, True, 25
    else:
        print(">>> Chế độ: Huấn luyện từ đầu với toàn bộ dữ liệu CSDL...")
        model_to_load, only_new_data, epochs = 'yolov8n-cls.pt', False, 50

    prepared_ids = prepare_dataset_from_db(only_new=only_new_data)
    if not prepared_ids:
        print("\n>>> KẾT THÚC: Không có dữ liệu để huấn luyện.")
        return
    
    # Tạo data generator với augmentation
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        brightness_range=[0.8, 1.2],
        fill_mode='nearest'
    )

    val_datagen = ImageDataGenerator(rescale=1./255)
    
    # Tạo luồng dữ liệu từ các thư mục đã chuẩn bị
    train_generator = train_datagen.flow_from_directory(
        TEMP_DATASET_DIR / "train",
        target_size=(IMAGE_SIZE, IMAGE_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical'
    )
    
    val_generator = val_datagen.flow_from_directory(
        TEMP_DATASET_DIR / "val",
        target_size=(IMAGE_SIZE, IMAGE_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical'
    )

    # Khởi tạo và huấn luyện model YOLO
    model = YOLO(model_to_load)
    print(f"\n--- Bắt đầu huấn luyện với Data Generator ---")
    
    results = model.train(
        data=None, # Không cần vì đã dùng data loader
        train_loader=train_generator,
        val_loader=val_generator,
        epochs=epochs,
        imgsz=IMAGE_SIZE,
        batch=BATCH_SIZE, # batch size được kiểm soát bởi generator, nhưng truyền vào đây để YOLO ghi log
        project='runs/train',
        name='yolo_db_training'
    )
    print("\n>>> Hoàn tất training!")
    
    # Lưu và cập nhật model tốt nhất
    best_model_path = Path(results.save_dir) / 'weights' / 'best.pt'
    shutil.copy(best_model_path, FINAL_MODEL_PATH)
    print(f"✅ Model tốt nhất đã được cập nhật tại: {FINAL_MODEL_PATH}")

    # Đánh dấu ảnh đã được huấn luyện trong CSDL
    db_handler.mark_images_as_trained(prepared_ids)
    print(f"✅ Đã cập nhật trạng thái 'is_trained=1' cho {len(prepared_ids)} ảnh trong CSDL.")
    
    # Dọn dẹp
    shutil.rmtree(TEMP_DATASET_DIR)
    print(f"✅ Đã xóa thư mục dữ liệu tạm.")

if __name__ == "__main__":
    run_training()