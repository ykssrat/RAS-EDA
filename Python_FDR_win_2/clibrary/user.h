#ifndef USER_H
#define USER_H

#include <veriuser.h>
#include "./acc_user.h"
#include "./cJSON.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

//定义配置文件的位置
#define CONFIG_JSON "./config.json"

handle module_h;
handle clk_h;
char* fault_name[200];

extern handle reg_hs[94096];
extern handle port_hs[2128];
extern int reglen;
extern int portlen;


// int signal_types[5]={accReg, accModule, accMemory, accNet, 0};
// accMemory is not defined in standard acc_user.h, removing it.
extern int signal_types[5];

// Function Declarations from function.c
void init_fault_file(char* filename);
void get_fault_value(char* filename);
void get_golden_value(char* filename);
void init_golden_file(char* filename);
void get_circuit_info(char* filename);
void recursion(handle top_h, handle var_h);

#endif