# Simplified Kubernetes+Sedna Installation Guide

This tutorial is divided in two parts:
1. In **Part 1**, we will install the following:
    - Docker
    - Kubernetes
    - Sedna
2. In **Part 2**, we will run the ReID application.

To complete it, a single VM suffices with 8 vCPUS, 8GB+ of RAM, and 100 GB of HD space.

Additionally, you need the resources in this repository (YAML files and AI models).

# Part 1: Infrastructure Setup

## Install Docker
```
sudo apt update
sudo apt install docker.io -y
sudo systemctl enable docker
sudo systemctl status docker
sudo usermod -aG docker $USER
```

## Install Kubernetes
```
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl
sudo curl -fsSLo /etc/apt/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet=1.22.0-00 kubeadm=1.22.0-00 kubectl=1.22.0-00
sudo apt-mark hold kubelet kubeadm kubectl
```

## Disable swap (required by kubelet)
```
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
sudo service kubelet restart
```

## Init Kubeadm
```
sudo kubeadm init --control-plane-endpoint=MASTER_NODE_IP --upload-certs
```

## CIDR (on master)
```
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.24.5/manifests/tigera-operator.yaml
kubectl apply -f https://docs.projectcalico.org/manifests/calico-typha.yaml
kubectl taint nodes --all node-role.kubernetes.io/master-
```

## K8s Autocompletion

Do the following:
- `sudo apt install nano`
- `nano ~/.bashrc`
- Add the following lines:
```
source <(kubectl completion bash)
alias k=kubectl
complete -F __start_kubectl k
```
- Save and close

**WARNING:** Stop at this point and check that all the pods are running: `kubectl get pods -A -o wide`.

## Install GO and other build tools
```
cd ~
sudo apt-get install build-essential make -y
wget https://go.dev/dl/go1.19.5.linux-amd64.tar.gz
sudo -s
rm -rf /usr/local/go && tar -C /usr/local -xzf go1.19.5.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin (add to .bashrc)
go version
```

## Install Sedna
```
cd ~
git clone https://github.com/kubeedge/sedna.git
cd sedna
k create ns sedna
k create -f build/crds/
k create -f build/gm/rbac/
```

## Build from source
- `nano Makefile`
- Change `IMAGE_TAG ?= v0.3.0` to `IMAGE_TAG ?= v0.5.0`

Then run:
```
make
make kbimage
make gmimage
make lcimage
```

## Deploy Sedna
Use the YAML files in the `res` subfolder and put them in your home folder. Edit `lc.yaml` to use the IP address of your master node (check the YAML file content).

```
cd ~
k create -f kb.yaml
k create -n sedna cm gm-config --from-file=gm-config.yaml
k create -f gm.yaml
k create -f lc.yaml
```

**WARNING:** Stop at this point and check that all the pods are running: `kubectl get pods -A -o wide`.

# Part 2: Application Deployment

From here on, we follow the instructions that can be found here in this Sedna [tutorial](https://github.com/kubeedge/sedna/blob/main/examples/multiedgeinference/pedestrian_tracking/README.md). However, they have been slighlty modified to adapt to this workshop.

## 1. NFS Setup

Using a local NFS allows to easily share folders between pods and the host. Also, it makes straightforward the use of PVs and PVCs which are used in this example to load volumes into the pods. However, there are other options to achieve the same result which you are free to explore.

1. To setup the NFS, run the following commands on a node of your cluster (for simplicity, we will assume that we selected the **master** node):

    ```
    sudo apt-get update && sudo apt-get install -y nfs-kernel-server
    sudo mkdir -p /data/network_shared/reid
    sudo mkdir /data/network_shared/reid/processed
    sudo mkdir /data/network_shared/reid/query
    sudo mkdir /data/network_shared/reid/images
    sudo chmod 1777 /data/network_shared/reid
    sudo bash -c "echo '/data/network_shared/reid *(rw,sync,no_root_squash,subtree_check)' >> /etc/exports"
    sudo exportfs -ra
    sudo showmount -e localhost # the output of this command should be the folders exposed by the NFS
    ```

## 2. PV and PVC

1. Change the server and storage capacity field in the `yaml/pv/reid_volume.yaml` as needed.
2. Run `kubectl create -f yaml/pv/reid_volume.yaml`.
3. Change the storage request field in the `yaml/pvc/reid-volume-claim.yaml` as needed.
4. Run `kubectl create -f yaml/pvc/reid-volume-claim.yaml`.

The VideoAnalytics and ReID jobs will make use of this PVC. The mounting is made so that the directory structure on the host is mirrored in the pods (the path is the same).

## 3. Apache Kafka

1. Edit the YAML files under `yaml/kafka` so that the IP/hostname address match the one of your master node. For a basic deployment, it's enough to have a single replica of Zookeeper and Kafka both running on the same node.
2. Run these commands:
    ```
    kubectl create -f yaml/kafka/kafkabrk.yaml
    kubectl create -f yaml/kafka/kafkasvc.yaml
    kubectl create -f yaml/kafka/zoodeploy.yaml
    kubectl create -f yaml/kafka/zooservice.yaml
    ```
3. Check that Zookeeper and the Kafka broker is healty (check the logs, it should print that the creation of the admin topic is successful).
4. Note down your master node external IP, you will need it later to update a field in two YAML files.
    - If you are running on a single node deployment, the above step is not required as the default service name should be automatically resolvable by all pods using the cluster DNS (*kafka-service*).
    - This step is also not necessary if you are not running kubeedge.

## 4. Application Deployment

First, make sure to copy the AI models to the correct path on the nodes **BEFORE** starting the pods. If you use the resources provided in this workhop:

1. On the node running the VideoAnalytics job, copy `res/yolox.pth` to `"/data/ai_models/object_detection/pedestrians/yolox.pth"`.
2. On the node running the Feature Extraction service, copy `res/m3l.pth` :`"/data/ai_models/m3l/m3l.pth"`.

Then, do the following:
- Run `kubectl create -f yaml/models/model_m3l.yaml`
- Run `kubectl create -f yaml/models/model_detection.yaml`

## 5. Running the application

In this workshop, we will **run everything on the master node** (for simplicity).

Copy the sample video and query images into the NFS folder:
```
sudo cp res/test_video/*.jpg /data/network_shared/reid/query
sudo cp res/test_video/test_video.mp4 /data/network_shared/reid/test_video.mp4
```

Now, let's create the feature extraction service: `kubectl create -f yaml/feature-extraction-service.yaml` and check that it's healhty.

Following, the application workflow is divided in 2 parts: analysis of the video and ReID.

## Workflow: Part 1

1. Modify the env variables in `yaml/video-analytics-job.yaml`:
    - Make sure that the IP in `video_address` is set to `/data/network_shared/reid/test_video.mp4`.
    - We recommend setting the FPS parameter to a small value in the range [1,5] when running on CPU.
2. Create the VideoAnalytics job: `kubectl create -f yaml/video-analytics-job.yaml`
4. If everything was setup correctly, the pod will start the processing of the video and move to the `Succeeded` phase when done.
5. **NOTE**: Keep in mind that, depending on the characteristics of the input video, this steps can take a considerable amount of time to complete especially if you are running on CPU. Moreover, this job will not exit until it receives all the results generated from the feature extraction service. Check the VideoAnalytics job and its logs to check the progress status.

## Workflow: Part 2
1. Modify the env variables in `yaml/reid-job.yaml`:
    - Make sure that `query_image` is a **pipe-separated** list of images matching the content of the `/data/network_shared/reid/query` folder.
2. Create the ReID job: `kubectl create -f yaml/reid-job.yaml`
3. If everything was setup correctly, the pod will start the target search in the frames extracted from the video and move to the `Succeeded` phase when done.
4. Finally, in the folder `/data/network_shared/reid/images` you will find the final results.


# Cleanup

Don't forget to delete the jobs once they are completed:
- `k delete -f multiedgeinference/pedestrian_tracking/yaml/video-analytics-job.yaml`
- `k delete -f multiedgeinference/pedestrian_tracking/yaml/reid-job.yaml`

To also delete the feature extraction service:
- `k delete -f multiedgeinference/pedestrian_tracking/yaml/feature-extraction.yaml`
