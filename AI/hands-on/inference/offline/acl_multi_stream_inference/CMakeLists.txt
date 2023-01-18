# Copyright (c) Huawei Technologies Co., Ltd. 2022. All rights reserved.
cmake_minimum_required(VERSION 3.5.1)
project(MultiStreamInference)

set(PROJECT_SRC_ROOT ${CMAKE_CURRENT_LIST_DIR})
set(CMAKE_SKIP_BUILD_RPATH True)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJECT_SRC_ROOT}/dist)
add_compile_options(-std=c++11 -fPIE -fstack-protector-all -Werror -Wreturn-type)
add_definitions(-DENABLE_DVPP_INTERFACE)
add_definitions(-DASCEND_MODULE_USE_ACL)

# Check environment variable
if(NOT DEFINED ENV{ASCEND_HOME})
    message(FATAL_ERROR "please define environment variable:ASCEND_HOME")
endif()
if(NOT DEFINED ENV{OPENCV_PATH})
    message(FATAL_ERROR "please define environment variable:OPENCV_PATH")
endif()

# Compatible with the scenario where the Hisilicon version is installed
SET(ASCEND_VERSION "")
if(NOT DEFINED ENV{ASCEND_VERSION})
    message(WARNING "please define environment variable:ASCEND_VERSION")
else()
    SET(ASCEND_VERSION $ENV{ASCEND_VERSION})
endif()

SET(ARCH_PATTERN "")
if(NOT DEFINED ENV{ARCH_PATTERN})
    message(WARNING "please define environment variable:ARCH_PATTERN")
else()
    set(ARCH_PATTERN $ENV{ARCH_PATTERN})
endif()

# Find acllib
set(ACL_INC_DIR $ENV{ASCEND_HOME}/${ASCEND_VERSION}/${ARCH_PATTERN}/acllib/include)

# Find Header
set(HEADER_FILE_DIR
    ${ACL_INC_DIR}
    ${ASCEND_BASE_DIR}
    ${ASCEND_BASE_DIR}/Framework
    ${PROJECT_SRC_ROOT}/inc
    $ENV{OPENCV_PATH}/include/opencv4
)
include_directories(${HEADER_FILE_DIR})

# Find Src
file(GLOB_RECURSE SRC_FILE
    ${PROJECT_SRC_ROOT}/main.cpp
    ${PROJECT_SRC_ROOT}/src/*.cpp
)

set(SOURCE_FILE
    ${SRC_FILE}
    # ${ASCEND_BASE_SRC_FILES}
)

# set the share library directory
set(ACL_LIB_DIR
    $ENV{ASCEND_HOME}/${ASCEND_VERSION}/${ARCH_PATTERN}/acllib/lib64/stub
    $ENV{OPENCV_PATH}/lib
)
link_directories(${ACL_LIB_DIR})

# Set the target executable file
add_executable(main ${SOURCE_FILE})

# set target link libraries
target_link_libraries(main ascendcl pthread opencv_core opencv_imgproc opencv_imgcodecs opencv_videoio)