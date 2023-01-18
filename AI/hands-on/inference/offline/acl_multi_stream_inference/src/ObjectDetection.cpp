// *******************************************************************************************
// NAME OF MODULE       : Ascend-Sample V.1.0 Object Detection Module [Cpp File]             #
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
#include <iostream>
#include <string> 

#include "ObjectDetection.h"


using namespace std;

namespace {
// Inferential output dataset subscript 0 unit is detection box information data
const uint32_t kBBoxDataBufId = 0;
// The unit with subscript 1 is the number of boxes
const uint32_t kBoxNumDataBufId = 1;
// Each field subscript in the box message
enum BBoxIndex { TOPLEFTX = 0, TOPLEFTY, BOTTOMRIGHTX, BOTTOMRIGHTY, SCORE, LABEL };
int num = 0;
}

ObjectDetection::ObjectDetection()
:imageDataBuf_(nullptr), imageInfoBuf_(nullptr), isInited_(false) {}

ObjectDetection::~ObjectDetection() {DestroyResource();}

APP_ERROR ObjectDetection::InitResource(const char *aclCfgPath) {
    // ACL init
    aclError ret = aclInit(aclCfgPath);
    if (ret != APP_ERR_OK) {
        LogError << "Acl init failed";
        return APP_ERR_COMM_FAILURE;
    }
    LogInfo << "Acl init success";

    // open device
    ret = aclrtSetDevice(deviceId_);
    if (ret != APP_ERR_OK) {
        LogError << "Acl open device %d failed", deviceId_;
        return APP_ERR_COMM_FAILURE;
    }
    LogInfo << "Open device %d success", deviceId_;
    // Gets whether the current application is running on host or Device
    ret = aclrtGetRunMode(&runMode_);
    if (ret != APP_ERR_OK) {
        LogError << "acl get run mode failed";
        return APP_ERR_COMM_FAILURE;
    }

    return APP_ERR_OK;
}

APP_ERROR ObjectDetection::InitModel(const char* omModelPath) {
    APP_ERROR ret = model_.LoadModelFromFileWithMem(omModelPath);
    if (ret != APP_ERR_OK) {
        LogError << "execute LoadModelFromFileWithMem failed";
        return APP_ERR_COMM_FAILURE;
    }

    aclmdlIODims *dims;
    ret = model_.CreateDesc(dims);
    // LogInfo << "Model input name --> " << dims->name; 
    if (ret != APP_ERR_OK) {
        LogError << "execute CreateDesc failed";
        return APP_ERR_COMM_FAILURE;
    }

    ret = model_.CreateOutput();
    if (ret != APP_ERR_OK) {
        LogError << "execute CreateOutput failed";
        return APP_ERR_COMM_FAILURE;
    }


    return APP_ERR_OK;
}

APP_ERROR ObjectDetection::CreateModelInputdDataset()
{
    // Request image data memory for input model
    aclError aclRet = aclrtMalloc(&imageDataBuf_, imageDataSize_, ACL_MEM_MALLOC_HUGE_FIRST);
    if (aclRet != APP_ERR_OK) {
        LogError << "malloc device data buffer failed, aclRet is " << aclRet;
        return APP_ERR_COMM_FAILURE;
    }
    // The second input to Yolov3 is the input image width and height parameter
    const float imageInfo[4] = {(float)modelWidth_, (float)modelHeight_,
    (float)modelWidth_, (float)modelHeight_};
    imageInfoSize_ = sizeof(imageInfo);
    if (runMode_ == ACL_HOST)
        imageInfoBuf_ = Utils::CopyDataHostToDevice((void *)imageInfo, imageInfoSize_);
    else
        imageInfoBuf_ = Utils::CopyDataDeviceToDevice((void *)imageInfo, imageInfoSize_);
    if (imageInfoBuf_ == nullptr) {
        LogError << "Copy image info to device failed";
        return APP_ERR_COMM_FAILURE;
    }
    // Use the applied memory to create the model and input dataset. After creation, only update 
    // the memory data for each frame of inference, instead of creating the input dataset every time
    APP_ERROR ret = model_.CreateInput(imageDataBuf_, imageDataSize_,
    imageInfoBuf_, imageInfoSize_);
    if (ret != APP_ERR_OK) {
        LogError << "Create mode input dataset failed";
        return APP_ERR_COMM_FAILURE;
    }

    return APP_ERR_OK;
}

APP_ERROR ObjectDetection::Init(int32_t deviceId, const char *aclCfgPath, const char *modelPath, 
                                const char *namesPath, int modelWidth, int modelHeight) 
{
    modelHeight_ = modelHeight;
    modelWidth_ = modelWidth;
    deviceId_ = deviceId;

    imageDataSize_ = RGBU8_IMAGE_SIZE(modelWidth_, modelHeight_);
    
    // Initializes the ACL resource
    RawData fileData;
    APP_ERROR ret = ReadFile(namesPath, fileData);
    if (ret != APP_ERR_OK) {
        LogError << "Init acl resource failed";
        return APP_ERR_COMM_FAILURE;
    }
    else {
        auto labels = stringstream{(char *)fileData.data.get()};
        for (string label; getline(labels, label, '\n');)
            labels_.push_back(label);
    }
    // If it is already initialized, it is returned
    if (isInited_) {
        LogInfo << "Classify instance is initied already!";
        return APP_ERR_COMM_FAILURE;
    }
    // Initializes the ACL resource
    ret = InitResource(aclCfgPath);
    if (ret != APP_ERR_OK) {
        LogError << "Init acl resource failed";
        return APP_ERR_COMM_FAILURE;
    }
    // Initializes the model management instance
    ret = InitModel(modelPath);
    if (ret != APP_ERR_OK) {
        LogError << "Init model failed";
        return APP_ERR_COMM_FAILURE;
    }
	
    ret = CreateModelInputdDataset();
    if (ret != APP_ERR_OK) {
        LogError << "Create image info buf failed";
        return APP_ERR_COMM_FAILURE;
    }

    isInited_ = true;
    return APP_ERR_OK;
}

APP_ERROR ObjectDetection::Preprocess(cv::Mat& frame) {
    // Scale the frame image to the desired size of the model
    cv::Mat reiszeMat;
    cv::resize(frame, reiszeMat, cv::Size(modelWidth_, modelHeight_));
    if (reiszeMat.empty()) {
        LogError << "Resize image failed";
        return APP_ERR_COMM_FAILURE;
    }
    // Copy the data into the cache of the input dataset
    aclrtMemcpyKind policy = (runMode_ == ACL_HOST)?
                             ACL_MEMCPY_HOST_TO_DEVICE:ACL_MEMCPY_DEVICE_TO_DEVICE;
    aclError ret = aclrtMemcpy(imageDataBuf_, imageDataSize_,
                               reiszeMat.ptr<uint8_t>(), imageDataSize_, policy);
    if (ret != APP_ERR_OK) {
        LogError << "Copy resized image data to device failed.";
        return APP_ERR_COMM_FAILURE;
    }

    return APP_ERR_OK;
}

APP_ERROR ObjectDetection::Inference(aclmdlDataset*& inferenceOutput) {
    // Perform reasoning
    APP_ERROR ret = model_.Execute();
    if (ret != APP_ERR_OK) {
        LogError << "Execute model inference failed";
        return APP_ERR_COMM_FAILURE;
    }
    // Get inference output
    inferenceOutput = model_.GetModelOutputData();

    return APP_ERR_OK;
}

APP_ERROR ObjectDetection::Postprocess(cv::Mat& frame,
                                    aclmdlDataset* modelOutput){
    // Get box information data
    uint32_t dataSize = 0;
    float* detectData = (float*)GetInferenceOutputItem(dataSize, modelOutput,
                                                       kBBoxDataBufId);
    if (detectData == nullptr) return APP_ERR_COMM_FAILURE;
    // Gets the number of boxes
    uint32_t* boxNum = (uint32_t*)GetInferenceOutputItem(dataSize, modelOutput,
                                                         kBoxNumDataBufId);
    if (boxNum == nullptr) return APP_ERR_COMM_FAILURE;

    // Number of boxes The first data is valid
    uint32_t totalBox = boxNum[0];
    //
    float widthScale = (float)(frame.cols) / modelWidth_;
    float heightScale = (float)(frame.rows) / modelHeight_;

    vector<DetectionResult> detectResults;
    for (uint32_t i = 0; i < totalBox; i++) {
        DetectionResult oneResult;
        Point point_lt, point_rb;
        // get the confidence of the detected object. Anything less than 0.8 is considered invalid
        uint32_t score = uint32_t(detectData[totalBox * SCORE + i] * 100);
        if (score < 80) continue;
        // get the frame coordinates and converts them to the coordinates on the original frame
        oneResult.lt.x = detectData[totalBox * TOPLEFTX + i] * widthScale;
        oneResult.lt.y = detectData[totalBox * TOPLEFTY + i] * heightScale;
        oneResult.rb.x = detectData[totalBox * BOTTOMRIGHTX + i] * widthScale;
        oneResult.rb.y = detectData[totalBox * BOTTOMRIGHTY + i] * heightScale;
        // Construct a string that marks the object: object name + confidence
        uint32_t objIndex = (uint32_t)detectData[totalBox * LABEL + i];
        oneResult.result_text = labels_[objIndex] + " " + std::to_string(score) + "%";
        
        cv::Point pt1(oneResult.lt.x, oneResult.lt.y); // top left
        cv::Point pt2(oneResult.rb.x, oneResult.rb.y); // bottom right
        cv::rectangle(frame, pt1, pt2, cv::Scalar(0,0,255));

        string save_target="./data/outputs/frame_" + to_string(num) + ".png";
        cv::imwrite(save_target, frame);

        LogInfo << "x1 is " << oneResult.lt.x;
        LogInfo << "y1 is " << oneResult.lt.y;
        LogInfo << "x2 is " << oneResult.rb.x;
        LogInfo << "y2 is " << oneResult.rb.y;
        LogInfo << "score is " << score;
        LogInfo << "label is " << oneResult.result_text.c_str();

        num++;
    }
    // If it is the host side, the data is copied from the device and 
    // the memory used by the copy is freed
    if (runMode_ == ACL_HOST) {
        delete[]((uint8_t*)detectData);
        delete[]((uint8_t*)boxNum);
    }

    return APP_ERR_OK;
}

void* ObjectDetection::GetInferenceOutputItem(uint32_t& itemDataSize,
                                           aclmdlDataset* inferenceOutput,
                                           uint32_t idx) {

    aclDataBuffer* dataBuffer = aclmdlGetDatasetBuffer(inferenceOutput, idx);
    if (dataBuffer == nullptr) {
        LogError << "Get the " << idx << 
                    "th dataset buffer from model. Inference output failed";
        return nullptr;
    }

    void* dataBufferDev = aclGetDataBufferAddr(dataBuffer);
    if (dataBufferDev == nullptr) {
        LogError << "Get the " << idx << 
                    "th dataset buffer address from model inference output failed.";
        return nullptr;
    }

    size_t bufferSize = aclGetDataBufferSizeV2(dataBuffer);
    if (bufferSize == 0) {
        LogError << "The " << idx << "th dataset buffer size of "
                "model inference output is 0";
        return nullptr;
    }

    void* data = nullptr;
    if (runMode_ == ACL_HOST) {
        data = Utils::CopyDataDeviceToLocal(dataBufferDev, bufferSize);
        if (data == nullptr) {
            LogError << "Copy inference output to host failed";
            return nullptr;
        }
    }
    else {
        data = dataBufferDev;
    }

    itemDataSize = bufferSize;
    return data;
}

void ObjectDetection::DestroyResource()
{
	aclrtFree(imageDataBuf_);
    aclrtFree(imageInfoBuf_);

    // The ACL resource held by the model instance must be released 
    // before the ACL exits or ABORT will be torn down
    model_.DestroyResource();

    aclError ret;
    ret = aclrtResetDevice(deviceId_);
    if (ret != APP_ERR_OK) {
        LogError << "reset device failed";
    }
    LogInfo << "end to reset device is " << deviceId_;

    ret = aclFinalize();
    if (ret != APP_ERR_OK) {
        LogError << "finalize acl failed";
    }
    LogInfo << "end to finalize acl";
}