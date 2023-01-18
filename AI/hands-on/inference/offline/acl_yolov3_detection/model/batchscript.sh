#!/bin/bash
#SBATCH --partition=a800-3000
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --nodes=1
atc --model=yolov3.prototxt --weight=yolov3.caffemodel --framework=0 --output=yolov3 --soc_version=Ascend310 --insert_op_conf=./aipp_yolov3_416_no_csc.cfg 
cd ../src
python3 object_detect.py ../data/
