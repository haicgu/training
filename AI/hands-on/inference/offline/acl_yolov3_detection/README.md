# HAICGU Training: PyACL Yolov3 Detection

## Introduction
This example shows how the pyACL Inference program performs using yolov3 (caffe) object detection.

## Getting started

### Download the pretrained model
```bash
cd model
wget https://modelzoo-train-atc.obs.cn-north-4.myhuaweicloud.com/003_Atc_Models/AE/ATC%20Model/Yolov3/yolov3.caffemodel 
```

### Load necessary modules
```bash
module load GCC/9.5.0 OpenMPI CANN-Toolkit
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
atc --model=yolov3.prototxt --weight=yolov3.caffemodel --framework=0 --output=yolov3 --soc_version=Ascend310 --insert_op_conf=./aipp_yolov3_416_no_csc.cfg 
cd ../src
python3 object_detect.py ../data/
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

## Result
After the running is complete, an inferred image is generated in the **out/** directory of the sample project. The comparison is as follows:
![输入图片说明](https://images.gitee.com/uploads/images/2021/1103/150340_e045f400_8070502.png "屏幕截图.png")

## Copyright
Huawei Technologies Co., Ltd

## License
Apache License, Version 2.0