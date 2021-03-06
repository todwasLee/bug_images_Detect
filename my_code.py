import numpy as np
import time
import cv2
import os
from flask import Flask, request, Response, jsonify
import jsonpickle
import io
import json
from PIL import Image
from collections import OrderedDict
import datetime

confthres = 0.2
nmsthres = 0.2


def mkdir_farm_name():
    farm_name = "TEST_FARM"
    year = datetime.datetime.now().strftime("%Y")
    month = datetime.datetime.now().strftime("%m")
    day = datetime.datetime.now().strftime("%d")

    if not os.path.exists('E:/ItTrap/' + farm_name):
        os.mkdir('E:/ItTrap/' + farm_name)

    if not os.path.exists('E:/ItTrap/' + farm_name + '/' + year):
        os.mkdir('E:/ItTrap/' + farm_name + '/' + year)

    if not os.path.exists('E:/ItTrap/' + farm_name + '/' + year + '/' + month):
        os.mkdir('E:/ItTrap/' + farm_name + '/' + year + '/' + month)

    if not os.path.exists('E:/ItTrap/' + farm_name + '/' + year + '/' + month + '/' + day):
        os.mkdir('E:/ItTrap/' + farm_name + '/' + year + '/' + month + '/' + day)

    saved_path = 'E:/ItTrap/' + farm_name + '/' + year + '/' + month + '/' + day + '/'

    return saved_path


def Images_saveName():
    basename = "image"
    suffix = datetime.datetime.now().strftime("%y%m%d")
    filename = "_".join([basename, suffix])

    return filename


def Images_saveName_detected():
    import datetime
    basename = "image"
    suffix = datetime.datetime.now().strftime("%y%m%d")
    filename = "_".join([basename, suffix, "detected"])

    return filename


# 라벨 파일 가져오기
def take_label(label_path):
    path = os.path.join(label_path)
    labels = open(path).read().strip().split("\n")
    # labels 출력값은 ['Aciatic leafroller', 'Oriental fruit moth', 'Peach fruit moth']와 같이 나온다

    return labels


# 라벨 색 지정하기
def take_random_color(label_color):
    np.random.seed(25)    # 무작위 색지정 난수 발생, 시드 생성
    color = np.random.randint(0,255, size=(len(label_color), 3), dtype="uint16")

    return color


# 설정 파일 가져오기
def take_cfg_file(cfg_path):
    path = os.path.join(cfg_path)

    return path


# yolov4 weights 파일 가져오기
def take_weights(weights_path):
    path = os.path.join(weights_path)

    return path


# 모델 설정
def load_model(cfg_path, weights_path):
    net = cv2.dnn.readNetFromDarknet(cfg_path, weights_path)

    return net


def image_to_byte_array(image: Image):
  imgByteArr = io.BytesIO()
  image.save(imgByteArr, format='PNG')
  imgByteArr = imgByteArr.getvalue()
  return imgByteArr


def get_predection(image, net, LABELS, COLORS):
    Aciatic_leafroller_Num = 0
    Oriental_fruit_moth_Num = 0
    Peach_fruit_moth_Num = 0

    global num_count

    (H, W) = image.shape[:2]

    # determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    # construct a blob from the input image and then perform a forward
    # pass of the YOLO object detector, giving us our bounding boxes and
    # associated probabilities
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (608, 608),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    print(layerOutputs)
    end = time.time()

    # show timing information on YOLO
    print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    # initialize our lists of detected bounding boxes, confidences, and
    # class IDs, respectively
    boxes = []
    confidences = []
    classIDs = []

    # loop over each of the layer outputs
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            # print(scores)
            classID = np.argmax(scores)
            # print(classID)
            confidence = scores[classID]

            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > confthres:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

    idxs = cv2.dnn.NMSBoxes(boxes, confidences, confthres,
                            nmsthres)

    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # extract the bounding box coordinates
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            # draw a bounding box rectangle and label on the image
            color = [int(c) for c in COLORS[classIDs[i]]]
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
            text = "{}: {:.4f}".format(LABELS[classIDs[i]], confidences[i])
            print(boxes)
            print(classIDs)
            cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            bug_name = LABELS[classIDs[i]]

            if bug_name == "Aciatic leafroller":
                Aciatic_leafroller_Num += 1
            if bug_name == "Oriental fruit moth":
                Oriental_fruit_moth_Num += 1
            if bug_name == "Peach fruit moth":
                Peach_fruit_moth_Num += 1

            data = OrderedDict()
            data["Aciatic leafroller : "] = Aciatic_leafroller_Num
            data["Oriental fruit moth : "] = Oriental_fruit_moth_Num
            data["Peach fruit moth : "] = Peach_fruit_moth_Num
            num_count = data

    return image


saveds_path = mkdir_farm_name()
label_Path = "C:/Users/jhday/python_test/bug.names"
cfg_path = "C:/Users/jhday/python_test/yolov4.cfg"
weights_path = "C:/Users/jhday/python_test/custom-yolov4-detector_last.weights"
lable = take_label(label_Path)
CFG = take_cfg_file(cfg_path)
Weights = take_weights(weights_path)
nets = load_model(CFG, Weights)
Colors = take_random_color(lable)
app = Flask(__name__)


# route http posts to this method
@app.route('/api/test', methods=['POST'])
def main():
    img = request.files["image"].read()
    img = Image.open(io.BytesIO(img))
    npimg = np.array(img)
    image = npimg.copy()
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    cv2.imwrite(saveds_path + Images_saveName() + '.jpg', image)
    res = get_predection(image, nets, lable, Colors)
    image = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
    np_img = Image.fromarray(image)
    img_encoded = image_to_byte_array(np_img)
    cv2.imwrite(saveds_path + Images_saveName_detected() + '.jpg', res)

    with open(saveds_path + Images_saveName_detected() + '.json', 'w', encoding="utf-8") as make_file:
        json.dump(num_count, make_file, ensure_ascii=False, indent="\t")

    return Response(response=img_encoded, status=200, mimetype="image/jpeg")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
