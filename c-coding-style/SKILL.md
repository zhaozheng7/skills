---
name: c-coding-style
description: C代码风格规范检查和应用。当用户需要编写C语言代码、检查C代码风格、修复C代码格式、或者需要确保C代码符合华为内部编码规范时使用此skill。触发场景包括：用户明确提到"C语言代码风格"、"华为编码规范"、"代码格式化"，或者用户正在编写/修改C代码文件，或者用户提供C代码要求检查或修复格式。
license: Copyright (c) Huawei Technologies Co., Ltd. 2026. All rights reserved.
---

# C语言代码风格规范

## 概述

本规范定义了C语言代码的编写风格，所有C代码都应严格遵守这些规范以确保代码的一致性和可读性。

**触发场景：**
- 编写新的C语言代码
- 检查现有C代码的风格符合性
- 修复不符合规范的C代码格式
- 用户提到"C风格"、"华为编码规范"、"代码格式化"

## 命名规范

### 函数（小写下划线）

**函数名使用小写+下划线命名（snake_case）：**
- 函数名：`get_data()`, `calculate_sum()`, `parse_config()`

**带模块前缀的函数名：**
- `hisi_get_data()`, `net_calc_packet_size()`, `util_parse_config()`

### 类型定义（大驼峰）

**以下类型使用大驼峰命名（PascalCase）：**
- 结构体类型：`struct UserInfo {}`, `struct DataBuffer {}`
- 枚举类型：`enum ColorType {}`, `enum HttpStatus {}`
- 联合体类型：`union DataContainer {}`
- typedef定义的类型：`typedef uint32_t UserId;`

### 局部变量、参数、字段（小驼峰）

**以下使用小驼峰命名（camelCase）：**
- 局部变量：`int totalCount;`, `char *userName;`
- 函数参数：`void Func(int inputVal, char *bufferPtr)`
- 宏参数：`#define MAX(x, y) ((x) > (y) ? (x) : (y))`
- 结构体字段：`userInfo.name`, `dataBuffer.size`
- 联合体成员：`dataContainer.intValue`

### 全局变量（g前缀+小驼峰）

- 全局变量必须带`g`前缀：`int gGlobalCounter;`, `char *gConfigPath;`

### 宏、枚举值（全大写下划线）

**以下使用全大写+下划线：**
- 宏定义：`#define MAX_SIZE 100`, `#define BUFFER_SIZE 256`
- 枚举值：`enum ColorType { COLOR_RED, COLOR_GREEN, COLOR_BLUE };`

### goto标签（小写下划线）

**goto标签使用小写+下划线命名：**
- `error_handler:`, `cleanup_exit:`, `retry_connect:`

### 函数式宏（全大写或大驼峰）

**函数式宏可以使用以下任一格式：**
- 全大写下划线：`#define CALC_SUM(x, y) ((x) + (y))`
- 大驼峰：`#define CalculateSum(x, y) ((x) + (y))`
- 带模块前缀大驼峰：`#define HisiCalcSum(x, y) ((x) + (y))`

### 常量

**常量命名格式：**
- 全大写下划线：`const int MAX_CONNECTIONS = 100;`
- g前缀小驼峰：`const int gMaxConnections = 100;`

## 注释风格

### 基本格式

- 使用 `/* */` 风格的注释
- 注释符与内容之间必须有1个空格：`/* 这是注释 */`
- 单行注释示例：
  ```c
  /* 获取用户数据 */
  int result = get_user_data();
  ```

### 多行注释

多行注释时，每行的 `*` 需要对齐：

```c
/*
 * 这是多行注释的第一行
 * 这是多行注释的第二行
 * 这是多行注释的第三行
 */
```

### 注释位置

- 注释应位于被注释代码的**上方**
- 注释与代码之间空一行可提高可读性（可选）

```c
/* 计算两个数的和 */
int add(int a, int b)
{
    return a + b;
}
```

### 文件头注释

每个C源文件开头必须包含版权声明：

```c
/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2026. All rights reserved.
 * 文件描述：简要描述此文件的功能
 */
```

## 缩进风格

- **使用Tab字符进行缩进**（不使用空格）
- 每层缩进使用一个Tab

## 大括号风格

### 函数大括号

函数的左大括号**另起一行，放在行首，独占一行**：

```c
int calculate_sum(int a, int b)
{
    return a + b;
}
```

### 单语句不加括号

**当 if、for、while 等控制语句后只有一行语句时，不使用大括号：**

```c
/* 单语句 - 不使用大括号 */
if (condition)
    do_something();

for (int i = 0; i < max; i++)
    process_item(i);

while (is_running)
    process();
```

### 多语句必须加括号

**当控制语句后有多行语句时，必须使用大括号：**

```c
/* 多语句 - 必须使用大括号 */
if (condition) {
    do_something();
    do_another_thing();
} else if (other_condition) {
    do_other_thing();
} else {
    do_default();
}

while (condition) {
    process();
    update();
}

for (int i = 0; i < max; i++) {
    process_item(i);
    update_item(i);
}

do {
    process();
} while (condition);
```

### 右大括号规则

- 右大括号**独占一行**
- 例外：后面紧跟同一语句的剩余部分时

```c
do {
    process();
} while (condition);  /* while跟在同一行 */

if (condition) {
    do_a();
} else {  /* else跟在同一行 */
    do_b();
}

if (condition) {
    do_a();
} else if (other) {  /* else if跟在同一行 */
    do_b();
}

struct Data {
    int value;
    char name[32];
};  /* 分号可以紧跟右大括号 */
```

## 行宽规范

### 基本规则

- **每行最多80个字符**
- **一行只写一条语句**

```c
/* 好的例子 */
int result = calculate_sum(a, b);
int count = get_count();

/* 不好的例子 */
int result = calculate_sum(a, b); int count = get_count();
```

### 换行原则

当语句过长，或换行能提高可读性时：

1. **根据层次或操作符优先级选择断行点**
2. **将未结束的操作符或连接符号留在行末**
3. **新行缩进一层（Tab）**
4. **同类元素对齐（可选）**

```c
/* 按操作符优先级换行 */
if (condition1 && condition2 && condition3 &&
    condition4 && condition5) {
    do_something();
}

/* 函数参数换行 */
long_result = very_long_function_name(parameter_one, parameter_two,
                                      parameter_three, parameter_four);

/* 函数调用换行，缩进对齐 */
result = function_with_long_name(
    first_parameter,
    second_parameter,
    third_parameter
);

/* 字符串拼接 */
char *message = "This is a very long message that needs to be "
                "split across multiple lines for readability";
```

## 空格空行规范

### 空格使用原则

空格应**突出关键字和重要信息**

```c
/* 关键字后加空格 */
if (condition) {        /* if 后有空格 */
while (running) {       /* while 后有空格 */
for (int i = 0; i < n; i++) {  /* for 后有空格 */
return value;           /* return 后有空格 */
sizeof(int);            /* sizeof 后有空格 */

/* 小括号内部不加空格 */
if ((a + b) > 0) {      /* 好 */
if ( ( a + b ) > 0 ) {  /* 不好 */
func(a, b);             /* 好 */
func( a, b );           /* 不好 */
```

### 运算符空格

```c
/* 赋值和二元运算符两边加空格 */
int result = a + b;
if (x == 0) {
    y = x * 2;
}

/* 一元运算符不加空格 */
x++;
--i;
value = *ptr;
flag = !condition;

/* 逗号后加空格 */
func(a, b, c);
```

### 行末不加空格

- 行末不应有空格（空白字符）

### 空行使用

适当使用空行提高可读性：
- 函数之间空1-2行
- 逻辑块之间空1行
- 相关的变量声明后可以空1行

## 使用脚本验证

当需要验证代码是否符合规范时，使用提供的检查脚本：

```bash
python scripts/check_c_style.py <文件或目录路径>
```

脚本会检查：
- 命名规范（函数、变量、宏等）
- 行宽是否超过80字符
- 大括号位置
- 注释格式
- 缩进是否使用Tab

## 修复代码风格

修复现有代码的风格问题：

1. 首先运行检查脚本识别问题
2. 逐项修复发现的问题
3. 修复后再次验证

对于大型代码库，建议逐文件处理，确保每次修改都通过验证。

## 编写新代码

编写新C代码时：
1. 参考本规范中的示例
2. 完成后运行验证脚本
3. 确保所有检查通过

## 常见错误示例

```c
/* 错误1: 函数名使用大驼峰 */
int CalculateSum(int a, int b)    /* 错误 */
{
    return a + b;
}

int calculate_sum(int a, int b)   /* 正确 */
{
    return a + b;
}

/* 错误2: 函数左大括号未另起一行 */
int calculate_sum() {    /* 错误 */
    return 0;
}

int calculate_sum()      /* 正确 */
{
    return 0;
}

/* 错误3: 全局变量缺少g前缀 */
int global_count;        /* 错误 */
int gGlobal_count;       /* 正确 */

/* 错误4: 结构体类型名使用小驼峰 */
struct user_info {};     /* 错误 */
struct UserInfo {};      /* 正确 */

/* 错误5: 单语句if使用大括号 */
if (condition) {         /* 不推荐：单语句不应使用大括号 */
    do_something();
}

if (condition)           /* 正确：单语句不使用大括号 */
    do_something();

/* 错误6: 使用空格缩进 */
void func()
{
    int x;               /* 错误：应该用Tab缩进 */
}

/* 错误7: 注释符后无空格 */
int x;/*这是注释*/       /* 错误 */
int x; /* 这是注释 */    /* 正确 */

/* 错误8: goto标签使用大写 */
ERROR_HANDLER:           /* 错误 */
error_handler:           /* 正确 */

/* 错误9: 行宽超过80字符 */
int result = some_very_long_function_name(with_many, parameters, that, exceed, limit);
```
