#xử lý logic
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import datetime
import os

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


def add_classification_result(user_id, file_path, detected_label, model_confidence):
    """
    Lưu kết quả phân loại (bao gồm user_id, file_path, label, confidence)
    trực tiếp vào bảng classification_history.
    """
    conn = get_db_connection()
    if not conn:
        print("Lỗi: Không thể kết nối CSDL để lưu kết quả.")
        return False
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Câu lệnh INSERT khớp với cấu trúc bảng mới của bạn
        # (user_id, label_name, confidence, file_path, uploaded_at)
        sql = """
            INSERT INTO classification_history
            (user_id, file_path, label_name, confidence, uploaded_at)
            VALUES (%s, %s, %s, %s, NOW()) 
        """
        # Lưu ý: Đảm bảo tên cột trong CSDL là 'label_name' và 'confidence'
        
        try:
            confidence_float = float(model_confidence)
        except (ValueError, TypeError):
            confidence_float = 0.0

        # Thực thi INSERT với các giá trị
        cursor.execute(sql, (user_id, file_path, detected_label, confidence_float))
        conn.commit() # Lưu thay đổi
        print(f"Đã lưu kết quả (Nhãn: {detected_label}) vào bảng classification_history.")
        return True # Trả về True nếu thành công

    except mysql.connector.Error as err:
        print(f"Lỗi lưu kết quả phân loại vào DB: {err}")
        return False # Trả về False nếu có lỗi
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def get_history_details(user_id):
    """Lấy chi tiết lịch sử phân loại bằng cách JOIN các bảng."""
    conn = get_db_connection()
    if not conn:
        print("Lỗi: Không thể kết nối CSDL để lấy lịch sử.")
        return None
    history = []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        # Câu lệnh SQL JOIN các bảng
        sql = """
            SELECT
                r.id AS result_id,
                r.user_id,
                r.file_path,
                r.label_name AS detected_label, -- Lấy tên cột đã đổi
                r.confidence AS model_confidence, -- Lấy tên cột đã đổi
                r.uploaded_at AS detection_time, -- Lấy tên cột đã đổi
                l.handling_suggestion
            FROM
                classification_history r
            LEFT JOIN
                labels l ON LOWER(r.label_name) = LOWER(l.name)
            WHERE
                r.user_id = %s
            ORDER BY
                r.uploaded_at DESC -- Sắp xếp theo cột đã đổi
        """
        cursor.execute(sql, (user_id,))
        history = cursor.fetchall()

        # Xử lý kết quả (định dạng thời gian, lấy tên file, đổi tên confidence)
        for record in history:
            if 'file_path' in record and record['file_path']:
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
                record['confidence'] = record['model_confidence']

            if 'handling_suggestion' not in record or record['handling_suggestion'] is None:
                record['handling_suggestion'] = 'Chưa có gợi ý.'

        return history

    except mysql.connector.Error as err:
        print(f"Lỗi lấy chi tiết lịch sử phân loại: {err}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            
# Đừng quên import datetime ở đầu file db_handler.py
if __name__ ==  "__main__":
    print("chạy file kiểm tra kết nối CSDL! ")
    check_db_connection()