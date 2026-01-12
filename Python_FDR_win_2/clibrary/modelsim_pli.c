#include <veriuser.h>
#include "acc_user.h"

// Include user-specific declarations
#include "user.h"

// 声明外部函数 (在 main.c 中定义)
extern int reg_call(int user_data, int reason);
extern int fault_call(int user_data, int reason);

// 定义系统任务注册表
s_tfcell veriusertfs[] = {
    {usertask, 0, 0, 0, reg_call, 0, "$rungolden"},
    {usertask, 0, 0, 0, fault_call, 0, "$runfault"},
    {0} // 结束标记
};

// ModelSim 需要的初始化函数 (可选，但通常 veriusertfs 就够了)
void init_usertfs() {
    p_tfcell tfcellp;
    tfcellp = veriusertfs;
    while (tfcellp->type) {
        io_printf("Registering system task: %s\n", tfcellp->tfname);
        tfcellp++;
    }
}

// ModelSim/Questasim looks for this array to bootstrap PLI registration
#ifdef _WIN32
__declspec(dllexport) void (*vlog_startup_routines[])() = {
#else
void (*vlog_startup_routines[])() = {
#endif
    init_usertfs,
    0
};
