// *******************************************************************************************
// NAME OF MODULE       : Ascend-Sample V.1.0 Model Process Module [Header File]             #
// NAME OF FILE         : ModelProcess.h                                                     #
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
#pragma once
#include <iostream>

#include "Utils.h"
#include "acl/acl.h"


/**
* ModelProcess
*/
class ModelProcess {
public:
    /**
    * @brief Constructor
    */
    ModelProcess();

    /**
    * @brief Destructor
    */
    ~ModelProcess();

    /**
    * @brief load model from file with mem
    * @param [in] modelPath: model path
    * @return result
    */
    APP_ERROR LoadModelFromFileWithMem(const char *modelPath);

    /**
    * @brief release all acl resource
    */
    void DestroyResource();

    /**
    * @brief unload model
    */
    void Unload();

    /**
    * @brief create model desc
    * @return result
    */
    APP_ERROR CreateDesc(aclmdlIODims *dims);

    /**
    * @brief destroy desc
    */
    void DestroyDesc();

    /**
    * @brief create model input
    * @param [in] inputDataBuffer: input buffer
    * @param [in] bufferSize: input buffer size
    * @return result
    */
    APP_ERROR CreateInput(void *input1, size_t input1size,
                       void* input2, size_t input2size);

    /**
    * @brief destroy input resource
    */
    void DestroyInput();

    /**
    * @brief create output buffer
    * @return result
    */
    APP_ERROR CreateOutput();

    /**
    * @brief destroy output resource
    */
    void DestroyOutput();

    /**
    * @brief model execute
    * @return result
    */
    APP_ERROR Execute();

    /**
    * @brief get model output data
    * @return output dataset
    */
    aclmdlDataset *GetModelOutputData();

private:
    bool loadFlag_;  // model load flag
    uint32_t modelId_;
    void *modelMemPtr_;
    size_t modelMemSize_;
    void *modelWeightPtr_;
    size_t modelWeightSize_;
    aclmdlDesc *modelDesc_;
    aclmdlDataset *input_;
    aclmdlDataset *output_;
    bool isReleased_;
};