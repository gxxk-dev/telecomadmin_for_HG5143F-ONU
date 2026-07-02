# telecomadmin_for_HG5143F-ONU
用于 搭载电信官方V4固件的 型号为HG5143F(ONU)的天翼光猫 的 超级密码获取工具

> 如果本项目帮到了你 那么请点亮右上角免费的Star吧 plz~

- 2026-07-03 更新：沟槽的烽火居然发patch静默更新，把 telnet 开启渠道堵上了，遂拆机逆向，似乎挖出了隐藏的调试工具，有时间的话我会再做一版关于 `fh_tool` 的完整分析，如果你很急的话给我发电邮也可以，看到了就会回

# How2Use

## 从 PyPI 直接运行

发布后无需手动安装，直接运行：

```bash
uvx telecomadmin-for-hg5143f-onu
```

脚本会自动探测 default gateway，并尝试从 ARP 表读取网关 MAC。

如果 ARP 表里没有网关 MAC，可以手动指定：

```bash
uvx telecomadmin-for-hg5143f-onu --mac AABBCCDDEEFF
```

如果 default gateway 探测不准，可以手动指定网关 IP：

```bash
uvx telecomadmin-for-hg5143f-onu --ip 192.168.1.1 --mac AABBCCDDEEFF
```

如果需要同时保持 Telnet 打开：

```bash
uvx telecomadmin-for-hg5143f-onu --ip 192.168.1.1 --mac AABBCCDDEEFF --enable-telnet
```

## 从源码运行

1. 确保 光猫型号为HG5143F-ONU 固件版本v4

    > 本项目在软件版本`V4.10.M5001p`的光猫上测试通过.

2. 准备一个 已安装 uv 的 Win10(或更高)/Linux 操作系统
    
3. 克隆仓库：`git clone https://github.com/gxxk-dev/telecomadmin_for_HG5143F-ONU.git`

4. 进入仓库目录并运行：`uv sync`

5. 运行代码获取超管密码：`uv run telecomadmin-for-hg5143f-onu`

    脚本会自动探测 default gateway，并尝试从 ARP 表读取网关 MAC。

    如果 ARP 表里没有网关 MAC，可以手动指定：

    `uv run telecomadmin-for-hg5143f-onu --mac AABBCCDDEEFF`

    如果 default gateway 探测不准，可以手动指定网关 IP：

    `uv run telecomadmin-for-hg5143f-onu --ip 192.168.1.1 --mac AABBCCDDEEFF`

    如果需要同时保持 Telnet 打开：

    `uv run telecomadmin-for-hg5143f-onu --ip 192.168.1.1 --mac AABBCCDDEEFF --enable-telnet`

6. 根据提示信息输入内容并确认以获取密码

7. Done!

# Build & Publish

构建 wheel 和 sdist：

```bash
uv build --clear
```

正式发布到 PyPI：

```bash
UV_PUBLISH_TOKEN='pypi-你的token' uv publish
```

也可以显式传 token：

```bash
uv publish --token 'pypi-你的token'
```

# License

本项目在`AGPL v3.0+`许可下发布 作者`Gxxk`不对因使用此项目导致的任何纠纷/损失承担责任.
