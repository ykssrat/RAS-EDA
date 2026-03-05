#include "./user.h"
#include "./cJSON.c"


//初始化fault文件
void init_fault_file(char* filename){
  cJSON* golden_obj[reglen+portlen];
  cJSON* root = cJSON_CreateObject();
  cJSON* fault = cJSON_CreateObject();
  char* obj_name[200];
  int i = 0;

  for(i=0; i<reglen; i++){
    golden_obj[i] = cJSON_CreateArray();
    cJSON_AddItemToObject(fault, acc_fetch_fullname(reg_hs[i]), golden_obj[i]);
  }
  for(i=reglen; i<reglen+portlen; i++){
    golden_obj[i] = cJSON_CreateArray();
    cJSON_AddItemToObject(fault, acc_fetch_fullname(port_hs[i-reglen]), golden_obj[i]);
  }

  FILE* file = fopen(filename, "r");
  if(file == NULL)
  {
    //空文件，直接将结果保存在root
    cJSON_AddItemToObject(root, fault_name, fault);
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

    cJSON_AddItemToObject(root, fault_name, fault);
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
    fault = cJSON_GetObjectItem(root, fault_name);
    item = cJSON_GetObjectItem(fault, acc_fetch_fullname(reg_hs[i]));
    cJSON_AddItemToArray(item, cJSON_CreateString(acc_fetch_value(reg_hs[i],"%b",null)));
  }
  for(i=0; i<portlen; i++){
    fault = cJSON_GetObjectItem(root, fault_name);
    item = cJSON_GetObjectItem(fault, acc_fetch_fullname(port_hs[i]));
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
  
  // 尝试读取现有内容，合并 Python 端的 injection_reg
  cJSON* existing_root = NULL;
  FILE* rf = fopen(filename, "r");
  if (rf) {
    fseek(rf, 0, SEEK_END);
    long fsize = ftell(rf);
    fseek(rf, 0, SEEK_SET);
    if (fsize > 2) {
      char* buf = malloc(fsize + 1);
      fread(buf, 1, fsize, rf);
      buf[fsize] = '\0';
      existing_root = cJSON_Parse(buf);
      free(buf);
    }
    fclose(rf);
  }

  //根节点字典
  cJSON* root = cJSON_CreateObject();
  //子列表
  cJSON* reg_list = cJSON_CreateArray();
  cJSON* port_list = cJSON_CreateArray();
  cJSON* injt_reg_list = (existing_root) ? cJSON_DetachItemFromObject(existing_root, "injection_reg") : cJSON_CreateArray();
  
  if (existing_root) cJSON_Delete(existing_root);

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
    //module类型
    if(acc_fetch_type(signal_h) == accModule){
      recursion(top_h, signal_h);
    }
    //reg类型
    else if(acc_fetch_type(signal_h) == accReg &&
            acc_handle_parent(signal_h) != top_h){
      reg_hs[reglen] = signal_h;
      reglen += 1;
      io_printf("%s\n", acc_fetch_fullname(signal_h));
    }
    //output
    else if(acc_fetch_type(signal_h) == accNet &&
            acc_handle_parent(signal_h) == top_h){
      port_hs[portlen] = signal_h;
      portlen += 1;
      io_printf("%s\n", acc_fetch_fullname(signal_h));
    }
  }
  return;
}


