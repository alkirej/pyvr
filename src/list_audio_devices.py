import cv2

video = cv2.VideoCapture("/dev/video0")
video.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
video.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)


success = True
while success:
    success, frame = video.read()
    keypress = cv2.waitKey(1)
    if keypress & 0xFF == 27:
        break

    cv2.imshow("Preview", frame)

    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    print(f"({width}, {height})")
