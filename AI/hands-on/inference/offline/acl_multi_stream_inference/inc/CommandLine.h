/*
 * Copyright(C) 2020. Huawei Technologies Co.,Ltd. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef INC_COMMAND_LINE_H
#define INC_COMMAND_LINE_H
#include <unistd.h>

#include "CommandParser.h"
#include "ErrorCode.h"
#include "Log.h"

// parameters of command line
struct CmdParams {
    std::string aclCfg;
    std::string cfg;
    int logLevel;
    bool statEnable;
};

APP_ERROR ParseACommandLine(int argc, const char *argv[], CmdParams &cmdParams)
{
    LogDebug << "Begin to parse and check command line.";
    CommandParser option;

    option.add_option("--sample_command", "", "./main");
    option.add_option("--cfg", "./data/config/setup.cfg", "the config file using for face recognition pipeline.");
    option.add_option("--acl_cfg", "./data/config/acl.json", "the config file using for ACL init.");
    option.add_option("--log_level", "1", "debug level:0-debug, 1-info, 2-warn, 3-error, 4-fatal, 5-off.");

    option.ParseArgs(argc, argv);
    cmdParams.cfg = option.GetStringOption("--cfg");
    cmdParams.aclCfg = option.GetStringOption("--acl_cfg");
    cmdParams.logLevel = option.GetIntOption("--log_level");

    // check invalidity of input parameters
    if (cmdParams.logLevel < AtlasAscendLog::LOG_LEVEL_DEBUG || cmdParams.logLevel > AtlasAscendLog::LOG_LEVEL_NONE) {
        LogError << "Please check invalid parameter --log_level, is not in [" << AtlasAscendLog::LOG_LEVEL_DEBUG \
                 << ", " << AtlasAscendLog::LOG_LEVEL_NONE << "].";
        return APP_ERR_COMM_OUT_OF_RANGE;
    }

    return APP_ERR_OK;
}

void SetLogLevel(int debugLevel)
{
    switch (debugLevel) {
        case AtlasAscendLog::LOG_LEVEL_DEBUG:
            AtlasAscendLog::Log::LogDebugOn();
            break;
        case AtlasAscendLog::LOG_LEVEL_INFO:
            AtlasAscendLog::Log::LogInfoOn();
            break;
        case AtlasAscendLog::LOG_LEVEL_WARN:
            AtlasAscendLog::Log::LogWarnOn();
            break;
        case AtlasAscendLog::LOG_LEVEL_ERROR:
            AtlasAscendLog::Log::LogErrorOn();
            break;
        case AtlasAscendLog::LOG_LEVEL_FATAL:
            AtlasAscendLog::Log::LogFatalOn();
            break;
        case AtlasAscendLog::LOG_LEVEL_NONE:
            AtlasAscendLog::Log::LogAllOff();
            break;
        default:
            break;
    }
}

#endif