#kiêrm tra kết nối vs CSDL
#hàm kết nối db_handeler.py
from db_handler import get_db_connection

def runtest():
    print("bắt đầu kết nối với database")
    print("kết nối đến máy chủ mysql")
    
    conn = get_db_connection()
    
    if conn and conn.is_connected():
        print("\n **kết nối thành công!**")
        print("thông tin server:", conn.get_server_info())
        
        conn.close()
        print("kết nối đã đóng!")
    else:
        print("kết nối database thất bại")
        print("bước 1: kiểm tra đã bật xampp/wamp chưa?")
        print("bước 2: thông trong db_config trong 'db_handler.py' (host, user, password, đường dẫn database) đã nhập chính xác chưa?")
       
if __name__ == "__main__":
    runtest()