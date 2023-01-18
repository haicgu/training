// ***********************************************************************************************
// NAME OF MODULE       : Ascend-Sample V.1.0 Main Module [Cpp File]                             #
// NAME OF FILE         : Main.cpp                                                               #
// PROGRAMMING LANGUAGE : C++                                                                    #
// DATE OF CREATION/MOD : 14 - February - 2022                                                   #     
// AUTHOR               : Kubilay TUNA                                                           #
// COMPANY              : Copyright (c) 2022 Huawei Technologies Co., Ltd                        #
//                        https://www.huawei.com/en/                                             #
// PURPOSE/DESCRIPTION  : Provides single stream inference using OpenCV for Yolov3 (caffe) model #
// LICENSE              : Copyright (c) 2022 Huawei Technologies Co., Ltd                        #
//                        Licensed under the Apache License, Version 2.0 (the "License");        #
//                        you may not use this file except in compliance with the License.       #
//                        You may obtain a copy of the License at                                #
//                                                                                               #
//                        http://www.apache.org/licenses/LICENSE-2.0                             #
//                                                                                               #
//                        Unless required by applicable law or agreed to in writing,             #
//                        software distributed under the License is distributed on an            #
//                        "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,           #
//                        either express or implied. See the License for the specific            #
//                        language governing permissions and limitations under the License.      #
// ***********************************************************************************************
#include <iostream>
#include <stdlib.h>
#include <dirent.h>

#include "ObjectDetection.h"
#include "ConfigParser.h"
#include "CommandLine.h"
#include "Log.h"


using namespace std;

namespace {    
string stream;
clock_t deltaTime = 0;
unsigned int frames = 0;
double  frameRate = 30;
double  averageFrameTimeMilliseconds = 33.333;

double clockToMilliseconds(clock_t ticks){
    // units/(units/time) => time (seconds) * 1000 = milliseconds
    return (ticks/(double)CLOCKS_PER_SEC)*1000.0;
}
}

APP_ERROR InitDetector(ObjectDetection &detect, string &cfgPath, string &aclCfgPath)
{
    // parse config file
    ConfigParser configParser;
    APP_ERROR ret = configParser.parse_config(cfgPath);
    if (ret != APP_ERR_OK) {
        LogFatal << "Failed to parse config file << " << cfgPath << ", ret = " << ret << ".";
        return ret;
    }
    // get device id
    std::string itemCfgStr = std::string("DeviceId");
    int deviceId = 0;
    ret = configParser.GetIntValue(itemCfgStr, deviceId);
    if (ret != APP_ERR_OK) {
        LogError << "Failed to parse device id, ret = " << ret << ".";
        return ret;
    }
    else if (deviceId < 0) {
        LogError << "The device id " << deviceId << 
                    " is invalid, please check the configuration in setup.config.";
        return APP_ERR_COMM_INVALID_PARAM;
    }
    // get model path
    itemCfgStr = std::string("ModelPath");
    string modelPath;
    ret = configParser.GetStringValue(itemCfgStr, modelPath);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to parse model path, ret = " << ret << ".";
        return ret;
    }
    // get names file path
    itemCfgStr = std::string("NamesPath");
    string namesPath;
    ret = configParser.GetStringValue(itemCfgStr, namesPath);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to parse model path, ret = " << ret << ".";
        return ret;
    }
    // get stream 
    itemCfgStr = std::string("Stream.ch0");
    ret = configParser.GetStringValue(itemCfgStr, stream);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to parse stream chanel 0, ret = " << ret << ".";
        return ret;
    }
    // get width 
    itemCfgStr = std::string("ModelWidth");
    int modelWidth;
    ret = configParser.GetIntValue(itemCfgStr, modelWidth);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to parse stream chanel 0, ret = " << ret << ".";
        return ret;
    }
    // get model height 
    itemCfgStr = std::string("ModelHeight");
    int modelHeight;
    ret = configParser.GetIntValue(itemCfgStr, modelHeight);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to parse stream chanel 0, ret = " << ret << ".";
        return ret;
    }

    // Initializes the ACL resource for categorical reasoning, 
    // loads the model and requests the memory used for reasoning input
    ret = detect.Init(deviceId, aclCfgPath.c_str(), modelPath.c_str(), 
                    namesPath.c_str(), modelWidth, modelWidth);
    if (ret != APP_ERR_OK) {
        LogError << "Classification Init resource failed";
        return APP_ERR_COMM_FAILURE;
    }
    return APP_ERR_OK;
}

APP_ERROR RunDetector(ObjectDetection &detect)
{
    // Use Opencv to open the video file
    cv::VideoCapture cap(stream);
    if (!cap.isOpened()) {
        LogError <<"Movie open Erro";
        return APP_ERR_COMM_FAILURE;
    }
    else {
        LogInfo << "Total number of frame : " << cap.get(cv::CAP_PROP_FPS);
    }
    // set clock for frame rate calculation
    clock_t current_ticks, delta_ticks;
    clock_t fps = 0;
    // Frame by frame reasoning
    while(1) {
        // get start time
        clock_t beginFrame = clock();

        // Read a frame of an image
        cv::Mat frame;
        if (!cap.read(frame)) {
            LogError << "Video capture return false";
            break;
        }
        // The frame image is preprocessed
        APP_ERROR ret = detect.Preprocess(frame);
        if (ret != APP_ERR_OK) {
            LogError << "Read file " << stream << " failed, continue to read next";
            continue;
        }
        // The preprocessed images are fed into model reasoning and 
        // the reasoning results are obtained
        aclmdlDataset* inferenceOutput = nullptr;
        ret = detect.Inference(inferenceOutput);
        if ((ret != APP_ERR_OK) || (inferenceOutput == nullptr)) {
            LogError << "Inference model inference output data failed";
            return APP_ERR_COMM_FAILURE;
        }
        // Parses the inference output and sends the inference class, location, 
        // confidence, and image to the Presenter Server for display
        ret = detect.Postprocess(frame, inferenceOutput);
        if (ret != APP_ERR_OK) {
            LogError << "Process model inference output data failed";
            return APP_ERR_COMM_FAILURE;
        }
        // get stop time
        clock_t endFrame = clock();
        deltaTime += endFrame - beginFrame;
        frames ++;
        // Get FPS
        if (clockToMilliseconds(deltaTime)>1000.0){ //every second
            frameRate = (double)frames*0.5 +  frameRate*0.5; //more stable
            frames = 0;
            deltaTime -= CLOCKS_PER_SEC;
            averageFrameTimeMilliseconds  = 1000.0/(frameRate==0?0.001:frameRate);
            LogInfo << "FPS : " << frameRate;
        }
    }
    return APP_ERR_OK;
}


int main(int argc, const char *argv[]) {
    CmdParams cmdParams;
    APP_ERROR ret = ParseACommandLine(argc, argv, cmdParams);
    if (ret != APP_ERR_OK) {
        return ret;
    }
    SetLogLevel(cmdParams.logLevel);
    
    ObjectDetection detect;
    // Initialize detector
    InitDetector(detect, cmdParams.cfg, cmdParams.aclCfg);
    // Run detector
    RunDetector(detect);

    LogInfo << "Object detection from stream sccuess";
    return APP_ERR_OK;
}