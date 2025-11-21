from ultralytics import YOLO

# Cargar un modelo YOLOv8 (yolov8n, yolov8s, yolov8m, etc.)
model = YOLO("yolov8s.pt")

# Entrenar
model.train(
    data="LED.v6i.yolov8/data.yaml",
    epochs=5,
    imgsz=640,
    batch=10,
    name="yolov8_custom"
)