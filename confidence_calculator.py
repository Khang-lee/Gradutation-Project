# confidence_calculator.py

import cv2
import numpy as np

def calculate_confidence(image_path: str) -> float:
    """
    Tính toán độ tin cậy của một bức ảnh dựa trên một thuật toán tùy chỉnh.

    Đây là một ví dụ đơn giản dựa trên độ sắc nét của ảnh.
    Ảnh mờ sẽ có độ tin cậy thấp, ảnh rõ nét sẽ có độ tin cậy cao.
    BẠN CÓ THỂ THAY THẾ TOÀN BỘ LOGIC BÊN TRONG HÀM NÀY BẰNG THUẬT TOÁN CỦA RIÊNG BẠN.

    Args:
        image_path (str): Đường dẫn đến file ảnh cần phân tích.

    Returns:
        float: Một giá trị từ 0.0 đến 1.0 đại diện cho độ tin cậy.
    """
    try:
        # Đọc ảnh ở dạng thang xám
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            print(f"Warning: Không thể đọc ảnh từ '{image_path}'")
            return 0.3 # Trả về giá trị thấp nếu không đọc được ảnh

        # Tính toán phương sai của toán tử Laplacian để đo độ mờ
        # Giá trị này càng cao, ảnh càng sắc nét
        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()

        # Ánh xạ giá trị phương sai vào thang điểm 0.0 - 1.0
        # Ngưỡng 100 là một giá trị tham khảo, bạn có thể điều chỉnh
        # Ví dụ: nếu laplacian_var = 50, confidence = 0.5
        # Nếu laplacian_var >= 100, confidence = 1.0 (tối đa)
        confidence = min(1.0, laplacian_var / 100.0)
        
        # Làm tròn đến 4 chữ số thập phân
        return round(confidence, 4)

    except Exception as e:
        print(f"Lỗi trong quá trình tính độ tin cậy: {e}")
        return 0.1 # Trả về một giá trị rất thấp nếu có lỗi

# --- Ví dụ cách sử dụng (để test) ---
if __name__ == '__main__':
    # Bạn cần có một ảnh tên là 'test_image.jpg' để chạy thử
    test_image_file = 'test_image.jpg' 
    if cv2.imread(test_image_file) is not None:
        score = calculate_confidence(test_image_file)
        print(f"Độ tin cậy của ảnh '{test_image_file}' là: {score:.2%}")
    else:
        print(f"Vui lòng tạo một file ảnh tên '{test_image_file}' để chạy thử.")