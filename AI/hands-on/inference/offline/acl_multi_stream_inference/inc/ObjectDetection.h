// *******************************************************************************************
// NAME OF MODULE       : Ascend-Sample V.1.0 Object Detection Module [Header File]          #
// NAME OF FILE         : ObjectDetection.cpp                                                #
// PROGRAMMING LANGUAGE : C++                                                                #
// DATE OF CREATION/MOD : 15 - February - 2022                                               #     
// AUTHOR               : Kubilay TUNA                                                       #
// COMPANY              : Copyright (c) 2022 Huawei Technologies Co., Ltd                    #
//                        https://www.huawei.com/en/                                         #
// PURPOSE/DESCRIPTION  : Provides preprocessing, model running, postprocessing,             #
//                        processes for object detection                                     #
// LICENSE              : Copyright (c) 2022 Huawei Technologies Co., Ltd                    #
//                        Licensed under the Apache License, Version 2.0 (the "License");    #
//                        you may not use this file except in compliance with the License.   #
//                        You may obtain a copy of the License at                            #
//                                                                                           #
//                        http://www.apache.org/licenses/LICENSE-2.0                         #
//                                                                                           #
//                        Unless required by applicable law or agreed to in writing,         #
//                        software distributed under the License is distributed on an        #
//                        "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,       #
//                        either express or implied. See the License for the specific        #
//                        language governing permissions and limitations under the License.  #
// *******************************************************************************************
#pragma once
#include <memory>
#include <opencv2/opencv.hpp>

#include "opencv2/imgproc/types_c.h"
#include "ModelProcess.h"
#include "FileManager.h"
#include "acl/acl.h"
#include "Utils.h"


using namespace std;


struct Point {
    std::uint32_t x;
    std::uint32_t y;
};

struct DetectionResult {
    Point lt;   //The coordinate of left top point
    Point rb;   //The coordinate of the right bottom point
    std::string result_text;  // Face:xx%
};


/**
* ObjectDetection
*/
class ObjectDetection {
public:
    ObjectDetection();
    ~ObjectDetection();
    //Inference initialization
    APP_ERROR Init(int32_t deviceId, const char *aclCfgPath, const char *modelPath, 
                    const char *namesPath, int modelWidth, int modelHeight);
    //nference frame image preprocessing
    APP_ERROR Preprocess(cv::Mat& frame);
    //Inference frame picture
    APP_ERROR Inference(aclmdlDataset*& inferenceOutput);
    //Inference output post-processing
    APP_ERROR Postprocess(cv::Mat& frame, aclmdlDataset* modelOutput);
    
private:
    //Initializes the ACL resource
    APP_ERROR InitResource(const char *aclCfgPath);
    //Loading reasoning model
    APP_ERROR InitModel(const char* omModelPath);
    APP_ERROR CreateModelInputdDataset();
    //Establish a connection to the Presenter Server
    APP_ERROR OpenPresenterChannel();
    //Get data from model inference output aclmdlDataset to local
    void* GetInferenceOutputItem(uint32_t& itemDataSize,
    aclmdlDataset* inferenceOutput,
    uint32_t idx);
    //Release the requested resources
    void DestroyResource();

private:
    vector<string> labels_; // Labe names vector, default coco names 

    int32_t deviceId_;  //Device ID, default is 0
    ModelProcess model_; //Inference model instance

    uint32_t modelWidth_;   //The input width required by the model
    uint32_t modelHeight_;  //The model requires high input
    uint32_t imageDataSize_; //Model input data size
    void*    imageDataBuf_;      //Model input data cache
    uint32_t imageInfoSize_;
    void*    imageInfoBuf_;
    aclrtRunMode runMode_;   //Run mode, which is whether the current application is running on atlas200DK or AI1

    bool isInited_;     //Initializes the tag to prevent inference instances from being initialized multiple times
};