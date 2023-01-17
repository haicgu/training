# Multi-node Kubernetes+KubeEdge+Sedna Installation Guide

In this tutorial, we will install the following:
- Docker
- Kubernetes
- KubeEdge
- Sedna

To complete it, you need two VMs:
- A master VM with with 4 vCPUS, 8GB of RAM, and 100 GB of HD space.
- A worker VM with with 4 vCPUS, 8GB of RAM, and 100 GB of HD space.

Additionally, you need the resources in this repository (YAML files and AI models).


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

## Disable swap
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


## Install Kubeedge on the Master
```
sudo -s
docker run --rm kubeedge/installation-package:v1.12.1 cat /usr/local/bin/keadm > /usr/local/bin/keadm && chmod +x /usr/local/bin/keadm
exit
keadm init --advertise-address=x.x.x.x --profile version=v1.12.1 --kube-config=/home/ubuntu/.kube/config
```

## Install Kubeedge on the Worker
```
sudo -s
docker run --rm kubeedge/installation-package:v1.12.1 cat /usr/local/bin/keadm > /usr/local/bin/keadm && chmod +x /usr/local/bin/keadm
exit
```
Run the following commands:
 - `sudo nano /etc/kubeedge/config/edgecore.yaml`
 - Edit the following lines:
    - Change `cgroupDriver` to `systemd`
    - Enable `edgestream`

Run the following commands:
- `sudo nano /etc/systemd/system/edgecore.service`
- Add the following lines below `"ExecStart"`:
    - `Environment="CHECK_EDGECORE_ENVIRONMENT=false"`

```
sudo systemctl daemon-reload
sudo service edgecore restart
```

## Joining process
On the master, run: `keadm gettoken`

On the worker, use the token as: `keadm join --cloudcore-ipport="THE-EXPOSED-IP":10000 --token=...`


**WARNING:** Stop at this point and check that all the nodes are ready: `kubectl get nodes -A`.

You can also read the kubeedge logs with: sudo journalctl -u edgecore.service -xe

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

From here on , continue with the tutorial that can be found at https://github.com/kubeedge/sedna/blob/main/examples/multiedgeinference/pedestrian_tracking/README.md
