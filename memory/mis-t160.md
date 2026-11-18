# MIS-T160 云台工程记忆（开发此工程时先读一次）

## 路径（2026-11-14 起以桥 `/ping` 的 `roots` 为准；明文副本已废弃）
- XH: d:\aMyProject\Project\MIS-T160\XH\mis-t160\ptz_source_code\source_code
- main: d:\aMyProject\Project\MIS-T160\mian\mis-t160\ptz_source_code\source_code
- VSCode 与 Keil 打开的是**同一个真实工程文件**；`D:\plain_view` 不读不写。
  源码读写只经 `python D:\Codebuddy\toolbox\bridge-edit.py`。

## 硬件与量纲
GD32F470VI（hal 用 stm32f429xx，除 DMA 外寄存器兼容）。PAN/TILT 双轴 BLDC。
速度环 10kHz；编码器 mt6835 21bit；POLE_PAIRS=10；ANGLE_RATIO=18.2044；1count=0.000549°，1count/100?s=5.49°/s。
IMU imu5146：标称 500Hz，UART8 PE0-PE1 AF8，921600，DMA 环形接收（512B，Stream6 ch5，实测可用勿改中断）；帧 54B，帧头 BD DB 09，CRC16，解析在 cmd_cfg[9]。约 665 帧/s。
PAN=YAW=gz，TILT=gy；姿态角单位度，加速度 m/s?（静止 az≈-9.78）；yaw 无磁力计缓慢漂移属正常。
速度滤波 α=0.05@10kHz → fc≈80Hz。
IMU 标定（编码器位置导数为基准）：gz*100 与编码器同号同比例（r=0.9951），速度量必须 +gz*100；低速零偏 +0.48 可忽略。调试打印 imu5146_debug_print_task 走 RS485，定版前必须从 main.c 删调用（9600 轮询阻塞主循环，DMA 512B 约 14~19ms 绕圈）。

## VOFA（XH 效果好版，勿回退）
VEL_FEEDBACK_FUSED=0 / VEL_FEEDBACK_GYRO=1；bldc_velocity_loop() 中 PAN current_velocity 覆盖为 (int32)(gyro(YAW)*100)（无滤波），TILT 编码器闭环；编码器/融合路径仅遥测。
通道：ch0=enc_velocity ch1=plan ch2=fuse ch3=target_Uq ch4=target_velocity ch5=gyro*100（判波动看 ch5）。MOTOR_VOFA_ALWAYS=1，10ms/帧。

## PID
velocity_pid_pan：kp=0.7 ki=0.01 kd=0 integral_max/min=±270000 output±4000；position_pid.kp=7.0。TILT 与 stable_* 未动。
回退基线（无等幅摆动）：kp=0.7 ki=0.01 integral±400000。kp 增大（如 3.85）低速/静止等幅摆动，编码器反馈更严重，去滤波减轻。

## 实测基准（目标 25107，匀速段判波动用 ch5 去趋势高频 rms，不能用 σ）
效果好版：gyro 高频 rms 112~122，Uq rms 114~123，Uq 饱和 0~0.5%；差旧版 871/1345/30.8%。改善根因=积分不冲饱和、Uq 不削顶成方波，与滤波/齿槽前馈无关（齿槽方案已否决）。
基准批（1325 帧）：峰峰 4877(19.5%)、p5-p95 2070(8.3%)；阶次 1~71 合计 17.4% → 82.6% 宽带随机；削顶 6.4% 是放大器，剔除削顶帧 p5-p95→4.9%。output_max 抬到 5500 更糟已回退。
日志：ef23f9a9（带滤波新参数）/ b337ce0d（无滤波）=好；1e3a7e35=差旧参数；785d6863=IMU 未就绪 gyro=0 乱晃。上午最初版源码用户自己保存过（纯编码器闭环 ch2=pos_err ch5=current_position integral±200000）。
未验证：低速带载 integral_max=270000 是否够顶负载。

## 未解矛盾（先查）
某批 FROM_IMU=1 数据：位置导数 +24987、ch0(+gz*100) +24933 同号，但 ch5（应为编码器差分）=-24981 反号 → 该批固件与源码不一致。每次分析数据先核对烧录固件与源码一致。

## 2026-11-13/14 稳像抖动专题（XH，装有耳罩）
### 用户确认的三个变量（"以前是正常的"）
后加的防飘（anchor_gain）、IMU 位置偏了一点、稳像环 PID 参数。**凡是"一直存在"的机制都
不能当根因**：dp 公式、kd=100、1/s2、交叉项、500Hz IMU/10kHz 不同步，全部从代码史核实过
从未变过，不能解释"以前正常"。用户明确否定过：IMU 跟 tilt 转、gz 读数坏/被低通、符号反、
输出饱和是根因、重力顺/逆、防飘是根因、装胶水振动、滤波/死区能解决。**不要再提这些。**

### 实测事实
- 现象：水平稳像正常；抬起球头后无论快慢都抖，且单向；球头右转 90° 减弱，转 180° 抖向反转；
  参数调大就抖、调小就不抖；快速小幅晃动一小会后"稳像失效"，继续晃不补偿；抬起来后曾"像退出
  稳像似的溜了"，该段输出满限幅。
- `kd=100` 是量纲锁死的精确抵消点（1 count = 0.01°，`pan_rate = current_velocity/100`，
  `dp = -(gz - pan_rate)`），此时编码器相对转速在速度环误差里恰好抵消，只剩陀螺绝对角速度阻尼。
  `kd=85` 会多出 15·ω_rel 阻尼 → 不抖，但稳态 ω_abs = 0.15·ω_body，**锁定精度只剩 85%**。
- 分离结论（实测）：`kp=3000/kd=85/integral_fast_decay=0.9` 不抖；`kp=6000/kd=100` 抖。
  降 kd 只降幅度、抖动仍在 → kd 不是根因。
- 降 `stable_velocity_pid_pan.ki`（0.005→0.0005）+ 加大 `output_max`（→5200）"不慌了"，
  但**稳像效果变差**（速度环积分是唯一提供直流刚度/顶重力矩的地方）。静止帧反推约需
  `Uq≈1000`、积分 `I≈200000`，内环积分在承重，不能简单加每拍泄漏。
- 数据链：VOFA JustFloat 9×float + 尾 `00 00 80 7F` = 40 B/帧，50 ms/帧（20 Hz）。
  ch0=enc_velocity(编码器路径) ch1=plan ch2=fuse ch3=target_Uq ch4=target_velocity
  ch5=gyro(YAW)×100 ch6=ep ch7=dp ch8=dt。串口 HEX 抓包必须落盘再解析，10 ms 会丢 83%。

### 仍未定论
抖动的根因**没有定论**。唯一能自洽的是"相位裕度不足 + 某个只在抬起/方位角变化时出现的
激励"，但缺一次能切开的实验。下一步若要查：在稳像环里把姿态角 roll/pitch 临时置零，或
按 PAN 方位角分段抓 ch7/ch8，不要再靠改公式猜。

### 已落地的两个确定性修复
1. **手动控只关本轴稳像**（bug）：`bldc_move_steps()` 原只 `bldc_stable_stop(&g_bldc[port])`，
   另一轴仍 `BLDC_STABLE` 且共享 `s_los_target` → 动水平时垂直跟着补偿。修法：手动移动时
   两轴一起挂起稳像，并在 `bldc_positon_plan_loop()` 恢复前检查两轴 `plan_distance == 0`
   （用 `== 0` 而非 `<= 0`，反向位移时 plan_distance 为负会被误判结束）。
   垂直电机在位置模式的响声是正常负载声，不是这个修复造成的。
2. **桥导致 Keil 改动不同步/被回滚**（2026-11-14）：见 tools.md。桥里 mirror 残留 +
   `/read` 无 no-store → 旧内容回灌/不刷新。已删除全部明文副本逻辑、加 stale 写保护与
   no-store、重启验证。

### 当前参数（以盘上源码为准，2026-11-14）
`stable_pid_pan`: kp=7000 ki=0.01 kd=110 Imax=5000 Umax=36000 decay=0.9
`stable_pid_tilt`: kp=6000 kd=135
`stable_velocity_pid_pan`: kp=1.5 ki=0.0005 Imax=520000 Umax=5200 decay=0
`stable_velocity_pid_tilt`: kp=0.9 ki=0.005 Imax=400000 Umax=5000
`anchor_gain=0.2`、`still_move=15`、VOFA 50 ms、ch7=dp ch8=dt。
注意用户常在 Keil Watch 里现场调参（RAM），与盘上文件经常不一致；每次分析先核对烧录版。
