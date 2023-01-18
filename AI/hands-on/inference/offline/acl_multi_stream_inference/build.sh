# Copyright (c) Huawei Technologies Co., Ltd. 2022. All rights reserved.
#!/bin/bash
rm -rf ./dist
path_cur=$(cd `dirname $0`; pwd)
build_type="Release"

function preparePath() {
    rm -rf $1
    mkdir -p $1
    cd $1
}

function build() {
    path_build=$path_cur/build
    preparePath $path_build
    cmake -DCMAKE_BUILD_TYPE=$build_type ..
    make -j
    ret=$?
    cd ..
    return ${ret}
}

# build
build
if [ $? -ne 0 ]; then
    exit 1
fi

# copy config file and model into dist
if [ ! -d dist ]; then
    echo "Build failed, dist directory does not exist."
    exit 1
fi

cp -r ./data ./dist/