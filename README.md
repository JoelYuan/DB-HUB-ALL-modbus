

# Modbus数据采集与分发系统

## 项目简介
这是一个基于Go语言开发的Modbus数据采集与分发系统，支持RTU和TCP两种通信方式，可以同时连接多个Modbus设备，实时采集数据并进行存储、分发。

## 功能特性
- 📡 支持Modbus RTU和TCP两种通信方式
- 📊 实时采集Modbus设备数据（功能码1-6）
- 💾 数据持久化存储到SQLite数据库
- 🌐 Web界面可视化监控
- ⚡ 高性能并发处理
- 🎯 灵活的配置管理

## 使用说明

### 1. 安装与运行

#### 前提条件
- Go 1.18+ 环境
- 串口设备（如果使用RTU模式）
- Modbus设备（RTU或TCP）

#### 编译与运行
```bash
# 克隆项目
git clone <项目地址>
cd DB-HUB-ALL-modbus

# 编译
go build -o modbus-hub.exe

# 运行
./modbus-hub.exe
```

或者直接使用预编译的可执行文件：
```bash
# 运行预编译的可执行文件
./全通道modbus数据存档与派发工具.exe
```

### 2. 配置文件说明

配置文件采用YAML格式，主要包含全局配置和设备列表两部分。

#### 全局配置
```yaml
global:
  poll_interval_ms: 20        # 调度心跳（每设备循环间隔，单位：毫秒）
  retry_times: 3              # 通信失败重试次数
  db_path: data.db            # 数据库文件路径
  web_port: 8080              # Web服务端口
```

#### 设备配置

##### RTU设备配置示例
```yaml
devices:
  - name: water_meter_01      # 设备名称
    type: rtu                 # 设备类型：rtu/tcp
    port: COM1                # 串口端口
    baud: 9600                # 波特率
    slave: 1                  # 从站地址

    # 读操作配置
    read:
      - fc: 4                 # 功能码：4-输入寄存器
        addr: 0               # 起始地址
        tag: register_0000    # 数据标签名
        period_ms: 500        # 读取周期（毫秒）

    # 写操作配置
    write:
      - fc: 5                 # 功能码：5-写线圈
        addr: 0               # 地址
        tag: flag_0001        # 数据标签名（写此标签的当前值）
```

##### TCP设备配置示例
```yaml
devices:
  - name: local_test_tcp      # 设备名称
    type: tcp                 # 设备类型：rtu/tcp
    address: 127.0.0.1:502    # TCP地址和端口
    unit: 1                   # 从站地址

    # 读操作配置
    read:
      - fc: 3                 # 功能码：3-保持寄存器
        addr: 1               # 起始地址
        tag: register_0003    # 数据标签名
        period_ms: 500        # 读取周期（毫秒）

    # 写操作配置
    write:
      - fc: 6                 # 功能码：6-写单寄存器
        addr: 5               # 地址
        tag: register_0001    # 数据标签名
```

### 3. Web界面使用

系统启动后，会自动启动Web服务（默认端口8080），可以通过浏览器访问：
```
http://localhost:8080
```

Web界面功能：
- 设备在线状态监控
- 实时数据查询
- 历史数据查询
- 标签管理

### 4. 数据存储

系统使用SQLite数据库存储数据，数据库文件默认路径为`data.db`。

数据存储特点：
- 每秒保存一次数据差异
- 支持历史数据查询
- 自动创建数据库表结构

### 5. Modbus功能码说明

## Modbus功能码1-6的定义
### 读操作功能码
1. FC1 (读线圈) ：
   - 对应Modbus的**线圈(Coils)**数据区
   - 用于读取数字量输出状态
   - 代码实现： c.client.ReadCoils(addr, qty)
2. FC2 (读离散输入) ：
   - 对应Modbus的**离散输入(Discrete Inputs)**数据区
   - 用于读取数字量输入状态
   - 代码实现： c.client.ReadDiscreteInputs(addr, qty)
3. FC3 (读保持寄存器) ：
   - 对应Modbus的**保持寄存器(Holding Registers)**数据区
   - 用于读取可读写的模拟量数据
   - 代码实现： c.client.ReadHoldingRegisters(addr, qty)
4. FC4 (读输入寄存器) ：
   - 对应Modbus的**输入寄存器(Input Registers)**数据区
   - 用于读取只读的模拟量数据
   - 代码实现： c.client.ReadInputRegisters(addr, qty)
### 写操作功能码
5. FC5 (写单线圈) ：
   - 对应Modbus的**线圈(Coils)**数据区
   - 用于控制数字量输出
   - 代码实现： c.client.WriteSingleCoil(addr, coil)
6. FC6 (写单寄存器) ：
   - 对应Modbus的**保持寄存器(Holding Registers)**数据区
   - 用于设置模拟量输出值
   - 代码实现： c.client.WriteSingleRegister(addr, reg)

## 与Modbus标准的对应关系
Modbus标准确实只有4个基本数据区：
1. Coils (线圈) - 可读写
2. Discrete Inputs (离散输入) - 只读
3. Holding Registers (保持寄存器) - 可读写
4. Input Registers (输入寄存器) - 只读
程序完全遵循了这个标准，功能码1-6分别对应不同数据区的读写操作：
- 线圈 ：FC1(读) + FC5(写)
- 离散输入 ：FC2(读)
- 保持寄存器 ：FC3(读) + FC6(写) + FC16(批量写)
- 输入寄存器 ：FC4(读)

## 常见问题

### Q1: 设备连接失败怎么办？
A: 检查设备连接参数是否正确（端口、波特率、从站地址、IP地址等），确保设备处于正常工作状态。

### Q2: Web界面无法访问？
A: 检查配置文件中的Web端口是否被占用，尝试修改端口号后重启服务。

### Q3: 数据没有保存到数据库？
A: 检查数据库文件路径是否正确，确保程序有写入权限。

### Q4: 如何添加新设备？
A: 在配置文件中添加新的设备配置，然后重启服务。



