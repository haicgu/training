#!/bin/bash
#SBATCH --partition=a800-3000
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
#SBATCH --nodes=1
npu-smi info
python3 main.py --model_path ./models/facenet_tf.pb --input_tensor_name input:0 --output_tensor_name embeddings:0 --image_path ./facenet_data
