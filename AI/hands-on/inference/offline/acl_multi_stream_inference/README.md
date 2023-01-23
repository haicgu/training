# HAICGU Training: ACL Single Stream Inference

## Introduction
This sample demonstrates how the ACL Single Stream Inference program to use the OpenCV and ACL to perform the yolov3 (caffe) object detection.

## Getting started

### Download video
```bash
cd ./data/video
wget https://obs-9be7.obs.cn-east-2.myhuaweicloud.com/models/YOLOV4_coco_detection_car_video/test_video/test.mp4
```

### Download the pretrained model
```bash
cd ./data/model
wget https://modelzoo-train-atc.obs.cn-north-4.myhuaweicloud.com/003_Atc_Models/AE/ATC%20Model/Yolov3/yolov3.caffemodel 
```

### Load necessary modules
```bash
module load GCC/9.5.0 OpenMPI CANN-Toolkit OpenCV
```

### Create bash script for slurm
```bash
cat <<EOF > batchscript.sh
```
Add this scripts.

```bash
#!/bin/bash
#SBATCH --partition=a800-3000
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --nodes=1

export OPENCV_PATH=$EBROOTOPENCV
atc --model=yolov3.prototxt --weight=yolov3.caffemodel --framework=0 --output=yolov3 --soc_version=Ascend310 --insert_op_conf=./aipp_yolov3_416_no_csc.cfg 
cd ../../
./build.sh
cd dist
./main
EOF
```

You can start the offline inference with slurm.
```bash
sbatch batchscript.sh
```

You can check your queue with this command.
```bash
squeue
```
You can check the progress with this command. 
```bash
tail -f slurm-xxxx.out
```

### Configurations
Configure the device_id, model_path and model input format in `data/config/setup.cfg`

Configure DeviceId
```bash
#chip config
DeviceId = 0 #use the device to run the program
```
Configure ChannelCount
```bash
ChannelCount = 1 # number of video/rts stream
```
Configure stream path
```bash
# stream of video file/rtsp
Stream.ch0 = ./data/video/test3.mp4
```
Configure model input format
```bash
# yolov3 model input width and height
ModelWidth = 416
ModelHeight = 416
```
Configure ModelPath
```bash
# yolov3 model path
ModelPath = ./data/model/yolov3.om
```
Configure NamesPath
```bash
# yolov3 label names path
NamesPath = ./data/config/coco.names
```

## Constraint
Support input format: mp4 or avi

## Result
Print the result on the terminal: fps, position, confidence and label, then write them into log file.
```bash
[INFO] [2022-03-04 09:50:42:683318][ObjectDetection.cpp Postprocess:256] x2 is 1353
[INFO] [2022-03-04 09:50:42:683329][ObjectDetection.cpp Postprocess:257] y2 is 152
[INFO] [2022-03-04 09:50:42:683339][ObjectDetection.cpp Postprocess:258] score is 84
[INFO] [2022-03-04 09:50:42:683349][ObjectDetection.cpp Postprocess:259] label is person 84%
[INFO] [2022-03-04 09:50:42:683381][main.cpp RunDetector:177] FPS : 25.358
[INFO] [2022-03-04 09:50:42:807613][ObjectDetection.cpp Postprocess:254] x1 is 1223
[INFO] [2022-03-04 09:50:42:807655][ObjectDetection.cpp Postprocess:255] y1 is 1
[INFO] [2022-03-04 09:50:42:807667][ObjectDetection.cpp Postprocess:256] x2 is 1351
[INFO] [2022-03-04 09:50:42:807677][ObjectDetection.cpp Postprocess:257] y2 is 152
[INFO] [2022-03-04 09:50:42:807687][ObjectDetection.cpp Postprocess:258] score is 85
[INFO] [2022-03-04 09:50:42:807698][ObjectDetection.cpp Postprocess:259] label is person 85%
[INFO] [2022-03-04 09:50:42:932701][ObjectDetection.cpp Postprocess:254] x1 is 1224
[INFO] [2022-03-04 09:50:42:932734][ObjectDetection.cpp Postprocess:255] y1 is 1
[INFO] [2022-03-04 09:50:42:932746][ObjectDetection.cpp Postprocess:256] x2 is 1350
[INFO] [2022-03-04 09:50:42:932757][ObjectDetection.cpp Postprocess:257] y2 is 152
[INFO] [2022-03-04 09:50:42:932767][ObjectDetection.cpp Postprocess:258] score is 85
[INFO] [2022-03-04 09:50:42:932777][ObjectDetection.cpp Postprocess:259] label is person 85%
```

## Authors
Kubilay Tuna

## Copyright
Huawei Technologies Co., Ltd

## License
Apache License, Version 2.0
