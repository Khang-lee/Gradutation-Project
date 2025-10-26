#backend - flask server
from flask import Flask, request, jsonify, render_template, send_from_directory
import db_handler
import os
import subprocess
import sys
import json
from werkzeug.utils import secure_filename
import base64
import datetime

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)),'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
@app.route('/')
def login_page():
    return render_template('login.html')
#API endpoint để client kiểm trả kết nối
@app.route('/api/health', methods=['GET'])
def api_health_check():
    if db_handler.check_db_connection():
        return jsonify({'status': 'ok', 'message': 'server và csdl đã sẵn sàng.'})
    else:
        return jsonify({'status': 'error', 'message': 'sever không thể kết nối đến csdl'})
#API BACKEND CHO SERVER
#đăng nhập user
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
#kiểm tra thông tin đăng nhập
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Thiếu username hoặc password đăng nhập'}), 400
    if not db_handler.check_db_connection():
# kiểm tra không kết nối được CSDL, báo lỗi server ngay
        print("Lỗi API Login: Không thể kết nối CSDL.")
        return jsonify({'status': 'error', 'message': 'không thể kết nối với server!'}), 500 # Mã lỗi 500
#gọi hàm authenticate_user từ db_handler xác thực
    user_data = db_handler.authenticate_user(username, password)
    if user_data:
        #thành công trả vể JSON user data
        return jsonify({'status': 'success', 'user': user_data})
    else:
        #nếu không đúng thông tin đăng nhập
        return jsonify({'status': 'error', 'message': 'Sai username hoặc password'}), 401

#đăng kí user mới
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Thiếu username hoặc password đăng kí'}), 400
    result = db_handler.add_user(username, password)

    if result is True:
        return jsonify({'status': 'success'})
    elif result == 'exists':
        return jsonify({'status': 'error', 'message': 'Username đã tồn tại'})
    else:
        return jsonify({'status': 'error', 'message': 'Đăng kí user thất bại do lỗi hệ thống'}), 500

@app.route('/home')
def home_page():
    # Hàm này chỉ đơn giản là render file home.html
    # JavaScript trong home.html sẽ tự xử lý việc lấy thông tin user
    return render_template('home.html')

@app.route('/api/classify_upload', methods=['POST'])
def api_classify_upload():
    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': 'Không có file ảnh nào được gửi lên'}), 400
    file = request.files['image']
    user_id = request.form.get('user_id') # Lấy user_id từ form data

    if not user_id:
         return jsonify({'status': 'error', 'message': 'Thiếu User ID'}), 400

    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Chưa chọn file ảnh'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # --- Gọi script phân loại ---
        try:
            predict_script_path = os.path.join(os.path.dirname(__file__), "trash_detection.py")
            cmd = [sys.executable, predict_script_path, "--file_path", file_path]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=os.path.dirname(__file__))
            result = json.loads(proc.stdout)
            detections_from_model = result.get("detections", []) # Lấy kết quả gốc từ model
            annotated_file_path = result.get("annotated_file_path", file_path) # Dùng ảnh gốc

            processed_detections = [] # Tạo list mới để chứa kết quả đầy đủ

            # --- Lưu vào CSDL và lấy Suggestion ---
            if detections_from_model:
                for detection in detections_from_model:
                    label_name = detection.get('label')
                    confidence = detection.get('confidence')

                    # === GỌI HÀM LƯU LỊCH SỬ ===
                    # Bỏ gọi db_handler.add_image()
                    # Gọi hàm lưu kết quả với các tham số đúng
                    db_handler.add_classification_result(
                        user_id=user_id,
                        file_path=file_path,        # Đường dẫn ảnh gốc đã lưu
                        detected_label=label_name,  # Tên nhãn dự đoán
                        model_confidence=confidence # Độ tin cậy
                    )
                    # ============================

                    # Vẫn lấy suggestion từ bảng labels để trả về frontend
                    label_info_for_suggestion = db_handler.get_label_by_name(label_name)
                    if label_info_for_suggestion:
                        detection['handling_suggestion'] = label_info_for_suggestion.get('handling_suggestion', 'Chưa có gợi ý.')
                    else:
                        detection['handling_suggestion'] = f"Nhãn '{label_name}' chưa có trong CSDL."

                    processed_detections.append(detection) # Thêm detection đã xử lý vào list

            # Trả kết quả về cho frontend
            original_filename = os.path.basename(file_path)
            image_url_to_display = f"/uploads/{original_filename}"

            return jsonify({
                'status': 'success',
                'annotated_image_url': image_url_to_display,
                'detections': processed_detections, # Trả về list đã xử lý
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Thêm timestamp
            })

        except subprocess.CalledProcessError as e:
            print(f"Lỗi khi chạy script phân loại: {e.stderr}")
            return jsonify({'status': 'error', 'message': f'Lỗi server khi phân loại: {e.stderr}'}), 500
        except Exception as e:
            print(f"Lỗi không xác định (upload): {e}")
            return jsonify({'status': 'error', 'message': f'Lỗi server không xác định: {str(e)}'}), 500
    else:
        return jsonify({'status': 'error', 'message': 'Loại file không hợp lệ'}), 400


@app.route('/api/classify_capture', methods=['POST'])
def api_classify_capture():
    data = request.get_json()
    image_data_base64 = data.get('image_data') # Dữ liệu ảnh dạng base64
    user_id = data.get('user_id')

    if not image_data_base64 or not user_id:
        return jsonify({'status': 'error', 'message': 'Thiếu dữ liệu ảnh hoặc User ID'}), 400

    try:
        header, encoded = image_data_base64.split(",", 1)
        image_data = base64.b64decode(encoded)

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"capture_{timestamp}.jpg"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(file_path, "wb") as fh:
            fh.write(image_data)

        # --- Gọi script phân loại ---
        predict_script_path = os.path.join(os.path.dirname(__file__), "trash_detection.py")
        cmd = [sys.executable, predict_script_path, "--file_path", file_path]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=os.path.dirname(__file__))
        result = json.loads(proc.stdout)
        detections_from_model = result.get("detections", [])
        annotated_file_path = result.get("annotated_file_path", file_path)

        processed_detections = []

        # --- Lưu vào CSDL và lấy Suggestion ---
        if detections_from_model:
            for detection in detections_from_model:
                label_name = detection.get('label')
                confidence = detection.get('confidence')

                # === GỌI HÀM LƯU LỊCH SỬ ===
                db_handler.add_classification_result(
                    user_id=user_id,
                    file_path=file_path,
                    detected_label=label_name,
                    model_confidence=confidence
                )
                # ============================

                # Vẫn lấy suggestion từ bảng labels
                label_info_for_suggestion = db_handler.get_label_by_name(label_name)
                if label_info_for_suggestion:
                    detection['handling_suggestion'] = label_info_for_suggestion.get('handling_suggestion', 'Chưa có gợi ý.')
                else:
                    detection['handling_suggestion'] = f"Nhãn '{label_name}' chưa có trong CSDL."

                processed_detections.append(detection)

        original_filename = os.path.basename(file_path)
        image_url_to_display = f"/uploads/{original_filename}"

        return jsonify({
            'status': 'success',
            'annotated_image_url': image_url_to_display,
            'detections': processed_detections,
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Thêm timestamp
        })

    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi chạy script phân loại (capture): {e.stderr}")
        return jsonify({'status': 'error', 'message': f'Lỗi server khi phân loại: {e.stderr}'}), 500
    except Exception as e:
        print(f"Lỗi không xác định (capture): {e}")
        return jsonify({'status': 'error', 'message': f'Lỗi xử lý ảnh chụp: {str(e)}'}), 500

#Lấy lịch sử phân loại
@app.route('/api/history', methods=['GET'])
def api_get_history():
    user_id = request.args.get('user_id') # Lấy user_id từ URL
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Thiếu User ID'}), 400

    # Gọi hàm xử lý trong db_handler
    history = db_handler.get_history_details(user_id) # << GỌI HÀM LẤY DATA

    if history is not None:
        # Trả về dữ liệu lịch sử nếu thành công
        return jsonify({'status': 'success', 'history': history})
    else:
        # Trả về lỗi nếu db_handler gặp sự cố
        return jsonify({'status': 'error', 'message': 'Không thể lấy lịch sử phân loại.'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Phục vụ file ảnh gốc từ thư mục uploads."""
    try:
        # Trực tiếp gửi file từ thư mục UPLOAD_FOLDER đã cấu hình
        print(f"Attempting to send file: {filename} from folder: {app.config['UPLOAD_FOLDER']}") # Thêm log để kiểm tra
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        print(f"Error: File not found - {filename} in {app.config['UPLOAD_FOLDER']}") # Log lỗi rõ hơn
        return "File not found", 404
    except Exception as e:
        print(f"Error serving file {filename}: {e}") # Bắt các lỗi khác
        return "Server error serving file", 500
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000, debug=True)