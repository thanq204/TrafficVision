# Minh họa TrafficVision

Ảnh và video trong thư mục này được tạo ngày 05/11/2026 bằng `main.py` gốc tại commit `64a2c2203a9365c2af2be17c2082a15eb64d4a25`. Pipeline YOLOv8 → DeepSORT → LineCounter được giữ nguyên.

## Nguồn video và ghi công

- Tác phẩm: **Street traffic**, cảnh đường phố San Francisco, ngày 28/05/2011.
- Tác giả: **Editor**, [kênh YouTube](https://www.youtube.com/user/Editor).
- [Trang nguồn trên Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Street_traffic.webm).
- [Bản gốc trên YouTube](https://www.youtube.com/watch?v=_7sCYyxw4Ic).
- Giấy phép: [Creative Commons Attribution 3.0 Unported (CC BY 3.0)](https://creativecommons.org/licenses/by/3.0/).
- Thay đổi: cắt 12 giây đầu, giảm kích thước còn 768 × 432, chuyển về 20 FPS và bỏ âm thanh; sau đó thêm bounding box, ID, điểm tham chiếu, đường đếm và tổng Up/Down bằng chương trình. Ảnh được trích từ video đã xử lý.

Ảnh, GIF và MP4 dẫn xuất từ video nguồn được chia sẻ theo CC BY 3.0, với ghi công như trên. Việc này không thay đổi giấy phép của thư viện hoặc trọng số mô hình.

## Tái tạo

Cài thư viện theo README gốc, sau đó tải bản nguồn từ trang Commons. Ví dụ PowerShell, chạy tại thư mục gốc kho:

```powershell
New-Item -ItemType Directory -Force data | Out-Null
Invoke-WebRequest -Uri 'https://upload.wikimedia.org/wikipedia/commons/7/70/Street_traffic.webm' -OutFile data/street_traffic.webm
```

Dùng FFmpeg chuẩn bị đoạn đầu vào, 12 giây và 240 khung hình:

```bash
ffmpeg -y -i data/street_traffic.webm -t 12 -an -vf "scale=768:432,fps=20" -c:v libx264 -pix_fmt yuv420p data/east.mp4
python main.py
```

Chờ video chạy hết. Khi tạo bản minh họa trên máy chạy tự động, phần cửa sổ được tắt qua wrapper Python bên dưới; không đổi thuật toán hoặc cách vẽ trong `main.py`:

```python
import runpy
import cv2
import torch

torch.set_num_threads(2)
cv2.imshow = lambda *args: None
cv2.waitKey = lambda *args: -1
cv2.destroyAllWindows = lambda: None
runpy.run_path("main.py", run_name="__main__")
```

Chuyển AVI kết quả thành MP4 H.264 để chia sẻ và lấy ảnh ở giây thứ 2:

```bash
ffmpeg -y -i output.avi -an -c:v libx264 -crf 24 -pix_fmt yuv420p -movflags +faststart docs/media/traffic-demo.mp4
ffmpeg -y -ss 2 -i docs/media/traffic-demo.mp4 -frames:v 1 docs/media/traffic-preview.jpg
ffmpeg -y -i docs/media/traffic-demo.mp4 -vf "fps=6,scale=400:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer" -loop 0 docs/media/traffic-demo.gif
```

Môi trường đã dùng: Windows, Python 3.11.15, torch 2.5.1+cpu, torchvision 0.20.1+cpu, ultralytics 8.0.200, deep-sort-realtime 1.3.2, NumPy 1.26.4, OpenCV 4.10.0.84, SciPy 1.17.1, setuptools 80.10.2. Chuyển mã bằng FFmpeg thông qua `imageio-ffmpeg`.

## Cách đọc kết quả

- Khung xanh: detection phương tiện; nhãn `ID`: track DeepSORT; chấm đỏ: tâm cạnh dưới bounding box.
- Hai đường ngang nằm tại 70% và 90% chiều cao ảnh.
- `Up`/`Down` là số lượt đã đếm theo hướng trong ảnh. Không phải tổng số xe đang có mặt.
- Đây là video đường phố với xe che khuất và chuyển động ngang/chéo; các đường mặc định chưa được hiệu chỉnh riêng cho camera này. Minh họa không chứng minh khả năng đếm chính xác hoặc tốc độ thời gian thực.
- MP4 và GIF phát theo thời gian video, không thể hiện thời gian suy luận thực tế trên CPU.
