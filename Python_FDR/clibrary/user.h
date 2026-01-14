#ifndef USER_H
#define USER_H

#include "./veriuser.h"
#include "./acc_user.h"
#include "./vcs_acc_user.h"
#include "./cJSON.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

//定义配置文件的位置
#define CONFIG_JSON "./config/config.json"

handle module_h;
handle clk_h;
char* fault_name[200];

handle reg_hs[94096];
handle port_hs[2128];
int reglen;
int portlen;


int signal_types[5]={accReg, accModule, accMemory, accNet, 0};

#endif