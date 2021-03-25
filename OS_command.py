import requests
import os


def Images_saveName():
    import datetime
    basename = "image"
    suffix = datetime.datetime.now().strftime("%y%m%d")
    # 제로보드 번호도 파일이름에 지정한다
    filename = "_".join([basename, suffix])

    return filename


os.chdir("C:/Users/jhday/PycharmProjects/Test_03-08/camera_capture_Images")
print(os.getcwd())

# 제로보드에서 바로 넘어온 사진 (이름 변경 필요)
files = {
    # 'image': (Images_saveName() + '.jpg', open(Images_saveName() + '.jpg', 'rb')),
    'image': ('test.jpg', open('test.jpg', 'rb')),
}
response = requests.post('http://localhost:5000/api/test', files=files)
