import numpy as np
import cv2
from collections import deque

def setValues(x):
    pass

def main():
    cv2.namedWindow("Color detectors")
    cv2.createTrackbar("Upper Hue", "Color detectors", 153, 180, setValues)
    cv2.createTrackbar("Upper Saturation", "Color detectors", 255, 255, setValues)
    cv2.createTrackbar("Upper Value", "Color detectors", 255, 255, setValues)
    cv2.createTrackbar("Lower Hue", "Color detectors", 64, 180, setValues)
    cv2.createTrackbar("Lower Saturation", "Color detectors", 72, 255, setValues)
    cv2.createTrackbar("Lower Value", "Color detectors", 49, 255, setValues)

    bpoints = [deque(maxlen=1024)]
    gpoints = [deque(maxlen=1024)]
    rpoints = [deque(maxlen=1024)]
    ypoints = [deque(maxlen=1024)]

    b_idx = g_idx = r_idx = y_idx = 0
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255)]
    colorIndex = 0

    paintWindow = np.ones((471, 636, 3), dtype=np.uint8) * 255

    def draw_toolbar(win):
        cv2.rectangle(win, (40, 1), (140, 65), (0, 0, 0), 2)
        cv2.rectangle(win, (160, 1), (255, 65), colors[0], -1)
        cv2.rectangle(win, (275, 1), (370, 65), colors[1], -1)
        cv2.rectangle(win, (390, 1), (485, 65), colors[2], -1)
        cv2.rectangle(win, (505, 1), (600, 65), colors[3], -1)
        cv2.putText(win, "CLEAR", (49, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.putText(win, "BLUE", (185, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(win, "GREEN", (298, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(win, "RED", (420, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(win, "YELLOW", (520, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 2)

    draw_toolbar(paintWindow)
    cv2.namedWindow('Paint', cv2.WINDOW_AUTOSIZE)

    kernel = np.ones((5, 5), np.uint8)
    cap = cv2.VideoCapture(0)

    def draw_strokes(frame):
        pts = [bpoints, gpoints, rpoints, ypoints]
        for i in range(len(pts)):
            for j in range(len(pts[i])):
                for k in range(1, len(pts[i][j])):
                    if pts[i][j][k - 1] is None or pts[i][j][k] is None:
                        continue
                    cv2.line(frame, pts[i][j][k - 1], pts[i][j][k], colors[i], 2)
                    cv2.line(paintWindow, pts[i][j][k - 1], pts[i][j][k], colors[i], 2)

    print("🎨 Air Draw running... Press ESC to exit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        u_h = cv2.getTrackbarPos("Upper Hue", "Color detectors")
        u_s = cv2.getTrackbarPos("Upper Saturation", "Color detectors")
        u_v = cv2.getTrackbarPos("Upper Value", "Color detectors")
        l_h = cv2.getTrackbarPos("Lower Hue", "Color detectors")
        l_s = cv2.getTrackbarPos("Lower Saturation", "Color detectors")
        l_v = cv2.getTrackbarPos("Lower Value", "Color detectors")

        upper = np.array([u_h, u_s, u_v])
        lower = np.array([l_h, l_s, l_v])

        toolbar = frame.copy()
        cv2.rectangle(toolbar, (40, 1), (140, 65), (122, 122, 122), -1)
        cv2.rectangle(toolbar, (160, 1), (255, 65), colors[0], -1)
        cv2.rectangle(toolbar, (275, 1), (370, 65), colors[1], -1)
        cv2.rectangle(toolbar, (390, 1), (485, 65), colors[2], -1)
        cv2.rectangle(toolbar, (505, 1), (600, 65), colors[3], -1)
        cv2.putText(toolbar, "CLEAR ALL", (49, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        cv2.putText(toolbar, "BLUE", (185, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        cv2.putText(toolbar, "GREEN", (298, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        cv2.putText(toolbar, "RED", (420, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        cv2.putText(toolbar, "YELLOW", (520, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (150, 150, 150), 2)

        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=1)

        cnts, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        center = None

        if len(cnts) > 0:
            cnt = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(cnt)
            if radius > 3:
                cv2.circle(toolbar, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                center = (int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"]))

            if center and center[1] <= 65:
                if 40 <= center[0] <= 140:
                    bpoints = [deque(maxlen=1024)]
                    gpoints = [deque(maxlen=1024)]
                    rpoints = [deque(maxlen=1024)]
                    ypoints = [deque(maxlen=1024)]
                    b_idx = g_idx = r_idx = y_idx = 0
                    paintWindow[67:, :, :] = 255
                elif 160 <= center[0] <= 255:
                    colorIndex = 0
                elif 275 <= center[0] <= 370:
                    colorIndex = 1
                elif 390 <= center[0] <= 485:
                    colorIndex = 2
                elif 505 <= center[0] <= 600:
                    colorIndex = 3
            else:
                if center:
                    if colorIndex == 0:
                        bpoints[b_idx].appendleft(center)
                    elif colorIndex == 1:
                        gpoints[g_idx].appendleft(center)
                    elif colorIndex == 2:
                        rpoints[r_idx].appendleft(center)
                    else:
                        ypoints[y_idx].appendleft(center)
        else:
            bpoints.append(deque(maxlen=1024)); b_idx += 1
            gpoints.append(deque(maxlen=1024)); g_idx += 1
            rpoints.append(deque(maxlen=1024)); r_idx += 1
            ypoints.append(deque(maxlen=1024)); y_idx += 1

        draw_strokes(toolbar)

        cv2.imshow("Tracking", cv2.resize(toolbar, (960, 540)))
        cv2.imshow("Paint", cv2.resize(paintWindow, (800, 600)))

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        elif key == ord('s'):
            cv2.imwrite("air_drawing.png", paintWindow)
            print("✅ Saved: air_drawing.png")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
