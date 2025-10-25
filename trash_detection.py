import argparse
import json
import os
from ultralytics import YOLO
import torch # Để kiểm tra thiết bị (tùy chọn)
import sys # Để in lỗi ra stderr

# --- CẤU HÌNH ---
# 1. Đường dẫn đến file model phân loại của bạn
#    Nếu 'yolov8n-cls.pt' nằm cùng thư mục với script này:
MODEL_PATH = r'D:\DTKL\XAYDUNGHETHONGPHANLOAIRAC\train\classify_trash\testtrainning\weights\best.pt'
# MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'yolov8n-cls.pt')

# 2. Chọn thiết bị (tự động chọn GPU nếu có, nếu không thì CPU)
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
# DEVICE = 'cpu' # Bỏ comment dòng này để luôn chạy trên CPU

def predict_trash_classification(image_path):
    # Chuẩn bị cấu trúc dữ liệu output mặc định
    output_data = {
        "original_file_path": image_path,
        "annotated_file_path": image_path, # Phân loại không thay đổi ảnh gốc
        "detections": [] # Sẽ chứa 1 kết quả dự đoán (label, confidence)
    }

    try:
        # 1. Kiểm tra xem file model có tồn tại không
        if not os.path.exists(MODEL_PATH):
             raise FileNotFoundError(f"Không tìm thấy file model tại: {MODEL_PATH}")

        # 2. Tải model đã huấn luyện
        model = YOLO(MODEL_PATH)

        # 3. Thực hiện dự đoán phân loại
        #    verbose=False để giảm bớt log in ra màn hình khi dự đoán
        results = model.predict(source=image_path, device=DEVICE, verbose=False)

        # 4. Xử lý kết quả phân loại
        if results and len(results) > 0:
            result = results[0] # Lấy kết quả cho ảnh đầu tiên (và duy nhất)

            # Kiểm tra xem có kết quả xác suất không
            if result.probs is not None:
                # Lấy chỉ số (index) của lớp có xác suất cao nhất
                top1_index = result.probs.top1
                # Lấy giá trị độ tin cậy (confidence) của lớp đó
                top1_confidence = float(result.probs.top1conf)
                # Lấy tên nhãn (label name) từ chỉ số, sử dụng names của model
                label_name = model.names[top1_index]

                # Thêm kết quả dự đoán tốt nhất vào danh sách detections
                output_data["detections"].append({
                    "label": label_name,
                    "confidence": top1_confidence
                })
            else:
                 # Trường hợp không lấy được xác suất (ít khi xảy ra với classification)
                 print(f"Cảnh báo: Không thể lấy xác suất cho ảnh {image_path}", file=sys.stderr)
                 output_data["detections"].append({
                    "label": "N/A", # Không xác định
                    "confidence": 0.0
                 })
        else:
            print(f"Cảnh báo: Model không trả về kết quả cho ảnh {image_path}", file=sys.stderr)
            output_data["detections"].append({
                "label": "N/A", # Không xác định
                "confidence": 0.0
            })


        return output_data

    except Exception as e:
        # Nếu có lỗi, in lỗi ra stderr và trả về thông tin lỗi dạng JSON
        print(f"Lỗi trong quá trình dự đoán ảnh {image_path}: {e}", file=sys.stderr)
        # Trả về cấu trúc JSON chứa lỗi
        return {
            "original_file_path": image_path,
            "annotated_file_path": image_path,
            "error": str(e),
            "detections": []
            }

# --- Khối main để chạy script trực tiếp từ dòng lệnh ---
if __name__ == "__main__":
    # Thiết lập bộ phân tích tham số dòng lệnh
    parser = argparse.ArgumentParser(description='Phân loại ảnh rác sử dụng YOLOv8.')
    # Tham số --img_path là bắt buộc
    parser.add_argument('--file_path', required=True, help='Đường dẫn đến file ảnh đầu vào.')
    args = parser.parse_args()

    # Gọi hàm dự đoán với đường dẫn ảnh từ tham số
    prediction_result = predict_trash_classification(args.file_path)

    # **Quan trọng:** In kết quả cuối cùng ra stdout dưới dạng chuỗi JSON.
    # Đảm bảo không có lệnh print nào khác xen vào output JSON này.
    print(json.dumps(prediction_result))