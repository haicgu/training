# Simplified KubeEdge Installation Guide

Before get started with KubeEdge, You need:

- a VM with 4 vCPUS, 8GB of RAM, and 100 GB of HD space.

It's better If you have two or more VMs, so that you can deploy cloudcore and edgecore on different VMs.This will help you understand edge scenes more clearly.
* * *

## Install Docker

```
sudo apt update
sudo apt install docker.io -y
sudo systemctl enable docker
sudo systemctl status docker
```
* * *
## Install Kubernetes

Here we use `kind` to install Kubernetes.

If you have two or more VMs, only cloud node needs to install Kubernetes.

- Step1: Install kind

```
curl -Lo ./kind "https://kind.sigs.k8s.io/dl/v0.11.1/kind-$(uname)-amd64"
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

- Step2: Install kubectl

```
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

- Step3: Install Kubernetest with kind

```
sudo kind create cluster
```
* * *
## Install KubeEdge

- Step1: Install keadm (install tool to install KubeEdge)

```
wget https://github.com/kubeedge/kubeedge/releases/download/v1.12.1/keadm-v1.12.1-linux-amd64.tar.gz
tar -zxvf keadm-v1.12.1-linux-amd64.tar.gz
sudo cp keadm-v1.12.1-linux-amd64/keadm/keadm /usr/local/bin/keadm
```

- Step2: Deploy cloudcore (on Master Node)

*Note: You need to get public IP of cloud node, make sure edge node can connect cloud node using this IP, and 10000 and 10002 in your cloudcore needs to be accessible for your edge nodes*

```
sudo keadm deprecated init --advertise-address="CloudCore-IP" --kubeedge-version=1.12.1 --kube-config=/root/.kube/config
```

check if cloudcore running successfully:

```
sudo kubectl get all -nkubeedge
```

- Step3: Get token from cloud side (on Master Node)

```
sudo keadm gettoken
```

- Step4: Setup edgecore(on Edge Node)

```
sudo systemctl set-environment CHECK_EDGECORE_ENVIRONMENT="false"
sudo keadm join --cloudcore-ipport="CloudCore-IP:10000" --token=${token} --kubeedge-version=v1.12.1
```

- Step5: Make sure edgecore running successfully

```
sudo kubectl get nodes 
```

If edge node join the matser successfully, you will see your edge node registered in the cluster with `edge` roles.
You can also check the edgecore status with:

```
sudo systemctl status edgecore
```

and view logs of edgecore：

```
sudo journalctl -f -u edgecore
```
* * *
## Deploy a simple pod on edge

On the cloud node, we can apply a pod like:

```
sudo cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx:1.14.2
    ports:
    - containerPort: 80
  nodeSelector:
    "node-role.kubernetes.io/edge": ""
EOF
```

Then you can see the pods is deployed to edge-node successfully.

```
sudo kubectl get pod -owide 
```

On edge node, you can also see the container running in the edge.

```
sudo docker ps 
```
* * *
## Demo for edge autonomy

- Step1: Set iptables rules, Shield 10000 port to cause edge node disconnected.

```
sudo iptables -A INPUT -p tcp --dport 10000 -j DROP
```

- Step2: Stop edgecore

```
sudo systemctl stop edgecore.service
```

- Step3: Kill contailer on edge node

```
sudo docker ps 
sudo docker kill {containerID}
```

- Step4: Start edgecore

```
sudo systemctl start edgecore.service
```

- Step5: Watch the container running again

```
sudo docker ps 
```

- Step6: Cancel iptables rules in step1, wait for edge node re-connect.

```
sudo iptables -L -n --line-number
sudo iptables -D INPUT 1
```