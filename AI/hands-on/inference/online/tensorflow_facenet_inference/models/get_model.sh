# Copyright 2022 Huawei Technologies Co., Ltd
# CREATED:  2022-12-23 10:00:00
# MODIFIED: 2022-12-23 11:37:18
#!/bin/bash

# Get model from Huawei modelzoo
wget https://modelzoo-train-atc.obs.cn-north-4.myhuaweicloud.com/003_Atc_Models/modelzoo/Official/cv/Facenet_for_ACL.zip --no-check-certificate

#Unzip the model file
unzip Facenet_for_ACL.zip

# Copy tensorflow model weights to /model folder
cp ./Facenet_for_ACL/facenet_tf.pb .

rm -r ./Facenet_for_ACL

rm Facenet_for_ACL.zip

echo "[MODEL] Download done!"