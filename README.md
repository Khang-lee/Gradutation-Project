
Trash Classification - WinForm (tkinter) + YOLOv8

Contents:
- main_app.py            : Tkinter WinForm GUI (login/register/upload/capture/train/predict)
- train.py               : Training script (uses ultralytics YOLOv8 when available)
- predict.py             : Inference script (uses ultralytics)
- utils.py               : Helpers
- database/app.db        : SQLite database (with default admin account)
- models/best.pt         : placeholder model file (binary placeholder)
- dataset/               : (not included) expected dataset folder (place your images & labels here)

mở máy ảo (Windows):
1) Install Python 3.10 and create venv:
   python -m venv venv
   venv\Scripts\activate

2) Tải requirements:
   pip install -r requirements.txt

3) Prepare dataset folder:
   ./dataset/
     images/
       train/*.jpg
       val/*.jpg
     labels/
       train/*.txt
       val/*.txt

4) Chạy WinForm app:
   python main_app.py

Notes:
- This ZIP is a template and integration point. For full YOLOv8 training, ensure:
  * ultralytics installed (pip install ultralytics)
  * dataset in proper structure
  * optionally download yolov8n.pt and place in models/ or allow ultralytics to download it.

Contact:
- khangleben123@gmail.com
- 0338351280
