# db_handler_mysql.py
import mysql.connector
from mysql.connector import errorcode

# --- CẤU HÌNH KẾT NỐI MYSQL ---
# !!! THAY THẾ BẰNG THÔNG TIN CỦA BẠN !!!
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # <-- THAY MẬT KHẨU MYSQL CỦA BẠN (để trống nếu không có)
    'database': 'db_dtck' # <-- TÊN DATABASE BẠN ĐANG DÙNG
}

def check_db_connection():
    conn = get_db_connection()
    if conn and conn.is_connected():
        print("Kết nối MySQL thành công.")
        conn.close()
        return True
    else:
        print("Kết nối MySQL thất bại.")
        return False

def get_db_connection():
    """Tạo và trả về một kết nối tới MySQL."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Lỗi kết nối MySQL: Sai username hoặc password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Lỗi kết nối MySQL: Không tìm thấy database được chỉ định.")
        else:
            print(f"Lỗi kết nối MySQL: {err}")
        return None

def add_user(username, password):
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        sql_query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        user_data = (username, password, 'user')
        
        cursor.execute(sql_query, user_data)
        conn.commit() # Chốt hạ lệnh INSERT, lưu vĩnh viễn
        return True
        
    except mysql.connector.Error as err:
        print(f"LỖI KHI THÊM USER: {err}")
        return False
        
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_training_images(only_new=False):
    """Lấy danh sách ảnh training từ CSDL."""
    conn = get_db_connection()
    if not conn: return []
    
    cursor = conn.cursor()
    query = "SELECT id, image_path, class_name FROM training_data"
    if only_new:
        query += " WHERE is_trained = FALSE"
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return results

def mark_images_as_trained(image_ids):
    """Đánh dấu các ảnh là đã được train (is_trained = TRUE)."""
    if not image_ids: return
    
    conn = get_db_connection()
    if not conn: return
    
    cursor = conn.cursor()
    
    # Tạo chuỗi placeholder (%s, %s, %s...) cho câu lệnh IN
    placeholders = ', '.join(['%s'] * len(image_ids))
    query = f"UPDATE training_data SET is_trained = TRUE WHERE id IN ({placeholders})"
    
    cursor.execute(query, tuple(image_ids))
    conn.commit() # Chốt hạ lệnh UPDATE
    
    cursor.close()
    conn.close()