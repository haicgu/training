#!/bin/bash
#SBATCH --partition=a800-9000
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --nodes=1
npu-smi info
export RANK_SIZE=1
python3 train_npu.py --epochs 10 --batch-size 64 --device_id 0
