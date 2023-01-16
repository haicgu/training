# Simplified Kubernetes+Sedna Installation Guide

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

## Sedna Installation
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
Use the YAML files provided and put them in your home folder. Edit `lc.yaml` to use the IP address of your master node (check the YAML file content).

```
cd ~
k create -f kb.yaml
k create -n sedna cm gm-config --from-file=gm-config.yaml
k create -f gm.yaml
k create -f lc.yaml
```

**WARNING:** Stop at this point and check that all the pods are running: `kubectl get pods -A -o wide`.

From here on , continue with the tutorial that can be found at https://github.com/kubeedge/sedna/blob/main/examples/multiedgeinference/pedestrian_tracking/README.md
