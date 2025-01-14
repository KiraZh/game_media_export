from datetime import datetime
from utils import load_json, parse_steam_filename, save_to_json, load_last_run_time, save_last_run_time, parse_windows_filename, copy_and_rename_file
from pathlib import Path
import requests
import os
import sys


WINDOWS_FOLDER = r"C:\Users\USERNAMEE\Videos\Captures"  # 替换为你 Windows 截图路径
STEAM_USERDATA_PATH = r"C:\Program Files (x86)\Steam\userdata\STEAMID"  # 替换为你的 userdata 路径
GAME_INFO_JSON = "./games.json"
OUTPUT_FOLDER = "./out"

# 定义截图和视频的文件扩展名
SCREENSHOT_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.jxr', '.gif'}
VIDEO_EXTENSIONS = {'.webm', '.mp4', '.avi', '.mov', '.mkv'}


def get_configs():
    return load_json("./config.json")


def get_steam_game_name(app_id):
    """
    通过 Steam 官方商店 API 获取游戏名称
    :param app_id: Steam 应用 ID（数字形式的字符串）
    :return: 对应的游戏名称字符串，如果获取失败则返回 "Unknown Game"
    """
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=schinese"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and data.get(app_id, {}).get("success", False):
            return data[app_id]["data"]["name"]
        else:
            return "Unknown Game"
    except Exception as e:
        print(f"获取 App ID {app_id} 的游戏名称时出错：{e}")
        return "Unknown Game"


def get_and_update_steam_game_info():
    if not STEAM_USERDATA_PATH:
        return {}
    game_info = load_json(GAME_INFO_JSON)
    mapping_in_json = game_info["steam_games"]

    path = rf"{STEAM_USERDATA_PATH}\760\remote"
    folder_names = [
        f for f in os.listdir(path)
        if os.path.isdir(os.path.join(path, f)) and f.isdigit()
    ]
    game_ids = set(folder_names)
    new_app_ids = set(game_ids) - set(mapping_in_json.keys())
    if new_app_ids:
        print(f"发现 {len(new_app_ids)} 个新游戏，正在获取名称...")
        for app_id in new_app_ids:
            game_name = get_steam_game_name(app_id)
            mapping_in_json[app_id] = game_name
            print(f"添加新游戏：{app_id} -> {game_name}")
        
        # 更新并保存映射字典到 JSON 文件
        save_to_json(GAME_INFO_JSON, game_info)
        print(f"游戏信息已更新并保存到 {GAME_INFO_JSON}。")
    else:
        print("没有发现新的游戏，无需更新。")
    return mapping_in_json


def export_steam(mappings):
    if not STEAM_USERDATA_PATH:
        return
    input_folder = Path(rf"{STEAM_USERDATA_PATH}\760\remote")
    # 1. 检查输入文件夹是否存在
    if not input_folder.exists() or not input_folder.is_dir():
        print(f"输入文件夹不存在或不是一个文件夹：{input_folder}")
        return
    
    # 2. 创建输出文件夹
    output_folder = Path(OUTPUT_FOLDER)
    output_folder.mkdir(exist_ok=True)

    # 3. 加载上次运行时间
    last_run_time = load_last_run_time("steam_last_run_time")
    print(f"上次运行时间：{last_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
    current_latest_time = last_run_time

    # 4. 开始导出
    for app_id, game_name in mappings.items():
        print(f"处理游戏：{game_name} (App ID: {app_id})")
        game_path = input_folder / app_id
        if not game_path.exists():
            print(f"  路径不存在，跳过：{game_path}")
            continue
        # 处理截图
        screenshots_dir = Path(game_path) / "screenshots"
        if screenshots_dir.exists():
            for file in screenshots_dir.iterdir():
                if file.is_file():
                    timestamp = parse_steam_filename(file.name)
                    if timestamp and timestamp > last_run_time:
                        copy_and_rename_file(file, game_name, timestamp, "screenshots", output_folder)
                        if current_latest_time < timestamp:
                            current_latest_time = timestamp
        # 处理视频
        media_dir = Path(game_path) / "media"
        if media_dir.exists():
            for file in media_dir.iterdir():
                if file.is_file():
                    # 使用文件的修改时间作为时间戳
                    file_mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    if file_mtime > last_run_time:
                        copy_and_rename_file(file, game_name, timestamp, "screenshots", output_folder)
                        if current_latest_time < file_mtime:
                            current_latest_time = file_mtime
    
    # 5. 保存此次运行的最新时间戳
    if current_latest_time > last_run_time:
        save_last_run_time("steam_last_run_time", current_latest_time)
        print(f"脚本运行完成。最新截图时间 {current_latest_time.strftime('%Y-%m-%d %H:%M:%S')} 已保存。")
    else:
        print("没有找到新的截图或视频文件，无需更新最后运行时间。")


def get_and_update_windows_game_info():
    """
    获取和更新 Windows 截图路径中的游戏信息（进程名到游戏名的映射）后返回
    """
    if not WINDOWS_FOLDER:
        return {}
    game_info = load_json(GAME_INFO_JSON)
    mapping_in_json = game_info["process_to_name"]

    input_path = Path(WINDOWS_FOLDER)
    if not input_path.exists() or not input_path.is_dir():
        print(f"输入文件夹不存在或不是一个文件夹：{input_path}")
        return mapping_in_json
    for file in input_path.iterdir():
        if file.is_file():
            game_name, timestamp = parse_windows_filename(file.name)
            if game_name:
                game_name = game_name.strip()
                if game_name not in mapping_in_json:
                    mapping_in_json[game_name] = game_name
            else:
                print(f"无法解析文件 '{file.name}'，跳过。")

    save_to_json(GAME_INFO_JSON, game_info)
    print(f"游戏信息已更新并保存到 {GAME_INFO_JSON}。")
    return mapping_in_json


def export_from_windows(mappings):
    if not WINDOWS_FOLDER:
        return
    # 1. 检查输入文件夹是否存在
    input_folder = Path(WINDOWS_FOLDER)
    if not input_folder.exists() or not input_folder.is_dir():
        print(f"输入文件夹不存在或不是一个文件夹：{input_folder}")
        return
    
    # 2. 创建输出文件夹
    output_folder = Path(OUTPUT_FOLDER)
    output_folder.mkdir(exist_ok=True)

    # 3. 加载上次运行时间
    last_run_time = load_last_run_time("windows_last_run_time")
    print(f"上次运行时间：{last_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
    current_latest_time = last_run_time

    # 4. 遍历输入文件夹中的所有文件
    failed_files = []
    for file in input_folder.iterdir():
        if file.is_file():
            process_name, timestamp = parse_windows_filename(file.name)
            if process_name and timestamp:
                game_name = mappings[process_name.strip()]
                if timestamp > last_run_time:
                    # 判断文件类型
                    ext = file.suffix.lower()
                    if ext in SCREENSHOT_EXTENSIONS:
                        file_type = "screenshots"
                    elif ext in VIDEO_EXTENSIONS:
                        file_type = "media"
                    else:
                        print(f"未知的文件类型：{file.name}，跳过。")
                        continue
                    
                    # 复制并重命名文件
                    copy_and_rename_file(file, game_name, timestamp, file_type, output_folder)
                    
                    # 更新此次运行的最新时间
                    if timestamp > current_latest_time:
                        current_latest_time = timestamp
                else:
                    print(f"文件 '{file.name}' 的时间戳早于或等于上次运行时间，跳过。")
            else:
                print(f"无法解析文件 '{file.name}'，跳过。")
                failed_files.append(file.name)
    
    # 5. 保存此次运行的最新时间戳
    if current_latest_time > last_run_time:
        save_last_run_time("windows_last_run_time", current_latest_time)
        print(f"脚本运行完成。最新截图时间 {current_latest_time.strftime('%Y-%m-%d %H:%M:%S')} 已保存。")
    else:
        print("没有找到新的截图或视频文件，无需更新最后运行时间。")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "gather":
            get_and_update_windows_game_info()
            get_and_update_steam_game_info()
    else:
        mapping = get_and_update_windows_game_info()
        export_from_windows(mapping)
        mapping = get_and_update_steam_game_info()
        export_steam(mapping)