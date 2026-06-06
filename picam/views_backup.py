from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
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
from django.views.decorators.csrf import csrf_exempt

# YOLO 모델 로드
# model=YOLO("static/yolo/yolov5su.pt")

model = None

def load_model():
    """YOLOv5 모델 로드"""
    global model
    if model is None:
        # PyTorch Hub에서 YOLOv5 모델 로드
        # model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        
        # YOLO 모델 로드
        model=YOLO("static/yolo/yolov5su.pt")

        model.eval()
        if torch.cuda.is_available():
            model.cuda()
    return model

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

# MQTT 브로커 정보
MQTT_BROKER = "192.168.0.44"
MQTT_PORT = 1883
MQTT_TOPICS = ["pi/picam", "rpi1/picam", "ubt/picam", "piz1/picam", "piz2/picam", "piz3/picam"]  # 여러 개의 토픽 등록
object_detection_enabled = False
deviceId = None

# 글로벌 변수로 각 라즈베리파이의 최신 프레임 저장
mqtt_clients = []
frames = {}
frame_lock = threading.Lock()  # 스레드 동기화를 위한 Lock 객체

def create_mqtt_client(topic):
    load_model()
    """ 각 토픽별로 개별 클라이언트를 생성하여 병렬로 Subscribe """
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.subscribe(topic, qos=0)  # QoS를 1로 설정하여 안정성 향상
    client.loop_start()
    return client

def on_message(client, userdata, msg):
    global frames, object_detection_enabled
    device_id = msg.topic.split("/")[0]
    #print(f'on_message_device_id = {device_id}')
    try:
        image_data = base64.b64decode(msg.payload)
        np_array = np.frombuffer(image_data, dtype=np.uint8)
        frame = cv2.imdecode(np_array, cv2.IMREAD_UNCHANGED)
        if object_detection_enabled and device_id == deviceId and not forceOff:
            frame = detect_objects(frame)
        if frame is not None:
            _, encoded_frame = cv2.imencode('.jpg', frame)
            with frame_lock:  # 동기화 처리
                frames[device_id] = base64.b64encode(encoded_frame).decode('utf-8')

    except Exception as e:
        print(f"Error decoding frame from {device_id}: {e}")

# 각 토픽별로 개별 스레드 생성
for topic in MQTT_TOPICS:
    client_thread = threading.Thread(target=create_mqtt_client, args=(topic,))
    client_thread.start()
    mqtt_clients.append(client_thread)

# 객체 탐지 함수
def detect_objects(frame):
    detections = model(frame, stream=True)

    for detection in detections:
        boxes=detection.boxes
        for box in boxes:
            x1,y1,x2,y2=box.xyxy[0]
            #print(x1, y1, x2, y2)
            x1,y1,x2,y2=int(x1), int(y1), int(x2), int(y2)
            print(x1,y1,x2,y2)
            cv2.rectangle(frame, (x1,y1), (x2,y2), (255,0,255),3)
            #print(box.conf[0])
            conf=math.ceil((box.conf[0]*100))/100
            cls=int(box.cls[0])
            class_name=classNames[cls]
            label=f'{class_name}{conf}'
            t_size = cv2.getTextSize(label, 0, fontScale=0.2, thickness=1)[0]
            #print(t_size)
            c2 = (x1 + t_size[0], y1 - t_size[1] - 3)
            cv2.rectangle(frame, (x1,y1), c2, [255,0,255], -1, cv2.LINE_AA)  # filled
            cv2.putText(frame, label, (x1,y1+2),0, 1,[255,255,255], thickness=1,lineType=cv2.LINE_AA)
    return frame

# 객체 감지 버튼 상태 토글
def toggle_detection(request):
    global object_detection_enabled, deviceId, forceOff
    data = json.loads(request.body.decode('utf-8'))
    # deviceId = json.loads(deviceId)
    deviceId = data['device_id']
    forceOff = data['force_off']
    print(f'deviceId ={deviceId}, type={type(deviceId)}')
    print(f'forceOff ={forceOff}, type={type(forceOff)}')
    object_detection_enabled = not object_detection_enabled  # 상태 변경
    return JsonResponse({"detection_enabled": object_detection_enabled})

def picam(request):
    """ 웹페이지 렌더링 """
    return render(request, 'picam/picam3.html')

def picam_data(request):
    """ JSON 형식으로 실시간 프레임 데이터 반환 """
    return JsonResponse({"frames": frames}, safe=False)

# PC webcam을 이용한 객체 탐지
def webcam(request):
    load_model()
    return render(request, 'picam/webcam.html')


@csrf_exempt
def webcam_detect_objects(request):
    """객체 감지 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다.'})
    
    try:
        # 모델 로드
        model = load_model()
        
        # POST 데이터에서 이미지 추출
        image_data = request.POST.get('image')
        if not image_data:
            return JsonResponse({'success': False, 'error': '이미지 데이터가 없습니다.'})
        
        # base64 문자열에서 이미지 데이터 추출
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        
        # 바이트 스트림을 이미지로 변환
        image = Image.open(io.BytesIO(image_bytes))
        
        # 예측 수행
        results = model(image)
        
        # 결과 추출
        predictions = results.xyxy[0].cpu().numpy()  # x1, y1, x2, y2, confidence, class
        
        detected_objects = []
        for x1, y1, x2, y2, conf, class_id in predictions:
            class_id = int(class_id)
            class_name = classNames[class_id]
            ko_class_name = CLASSES_KO.get(class_name, class_name)  # 한국어 이름이 있으면 사용
            
            detected_objects.append({
                'class': class_name,
                'ko_class': ko_class_name,
                'confidence': float(conf),
                'bbox': [float(x1), float(y1), float(x2), float(y2)]
            })
            
        # 결과 이미지 생성
        result_image = results.render()[0]  # 박스가 그려진 이미지
        _, buffer = cv2.imencode('.jpg', result_image)
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

def system_status(request):
    """시스템 상태 정보 제공"""
    gpu_available = torch.cuda.is_available()
    if gpu_available:
        gpu_name = torch.cuda.get_device_name(0)
    else:
        gpu_name = "Not available"
    
    return JsonResponse({
        'status': 'running',
        'gpu_available': gpu_available,
        'gpu_name': gpu_name,
        'framework': 'Django'
    })

