class LineCounter:
    def __init__(self, line1_y, line2_y, min_frames=2):
        self.line1_y = line1_y
        self.line2_y = line2_y

        self.up = 0
        self.down = 0

        self.history = {}
        self.state = {}
        self.track_len = {}
        self.counted = set()

        self.min_frames = min_frames

    # 🔥 detect cắt line (chống miss do box to)
    def cross_line(self, prev_y, curr_y, line_y):
        return (prev_y < line_y and curr_y >= line_y) or \
               (prev_y > line_y and curr_y <= line_y)

    def update(self, objects):
        for obj_id, (cx, cy) in objects.items():

            # init
            if obj_id not in self.history:
                self.history[obj_id] = []
                self.state[obj_id] = "none"
                self.track_len[obj_id] = 0

            self.history[obj_id].append((cx, cy))
            self.track_len[obj_id] += 1

            if len(self.history[obj_id]) < 2:
                continue

            prev_y = self.history[obj_id][-2][1]
            curr_y = cy
            dy = curr_y - prev_y

            if self.track_len[obj_id] < self.min_frames:
                continue

            if obj_id in self.counted:
                continue

            state = self.state[obj_id]

            # =========================
            # 🔥 DOWN (đi xuống)
            # =========================
            if dy > 0:

                # case 1: full (line1 → line2)
                if state == "none":
                    if self.cross_line(prev_y, curr_y, self.line1_y):
                        self.state[obj_id] = "l1"

                elif state == "l1":
                    if self.cross_line(prev_y, curr_y, self.line2_y):
                        self.down += 1
                        self.counted.add(obj_id)
                        self.state[obj_id] = "done"

                # case 2: spawn giữa → qua line2
                if state == "none":
                    if self.cross_line(prev_y, curr_y, self.line2_y):
                        self.down += 1
                        self.counted.add(obj_id)
                        self.state[obj_id] = "done"

            # =========================
            # 🔥 UP (đi lên)
            # =========================
            elif dy < 0:

                # case 1: full (line2 → line1)
                if state == "none":
                    if self.cross_line(prev_y, curr_y, self.line2_y):
                        self.state[obj_id] = "l2"

                elif state == "l2":
                    if self.cross_line(prev_y, curr_y, self.line1_y):
                        self.up += 1
                        self.counted.add(obj_id)
                        self.state[obj_id] = "done"

                # case 2: spawn giữa → qua line1
                if state == "none":
                    if self.cross_line(prev_y, curr_y, self.line1_y):
                        self.up += 1
                        self.counted.add(obj_id)
                        self.state[obj_id] = "done"

        return self.up, self.down