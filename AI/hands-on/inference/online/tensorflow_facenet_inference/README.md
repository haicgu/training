# HAICGU Training: Tensorflow  FaceNet Online Inference

## Introduction
FaceNet is a general-purpose system that can be used for face verification (is it the same person?), recognition (who is this person?), and cluster (how to find similar people?). FaceNet uses a convolutional neural network to map images into Euclidean space. The spatial distance is directly related to the image similarity. The spatial distance between different images of the same person is small, and the spatial distance between images of different persons is large. As long as the mapping is determined, face recognition becomes simple. FaceNet directly uses the loss function of the triplets-based LMNN (large margin nearest neighbor) to train the neural network. The network directly outputs a 512-dimensional vector space. The triples we selected contain two matched face thumbnails and one unmatched face thumbnail. The objective of the loss function is to distinguish positive and negative classes by distance boundary.


## Getting started
Download the pretrained model.

```bash
cd ./models
bash get_model.sh
```

Load necessary modules.
```bash
module load GCC/9.5.0 OpenMPI TensorFlow-CANN/1.15.0
```

Create bash script for slurm.
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
npu-smi info
python3 main.py --model_path ./models/facenet_tf.pb --input_tensor_name input:0 --output_tensor_name embeddings:0 --image_path ./facenet_data
EOF
```

You can start the online inference with slurm.
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
