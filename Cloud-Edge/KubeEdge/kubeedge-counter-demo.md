# Example of Kubeedge-Counter-Demo
## Preparation

Install the following refer to Simplified KubeEdge Installation Guide:
- Docker
- Kubernetes
- KubeEdge

## Step 1 Check the Yaml
Please check the yamls of counter-instance, counter-model and counter-app from [kubedge-counter-demo](https://github.com/kubeedge/examples/tree/master/kubeedge-counter-demo/crds)

## Step 2 Deploy the Mapper of Counter
Deploy the mapper of counter with `kubeedge-pi-counter-app.yaml`.
```
wget https://raw.githubusercontent.com/kubeedge/examples/master/kubeedge-counter-demo/crds/kubeedge-pi-counter-app.yaml 
sed -i "s#kubeedge/#mayday/#" kubeedge-pi-counter-app.yaml
sudo kubectl create -f kubeedge-pi-counter-app.yaml
```

If you get more than one edge node, please just choose one node and set the `nodeSelector` of the mapper.

Now we can check if the mapper has been deployed successfully.
```
sudo kubectl get pod -owide |grep counter
```

## Step 3 Create the Device Model of Counter
Create the Device Model of counter to the cluster with `kubeedge-counter-model.yaml`.
```
sudo kubectl create -f https://raw.githubusercontent.com/kubeedge/examples/master/kubeedge-counter-demo/crds/kubeedge-counter-model.yaml

sudo kubectl get devicemodel counter-model
```

## Step 4 Create the Device Instance of Counter
Create the Device instance of counter to the cluster with `kubeedge-counter-instance.yaml`.

We should download the yaml first.
```
wget https://raw.githubusercontent.com/kubeedge/examples/master/kubeedge-counter-demo/crds/kubeedge-counter-instance.yaml
```

Check your `NodeName` which you want to deploy the device on.
```
sudo kubectl get node

NAME                      STATUS     ROLES                  AGE   VERSION
kubeedge-dev-linux-0002   Ready      agent,edge             21h   v1.22.6-kubeedge-v1.12.1
kubeedge-dev-linux-0006   NotReady   control-plane,master   42d   v1.21.0
```
In this case we choose the node of `kubeedge-dev-linux-0002`

Edit the `kubeedge-counter-instance.yaml` and change the `spec.nodeSelector.nodeSelectorTerms.matchExpressions.values` from `edge-node` to your `NodeName`, which is `kubeedge-dev-linux-0002` in this case.

After setting the `NodeName` of the device instance, we can create the device instance of counter.
``` 
sed -i "s#edge-node#<your edge node name>#" kubeedge-counter-instance.yaml
sudo kubectl create -f kubeedge-counter-instance.yaml
```
Now we can check the device instance of counter.
```
sudo kubectl get device 
or
sudo kubectl get device counter -ojson
```
We can also check the container of counter at edge. Get the ID of the container and follow the logs.
```
sudo docker ps |grep pi-counter-app
sudo docker logs -f {Docker_ID}
```
## Step 5 Turn on the Device Instance of Counter
We can edit the `desired status` and set it to the device instance. In this demo, we can set the `ON/OFF` status of the device.

Edit the `kubeedge-counter-instance.yaml` and change the field of `status.twins.desired.value` from `OFF` to `ON`. Apply the modification and check the device status.
```
sudo kubectl apply -f kubeedge-counter-instance.yaml
sudo kubectl get device counter -ojson
```
We can get that the field of `status.twins.desired.value` has been set to `ON` and the field of `status.twins.reported.value` has got the count result. At the sametime, we can get that the container of counter at edge has been activited.

## Step 6 Turn off the Device Instance of Counter
We can turn off the counter by edit the `desired status` from `ON` to `OFF` and apply the modification.

## Step 7 Delete the Device Instance of Counter
We can delete the device instance and the device model from cluster.
```
sudo kubectl delete device counter
sudo kubectl delete devicemodel counter-model
```
