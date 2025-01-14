import re
import os
import json
from datetime import datetime
from pathlib import Path
import shutil

LAST_RUN_FILE = Path("last_run.json")

# 文件名格式为 "<进程名> YYYY_M_D HH_MM_SS.<ext>" 也能匹配连字符
WINDOWS_FILENAME_REGEX = re.compile(
    r"^(?P<game_name>.+?)\s(?P<year>\d{4})[-_](?P<month>\d{1,2})[-_](?P<day>\d{1,2})\s(?P<hour>\d{1,2})[-_](?P<minute>\d{1,2})[-_](?P<second>\d{1,2})\.\w+$"
)
# steam 的文件名格式是 "YYYYMMDDHHMMSS_后缀.扩展名"
STEAM_SCREENSHOT_REGEX = re.compile(r"(\d{14})_.*\.\w+")

def sanitize_filename(name):
    """
    清理文件夹名称，去除非法字符
    :param name: 原始名称
    :return: 清理后的名称
    """
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def load_json(file_path):
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在。")
        return {}
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}")
        return data


def save_to_json(file_path, data):
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在。")
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


def load_last_run_time(section):
    """
    从 JSON 文件加载上次运行的时间戳
    :param section: JSON section
    :return: datetime 对象
    """
    if not LAST_RUN_FILE.exists():
        return datetime.min
    with open(LAST_RUN_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        last_run_time_str = data.get(section)
        if last_run_time_str:
            try:
                return datetime.strptime(last_run_time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return datetime.min
        return datetime.min


def save_last_run_time(section, run_time):
    """
    将当前运行的最新时间戳保存到 JSON 文件，同时保留其他数据
    :param section: JSON section
    :param run_time: datetime 对象
    """
    data = {}
    if LAST_RUN_FILE.exists():
        with open(LAST_RUN_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"警告：无法解析 JSON 文件 {LAST_RUN_FILE}，将重新创建。")
                data = {}
    
    # 更新 last_run_time
    data[section] = run_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 写回文件
    with open(LAST_RUN_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def parse_windows_filename(filename):
    """
    解析文件名，提取游戏名称和时间戳
    :param filename: 文件名
    :return: (游戏名称, datetime 对象) 或 (None, None) 如果解析失败
    """
    match = WINDOWS_FILENAME_REGEX.match(filename)
    if match:
        try:
            game_name = match.group("game_name")
            year = int(match.group("year"))
            month = int(match.group("month"))
            day = int(match.group("day"))
            hour = int(match.group("hour"))
            minute = int(match.group("minute"))
            second = int(match.group("second"))
            timestamp = datetime(year, month, day, hour, minute, second)
            return game_name, timestamp
        except Exception as e:
            print(f"解析文件名 '{filename}' 时出错：{e}")
            return None, None
    else:
        print(f"文件名 '{filename}' 不符合预期格式。")
        return None, None


def parse_steam_filename(filename):
    """
    从截图文件名中解析时间戳
    :param filename: 截图文件名
    :return: datetime 对象，如果解析失败则返回 None
    """
    match = STEAM_SCREENSHOT_REGEX.match(filename)
    if match:
        timestamp_str = match.group(1)  # "YYYYMMDDHHMMSS"
        try:
            return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
        except ValueError:
            return None
    return None


def copy_and_rename_file(file_path, game_name, timestamp, file_type, output_path):
    """
    复制并重命名文件到输出文件夹
    :param file_path: 源文件路径
    :param game_name: 游戏名称
    :param timestamp: datetime 对象
    :param file_type: 'screenshots' 或 'media'
    :param output_path: 输出路径
    """
    # 格式化时间戳为 YYYYMMDDHHMMSS
    timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")
    
    # 定义目标文件夹
    target_game_folder = output_path / sanitize_filename(game_name)
    target_subfolder = target_game_folder / file_type
    target_subfolder.mkdir(parents=True, exist_ok=True)
    
    # 定义新文件名
    new_filename = f"{game_name}_{timestamp_str}{file_path.suffix}"
    target_file_path = target_subfolder / sanitize_filename(new_filename)
    
    # 复制文件
    shutil.copy2(file_path, target_file_path)
    print(f"复制文件: {file_path} -> {target_file_path}")