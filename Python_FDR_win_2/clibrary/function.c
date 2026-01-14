#include "./user.h"
#include "./cJSON.h"


//初始化fault文件
void init_fault_file(char* filename){
  cJSON* golden_obj[reglen+portlen];
  cJSON* root = cJSON_CreateObject();
  cJSON* fault = cJSON_CreateObject();
  char* obj_name[200];
  int i = 0;

  for(i=0; i<reglen; i++){
    golden_obj[i] = cJSON_CreateArray();
    cJSON_AddItemToObject(fault, (const char*)acc_fetch_fullname(reg_hs[i]), golden_obj[i]);
  }
  for(i=reglen; i<reglen+portlen; i++){
    golden_obj[i] = cJSON_CreateArray();
    cJSON_AddItemToObject(fault, (const char*)acc_fetch_fullname(port_hs[i-reglen]), golden_obj[i]);
  }

  FILE* file = fopen(filename, "r");
  if(file == NULL)
  {
    //空文件，直接将结果保存在root
    cJSON_AddItemToObject(root, (const char*)fault_name, fault);
  }
  //存在json文件，先读取root，再将结果保存在root
  else
  {
    //获得文件大小
    struct stat statbuf;
    stat(filename, &statbuf);
    int file_size = statbuf.st_size;
    //分配内存
    char* jsonstr = (char*)malloc(sizeof(char) * file_size + 1);
    memset(jsonstr, 0, file_size + 1);
    //读取字符串
    int size = fread(jsonstr, sizeof(char), file_size, file);
    if (size == 0)
    {
      printf("read error!\n");
    } 
    fclose(file);
    //将字符串转换成json指针
    root = cJSON_Parse(jsonstr);
    free(jsonstr);

    cJSON_AddItemToObject(root, (const char*)fault_name, fault);
  }
  //写回json文件
  char* cPrint = cJSON_Print(root);
  file = fopen(filename, "w");
  int ret = fputs(cPrint, file);
  if (ret == EOF) {
    printf("Fault Result Init Failed!");
  }
  fclose(file);
  free(cPrint);
  cJSON_Delete(root);
}

//得到所有fault值文件
void get_fault_value(char* filename){
  int i;
  cJSON* item = NULL;
  cJSON* fault = NULL;

  FILE* file = fopen(filename, "r");
  if (file == NULL) 
  {
    printf("Open File Failed!\n");
  }
  //获得文件大小
  struct stat statbuf;
  stat(filename, &statbuf);
  int file_size = statbuf.st_size;
  //分配内存
  char* jsonstr = (char*)malloc(sizeof(char) * file_size + 1);
  memset(jsonstr, 0, file_size + 1);
  //读取字符串
  int size = fread(jsonstr, sizeof(char), file_size, file);
  if (size == 0)
  {
    printf("read error!\n");
  }
  fclose(file);
  //将字符串转换成json指针
  cJSON* root = cJSON_Parse(jsonstr);
  free(jsonstr);

  //获得fault value并写进json
  for(i=0; i<reglen; i++){
    fault = cJSON_GetObjectItem(root, (const char*)fault_name);
    item = cJSON_GetObjectItem(fault, (const char*)acc_fetch_fullname(reg_hs[i]));
    cJSON_AddItemToArray(item, cJSON_CreateString(acc_fetch_value(reg_hs[i],"%b",null)));
  }
  for(i=0; i<portlen; i++){
    fault = cJSON_GetObjectItem(root, (const char*)fault_name);
    item = cJSON_GetObjectItem(fault, (const char*)acc_fetch_fullname(port_hs[i]));
    cJSON_AddItemToArray(item, cJSON_CreateString(acc_fetch_value(port_hs[i],"%b",null)));
  }

  //写回json文件
  char* cPrint = cJSON_Print(root);
  file = fopen(filename, "w");
  int ret = fputs(cPrint, file);
  if (ret == EOF) {
    printf("Failed!");
  }
  fclose(file);
  free(cPrint);
  cJSON_Delete(root); 
}



//得到所有golden值文件
void get_golden_value(char* filename){
  int i;
  cJSON* item = NULL;

  FILE* file = fopen(filename, "r");
  if (file == NULL) 
  {
    printf("Open File Failed!\n");
  }
  //获得文件大小
  struct stat statbuf;
  stat(filename, &statbuf);
  int file_size = statbuf.st_size;
  //分配内存
  char* jsonstr = (char*)malloc(sizeof(char) * file_size + 1);
  memset(jsonstr, 0, file_size + 1);
  //读取字符串
  int size = fread(jsonstr, sizeof(char), file_size, file);
  if (size == 0)
  {
    printf("read error!\n");
  }
  fclose(file);
  //将字符串转换成json指针
  cJSON* root = cJSON_Parse(jsonstr);
  free(jsonstr);

  //获得golden value并写进json
  for(i=0; i<reglen; i++){
    item = cJSON_GetObjectItem(root, acc_fetch_fullname(reg_hs[i]));
    cJSON_AddItemToArray(item, cJSON_CreateString(acc_fetch_value(reg_hs[i],"%b",null)));
  }
  for(i=0; i<portlen; i++){
    item = cJSON_GetObjectItem(root, acc_fetch_fullname(port_hs[i]));
    cJSON_AddItemToArray(item, cJSON_CreateString(acc_fetch_value(port_hs[i],"%b",null)));
  }

  //写回json文件
  char* cPrint = cJSON_Print(root);
  file = fopen(filename, "w");
  int ret = fputs(cPrint, file);
  if (ret == EOF) {
    printf("Failed!");
  }
  fclose(file);
  free(cPrint);
  cJSON_Delete(root); 
}

//初始化golden文件
void init_golden_file(char* filename){
  cJSON* golden_obj[reglen+portlen];
  cJSON* root = cJSON_CreateObject();
  char* obj_name[200];
  int i = 0;
  for(i=0; i<reglen; i++){
    golden_obj[i] = cJSON_CreateArray();
    cJSON_AddItemToObject(root, acc_fetch_fullname(reg_hs[i]), golden_obj[i]);
  }
  for(i=reglen; i<reglen+portlen; i++){
    golden_obj[i] = cJSON_CreateArray();
    cJSON_AddItemToObject(root, acc_fetch_fullname(port_hs[i-reglen]), golden_obj[i]);
  }
  char* cPrint = cJSON_Print(root);
  FILE* file = fopen(filename, "w");
  int ret = fputs(cPrint, file);
  if (ret == EOF) {
    io_printf("Golden Result Write Failed!");
  }
  fclose(file);
  free(cPrint);
  cJSON_Delete(root);
}

//得到电路内部信息,故障注入reg，输出端口
void get_circuit_info(char* filename){
  int i, j;
  int obj_size, msb, lsb;
  char new_name[200];
  //根节点字典
  cJSON* root = cJSON_CreateObject();
  //子列表
  cJSON* reg_list = cJSON_CreateArray();
  cJSON* port_list = cJSON_CreateArray();
  cJSON* injt_reg_list = cJSON_CreateArray();
  //加入列表元素
  //reg
  for(i=0; i<reglen; i++)
  {
    io_printf("%s\n",acc_fetch_fullname(reg_hs[i]));
    //状态reg
    cJSON_AddItemToArray(reg_list, cJSON_CreateString(acc_fetch_fullname(reg_hs[i])));
    //注入reg
    obj_size = acc_fetch_size(reg_hs[i]);
    if(obj_size >= 2)
    {
        acc_fetch_range(reg_hs[i], &msb, &lsb);
        if(lsb > msb)
        {
          obj_size = lsb;
          lsb = msb;
          msb = obj_size;
        }
        for(j = lsb; j<= msb; j++)
        {
          //初始化
          memset(new_name, 0, sizeof(new_name));
          sprintf(new_name, "%s[%d]", acc_fetch_fullname(reg_hs[i]), j);
          cJSON_AddItemToArray(injt_reg_list, cJSON_CreateString(new_name));
        }
    }
    else{
      cJSON_AddItemToArray(injt_reg_list, cJSON_CreateString(acc_fetch_fullname(reg_hs[i])));
    }
  }
  //端口
  for(i=0; i<portlen; i++){
    cJSON_AddItemToArray(port_list, cJSON_CreateString(acc_fetch_fullname(port_hs[i])));
    io_printf("%s\n",acc_fetch_fullname(port_hs[i]));
  }
  //将数据保存在根结点字典中
  cJSON_AddItemToObject(root, "state_reg", reg_list);
  cJSON_AddItemToObject(root, "out_port", port_list);
  cJSON_AddItemToObject(root, "injection_reg", injt_reg_list);
  //转换成数据流
  char* c_root = cJSON_Print(root);
  //写入json文件
  FILE* file = fopen(filename, "w");
  if (file == NULL) {
    printf("Open File Failed!\n");
  }
  int ret = fputs(c_root, file);
  if(ret == EOF) {
      printf("Circuit Info Write Failed!");
  }
  fclose(file);
  free(c_root);
  cJSON_Delete(root);

}


//递归查找句柄
void recursion(handle top_h, handle var_h){
  //使用递归的方式遍历到类型
  handle signal_h = null;
  if(var_h == null)
    var_h = top_h;
  while(signal_h = acc_next(signal_types, var_h, signal_h)){
    int type = acc_fetch_type(signal_h);
    //module类型
    if(type == accModule){
      char *defname = acc_fetch_defname(signal_h);
      int is_dff = 0;
      // 检查是否为触发器单元 (Gate-level heurustics)
      if (defname && (strstr(defname, "DFF") || strstr(defname, "dff") || strstr(defname, "DLY"))) {
          // 在模块内寻找 Q 端口
          handle port_h = acc_handle_by_name("Q", signal_h);
          if (port_h) {
              // 在老版本或某些优化下，acc_handle_hiconn 需作用于端口位
              // 我们先尝试获取端口直接连接的信号
              handle net_h = acc_handle_conn(port_h); 
              if (!net_h) {
                  net_h = acc_handle_hiconn(port_h);
              }
              
              if (net_h) {
                  reg_hs[reglen] = net_h;
                  reglen += 1;
                  io_printf("[PLI] Found DFF cell: %s -> Target net: %s\n", acc_fetch_fullname(signal_h), acc_fetch_fullname(net_h));
                  is_dff = 1;
              } else {
                  // 回退策略：直接获取父模块中同名的 net (常见于扁平化后的网表)
                  io_printf("[PLI] Warning: Could not resolve net for %s.Q, attempting sibling search.\n", acc_fetch_fullname(signal_h));
              }
          }
      }
      // 如果不是 DFF 或者没找到 Q 端口，继续递归
      if (!is_dff) {
          recursion(top_h, signal_h);
      }
    }
    //reg类型
    else if(type == accReg){
      char *name = acc_fetch_name(signal_h);
      // 过滤掉仿真模型内部的 NOTIFIER 等非逻辑寄存器
      if (name && (strstr(name, "NOTIFIER") || strstr(name, "notifier"))) {
          continue;
      }
      
      if(acc_handle_parent(signal_h) != top_h){
        reg_hs[reglen] = signal_h;
        reglen += 1;
        io_printf("[PLI] Found State Register: %s\n", acc_fetch_fullname(signal_h));
      }
    }
    //output
    else if(type == accNet &&
            acc_handle_parent(signal_h) == top_h){
      port_hs[portlen] = signal_h;
      portlen += 1;
      io_printf("[PLI] Found Output Port: %s\n", acc_fetch_fullname(signal_h));
    }
  }
  return;
}


