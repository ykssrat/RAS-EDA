#include "./user.h"
#include "cJSON.h"

// Definitions of globals declared in user.h
handle reg_hs[94096];
handle port_hs[2128];
int reglen;
int portlen;
int signal_types[5]={accReg, accModule, accNet, 0, 0};

//黄金执行
extern void recursion(handle top_h, handle var_h);
extern void get_circuit_info(char* filename);
extern void get_golden_value(char* filename);
extern void init_golden_file(char* filename);
//故障执行
extern void init_fault_file(char* filename);
extern void get_fault_value(char* filename);

int flag;
char* clk_name;
char* circuit_info_file;
char* golden_file;
char* fault_file;

void get_config()
{
  FILE* file = fopen(CONFIG_JSON, "r");
  if(file == NULL)
  {
    printf("config.json open failed!\n");
  }
  //获得文件大小
  struct stat statbuf;
  stat(CONFIG_JSON, &statbuf);
  int file_size = statbuf.st_size;
  printf("config.json size=%d\n", file_size);
  //分配内存
  char* jsonstr = (char*)malloc(sizeof(char)*file_size+1);
  memset(jsonstr, 0, file_size+1);
  //保存为字符串
  int size = fread(jsonstr, sizeof(char), file_size, file);
  if(size == 0){
    printf("json to string failed!\n");
  }
  fclose(file);
  //将字符串转换成json指针
  cJSON* root = cJSON_Parse(jsonstr);
  free(jsonstr);
  //解析
  cJSON* item = NULL;
  // item = cJSON_GetObjectItem(root, "top_name");
  // top_name = item->valuestring;
  item = cJSON_GetObjectItem(root, "clk_name");
  clk_name = item->valuestring;
  item = cJSON_GetObjectItem(root, "circuit_info_file");
  circuit_info_file = item->valuestring;
  item = cJSON_GetObjectItem(root, "golden_file");
  golden_file = item->valuestring;
  item = cJSON_GetObjectItem(root, "fault_file");
  fault_file = item->valuestring;
}


int reg_consumer(p_vc_record vc_record){
  switch (vc_record->out_value.logic_value)
  {
    case vcl0:
      if(flag == 0)
        flag = 1;
      else if(flag == 1)
        get_golden_value(golden_file);
      break;
  }
}

int reg_call(int user_data, int reason){
  acc_initialize();

  reglen = 0;
  portlen = 0;
  flag = 0;
  get_config();

  io_printf("[PLI] reg_call start. clk=%s, circuit_info=%s, golden=%s\n", clk_name, circuit_info_file, golden_file);

  //获得模块句柄
  module_h = acc_handle_scope(acc_handle_tfinst());
  //获得时钟句柄
  clk_h = acc_handle_by_name(clk_name, module_h);

  // 获取所有句柄
  recursion(module_h, null);
  get_circuit_info(circuit_info_file);

  //初始化黄金结果文件
  init_golden_file(golden_file);
  //创建时钟consumer历程
  acc_vcl_add(clk_h,reg_consumer,null,vcl_verilog_logic);

  io_printf("[PLI] reg_call done. regs=%d, ports=%d\n", reglen, portlen);

  acc_close();
  return 0;
}



int fault_consumer(p_vc_record vc_record){
  switch (vc_record->out_value.logic_value)
  {
    case vcl0:
      if(flag == 0)
        flag = 1;
      else if(flag == 1)
        get_fault_value(fault_file);
      break;
  }
}

int fault_call(int user_data, int reason){
  acc_initialize();

  reglen = 0;
  portlen = 0;
  flag = 0;
  get_config();

  //获得模块句柄
  module_h = acc_handle_scope(acc_handle_tfinst());
  //获得时钟句柄
  clk_h = acc_handle_by_name(clk_name, module_h);
  //获取所有句柄
  recursion(module_h, null);
  //获取传递参数
  memset(fault_name, 0, sizeof(fault_name));
  strcat((char*)fault_name, acc_fetch_tfarg_str(1));
  io_printf("[PLI] fault_call start. clk=%s, fault=%s, fault_file=%s\n", clk_name, fault_name, fault_file);
  init_fault_file(fault_file);
  //创建时钟consumer历程
  acc_vcl_add(clk_h,fault_consumer,null,vcl_verilog_logic);

  io_printf("[PLI] fault_call done. regs=%d, ports=%d\n", reglen, portlen);

  acc_close();
  return 0;
}



