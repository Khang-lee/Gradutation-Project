#xử lý logic
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import datetime

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # <-- THAY MẬT KHẨU MYSQL CỦA BẠN (để trống nếu không có)
    'database': 'db_dtck', # <-- TÊN DATABASE BẠN ĐANG DÙNG
    'connection_timeout': 5
}

#kết nối CSDL MySQL
def get_db_connection():
    """Tạo và trả về kết nối đến CSDL MySQL."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"lỗi kết nối với database: {err}")
        return None
   
#kiểm tra kết nối CSDL 
def check_db_connection():
    conn = get_db_connection()
    if conn and conn.is_connected():
        print("Kết nối CSDL thành công!")
        conn.close()
        return True
    else:
        print("Kết nối CSDL thất bại!")
        return False
    
#xác thực user đăng nhập
def authenticate_user(username, password):
    sql = "SELECT * FROM users WHERE username = %s"
    
    conn = get_db_connection()
    if not conn: 
        return None
    
    user_data = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (username,))
        user_data = cursor.fetchone()

        if user_data and check_password_hash(user_data['password'], password):
            return user_data
        else:
            return None
    except mysql.connector.errors as err:
        print(f"lỗi xác thực user: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            if 'cursor' in locals() and cursor:
                cursor.close()
            conn.close()
            
#thêm user mới
def add_user(username, password):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            print("Không thể kết nối đến CSDL.")
            return False
        cursor = conn.cursor()
        
        check_sql = "SELECT COUNT(*) FROM users WHERE username = %s"
        cursor.execute(check_sql, (username,))
        
        user_count = cursor.fetchone()[0]
        
        if user_count > 0:
            print(f"User {username} đã tồn tại.")
            return 'exists'
        
        hashed_pw = generate_password_hash(password)
        
        role = 'admin' if 'admin' in username.lower() else 'user'
        insert_sql = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        cursor.execute(insert_sql, (username, hashed_pw, role))
        
        conn.commit()
        print(f"Thêm user {username} thành công với '{role}'.")
        return True
    except mysql.connector.Error as err:
        print(f"Lỗi khi thêm user mới: {err}")
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_label_by_name(label_name):
    """Lấy thông tin nhãn (bao gồm ID) từ tên nhãn."""
    conn = get_db_connection()
    if not conn: return None
    label_info = None # Khởi tạo để chắc chắn
    cursor = None # Khởi tạo cursor
    try:
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT id, description, handling_suggestion FROM labels WHERE LOWER(name) = LOWER(%s)" # <<< ĐẢM BẢO LÀ 'name'
        cursor.execute(sql, (label_name,)) # Truyền tên nhãn gốc từ model
        label_info = cursor.fetchone()
        print(f"DEBUG: Tìm label '{label_name}', Kết quả DB: {label_info}")
        return label_info
    except mysql.connector.Error as err:
        print(f"Lỗi lấy thông tin nhãn: {err}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def add_image(image_path, user_id):
    """Lưu thông tin ảnh vào CSDL và trả về ID ảnh mới."""
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO images (user_id, file_path) VALUES (%s, %s)"
        cursor.execute(sql, (user_id, image_path))
        conn.commit()
        image_id = cursor.lastrowid # Lấy ID của dòng vừa chèn
        print(f"Đã lưu ảnh vào DB, ID: {image_id}")
        return image_id
    except mysql.connector.Error as err:
        print(f"Lỗi lưu ảnh vào CSDL: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def add_classification_result(image_id, label_id, confidence):
    """Lưu kết quả phân loại vào CSDL (bảng classification_history)."""
    conn = get_db_connection()
    if not conn:
        print("Lỗi: Không thể kết nối CSDL để lưu kết quả.")
        return False
    cursor = None # Khởi tạo cursor
    try:
        cursor = conn.cursor()
        # Đảm bảo tên bảng và tên cột khớp với CSDL của bạn
        # Dựa trên ảnh CSDL bạn gửi, bảng là classification_history, cột confidence là model_confidence
        sql = "INSERT INTO classification_history (image_id, label_id, model_confidence) VALUES (%s, %s, %s)"
        cursor.execute(sql, (image_id, label_id, confidence))
        conn.commit()
        print(f"Đã lưu kết quả phân loại cho image_id {image_id} vào DB.")
        return True
    except mysql.connector.Error as err:
        print(f"Lỗi lưu kết quả phân loại: {err}")
        return False
    finally:
        if cursor: # Đảm bảo cursor tồn tại
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            
def get_history_details(user_id):
    conn = get_db_connection()
    if not conn:
        print("không thể lấy dữ liệu từ những bảng khác!")
        return None
    history = []
    cursor = None
    try:
        sql = """
            SELECT
                r.id AS result_id,          -- ID của bản ghi lịch sử
                r.user_id,                  -- ID người dùng
                i.file_path,                -- Đường dẫn file ảnh từ bảng images
                r.detected_label,           -- Nhãn dự đoán từ bảng history
                r.model_confidence,         -- Độ tin cậy từ bảng history
                r.detection_time,           -- Thời gian từ bảng history
                l.name AS actual_label_name,-- Tên nhãn chuẩn từ bảng labels
            FROM
                classification_history r    -- Bảng lịch sử (chính)
            INNER JOIN                          -- Nên dùng INNER JOIN để chỉ lấy kết quả có ảnh tương ứng
                images i ON r.image_id = i.id -- JOIN với bảng images dựa trên image_id
            LEFT JOIN                           -- Dùng LEFT JOIN để vẫn lấy kết quả nếu nhãn không có trong bảng labels
                labels l ON LOWER(r.detected_label) = LOWER(l.name) -- JOIN với bảng labels dựa trên tên nhãn
            WHERE
                r.user_id = %s              -- Lọc theo user_id (từ bảng history)
            ORDER BY
                r.detection_time DESC       -- Sắp xếp mới nhất trước
        """
        cursor.execute(sql, (user_id,))
        history = cursor.fetchall()
        
        #hàm xử lý kết quả
        for record in history:
            if'file_path' in record and record['file_path']:
                record['file_name'] = os.path.basename(record['file_path'])
            else:
                record['file_name'] = 'N/A'
            if 'detection_time' in record and isinstance(record['detection_time'], datetime.datetime):
                record['detection_time_str'] = record['detection_time'].strftime('%Y-%m-%d %H:%M:%S')
            elif 'detection_time' in record:
                record['detection_time_str'] = str(record['detection_time'])
            else:
                record['detection_time_str'] = 'N/A'

            if 'model_confidence' in record:
                record['confidence'] = record['model_confidence'] # Tạo key 'confidence' cho tiện

            if 'handling_suggestion' not in record or record['handling_suggestion'] is None:
                record['handling_suggestion'] = 'Chưa có gợi ý.' # Giá trị mặc định
        return history

    except mysql.connector.Error as err:
        print(f"Lỗi lấy chi tiết lịch sử phân loại: {err}")
        # print(f"SQL Query Error: {sql}") # Bỏ comment để debug SQL nếu cần
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_classification_history(user_id):
    """Lấy lịch sử phân loại của một user, bao gồm gợi ý xử lý"""
    conn = get_db_connection()
    if not conn: 
        print("lỗi: không thể kết nói csdl để lấy dữ lịch sử")
        return None
    history = []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        # Nối các bảng để lấy thông tin đầy đủ
        sql = """
            SELECT
                r.id,
                r.user_id,
                r.file_path,
                r.detected_label,
                r.model_confidence,
                r.detection_time,
                l.handling_suggestion
            FROM classification_history r
            LEFT JOIN labels l ON LOWER(r.detected_label) = LOWER(l.name)
            WHERE r.user_id = %s
            ORDER BY r.detection_time DESC
        """
        cursor.execute(sql, (user_id,))
        history = cursor.fetchall()
        # Chuyển đổi datetime thành chuỗi cho JSON
        for record in history:
            # Lấy tên file từ đường dẫn đầy đủ (tùy chọn)
            if 'file_path' in record and record['file_path']:
                record['file_name'] = os.path.basename(record['file_path'])
            else:
                record['file_name'] = 'N/A'
            # Định dạng lại thời gian
            if 'detection_time' in record and isinstance(record['detection_time'], datetime.datetime):
                record['detection_time_str'] = record['detection_time'].strftime('%Y-%m-%d %H:%M:%S')
            elif 'detection_time' in record: # Giữ nguyên nếu không phải datetime
                 record['detection_time_str'] = str(record['detection_time'])
            else:
                 record['detection_time_str'] = 'N/A'
            if 'model_confidence' in record:
                record['confidence'] = record['model_confidence']
                # del record['model_confidence'] # Xóa key cũ nếu muốn

        return history
    except mysql.connector.Error as err:
        print(f"Lỗi không tìm lịch sử phân loại của người dùng: {err}")
        return None
    finally:
        if cursor: # Đảm bảo cursor tồn tại trước khi đóng
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# Đừng quên import datetime ở đầu file db_handler.py
if __name__ ==  "__main__":
    print("chạy file kiểm tra kết nối CSDL! ")
    check_db_connection()