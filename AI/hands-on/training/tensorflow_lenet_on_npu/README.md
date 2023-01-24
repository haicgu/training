# HAICGU Training: Tensorflow LeNet MNIST NPU Training Example

## Introduction

The goal of this lab is to familiarise with the concepts of AI framework NPU training. For this purpose, a simple training example is considered. Here is the Tensorflow LeNet MNIST training example.


## Instructions

Load necessary modules.
```bash
module load GCC/9.5.0 OpenMPI TensorFlow-CANN/1.15.0
```

Create necessary folders and download dataset.
```bash
bash get_dataset.sh
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
python3 LeNet.py ---data_path ./MNIST
EOF
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
