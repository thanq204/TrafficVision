import cv2

def draw_all(frame, boxes, objects, count, line_y):
    # draw boxes
    for box in boxes:
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

    # draw IDs
    for object_id, (cx, cy) in objects.items():
        cv2.putText(frame, f"ID {object_id}", (cx, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)

    # draw line
    cv2.line(frame, (0, line_y), (frame.shape[1], line_y), (0,0,255), 2)

    # draw count
    cv2.putText(frame, f"Count: {count}", (20,40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    return frame