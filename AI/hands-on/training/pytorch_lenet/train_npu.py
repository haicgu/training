import torch
from torchvision.datasets import mnist
from torchvision.transforms import ToTensor
from torch.utils.data import DataLoader
from torch.nn import CrossEntropyLoss
import torch.multiprocessing as mp
from model import Model

import time
import argparse
import os
import numpy as np
from tqdm import tqdm

def make_data_loader(args, **kwargs):
    
    train_set = mnist.MNIST(root='./datasets', train=True, transform=ToTensor(), download=True)
    train_sampler = None

    if args.multiprocessing_distributed:
        train_sampler = torch.utils.data.distributed.DistributedSampler(train_set)
        train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=False, sampler=train_sampler,**kwargs)
    else: 
        train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True,**kwargs)

    val_set = mnist.MNIST(root='./datasets', train=False, transform=ToTensor(), download=True)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False, **kwargs)

    return train_loader, train_sampler, val_loader

class Trainer(object):
    def __init__(self, args):
        self.args = args
        
        # Define Dataloader
        kwargs = {'num_workers': args.workers, 'pin_memory': True}
        kwargs['drop_last'] = False if args.multiprocessing_distributed else True

        self.train_loader, self.train_sampler, self.val_loader = make_data_loader(args, **kwargs)
        # self.nclass = args.num_classes if args.num_classes else self.nclass

        # Define network
        model = Model()

        if args.is_master_node:
            print(model)

        # Define Optimizer
        optimizer = torch.optim.SGD(model.parameters(), lr=args.lr)

        # Define Criterion
        self.criterion = CrossEntropyLoss().to(args.device)
        self.model, self.optimizer = model, optimizer
        self.model.to(args.device)

    def training(self, epoch):
        if self.args.multiprocessing_distributed:
            self.train_sampler.set_epoch(epoch)

        self.model.train()
        tbar = tqdm(self.train_loader)

        for _, (train_x, train_label) in enumerate(tbar):

            self.optimizer.zero_grad()
            predict_y = self.model(train_x.to(self.args.device, non_blocking=True))
            target = train_label.to(torch.int32).to(self.args.device, non_blocking=True)
            loss = self.criterion(predict_y, target)
            loss.backward()
            self.optimizer.step()

    def validation(self, epoch):
        self.model.eval()
        tbar = tqdm(self.val_loader, desc='\r')
        val_loss = 0.0
        acc = [0.0] * len(self.val_loader)

        for i, sample in enumerate(tbar):
            image, target = sample[0], sample[1]
            with torch.no_grad():
                predict_y = self.model(image.to(self.args.device, non_blocking=True))
            
            target = target.to(torch.int32).to(self.args.device, non_blocking=True)
            loss = self.criterion(predict_y, target)

            val_loss += loss.item()

            pred = np.argmax(predict_y.data.cpu().numpy(), axis=1)
            target = sample[1].numpy()
            batch_size = sample[1].shape[0]

            acc[i] = float(np.sum(pred == target)) / batch_size

        print("Val loss : %.3f Acc :%.3f" % (val_loss, np.sum(acc) / len(self.val_loader)))
        print()

def parse_args():
    
    parser = argparse.ArgumentParser(description="PyTorch LeNet Training")
    parser.add_argument('--workers', type=int, default=4,
                        metavar='N', help='dataloader threads')
    # training hyper params
    parser.add_argument('--epochs', type=int, default=100, metavar='N',
                        help='number of epochs to train (default: auto)')
    parser.add_argument('--start_epoch', type=int, default=0,
                        metavar='N', help='start epochs (default:0)')
    parser.add_argument('--batch-size', type=int, default=None,
                        metavar='N', help='input batch size for \
                                training (default: auto)')
    # optimizer params
    parser.add_argument('--lr', type=float, default=0.01, metavar='LR',
                        help='learning rate (default: auto)')
    # evaluation option
    parser.add_argument('--eval-interval', type=int, default=1,
                        help='evaluuation interval (default: 1)')
    parser.add_argument('--no-val', action='store_true', default=False,
                        help='skip validation during training')
    # mix precision training
    parser.add_argument('--loss-scale-value', default=1024., type=float,
                        help='loss scale using in amp, default -1 means dynamic')
    parser.add_argument('--multiprocessing_distributed', action='store_true',
                        help='Use multi-processing distributed training to'
                             'launch N processes per node, which has N NPUs.'
                             'This is the fastest way to use PyTorch for'
                             'either single node or multi node data parallel'
                             'training')
    parser.add_argument('--device_id', default=0, type=int, help='device id')
    parser.add_argument('--device-list', default='0,1', type=str, help='device id list')
    parser.add_argument('--world-size', default=1, type=int,
                    help='number of nodes for distributed training')
    parser.add_argument('--rank', default=0, type=int,
                    help='node rank for distributed training')

    return parser.parse_args()

def device_id_to_process_device_map(device_list):
    devices = device_list.split(",")
    devices = [int(x) for x in devices]
    devices.sort()

    process_device_map = dict()
    for process_id, device_id in enumerate(devices):
        process_device_map[process_id] = device_id

    return process_device_map

def main_worker(npu, ngpus_per_node, args):
    
    os.environ['MASTER_ADDR'] = '127.0.0.1'
    os.environ['MASTER_PORT'] = '29688'
    args.device_id = args.process_device_map[npu]

    if args.multiprocessing_distributed:
        args.rank = args.rank * ngpus_per_node + npu
        
        torch.distributed.init_process_group(backend='hccl', world_size=args.world_size, rank=args.rank)
    
    args.is_master_node = not args.multiprocessing_distributed or npu == 0
    if args.is_master_node:
        print(args)

    args.device = torch.device(f'npu:{args.device_id}')

    if args.multiprocessing_distributed:
        args.batch_size = int(args.batch_size / args.world_size)
        args.workers = int((args.workers + args.world_size - 1) / args.world_size)

    trainer = Trainer(args)
    if args.multiprocessing_distributed:
        trainer.model = torch.nn.parallel.DistributedDataParallel(trainer.model,
                                        device_ids=[args.device_id])

    if args.is_master_node:
        print('Starting Epoch:', trainer.args.start_epoch)
        print('Total Epoches:', trainer.args.epochs)

    used_time = []
    for epoch in range(trainer.args.start_epoch, trainer.args.epochs):
        t_s = time.time()
        trainer.training(epoch)
        if args.is_master_node:
            used_time.append(time.time() - t_s)
            avg_time = np.average(used_time)
            no_image_per_epoch = args.batch_size * args.world_size * len(trainer.train_loader)
            print("Epoch {}: average s/epoch: {} FPS: {} Images trained: {}".format(epoch, avg_time, no_image_per_epoch/avg_time, no_image_per_epoch))
            trainer.validation(epoch)

def main():

    args = parse_args()
    args.process_device_map = device_id_to_process_device_map(args.device_list)

    if args.multiprocessing_distributed:
        # Since we have ngpus_per_node processes per node, the total world_size
        # needs to be adjusted accordingly
        ngpus_per_node = len(args.process_device_map)
        args.world_size = ngpus_per_node * args.world_size
        # Use torch.multiprocessing.spawn to launch distributed processes: the
        # main_worker process function
        mp.spawn(main_worker, nprocs=ngpus_per_node, args=(ngpus_per_node, args))
    else:
        # Simply call main_worker function
        main_worker(args.device_id, 1, args)

if __name__ == "__main__":
    main()
