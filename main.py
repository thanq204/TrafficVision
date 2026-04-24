import cv2
from ultralytics import YOLO
from src.analytics.counter import LineCounter
from deep_sort_realtime.deepsort_tracker import DeepSort

# =========================
# CONFIG
# =========================
source = "data/east.mp4"

# =========================
# LOAD MODEL
# =========================
model = YOLO("yolov8n-seg.pt")

# =========================
# INIT
# =========================
tracker = DeepSort(max_age=30)
counter = None

highlight_ids = {}  # id -> frame countdown

# =========================
# VIDEO
# =========================
cap = cv2.VideoCapture(source)

if not cap.isOpened():
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ No video")
    exit()

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter("output.avi", fourcc, 20.0, (width, height))

# =========================
# MAIN LOOP
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    if counter is None:
        line1 = int(height * 0.7)
        line2 = int(height * 0.9)
        counter = LineCounter(line1, line2, min_frames=2)

    # YOLO
    results = model(frame, verbose=False)[0]

    boxes = []
    if results.boxes is not None:
        for box, cls in zip(results.boxes.xyxy, results.boxes.cls):
            if int(cls) in [2, 3, 5, 7]:
                boxes.append(box.cpu().numpy())

    # DeepSORT
    detections = []
    for box in boxes:
        x1, y1, x2, y2 = box
        detections.append(([x1, y1, x2-x1, y2-y1], 1.0, 'vehicle'))

    tracks = tracker.update_tracks(detections, frame=frame)

    objects = {}

    for track in tracks:
        if not track.is_confirmed():
            continue

        track_id = track.track_id
        l, t, r, b = track.to_ltrb()

        cx = int((l + r) / 2)
        cy = int(b)

        objects[track_id] = (cx, cy)

    # COUNT
    prev_down = counter.down
    prev_up = counter.up

    up, down = counter.update(objects)

    # =========================
    # HIGHLIGHT LOGIC
    # =========================
    if down > prev_down or up > prev_up:
        for obj_id in objects.keys():
            highlight_ids[obj_id] = 10  # highlight 10 frame

    # giảm countdown
    for obj_id in list(highlight_ids.keys()):
        highlight_ids[obj_id] -= 1
        if highlight_ids[obj_id] <= 0:
            del highlight_ids[obj_id]

    # =========================
    # DRAW
    # =========================
    for box in boxes:
        x1, y1, x2, y2 = map(int, box)

        color = (0,255,0)

        # nếu ID thuộc highlight thì đỏ
        for obj_id, (cx, cy) in objects.items():
            if obj_id in highlight_ids:
                if x1 < cx < x2 and y1 < cy < y2:
                    color = (0,0,255)

        cv2.rectangle(frame, (x1,y1),(x2,y2), color, 2)

    # draw ID + center
    for obj_id, (cx, cy) in objects.items():
        cv2.circle(frame, (cx, cy), 4, (0,0,255), -1)
        cv2.putText(frame, f"ID {obj_id}", (cx, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 2)

    # lines
    cv2.line(frame, (0, line1), (width, line1), (255,0,0), 2)
    cv2.line(frame, (0, line2), (width, line2), (0,0,255), 2)

    # count
    cv2.putText(frame, f"Up: {up}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.putText(frame, f"Down: {down}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    # show
    out.write(frame)
    cv2.imshow("Traffic System", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
out.release()
cv2.destroyAllWindows()