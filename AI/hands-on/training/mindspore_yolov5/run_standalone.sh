#!/bin/bash
#SBATCH --partition=a800-9000
#SBATCH --time=10:00:00
#SBATCH --ntasks=1
#SBATCH --nodes=1
npu-smi info
export RANK_SIZE=1
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


#python3 train.py     --device_target="Ascend"     --data_dir=/home/share/coco/     --yolov5_version='yolov5s'     --is_distributed=0     --lr=0.01     --T_max=320     --max_epoch=320     --warmup_epochs=4     --train_per_batch_size=32 
