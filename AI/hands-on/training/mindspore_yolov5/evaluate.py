# Copyright 2022 Huawei Technologies Co., Ltd
# CREATED:  2022-11-25 10:12:13
# MODIFIED: 2022-12-05 12:48:45
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""YoloV5 eval"""
import os
import time
import argparse
import datetime
import threading
import numpy as np
import pandas as pd
import mindspore as ms

from glob import glob
from src.yolo import YOLOV5
from tabulate import tabulate
from src.logger import get_logger
from src.util import DetectionEngine
from model_utils.config import config
from src.yolo_dataset import create_yolo_dataset

# only useful for huawei cloud modelarts
from model_utils.moxing_adapter import moxing_wrapper, modelarts_pre_process

# lock object for multi threading opeartions
lock = threading.Lock()
# Loger initialization 
config.logger = get_logger(config.output_dir, 0)

# Loading checkpoint and placing into model. (Model = YOLOV5, File = .ckpt file which selected)
def load_parameters(network, filename):
    config.logger.info("yolov5 checkpoint file: %s"% (filename))
    param_dict = ms.load_checkpoint(filename)
    param_dict_new = {}
    for key, values in param_dict.items():
        if key.startswith('moments.'):
            continue
        elif key.startswith('yolo_network.'):
            param_dict_new[key[13:]] = values
        else:
            param_dict_new[key] = values
    ms.load_param_into_net(network, param_dict_new)
    config.logger.info('load_model %s success'% (filename))


@moxing_wrapper(pre_process=modelarts_pre_process, pre_args=[config])
def run_eval(epoches = 1, network_params=None):
    with lock:
        # locking the evaluation function to avoid conflict of threads
        config.logger.info(f'Eval function is locked . . .')

        # seting network for evaluation
        network, detection, ds, input_shape = network_params
        # Selecting Huawei Ascend Device to run all evaluation process
        config.logger.info(f'Device is {config.eval_device}')
        ms.set_context(mode = ms.GRAPH_MODE, device_target = config.eval_device)

        start_time = time.time()
        
        batch = config.train_per_batch_size
        if network_params==None:
            config.logger.info(f'================= CONFIG MODE ON =================') # Path to files from config file
            # image folder path from config file
            config.eval_img_dir = os.path.join(config.data_dir, config.eval_img_dir)
            config.logger.info(f'[CONFIG FILE] Image Folder Path Obtained from {config.eval_img_dir}')
            # ann_json file path from config file
            config.eval_json_file = os.path.join(config.data_dir, config.eval_json_file)
            config.logger.info(f'[CONFIG FILE] Annotations File Path Obtained from {config.eval_json_file}')
            
            # Network Creation
            config.logger.info('Netwotk is Creating for Current .ckpt Evaluetion')
            dict_version = {'yolov5s': 0, 'yolov5m': 1, 'yolov5l': 2, 'yolov5x': 3}
            # Calling YOLOv5 Model to update weights with selected ckpt file
            network = YOLOV5(is_training = False, version = dict_version[config.yolov5_version])

            batch = config.eval_per_batch_size
            config.logger.info('Dataset Creating')
            ds = create_yolo_dataset(config.eval_img_dir, config.eval_json_file, is_training=False, 
                                batch_size=batch, device_num=1, rank=0, shuffle=False, config=config) 

            # Changing Model Mode Train to False for Inference
            network.set_train(False) 
            # Calling detection engine to test all process
            detection = DetectionEngine(config, config.test_ignore_threshold, only_eval = True)
            # Setting up the input shape of the model
            input_shape = ms.Tensor(tuple(config.eval_img_shape), ms.float32) 

        # Taking ckpt file by looking its extension, otherwise it takes latest one in the folder
        if config.eval_ckpt_file[-4:] == 'ckpt':
            config.logger.info(f'Your .ckpt File is {config.eval_ckpt_file}')
        elif config.eval_ckpt_file[-4:] == 'ndir':
            return config.logger.important_info(f'Your .mindir File is {config.eval_ckpt_file}')
        else:
            config.eval_ckpt_file = sorted(glob(f'{config.eval_ckpt_file}/*.ckpt'), key=os.path.getmtime)[-1]
            config.logger.info(f'Your .ckpt Folder is {config.eval_ckpt_file}')

        if os.path.isfile(config.eval_ckpt_file):
            load_parameters(network, config.eval_ckpt_file)
        else:
            raise FileNotFoundError(f"{config.eval_ckpt_file} is not a filename.")

        config.logger.info(f'Shape of Test File is: {config.eval_img_shape}')
        config.logger.info('Total %d Images to Eval'% (ds.get_dataset_size() * batch))
        
        # INFERENCE EXECUTION PART
        config.logger.info(f'Inference Begins...')
        
        batches_track = 0
        if config.eval_batch_limit == 0:
            config.eval_batch_limit = int(config.dataset_size / batch)
            print(f'Evaluation batch limit set: {config.eval_batch_limit}')
            
        for index, data in enumerate(ds.create_dict_iterator(output_numpy=True, num_epochs=1)):
            image = data["image"]
            image_shape_ = data["image_shape"]
            image_id_ = data["img_id"]

            # Shaping data to corresponding input format
            image = np.concatenate((image[..., ::2, ::2], image[..., 1::2, ::2],
                                    image[..., ::2, 1::2], image[..., 1::2, 1::2]), axis=1)

            # Changing image array into Tensor(Like pytorch Tensor and numpys np.array) and process all
            image = ms.Tensor(image)
            output_big, output_me, output_small = network(image, input_shape)
            output_big = output_big.asnumpy()
            output_me = output_me.asnumpy()
            output_small = output_small.asnumpy()

            # Detection part
            detection.detect([output_small, output_me, output_big], batch, image_shape_, image_id_)
            batches_track += 1

            # Limiting batches to create test result with limited image to process faster
            if batches_track == config.eval_batch_limit and config.eval_batch_limit != 0:
                break

            # Printing process every 10 step with adjusted percentage
            if index % 2 == 0:
                config.logger.info(f'current Process: {index / config.eval_batch_limit * 100:.2f}% done . . .')
        config.logger.important_info(f'Current Process: %100 done!!!')
        
        # Mean Absolute Precision Calculation with outputs. This process took longer than others
        config.logger.info(f'mAP is Calculating... Note: This process may take a while.')
        detection.do_nms_for_results()
        result_file_path = detection.write_result()

        # Getting evaluated result
        config.logger.info('File Path of the Result: %s'% (result_file_path))
        eval_result = detection.get_eval_result()

        # Write output to txt file
        with  open("output.txt", "w") as file:
            file.write(eval_result)
            file.close()

        # Save output as JSON
        config.logger.info('Saving As Json')
        if os.path.exists("./output/evals.json"):
            df = pd.read_json('./output/evals.json')
            new = pd.read_csv('output.txt', names = [f'epoches_{epoches}'], sep=' = ',  header=None, index_col=0)[f'epoches_{epoches}']
            df[f'epoches_{epoches}'] = new.values
            df = df.T
            df.to_json(r'./output/evals.json', orient='index')
        else:
            new = pd.read_csv('./output.txt', names = [f'epoches_{epoches}'], sep=' = ',  header=None, index_col=0).T
            new.to_json(r'./output/evals.json', orient='index')

        # Remove thrash txt file
        if os.path.exists("./output.txt"):
            os.remove("./output.txt")
        config.logger.important_info('Step Saved')

        # Displaying output of the result on terminal
        cost_time = time.time() - start_time
        eval_log_string = '\n================== Eval Result of the Process ==================\n' + eval_result
        config.logger.info(eval_log_string)
        config.logger.important_info('testing cost time %.2f h'% (cost_time / 3600.))

        config.logger.info(f'Eval function is relased . . .')
        
        return new.to_dict()


if __name__ == "__main__":
    run_eval()