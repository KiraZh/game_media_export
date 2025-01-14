# PC 游戏截图（视频）导出工具

## 功能介绍

可以将 PC 端的 steam 游戏截图和视频以及通过 Windows 系统截图（XGP for pc 使用这种截图方法）和视频导出并整理。

## 使用方法

### 路径配置

需要手动修改 `main.py` 中的 `WINDOWS_FOLDER` 以及 `STEAM_USERDATA_PATH`，默认输出位置为脚本运行文件夹的 `out` 文件夹。

### 配置游戏名称

可以使用 `main.py gather` 来收集游戏信息而不实际执行导出，你可以在这一步生成的 `games.json` 对导出时使用的游戏名称进行修改。

运行时，两个模式有不同的策略：

- steam 平台游戏会自动从 steam 网站查询其名称。
- Windows 截图以进程名为名称。

上述配置可以通过修改 `games.json` 文件来进行修改。以《博德之门3》为例，在默认状态下，游戏名称为 "Baldur's Gate 3"，而进程名比较奇怪。

```json
    "steam_games": {
        "1086940": "Baldur's Gate 3",
    },
    "process_to_name": {
        "Baldur's Gate 3 (3840x2160) - (DX11) - (6 + 6 WT)": "Baldur's Gate 3 (3840x2160) - (DX11) - (6 + 6 WT)",
    }
```

在正式导出前，通过将上述 json 修改为以下形式，可以将导出的文件改为中文名称。

```json
    "steam_games": {
        "1086940": "博德之门3",
    },
    "process_to_name": {
        "Baldur's Gate 3 (3840x2160) - (DX11) - (6 + 6 WT)": "博德之门3",
    }
```

### 运行

无输入参数时，会执行导出。每个游戏以游戏名称为文件夹名称，截图保存在 `screenshots` 中，视频保存在 `media` 中。

## TODO

1. 日志功能
2. 更完善的配置功能，不需要再修改代码
3. 更完善的错误处理
4. jxr 转码
