// *******************************************************************************************
// NAME OF MODULE       : Ascend-Sample V.1.0 Model Process Module [Cpp File]                #
// NAME OF FILE         : ModelProcess.cpp                                                   #
// PROGRAMMING LANGUAGE : C++                                                                #
// DATE OF CREATION/MOD : 15 - February - 2022                                               #     
// AUTHOR               : Kubilay TUNA                                                       #
// COMPANY              : Copyright (c) 2022 Huawei Technologies Co., Ltd                    #
//                        https://www.huawei.com/en/                                         #
// PURPOSE/DESCRIPTION  : Provides model processing functions                                #
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

#include "ModelProcess.h"


using namespace std;

ModelProcess::ModelProcess():loadFlag_(false), modelId_(0), modelMemPtr_(nullptr), modelMemSize_(0),
modelWeightPtr_(nullptr),modelWeightSize_(0), modelDesc_(nullptr), input_(nullptr), output_(nullptr),
isReleased_(false){

}

ModelProcess::~ModelProcess() {
    DestroyResource();
}

void ModelProcess::DestroyResource() {
    if (isReleased_)
        return;
    
    Unload();
    DestroyDesc();
    DestroyInput();
    DestroyOutput();
    isReleased_ = true;
}

APP_ERROR ModelProcess::LoadModelFromFileWithMem(const char *modelPath) {
    if (loadFlag_) {
        LogError << "has already loaded a model";
        return APP_ERR_COMM_FAILURE;
    }

    aclError ret = aclmdlQuerySize(modelPath, &modelMemSize_, &modelWeightSize_);
    if (ret != APP_ERR_OK) {
        LogError << "query model failed, model file is " << modelPath;
        return APP_ERR_COMM_FAILURE;
    }

    ret = aclrtMalloc(&modelMemPtr_, modelMemSize_, ACL_MEM_MALLOC_HUGE_FIRST);
    if (ret != APP_ERR_OK) {
        LogError << "malloc buffer for mem failed, require size is " << modelMemSize_;
        return APP_ERR_COMM_FAILURE;
    }

    ret = aclrtMalloc(&modelWeightPtr_, modelWeightSize_, ACL_MEM_MALLOC_HUGE_FIRST);
    if (ret != APP_ERR_OK) {
        LogError << "malloc buffer for weight failed, require size is " << modelWeightSize_;
        return APP_ERR_COMM_FAILURE;
    }

    ret = aclmdlLoadFromFileWithMem(modelPath, &modelId_, modelMemPtr_,
        modelMemSize_, modelWeightPtr_, modelWeightSize_);
    if (ret != APP_ERR_OK) {
        LogError << "load model from file failed, model file is " << modelPath;
        return APP_ERR_COMM_FAILURE;
    }

    loadFlag_ = true;
    LogInfo << "load model %s success", modelPath;
    return APP_ERR_OK;
}

APP_ERROR ModelProcess::CreateDesc(aclmdlIODims *dims)
{
    modelDesc_ = aclmdlCreateDesc();
    if (modelDesc_ == nullptr) {
        LogError << "create model description failed";
        return APP_ERR_COMM_FAILURE;
    }

    aclError ret = aclmdlGetDesc(modelDesc_, modelId_);
    if (ret != APP_ERR_OK) {
        LogError << "get model description failed";
        return APP_ERR_COMM_FAILURE;
    }

    // To Do, there is a bug and if you can fix it, it will have auto resolation seting
    // ret = aclmdlGetInputDims(modelDesc_, 1, dims);
    // if (ret != APP_ERR_OK) {
    //     LogError << "get model input dimension failed";
    //     return APP_ERR_COMM_FAILURE;
    // }

    LogInfo << "create model description success";
    return APP_ERR_OK;
}

void ModelProcess::DestroyDesc()
{
    if (modelDesc_ != nullptr) {
        (void)aclmdlDestroyDesc(modelDesc_);
        modelDesc_ = nullptr;
    }
}

APP_ERROR ModelProcess::CreateInput(void *input1, size_t input1size, 
                                 void* input2, size_t input2size)
{
    input_ = aclmdlCreateDataset();
    if (input_ == nullptr) {
        LogError << "can't create dataset, create input failed";
        return APP_ERR_COMM_FAILURE;
    }

    aclDataBuffer* inputData = aclCreateDataBuffer(input1, input1size);
    if (inputData == nullptr) {
        LogError << "can't create data buffer, create input failed";
        return APP_ERR_COMM_FAILURE;
    }

    aclError ret = aclmdlAddDatasetBuffer(input_, inputData);
    if (inputData == nullptr) {
        LogError << "can't add data buffer, create input failed";
        aclDestroyDataBuffer(inputData);
        inputData = nullptr;
        return APP_ERR_COMM_FAILURE;
    }

    aclDataBuffer* inputData2 = aclCreateDataBuffer(input2, input2size);
    if (inputData == nullptr) {
        LogError << "can't create data buffer, create input failed";
        return APP_ERR_COMM_FAILURE;
    }

    ret = aclmdlAddDatasetBuffer(input_, inputData2);
    if (inputData == nullptr) {
        LogError << "can't add data buffer, create input failed";
        aclDestroyDataBuffer(inputData2);
        inputData = nullptr;
        return APP_ERR_COMM_FAILURE;
    }

    return APP_ERR_OK;
}

void ModelProcess::DestroyInput()
{
    if (input_ == nullptr) {
        return;
    }

    for (size_t i = 0; i < aclmdlGetDatasetNumBuffers(input_); ++i) {
        aclDataBuffer* dataBuffer = aclmdlGetDatasetBuffer(input_, i);
        aclDestroyDataBuffer(dataBuffer);
    }
    aclmdlDestroyDataset(input_);
    input_ = nullptr;
}

APP_ERROR ModelProcess::CreateOutput()
{
    if (modelDesc_ == nullptr) {
        LogError << "no model description, create ouput failed";
        return APP_ERR_COMM_FAILURE;
    }

    output_ = aclmdlCreateDataset();
    if (output_ == nullptr) {
        LogError << "can't create dataset, create output failed";
        return APP_ERR_COMM_FAILURE;
    }

    size_t outputSize = aclmdlGetNumOutputs(modelDesc_);
    for (size_t i = 0; i < outputSize; ++i) {
        size_t buffer_size = aclmdlGetOutputSizeByIndex(modelDesc_, i);

        void *outputBuffer = nullptr;
        aclError ret = aclrtMalloc(&outputBuffer, buffer_size, ACL_MEM_MALLOC_NORMAL_ONLY);
        if (ret != APP_ERR_OK) {
            LogError << "can't malloc buffer, size is " << buffer_size <<  ", create output failed";
            return APP_ERR_COMM_FAILURE;
        }

        aclDataBuffer* outputData = aclCreateDataBuffer(outputBuffer, buffer_size);
        if (ret != APP_ERR_OK) {
            LogError << "can't create data buffer, create output failed";
            aclrtFree(outputBuffer);
            return APP_ERR_COMM_FAILURE;
        }

        ret = aclmdlAddDatasetBuffer(output_, outputData);
        if (ret != APP_ERR_OK) {
            LogError << "can't add data buffer, create output failed";
            aclrtFree(outputBuffer);
            aclDestroyDataBuffer(outputData);
            return APP_ERR_COMM_FAILURE;
        }
    }

    LogInfo << "create model output success";
    return APP_ERR_OK;
}

void ModelProcess::DestroyOutput()
{
    if (output_ == nullptr) {
        return;
    }

    for (size_t i = 0; i < aclmdlGetDatasetNumBuffers(output_); ++i) {
        aclDataBuffer* dataBuffer = aclmdlGetDatasetBuffer(output_, i);
        void* data = aclGetDataBufferAddr(dataBuffer);
        (void)aclrtFree(data);
        (void)aclDestroyDataBuffer(dataBuffer);
    }

    (void)aclmdlDestroyDataset(output_);
    output_ = nullptr;
}

APP_ERROR ModelProcess::Execute()
{
    aclError ret = aclmdlExecute(modelId_, input_, output_);
    if (ret != APP_ERR_OK) {
        LogError << "execute model failed, modelId is " << modelId_;
        return APP_ERR_COMM_FAILURE;
    }

    return APP_ERR_OK;
}

void ModelProcess::Unload()
{
    if (!loadFlag_) {
        LogWarn <<"no model had been loaded, unload failed";
        return;
    }

    aclError ret = aclmdlUnload(modelId_);
    if (ret != APP_ERR_OK) {
        LogError << "unload model failed, modelId is " << modelId_;
    }

    if (modelDesc_ != nullptr) {
        (void)aclmdlDestroyDesc(modelDesc_);
        modelDesc_ = nullptr;
    }

    if (modelMemPtr_ != nullptr) {
        aclrtFree(modelMemPtr_);
        modelMemPtr_ = nullptr;
        modelMemSize_ = 0;
    }

    if (modelWeightPtr_ != nullptr) {
        aclrtFree(modelWeightPtr_);
        modelWeightPtr_ = nullptr;
        modelWeightSize_ = 0;
    }

    loadFlag_ = false;
    LogInfo << "unload model success, modelId is " << modelId_;
}

aclmdlDataset *ModelProcess::GetModelOutputData()
{
    return output_;
}