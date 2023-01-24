# HAICGU Training: Pytorch LeNet MNIST NPU Training Example

## Introduction

The goal of this lab is to familiarise with the concepts of AI framework NPU training. For this purpose, a simple training example is considered. Here is the Pytorch LeNet MNIST training example.


## Instructions

Install necessarry library.
```bash
pip3 install torchvision==0.2.0
```
Load necessary modules.
```bash
module load GCC/9.5.0 OpenMPI PyTorch-CANN/1.5.0 apex
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
python3 train_npu.py --epochs 1 --batch-size 64 --device_id 3
EOF
```

You can change your NPU device. For this example, you need to change `--device_id` flag.


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

