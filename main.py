"""Run YOLOv8 and DeepSORT on a video or camera and count line crossings."""

import argparse
import json
import math
from pathlib import Path

from src.analytics.counter import LineCounter

DEFAULT_SOURCE = "data/east.mp4"
VEHICLE_CLASSES = {2, 3, 5, 7}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="Video path, URL, or camera index (for example, 0).")
    parser.add_argument("--weights", default="yolov8n-seg.pt")
    parser.add_argument("--output", type=Path, default=Path("output.avi"), help="XVID AVI output.")
    parser.add_argument("--summary", type=Path, help="Optional JSON report.")
    parser.add_argument("--headless", action="store_true", help="Disable the OpenCV window.")
    parser.add_argument("--device", help="Ultralytics device, for example cpu or 0.")
    parser.add_argument("--line-top", type=float, default=0.7, help="Top line as a fraction of image height.")
    parser.add_argument("--line-bottom", type=float, default=0.9, help="Bottom line as a fraction of image height.")
    args = parser.parse_args()
    if not 0 < args.line_top < args.line_bottom < 1:
        parser.error("Lines must satisfy 0 < --line-top < --line-bottom < 1.")
    if args.output.suffix.lower() != ".avi":
        parser.error("--output must be an .avi path.")
    if args.summary and args.summary.suffix.lower() != ".json":
        parser.error("--summary must be a .json path.")
    source = args.source or DEFAULT_SOURCE
    if not source.isdecimal() and Path(source).resolve() in {
        args.output.resolve(), args.summary.resolve() if args.summary else None,
    }:
        parser.error("Output paths must be different from the input video.")
    return args


def run(args):
    import cv2
    from deep_sort_realtime.deepsort_tracker import DeepSort
    from ultralytics import YOLO

    source = args.source or DEFAULT_SOURCE
    capture = cv2.VideoCapture(int(source) if source.isdecimal() else source)
    if not capture.isOpened() and args.source is None:
        capture.release()
        capture = cv2.VideoCapture(0)
        source = "0"
    writer = None
    frames = 0
    try:
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"Could not read video source {source!r}. Set --source to a readable video or camera.")
        height, width = frame.shape[:2]
        top, bottom = int(height * args.line_top), int(height * args.line_bottom)
        if top >= bottom:
            raise RuntimeError("Counting lines overlap at this video resolution.")
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps <= 0:
            fps = 20.0

        model = YOLO(args.weights)
        tracker = DeepSort(max_age=30, embedder_gpu=args.device != "cpu")
        counter = LineCounter(top, bottom, min_frames=2)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(
            str(args.output), cv2.VideoWriter_fourcc(*"XVID"), fps, (width, height),
        )
        if not writer.isOpened():
            raise RuntimeError(f"Could not open the XVID writer for {args.output}.")

        while ok:
            result = model(frame, device=args.device, verbose=False)[0]
            detections = []
            if result.boxes is not None:
                for xyxy, confidence, label in zip(
                    result.boxes.xyxy.cpu().numpy(),
                    result.boxes.conf.cpu().numpy(),
                    result.boxes.cls.cpu().numpy(),
                ):
                    if int(label) in VEHICLE_CLASSES:
                        left, upper, right, lower = map(float, xyxy)
                        detections.append(([left, upper, right - left, lower - upper],
                                           float(confidence), "vehicle"))

            tracks = tracker.update_tracks(detections, frame=frame)
            visible = {track.track_id: tuple(map(int, track.to_ltrb()))
                       for track in tracks if track.is_confirmed() and track.time_since_update == 0}
            points = {track_id: ((left + right) // 2, lower)
                      for track_id, (left, _, right, lower) in visible.items()}
            up, down = counter.update(points)

            for track_id, (left, upper, right, lower) in visible.items():
                color = (0, 165, 255) if track_id in counter.counted else (0, 255, 0)
                cv2.rectangle(frame, (left, upper), (right, lower), color, 2)
                cv2.circle(frame, points[track_id], 4, (0, 0, 255), -1)
                cv2.putText(frame, f"ID {track_id}", points[track_id],
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            cv2.line(frame, (0, top), (width, top), (255, 0, 0), 2)
            cv2.line(frame, (0, bottom), (width, bottom), (0, 0, 255), 2)
            cv2.putText(frame, f"Up: {up}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Down: {down}", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            writer.write(frame)
            frames += 1
            if not args.headless:
                cv2.imshow("Traffic System", frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break
            ok, frame = capture.read()
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        if not args.headless:
            cv2.destroyAllWindows()

    return {
        "source": source, "weights": args.weights, "output": str(args.output),
        "frames": frames, "fps": fps, "width": width, "height": height,
        "lines_px": [top, bottom], "up": up, "down": down,
    }


def main():
    args = parse_args()
    try:
        result = run(args)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None
    report = json.dumps(result, indent=2)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
