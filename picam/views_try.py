from django.shortcuts import render
from django.http import JsonResponse
import paho.mqtt.client as mqtt
import base64
import cv2
import numpy as np
import threading
from ultralytics import YOLO
import math
import json
import torch
from PIL import Image
import io
from queue import Queue
import time
from django.views.decorators.csrf import csrf_exempt
from torchvision import transforms

model = None
load_lock = threading.Lock()

def load_model():
    global model
    with load_lock:
        if model is None:
            model = YOLO("static/yolo/yolov5su.pt")
            model.eval()
            if torch.cuda.is_available():
                model.to(torch.device('cuda'))
                model = model.half()
    return model

# 클래스 이름 정의의
classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
              "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
              "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
              "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
              "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
              "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
              "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
              "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
              "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
              "teddy bear", "hair drier", "toothbrush"
              ]

# 한국어 클래스 레이블
CLASSES_KO = {
    'person': '사람', 'bicycle': '자전거', 'car': '자동차', 'motorcycle': '오토바이',
    'airplane': '비행기', 'bus': '버스', 'train': '기차', 'truck': '트럭', 'boat': '보트',
    'traffic light': '신호등', 'fire hydrant': '소화전', 'stop sign': '정지 표지판',
    'parking meter': '주차 미터기', 'bench': '벤치', 'bird': '새', 'cat': '고양이',
    'dog': '개', 'horse': '말', 'sheep': '양', 'cow': '소', 'elephant': '코끼리',
    'bear': '곰', 'zebra': '얼룩말', 'giraffe': '기린', 'backpack': '백팩',
    'umbrella': '우산', 'handbag': '핸드백', 'tie': '넥타이', 'suitcase': '여행 가방',
    'frisbee': '프리스비', 'skis': '스키', 'snowboard': '스노우보드', 'sports ball': '스포츠 공',
    'kite': '연', 'baseball bat': '야구 방망이', 'baseball glove': '야구 글러브',
    'skateboard': '스케이트보드', 'surfboard': '서핑보드', 'tennis racket': '테니스 라켓',
    'bottle': '병', 'wine glass': '와인 잔', 'cup': '컵', 'fork': '포크',
    'knife': '나이프', 'spoon': '숟가락', 'bowl': '그릇', 'banana': '바나나',
    'apple': '사과', 'sandwich': '샌드위치', 'orange': '오렌지', 'broccoli': '브로콜리',
    'carrot': '당근', 'hot dog': '핫도그', 'pizza': '피자', 'donut': '도넛',
    'cake': '케이크', 'chair': '의자', 'couch': '소파', 'potted plant': '화분',
    'bed': '침대', 'dining table': '식탁', 'toilet': '화장실', 'tv': 'TV',
    'laptop': '노트북', 'mouse': '마우스', 'remote': '리모컨', 'keyboard': '키보드',
    'cell phone': '휴대전화', 'microwave': '전자레인지', 'oven': '오븐', 'toaster': '토스터',
    'sink': '싱크대', 'refrigerator': '냉장고', 'book': '책', 'clock': '시계',
    'vase': '꽃병', 'scissors': '가위', 'teddy bear': '테디 베어', 'hair drier': '헤어 드라이어',
    'toothbrush': '칫솔'
}

MQTT_BROKER = "192.168.0.44"
MQTT_PORT = 1883
MQTT_TOPICS = ["pi/picam", "rpi1/picam", "ubt/picam", "piz1/picam", "piz2/picam", "piz3/picam"]
object_detection_enabled = False
forceOff = False
deviceId = None

frames = {}
frame_lock = threading.Lock()
frame_queue = Queue()

def on_message(client, userdata, msg):
    global frames
    device_id = msg.topic.split("/")[0]
    try:
        image_data = base64.b64decode(msg.payload)
        np_array = np.frombuffer(image_data, dtype=np.uint8)
        frame = cv2.imdecode(np_array, cv2.IMREAD_UNCHANGED)
        if frame is not None:
            with frame_lock:
                frames[device_id] = frame
            if object_detection_enabled and device_id == deviceId and not forceOff:
                frame_queue.put((device_id, frame))
    except Exception as e:
        print(f"Error decoding frame from {device_id}: {e}")

last_detection_time = 0
DETECTION_INTERVAL = 2

TRANSFORM = transforms.Compose([
    transforms.Resize((320, 240)),  # YOLO 입력 해상도 고정
    transforms.ToTensor(),
])

def preprocess_frame(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(frame_rgb)
    tensor = TRANSFORM(image).unsqueeze(0)

    if torch.cuda.is_available():
        tensor = tensor.cuda().half()
    return tensor

def detection_worker():
    global last_detection_time
    load_model()
    while True:
        device_id, frame = frame_queue.get()
        now = time.time()
        if now - last_detection_time < DETECTION_INTERVAL:
            continue
        last_detection_time = now
        detected_frame = detect_objects(frame)
        _, encoded_frame = cv2.imencode('.jpg', detected_frame)
        with frame_lock:
            frames[device_id] = base64.b64encode(encoded_frame).decode('utf-8')

def detect_objects(frame):
    input_tensor = preprocess_frame(frame)
    with torch.no_grad():
        results = model(input_tensor, batch=32)[0]  # 첫 번째 결과만 사용
        boxes = results.boxes
        if boxes is None or boxes.shape[0] == 0:
            return frame

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = round(float(box.conf[0]), 2)
            cls = int(box.cls[0])
            class_name = classNames[cls]
            label = f'{class_name} {conf}'

            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
            cv2.putText(frame, label, (x1, y1 - 5), 0, 0.6, [255, 255, 255], 1, lineType=cv2.LINE_AA)

    return frame

def create_mqtt_client(topic):
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(topic)
    client.loop_start()
    return client

mqtt_clients = []
for topic in MQTT_TOPICS:
    t = threading.Thread(target=create_mqtt_client, args=(topic,))
    t.start()
    mqtt_clients.append(t)

def toggle_detection(request):
    global object_detection_enabled, deviceId, forceOff
    data = json.loads(request.body.decode('utf-8'))
    deviceId = data['device_id']
    forceOff = data['force_off']
    object_detection_enabled = not object_detection_enabled
    return JsonResponse({"detection_enabled": object_detection_enabled})

def picam(request):
    return render(request, 'picam/picam3.html')

def picam_data(request):
    return JsonResponse({"frames": frames}, safe=False)

def webcam(request):
    load_model()
    return render(request, 'picam/webcam.html')

@csrf_exempt
def webcam_detect_objects(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    try:
        model = load_model()
        image_data = request.POST.get('image')
        if not image_data:
            return JsonResponse({'success': False, 'error': '이미지 데이터가 없습니다.'})
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        tensor = transforms.ToTensor()(image).unsqueeze(0)
        if torch.cuda.is_available():
            tensor = tensor.cuda().half()
        results = model(tensor)[0]
        boxes = results.boxes
        detected_objects = []
        for box in boxes:
            x1, y1, x2, y2 = map(float, box.xyxy[0].tolist())
            conf = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = classNames[class_id]
            ko_class_name = CLASSES_KO.get(class_name, class_name)
            detected_objects.append({
                'class': class_name,
                'ko_class': ko_class_name,
                'confidence': conf,
                'bbox': [x1, y1, x2, y2]
            })
        img = results.plot()[0].permute(1, 2, 0).cpu().numpy()
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        _, buffer = cv2.imencode('.jpg', img)
        result_image_b64 = base64.b64encode(buffer).decode('utf-8')
        return JsonResponse({
            'success': True,
            'objects': detected_objects,
            'result_image': f'data:image/jpeg;base64,{result_image_b64}'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

threading.Thread(target=detection_worker, daemon=True).start()

