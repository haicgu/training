# HAICGU Training: MindSpore YOLOv5 COCO NPU Training Example

## Introduction

The goal of this lab is to familiarise with the concepts of AI framework NPU training. For this purpose, a simple training example is considered. Here is the MindSpore YOLOv5 COCO training example.

## Instructions

Load necessary modules.
```bash
module load GCC/9.5.0 OpenMPI/4.1.3  MindSpore/1.6.2-Python-3.7.5
```
Create bash script for slurm.
```bash
cat <<EOF > batchscript.sh
```
Add this scripts.

```bash
#!/bin/bash
#SBATCH --partition=a800-9000
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --nodes=1
npu-smi info
export RANK_SIZE=1
export DEVICE_ID=1
python3 train.py  \
    --device_target="Ascend" \
    --data_dir=/home/share/coco/ \
    --yolov5_version='yolov5s' \
    --is_distributed=0 \
    --lr=0.01 \
    --T_max=320 \
    --max_epoch=320 \
    --warmup_epochs=4 \
    --train_per_batch_size=32
```
You can change training epoch value with changing `max_epoch` flag. Also you need to change this value with editing `default_config.cfg` file.

You can change your NPU device. You should add this export script to your `batchscript.sh` bash command. You should add this before starting training script.
```bash
export DEVICE_ID=1 # For training server = 0-7
```

You can start the training with slurm.
```bash
sbatch batchscript.sh
```

You can check your queue with this command.
```bash
squeue
```
You can check the progress with this command.
[Example] -> (slurm-xxxx.out = slurm-1111.out)
```bash
tail -f slurm-xxxx.out
```
Example output;

```bash
cat slurm-1111.out
```
## Copyright
Huawei Technologies Co., Ltd

## License
Apache License, Version 2.0
