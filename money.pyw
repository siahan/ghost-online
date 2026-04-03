import os
import glob
import tempfile
import discord
from discord.ext import commands
from PIL import ImageGrab
import asyncio
import datetime
import cv2
import numpy as np
from pynput import keyboard
from pynput.keyboard import Key, Controller
import pyautogui
from concurrent.futures import ThreadPoolExecutor
import configparser
import time
import subprocess
import shutil
import psutil
from typing import Dict, Optional, Tuple, Union
import tkinter as tk
from tkinter import ttk
import threading
import random
import pyperclip
import traceback
from zoneinfo import ZoneInfo


async def _run_sync_in_executor(func, *args, **kwargs):
    """PIL·subprocess·pyautogui 등 동기 호출을 스레드에서 실행 (이벤트 루프 블로킹 완화)."""
    loop = asyncio.get_running_loop()

    def _call():
        return func(*args, **kwargs)

    return await loop.run_in_executor(None, _call)


# 버전 전역변수
version = "1.2.7"  # 커서가 코드수정할때마다 변경

# =============================================================================
# 1. INI 및 상태 전역변수 설정
# =============================================================================

# configparser 객체 생성
config = configparser.ConfigParser()

# settings.ini 파일 경로 (디스코드·모드 등 — 실행 파일과 같은 폴더)
script_dir = os.path.dirname(os.path.abspath(__file__))
image_dir = os.path.join(script_dir, "image")
ini_dir = os.path.join(script_dir, "ini")
settings_file = os.path.join(script_dir, 'settings.ini')
try:
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(ini_dir, exist_ok=True)
except Exception:
    pass


def image_file_path(image_name: str) -> str:
    """템플릿 PNG 경로 (확장자 없는 이름)."""
    return os.path.join(image_dir, f"{image_name}.png")

# settings.ini 파일이 존재하는지 확인 및 생성
if not os.path.isfile(settings_file):
    config['DEFAULT'] = {
        'Token': 'Your Bot Token',
        'ChannelID': 'Your Channel ID',
        'IntegratedChannelID': 'Your Intergrated Channel ID',
        'Channel': '4',
        'Web': 'mgame',  # 기본 웹 설정
        '2pw': 'None',  # 2pw 설정 추가
        'Name': 'None',  # name 설정 추가
        'Id': 'None',  # id 설정 추가
        'Pw': 'None',  # pw 설정 추가
        'Vm': '1',  # vm 설정 추가
        'Grow': 'False',  # grow 설정 추가
        'Delete': 'None',  # delete 설정 추가
        'Language': 'True',  # language 설정 추가
        'Mode': 'cheat',  # cheat|normal|exp
        'Pc': '1',
    }
    with open(settings_file, 'w', encoding='utf-8') as configfile:
        config.write(configfile)

# settings.ini 파일을 읽습니다.
try:
    config.read(settings_file, encoding='utf-8')
except Exception as e:
    # 기본 설정으로 초기화
    config['DEFAULT'] = {
        'Token': 'Your Bot Token',
        'ChannelID': 'Your Channel ID',
        'IntegratedChannelID': 'Your Intergrated Channel ID',
        'Channel': '4',
        'Web': 'mgame',
        '2pw': 'None',
        'Name': 'None',
        'Id': 'None',
        'Pw': 'None',
        'Vm': '1',
        'Grow': 'False',
        'Delete': 'None',
        'Language': 'True',
        'Mode': 'cheat',
        'Pc': '1',
    }
    with open(settings_file, 'w', encoding='utf-8') as configfile:
        config.write(configfile)

# 필수값만 있을 때 기본값 보장
if 'Web' not in config['DEFAULT']:
    config['DEFAULT']['Web'] = 'mgame'
if 'Channel' not in config['DEFAULT']:
    config['DEFAULT']['Channel'] = '4'
if '2pw' not in config['DEFAULT']:
    config['DEFAULT']['2pw'] = 'None'
if 'Name' not in config['DEFAULT']:
    config['DEFAULT']['Name'] = 'None'
if 'Id' not in config['DEFAULT']:
    config['DEFAULT']['Id'] = 'None'
if 'Pw' not in config['DEFAULT']:
    config['DEFAULT']['Pw'] = 'None'
if 'Vm' not in config['DEFAULT']:
    config['DEFAULT']['Vm'] = '1'
if 'Grow' not in config['DEFAULT']:
    config['DEFAULT']['Grow'] = 'False'
if 'Delete' not in config['DEFAULT']:
    config['DEFAULT']['Delete'] = 'None'
if 'Language' not in config['DEFAULT']:
    config['DEFAULT']['Language'] = 'True'
if 'Mode' not in config['DEFAULT']:
    config['DEFAULT']['Mode'] = 'cheat'
    with open(settings_file, 'w', encoding='utf-8') as configfile:
        config.write(configfile)

if 'DayNightEnabled' not in config['DEFAULT']:
    config['DEFAULT']['DayNightEnabled'] = 'True'
if 'OptionIniPath' not in config['DEFAULT']:
    config['DEFAULT']['OptionIniPath'] = r'C:\option.ini'
if 'OptionIniSection' not in config['DEFAULT']:
    config['DEFAULT']['OptionIniSection'] = 'config'
if 'CheatIniNightPath' not in config['DEFAULT']:
    config['DEFAULT']['CheatIniNightPath'] = os.path.join(ini_dir, 'night.ini')
if 'CheatIniDayPath' not in config['DEFAULT']:
    config['DEFAULT']['CheatIniDayPath'] = os.path.join(ini_dir, 'day.ini')
if 'CheatOptionHPath' not in config['DEFAULT']:
    _oh = os.path.join(ini_dir, 'optionH.ini')
    config['DEFAULT']['CheatOptionHPath'] = _oh if os.path.isfile(_oh) else os.path.join(script_dir, 'optionH.ini')
if 'ExpIniPath' not in config['DEFAULT']:
    config['DEFAULT']['ExpIniPath'] = os.path.join(ini_dir, 'exp.ini')
if 'NormalIniPath' not in config['DEFAULT']:
    config['DEFAULT']['NormalIniPath'] = os.path.join(ini_dir, 'normal.ini')
if 'Pc' not in config['DEFAULT']:
    config['DEFAULT']['Pc'] = '1'
if 'CheatActiveProfile' not in config['DEFAULT']:
    config['DEFAULT']['CheatActiveProfile'] = ''

# 설정을 읽습니다.
token = config['DEFAULT']['Token']
channel_id = int(config['DEFAULT']['ChannelID'])
intergrated_channel_id = int(config['DEFAULT']['IntegratedChannelID'])

# 봇 설정
intents = discord.Intents.default()
intents.message_content = True  # 메시지 내용에 접근할 수 있도록 설정
bot = commands.Bot(command_prefix='!', intents=intents)  # 명령어 !설정

# 상태 전역변수: 첫 실행에만 ini에서 불러오고, 이후엔 명령어로만 변경됨
web = config['DEFAULT'].get('Web', 'mgame')
channel = int(config['DEFAULT'].get('Channel', 4))
# 2pw 전역변수 추가
pw2_value = config['DEFAULT'].get('2pw', 'None')
if pw2_value == 'None':
    pw2_value = None
# name 전역변수 추가
name = config['DEFAULT'].get('Name', 'None')
if name == 'None':
    name = None


# id 전역변수 추가
id_value = config['DEFAULT'].get('Id', 'None')
if id_value == 'None':
    id_value = None

# pw 전역변수 추가
pw_value = config['DEFAULT'].get('Pw', 'None')
if pw_value == 'None':
    pw_value = None

# vm 전역변수 추가 (정수형 1~4, 기본 1)
vm_value = config['DEFAULT'].get('Vm', '1')
try:
    vm = int(vm_value)
    if vm < 1 or vm > 4:
        vm = 1
except Exception:
    vm = 1


def vm_delay_seconds_integrated_only(invoker_channel_id: int, vm_num: int) -> int:
    """통합채널(IntegratedChannelID)에서만 VM 지연: 1→0초, 2→5, 3→10, 4→15. 일반 채널에서는 항상 0."""
    if invoker_channel_id != intergrated_channel_id:
        return 0
    return {1: 0, 2: 5, 3: 10, 4: 15}.get(vm_num, 0)


pc_value = config['DEFAULT'].get('Pc', '1')
try:
    pc = int(pc_value)
    if pc < 1 or pc > 14:
        pc = 1
except Exception:
    pc = 1

# grow 전역변수 추가 (불린형 true/false, 기본 false)
grow_value = config['DEFAULT'].get('Grow', 'False')
grow = grow_value.lower() == 'true'

# delete 전역변수 추가 (문자열형, 기본 None)
delete_value = config['DEFAULT'].get('Delete', 'None')
delete = None if delete_value == 'None' else delete_value

# language 전역변수 추가 (불린형 true/false, 기본 true - 한국어)
language_value = config['DEFAULT'].get('Language', 'True')
language = language_value.lower() == 'true'

def parse_run_mode(raw: Optional[str]) -> str:
    """settings.ini Mode → cheat | normal | exp. 구버전 True/False 호환."""
    s = (raw or "").strip().lower()
    if s in ("cheat", "normal", "exp"):
        return s
    if s == "true":
        return "normal"
    if s == "false":
        return "cheat"
    return "cheat"

run_mode = parse_run_mode(config["DEFAULT"].get("Mode", "cheat"))

daynight_enabled = config['DEFAULT'].get('DayNightEnabled', 'True').lower() == 'true'
option_ini_path = config['DEFAULT'].get('OptionIniPath', r'C:\option.ini').strip()
option_ini_section = config['DEFAULT'].get('OptionIniSection', 'config').strip()
cheat_ini_day_path = config['DEFAULT'].get('CheatIniDayPath', os.path.join(ini_dir, 'day.ini')).strip()
cheat_ini_night_path = config['DEFAULT'].get('CheatIniNightPath', os.path.join(ini_dir, 'night.ini')).strip()
cheat_option_h_path = config['DEFAULT'].get('CheatOptionHPath', os.path.join(ini_dir, 'optionH.ini')).strip()
exp_ini_path = config['DEFAULT'].get('ExpIniPath', os.path.join(ini_dir, 'exp.ini')).strip()
normal_ini_path = config['DEFAULT'].get('NormalIniPath', os.path.join(ini_dir, 'normal.ini')).strip()
discord_loop = None
daynight_async_lock = None
_daynight_scheduler_started = False

# 프로그램 상태 전역변수들
macro = False
game_access_running = False
tasks = []
exp_wiggle_last = 0.0

def save_settings():
    """현재 전역변수 설정값들을 settings.ini 파일에 저장"""
    config['DEFAULT']['Web'] = str(web)
    config['DEFAULT']['Channel'] = str(channel)
    config['DEFAULT']['Token'] = str(token)
    config['DEFAULT']['ChannelID'] = str(channel_id)
    config['DEFAULT']['IntegratedChannelID'] = str(intergrated_channel_id)
    config['DEFAULT']['2pw'] = str(pw2_value) if pw2_value is not None else 'None'
    config['DEFAULT']['Name'] = str(name) if name is not None else 'None'
    config['DEFAULT']['Id'] = str(id_value) if id_value is not None else 'None'
    config['DEFAULT']['Pw'] = str(pw_value) if pw_value is not None else 'None'
    config['DEFAULT']['Vm'] = str(vm)
    config['DEFAULT']['Pc'] = str(pc)
    config['DEFAULT']['Grow'] = str(grow)
    config['DEFAULT']['Delete'] = str(delete) if delete is not None else 'None'
    config['DEFAULT']['Language'] = str(language)
    config['DEFAULT']['Mode'] = str(run_mode)
    config['DEFAULT']['CheatActiveProfile'] = str(cheat_active_profile)
    with open(settings_file, 'w', encoding='utf-8') as configfile:
        config.write(configfile)

def _make_ini_parser():
    p = configparser.ConfigParser()
    p.optionxform = str
    return p

_KST_TZ_FALLBACK = datetime.timezone(datetime.timedelta(hours=9))


def _now_kst() -> datetime.datetime:
    """한국 표준시. Windows에서 tzdata(Asia/Seoul) 없으면 UTC+9 고정으로 대체."""
    try:
        return datetime.datetime.now(ZoneInfo("Asia/Seoul"))
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc).astimezone(_KST_TZ_FALLBACK)


def desired_profile_kst(now_aware=None):
    """평일 08:50~18:00 day, 주말·그 외 시간 night (Asia/Seoul)."""
    if now_aware is None:
        now_aware = _now_kst()
    wd = now_aware.weekday()
    if wd >= 5:
        return "night"
    minutes = now_aware.hour * 60 + now_aware.minute
    day_start = 8 * 60 + 50
    day_end = 18 * 60
    if day_start <= minutes < day_end:
        return "day"
    return "night"


def _load_cheat_active_profile_initial() -> str:
    raw = (config['DEFAULT'].get('CheatActiveProfile') or '').strip().lower()
    if raw in ('day', 'night'):
        return raw
    return desired_profile_kst()


cheat_active_profile: str = _load_cheat_active_profile_initial()


def _read_option_ini_parser():
    p = _make_ini_parser()
    if os.path.isfile(option_ini_path):
        try:
            p.read(option_ini_path, encoding='utf-8-sig')
        except Exception:
            pass
    if not p.has_section(option_ini_section):
        p.add_section(option_ini_section)
    return p

def local_temp_has_any_exe() -> bool:
    """%LOCALAPPDATA%\\Temp 아래에 .exe 파일이 하나라도 있으면 True."""
    localappdata = os.environ.get("LOCALAPPDATA", "")
    if not localappdata:
        return False
    temp_root = os.path.join(localappdata, "Temp")
    if not os.path.isdir(temp_root):
        return False
    return len(glob.glob(os.path.join(temp_root, "*.exe"))) > 0

async def dismiss_temp_exe_via_ui_click():
    """Temp 에 .exe 가 있을 때 프로세스 kill 대신 (770, 17) 클릭으로 UI 정리."""
    if not local_temp_has_any_exe():
        return
    await _run_sync_in_executor(pyautogui.click, 770, 17)
    await asyncio.sleep(0.5)


async def kill_game_exe_only():
    """game.exe 종료. subprocess는 스레드에서 실행해 디스코드 이벤트 루프 블로킹을 줄임."""
    def _taskkill_sync():
        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "game.exe"],
                capture_output=True,
                timeout=12,
            )
        except (subprocess.TimeoutExpired, Exception):
            pass

    try:
        await asyncio.wait_for(asyncio.to_thread(_taskkill_sync), timeout=20.0)
    except asyncio.TimeoutError:
        pass
    await asyncio.sleep(1)


CHEAT_PC_MAPLINK_IDX = {
    1: 212, 2: 213, 3: 214, 4: 197, 5: 198, 6: 199, 7: 200, 8: 201,
    9: 203, 10: 204, 11: 205, 12: 206, 13: 207, 14: 208,
}

# PauseWhenExp98_levelLimit_lv: PC 그룹 기본 → 101(pc 1,4~8), 104(pc 2,3,9~12), 105(pc 13,14).
# 아래 맵에만 넣은 PC는 그 값으로 덮어씀(예외 설정).
CHEAT_PC_PAUSE_LEVEL_LIMIT_LV: Dict[int, int] = {}
# PC별 PauseWhenExp98_levelLimit 켬(1)/끔(0). 키 없으면 1.
CHEAT_PC_PAUSE_LEVEL_LIMIT_ON: Dict[int, str] = {}


def cheat_pause_exp98_level_limit_on_for_pc(pc_num: int) -> str:
    pc_c = max(1, min(14, int(pc_num)))
    v = CHEAT_PC_PAUSE_LEVEL_LIMIT_ON.get(pc_c, "1")
    return v if v in ("0", "1") else "1"


def cheat_pause_exp98_level_limit_lv_for_pc(pc_num: int, profile: Optional[str] = None) -> int:
    """PauseWhenExp98_levelLimit_lv. profile은 호환용(미사용)."""
    pc_c = max(1, min(14, int(pc_num)))
    if pc_c in CHEAT_PC_PAUSE_LEVEL_LIMIT_LV:
        return int(CHEAT_PC_PAUSE_LEVEL_LIMIT_LV[pc_c])
    if pc_c in (1, 4, 5, 6, 7, 8):
        return 101
    if pc_c in (2, 3, 9, 10, 11, 12):
        return 104
    if pc_c in (13, 14):
        return 105
    return 101


def cheat_teleport_filter_mob_for_pc(pc_num: int) -> str:
    """cheat 반영 시 OptionIni [config] TeleportToMob_filter_mob."""
    pc_c = max(1, min(14, int(pc_num)))
    if pc_c in (1, 4, 5, 6, 7, 8):
        return "111"
    if pc_c in (2, 3, 9, 10, 11, 12):
        return "113"
    if pc_c in (13, 14):
        return "114"
    return "111"


CHEAT_PC_NAME_BASE = {
    1: "숨은계단1", 2: "숨은계단2", 3: "숨은계단3", 4: "계단입구",
    5: "계단1", 6: "계단2", 7: "계단3", 8: "계단4", 9: "계단6",
    10: "계단7", 11: "계단8", 12: "계단9", 13: "계단10", 14: "계단11",
}
# 표시용 name: "숨은계단1-78" (하이픈 + VM별 두 자리). 채널은 동일 숫자 쌍에서 랜덤(78→7 또는 8).
CHEAT_VM_DISPLAY_SUFFIX = {1: "12", 2: "34", 3: "56", 4: "78"}
CHEAT_VM_CHANNEL_PAIR = {1: (1, 2), 2: (3, 4), 3: (5, 6), 4: (7, 8)}


def pick_cheat_channel_for_vm(vm_num: int) -> int:
    """cheat용: vm1→1·2, vm2→3·4, vm3→5·6, vm4→7·8 중 하나 무작위."""
    vm_c = max(1, min(4, int(vm_num)))
    a, b = CHEAT_VM_CHANNEL_PAIR.get(vm_c, (1, 2))
    return random.choice([a, b])


def cheat_autorechannel_values(vm_num: int) -> dict:
    """vm 1~4 → AutoReChannel_channel_01~08 값."""
    keys = {f"AutoReChannel_channel_{i:02d}": "0" for i in range(1, 9)}
    if vm_num == 1:
        keys["AutoReChannel_channel_01"] = "1"
        keys["AutoReChannel_channel_02"] = "1"
    elif vm_num == 2:
        keys["AutoReChannel_channel_03"] = "1"
        keys["AutoReChannel_channel_04"] = "1"
    elif vm_num == 3:
        keys["AutoReChannel_channel_05"] = "1"
        keys["AutoReChannel_channel_06"] = "1"
    elif vm_num == 4:
        keys["AutoReChannel_channel_07"] = "1"
        keys["AutoReChannel_channel_08"] = "1"
    return keys

def build_cheat_display_name(pc_num: int, vm_num: int) -> str:
    pc_c = max(1, min(14, pc_num))
    vm_c = max(1, min(4, vm_num))
    base = CHEAT_PC_NAME_BASE.get(pc_c, CHEAT_PC_NAME_BASE[1])
    pair = CHEAT_VM_DISPLAY_SUFFIX.get(vm_c, "12")
    return f"{base}-{pair}"


def sync_display_name_from_pc_vm() -> None:
    """settings.ini·GUI용 name(pc·vm). cheat 모드면 channel을 name 뒤 두 자리 쌍에 맞춰 랜덤(예 78→7 또는 8)."""
    global name, channel
    name = build_cheat_display_name(pc, vm)
    if run_mode == "cheat":
        channel = pick_cheat_channel_for_vm(vm)
    save_settings()


def normalize_stored_cheat_display_name() -> None:
    """구버전 Name(하이픈 없음, 예 숨은계단178)이면 현재 pc·vm 기준 표준 표기(숨은계단1-78)로 맞춤."""
    global name
    if run_mode != "cheat" or not isinstance(name, str) or not name.strip():
        return
    want = build_cheat_display_name(pc, vm)
    if name.replace("-", "") != want.replace("-", ""):
        return
    if name != want:
        name = want
        save_settings()


normalize_stored_cheat_display_name()


def _option_section_dict(p) -> dict:
    if not p.has_section(option_ini_section):
        return {}
    return {k: p.get(option_ini_section, k) for k in p.options(option_ini_section)}

def _write_parser_to_option_ini(p) -> bool:
    try:
        with open(option_ini_path, "w", encoding="utf-8", newline="") as f:
            p.write(f)
        return True
    except Exception:
        return False


def _write_parser_to_option_ini_fresh(p) -> bool:
    """치트용: 전체 내용을 임시 파일에 쓴 뒤 os.replace로 OptionIniPath에 교체(기존 option.ini를 원자적으로 갈아끼움)."""
    dst = os.path.abspath(option_ini_path)
    parent = os.path.dirname(dst)
    if parent:
        try:
            os.makedirs(parent, exist_ok=True)
        except OSError:
            pass
    dir_arg = parent if parent else os.getcwd()
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(prefix="option_", suffix=".ini.tmp", dir=dir_arg)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            p.write(f)
        os.replace(tmp_path, dst)
        tmp_path = None
        return True
    except Exception:
        if tmp_path and os.path.isfile(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return False


def _copy_whole_ini_file_to_option(src_path: str) -> bool:
    """템플릿 INI 전체를 OptionIniPath에 기록."""
    if not os.path.isfile(src_path):
        return False
    p = _make_ini_parser()
    try:
        p.read(src_path, encoding="utf-8-sig")
    except Exception:
        return False
    return _write_parser_to_option_ini(p)

def _apply_cheat_pc_vm_to_parser(
    p, update_display_name: bool, profile: Optional[str] = None
) -> None:
    """[config]에 PC·VM·주간/야간(profile) 반영.

    PC(1~14, settings Pc):
      - AutoTravel_saveMapLink_idx: CHEAT_PC_MAPLINK_IDX (맵링크 슬롯 번호)
      - TeleportToMob_filter_mob: 111(pc 1,4~8) / 113(pc 2,3,9~12) / 114(pc 13,14)
      - PauseWhenExp98_levelLimit / PauseWhenExp98_levelLimit_lv: CHEAT_PC_PAUSE_LEVEL_LIMIT_ON,
        기본 lv 101(pc 1,4~8) / 104(pc 2,3,9~12) / 105(pc 13,14), CHEAT_PC_PAUSE_LEVEL_LIMIT_LV로 예외

    VM(1~4, settings Vm):
      - AutoReChannel_channel_01~08: 해당 VM 구간만 1, 나머지 0
        vm1→01·02, vm2→03·04, vm3→05·06, vm4→07·08

    profile: \"day\"|\"night\" (스테이징·설치 시, 레벨리밋 lv 계산에는 미사용).

    update_display_name True면 전역 name·channel·save_settings(표시용 이름·치트 채널 랜덤).
    """
    pc_c = max(1, min(14, pc))
    vm_c = max(1, min(4, vm))
    if update_display_name:
        global name, channel
        name = build_cheat_display_name(pc_c, vm_c)
        if run_mode == "cheat":
            channel = pick_cheat_channel_for_vm(vm_c)
    if not p.has_section(option_ini_section):
        p.add_section(option_ini_section)
    idx = CHEAT_PC_MAPLINK_IDX.get(pc_c, 212)
    p.set(option_ini_section, "AutoTravel_saveMapLink_idx", str(idx))
    p.set(
        option_ini_section,
        "TeleportToMob_filter_mob",
        cheat_teleport_filter_mob_for_pc(pc_c),
    )
    p.set(
        option_ini_section,
        "PauseWhenExp98_levelLimit",
        cheat_pause_exp98_level_limit_on_for_pc(pc_c),
    )
    p.set(
        option_ini_section,
        "PauseWhenExp98_levelLimit_lv",
        str(cheat_pause_exp98_level_limit_lv_for_pc(pc_c, profile)),
    )
    for k, v in cheat_autorechannel_values(vm_c).items():
        p.set(option_ini_section, k, v)


def _cheat_template_ini_path(profile: str) -> str:
    return cheat_ini_day_path if profile == "day" else cheat_ini_night_path


def _delete_legacy_cheat_optiond_optionn_files() -> None:
    """구버전 스크립트가 쓰던 optiond.ini·optionn.ini가 남아 있으면 삭제(외부에서 복사원으로 쓰이면 옛 내용이 C:\\option 등으로 갈 수 있음)."""
    for base in (script_dir, ini_dir):
        for name in ("optiond.ini", "optionn.ini"):
            path = os.path.join(base, name)
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except OSError:
                pass


def _parser_from_cheat_template_patched(profile: str):
    """CheatIniDayPath·CheatIniNightPath 중 profile에 해당하는 템플릿을 읽고 PC·VM 패치만 반영한 파서(비교·설치용)."""
    path = _cheat_template_ini_path(profile)
    if not os.path.isfile(path):
        return None
    p = _make_ini_parser()
    try:
        p.read(path, encoding="utf-8-sig")
    except Exception:
        return None
    _apply_cheat_pc_vm_to_parser(p, False, profile)
    return p


def _install_cheat_profile_to_live_option(profile: str) -> bool:
    """KST 프로필(day|night)에 해당하는 CheatIniDayPath·CheatIniNightPath 템플릿 전체를 읽어
    PC·VM·레벨리밋 등 일부 [config]만 패치한 뒤, OptionIniPath(기본 C:\\option.ini)는 임시 파일에 쓴 뒤 replace로 새 파일로 교체. cheat_active_profile 갱신."""
    global cheat_active_profile
    p = _parser_from_cheat_template_patched(profile)
    if p is None:
        return False
    if not _write_parser_to_option_ini_fresh(p):
        return False
    cheat_active_profile = profile
    return True


def option_ini_matches_profile(profile: str) -> bool:
    """cheat: 패치된 day|night 템플릿의 [config]와 현재 OptionIniPath가 동일한지."""
    if run_mode != "cheat":
        return True
    exp_p = _parser_from_cheat_template_patched(profile)
    if exp_p is None:
        return False
    act_p = _read_option_ini_parser()
    return _option_section_dict(exp_p) == _option_section_dict(act_p)


def apply_cheat_disk_from_templates(profile: str) -> bool:
    """cheat 공통: settings 저장 → KST profile(day|night)에 맞는 CheatIniDayPath·CheatIniNightPath 템플릿 전체 로드 →
    PC·VM 등 [config] 일부 패치 → OptionIniPath는 임시 파일에 전체 쓴 뒤 os.replace로 교체 → name 동기화·저장.
    게임·exe 종료 및 cheat_config(off)는 호출부에서 먼저 수행할 것(!m cheat·check_game·daynight 파이프라인 순서 통일)."""
    _delete_legacy_cheat_optiond_optionn_files()
    save_settings()
    if not os.path.isfile(cheat_ini_day_path) or not os.path.isfile(cheat_ini_night_path):
        sync_display_name_from_pc_vm()
        return False
    if profile not in ("day", "night"):
        profile = desired_profile_kst()
    if not _install_cheat_profile_to_live_option(profile):
        sync_display_name_from_pc_vm()
        return False
    sync_display_name_from_pc_vm()
    save_settings()
    return True


def apply_option_profile(profile: str) -> bool:
    """cheat: apply_cheat_disk_from_templates와 동일(템플릿→패치→OptionIniPath)."""
    return apply_cheat_disk_from_templates(profile)


def apply_run_mode_option_and_name() -> bool:
    """run_mode별 OptionIniPath 반영. cheat: (after_run_mode_changed에서 종료·cheat off 후) settings→템플릿 재빌드→KST 프로필 복사."""
    if run_mode == "cheat":
        return apply_cheat_disk_from_templates(desired_profile_kst())
    if run_mode == "normal":
        ok = _copy_whole_ini_file_to_option(normal_ini_path)
        sync_display_name_from_pc_vm()
        return ok
    if run_mode == "exp":
        ok = _copy_whole_ini_file_to_option(exp_ini_path)
        sync_display_name_from_pc_vm()
        return ok
    return True

def refresh_macro_gui():
    """settings/모드 반영 후 GUI 정보 패널 즉시 갱신."""
    g = globals().get("gui")
    if g is None or not getattr(g, "root", None):
        return
    try:
        def _do():
            for attr in (
                "prev_macro", "prev_game_access_running", "prev_web",
                "prev_id_value", "prev_pw_value", "prev_pw2_value", "prev_channel",
                "prev_name", "prev_vm", "prev_pc", "prev_delete", "prev_run_mode",
            ):
                if hasattr(g, attr):
                    setattr(g, attr, None)
            g.update_status()
        g.root.after(0, _do)
    except Exception:
        pass

async def after_run_mode_changed(ctx=None, *, language: bool = True) -> Tuple[bool, Optional[str]]:
    """모드 전환: game → DLL 클릭 → cheat off → INI·저장·GUI. ctx 있으면 단계별 디스코드 디버그.
    반환: (성공 여부, 오류 요약 또는 None). INI apply가 False여도 치명적이지 않으면 성공으로 본다."""
    t0 = time.monotonic()
    last = t0

    async def dbg(ko: str, en: str) -> None:
        nonlocal last
        now = time.monotonic()
        d_step = now - last
        d_tot = now - t0
        last = now
        if ctx is not None:
            msg = (
                f"[모드전환·디버그] {ko}  Δ{d_step:.2f}s / Σ{d_tot:.2f}s"
                if language
                else f"[mode debug] {en}  Δ{d_step:.2f}s / Σ{d_tot:.2f}s"
            )
            await notify_discord_command_channels(ctx, msg)
            await asyncio.sleep(0.05)

    try:
        await dbg("시작", "start")
        await kill_game_exe_only()
        await dbg("① game.exe 종료·대기 완료", "① after game.exe kill")
        await dismiss_temp_exe_via_ui_click()
        await dbg("② DLL(UI) 좌표 처리 완료", "② after DLL UI click")
        await cheat_config("off")
        await dbg("③ cheat_config(off) 완료", "③ after cheat_config(off)")
        apply_ok = False
        try:
            apply_ok = apply_run_mode_option_and_name()
        except Exception as ini_e:
            if ctx is not None:
                await notify_discord_command_channels(
                    ctx,
                    (f"[모드전환·오류] INI 적용 중 예외: {ini_e}" if language else f"[mode error] INI apply: {ini_e}"),
                )
            raise
        await dbg(
            f"④ apply_run_mode_option_and_name → {apply_ok}",
            f"④ apply_run_mode_option_and_name → {apply_ok}",
        )
        if not apply_ok and ctx is not None:
            await notify_discord_command_channels(
                ctx,
                (
                    "[모드전환·경고] INI 적용 False (day.ini/night.ini 없음·읽기 실패 등). name·설정만 갱신됐을 수 있음."
                    if language
                    else "[mode warn] INI apply False; check CheatIniDayPath/CheatIniNightPath."
                ),
            )
        try:
            save_settings()
        except Exception as save_e:
            if ctx is not None:
                await notify_discord_command_channels(
                    ctx,
                    (f"[모드전환·오류] settings.ini 저장 실패: {save_e}" if language else f"[mode error] save_settings: {save_e}"),
                )
            raise
        refresh_macro_gui()
        await dbg("⑤ save_settings·GUI 완료", "⑤ after save·GUI")
        if ctx is not None:
            await notify_discord_command_channels(
                ctx,
                (
                    "(유추) 단계별 Δ가 수초면 정상. 한 단계만 수 분이면 그 직전 작업(화면 캡처·taskkill·pyautogui·디스크)이 루프를 막았을 가능성."
                    if language
                    else "(hint) Huge Δ on one step → sync block (capture/taskkill/pyautogui/disk) at that step."
                ),
            )
        return True, None
    except asyncio.CancelledError:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        err = f"{type(e).__name__}: {e}"
        if ctx is not None:
            tail = tb[-1200:] if len(tb) > 1200 else tb
            await notify_discord_command_channels(
                ctx,
                (f"[모드전환·오류] {err}\n```\n{tail}\n```" if language else f"[mode error] {err}\n```\n{tail}\n```"),
            )
            await notify_discord_command_channels(
                ctx,
                (
                    "(유추) 예외로 중단되어 '완료' 메시지가 없었을 수 있음. 권한·경로·keyboard_controller·디스크 풀 확인."
                    if language
                    else "(hint) Exception prevented 'complete' message; check perms/paths/disk."
                ),
            )
        return False, err

# =============================================================================
# 2. 이미지 관련 함수들
# =============================================================================

async def send_message(channel, message):
    """Discord 채널에 메시지를 전송. channel이 TextChannel인 경우에만 전송"""
    if channel and isinstance(channel, discord.TextChannel):
        await channel.send(message)


async def notify_discord_command_channels(ctx, message: str) -> None:
    """VM 채널(channel_id)과, 통합 채널에서 명령한 경우 그 채널 둘 다에 안내(한쪽만 보면 무반응처럼 보이는 문제 방지)."""
    ch = bot.get_channel(channel_id)
    if ch and isinstance(ch, discord.TextChannel):
        try:
            await ch.send(message)
        except Exception:
            pass
    if (
        isinstance(ctx.channel, discord.TextChannel)
        and ctx.channel.id != channel_id
        and "intergrated_channel_id" in globals()
        and ctx.channel.id == intergrated_channel_id
    ):
        try:
            await ctx.channel.send(message)
        except Exception:
            pass


async def error_message(image_name):
    """이미지를 찾을 수 없을 때 Discord 채널에 에러 메시지 전송 (@everyone @here 포함). 전송 실패해도 접속 흐름이 끊기지 않도록 예외 삼킴."""
    try:
        channel_obj = bot.get_channel(channel_id)
        if channel_obj and isinstance(channel_obj, discord.TextChannel):
            await send_message(
                channel_obj,
                f"{image_name}을 찾을 수 없음 예외에러 발생 @everyone @here",
            )
    except Exception:
        pass

async def image_search(image_name, time=100, delay=0.1, region=None, alert_on_miss=True) -> Tuple[Optional[bool], Optional[Tuple[int, int]], Optional[float], Optional[Tuple[int, int]]]:
    """화면에서 이미지를 검색. time 횟수만큼 delay 간격으로 반복 검색. 찾으면 (True, 좌표, 유사도, 최소좌표) 반환. 실패 시 alert_on_miss=False면 (False, …)만, True면 error_message 후 (None, …). time=1이면 항상 실패 시 (False, …). region은 (x1, y1, x2, y2)."""
    path = image_file_path(image_name)
    opencv_image = cv2.imread(path)
    if opencv_image is None:
        raise ValueError(f"Image {path} could not be read.")

    attempt = 0
    while True:
        screen = np.array(ImageGrab.grab())
        screen = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
        
        # 영역이 지정되면 해당 영역만 잘라서 검색
        if region is not None:
            x1, y1, x2, y2 = region
            screen = screen[y1:y2, x1:x2]
            offset_x, offset_y = x1, y1  # 원본 좌표로 변환하기 위한 오프셋
        else:
            offset_x, offset_y = 0, 0
        
        result = cv2.matchTemplate(screen, opencv_image, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val > 0.8:
            # 원본 좌표로 변환
            original_max_loc = (int(max_loc[0] + offset_x), int(max_loc[1] + offset_y))
            original_min_loc = (int(min_loc[0] + offset_x), int(min_loc[1] + offset_y))
            return (True, original_max_loc, min_val, original_min_loc)  # 이미지를 찾으면 True와 좌표 반환
        attempt += 1
        if time > 0 and attempt >= time:
            if time == 1 or not alert_on_miss:
                return (False, None, None, None)
            await error_message(image_name)
            return (None, None, None, None)
        await asyncio.sleep(delay)

async def ensure_image_or_alert(image_name: str):
    """이미지를 60초 동안 1초 간격으로 검색. 실패 시 1분마다 error_message를 반복 전송"""
    result = await image_search(image_name, time=60, delay=1)
    if not result or not result[0]:
        while True:
            await error_message(image_name)
            await asyncio.sleep(60)
    return result

async def image_click(
    image_name,
    time=100,
    delay=0.1,
    click_type="double",
    threshold=0.9,
    use_grayscale=False,
    alert_on_fail=True,
):
    """이미지를 검색하여 클릭. 실패 시 alert_on_fail=False면 error_message 없이 None. 나머지는 image_search와 동일 개념."""
    path = image_file_path(image_name)
    opencv_image = cv2.imread(path)
    if opencv_image is None:
        raise ValueError(f"Image {path} could not be read.")

    attempt = 0
    while True:
        screen = np.array(ImageGrab.grab())
        screen = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
        
        # 그레이스케일 변환 여부에 따라 처리
        if use_grayscale:
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
            # 템플릿 이미지가 컬러인지 그레이스케일인지 확인
            if len(opencv_image.shape) == 3 and opencv_image.shape[2] == 3:
                template_gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            else:
                template_gray = opencv_image
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        else:
            result = cv2.matchTemplate(screen, opencv_image, cv2.TM_CCOEFF_NORMED)
        
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val > threshold:
            h, w = opencv_image.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            
            if click_type == "single":
                await asyncio.sleep(2)
                pyautogui.moveTo(center_x, center_y)
                pyautogui.mouseDown(center_x, center_y)
                await asyncio.sleep(0.1)
                pyautogui.mouseUp(center_x, center_y)
            else:  # double (기본값)
                pyautogui.moveTo(center_x, center_y)
                pyautogui.doubleClick(center_x, center_y)
                await asyncio.sleep(0.1)
                pyautogui.doubleClick(center_x, center_y)
            
            return max_loc
        attempt += 1
        if time > 0 and attempt >= time:
            if alert_on_fail:
                await error_message(image_name)
            return None
        await asyncio.sleep(delay)

async def password(pwd="258960"):
    """2pw 이미지 확인 후 지정 영역(1040,500~1140,630)에서 숫자 이미지를 찾아 클릭하여 비밀번호 입력. 각 숫자는 3회 시도하여 최고 정확도로 클릭. 완료 후 pw 버튼 클릭"""
    # 2pw 이미지를 먼저 찾음
    image_search_result = await image_search('2pw', time=10, delay=0.1)
    if image_search_result[0] is None or not image_search_result[0]:
        await error_message('2pw')
        return None

    # 지정한 영역만 캡처 (좌상단 1040,500 ~ 우하단 1140,630)
    bbox = (1040, 500, 1140, 630)
    screen = np.array(ImageGrab.grab(bbox=bbox))
    screen = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)

    # 비밀번호를 문자열로 변환하여 각 숫자 처리
    numbers = list(str(pwd))

    for num in numbers:
        digit_path = image_file_path(str(num))
        template = cv2.imread(digit_path)
        if template is None:
            await error_message(f'{digit_path} 파일을 찾을 수 없습니다.')
            return None
        
        # 여러 번 시도하여 정확도 향상
        max_attempts = 3
        best_match = None
        best_val = 0
        
        for attempt in range(max_attempts):
            # 화면을 다시 캡처하여 최신 상태 확인
            screen = np.array(ImageGrab.grab(bbox=bbox))
            screen = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
            
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > best_val:
                best_val = max_val
                best_match = max_loc
            
            if max_val >= 0.85:  # 정확도 임계값을 높임
                break
            await asyncio.sleep(0.1)
        
        if best_val < 0.75 or best_match is None:  # 최종 임계값을 낮춰서 더 관대하게 처리
            await error_message(f'{num} 버튼을 찾을 수 없습니다. (정확도: {best_val:.3f})')
            return None
        
        h, w = template.shape[:2]
        center = (best_match[0] + w // 2, best_match[1] + h // 2)
        # 절대좌표로 변환
        real_center_x = center[0] + bbox[0]
        real_center_y = center[1] + bbox[1]
        pyautogui.click(real_center_x, real_center_y)
        await asyncio.sleep(0.1)  # 클릭 간격을 늘려서 안정성 향상
        pyautogui.click(930, 525) #마우스클릭버그방지 허공 클릭
        await asyncio.sleep(0.1)
        

    # pw 버튼 클릭은 image_click 함수로 처리
    await image_click('pw', click_type="single")
    await asyncio.sleep(0.1)

async def channel_click(ch: Optional[int] = None):
    """channel 이미지 검색 후 채널 선택. ch가 있으면 해당 채널, 없으면 전역변수 channel 사용. 2자릿수(10~99)면 첫 자릿수~두 자릿수 범위에서 랜덤 선택. 미리 정의된 좌표로 클릭 후 더블클릭"""
    # 채널별 좌표 사전
    channel_coordinates = {
        1: (1000, 450),
        2: (1000, 480),
        3: (1000, 510),
        4: (1000, 540),
        5: (1000, 570),
        6: (1000, 600),
        7: (1000, 630),
        8: (1000, 660)
    }
    
    # channel 이미지 검색
    result = await image_search('channel', time=100, delay=0.1)
    if not result[0]:
        await error_message('channel')
        return None
    
    # 사용할 채널 번호 결정 (인자 우선, 없으면 상태 전역변수)
    selected_channel = None
    if ch is not None:
        try:
            selected_channel = int(ch)
        except Exception:
            selected_channel = None
    if selected_channel is None:
        selected_channel = channel
    
    # 채널 값이 2자릿수(10~99)인 경우 랜덤 처리
    if 10 <= selected_channel <= 99:
        # 첫 번째 자릿수와 두 번째 자릿수 추출
        channel_str = str(selected_channel)
        start_channel = int(channel_str[0])
        end_channel = int(channel_str[1])
        
        # 첫 번째 자릿수부터 두 번째 자릿수까지의 범위에서 랜덤 선택
        selected_channel = random.randint(start_channel, end_channel)

    # 현재 채널에 해당하는 좌표 가져오기
    if selected_channel in channel_coordinates:
        x, y = channel_coordinates[selected_channel]
        # 클릭 실행
        pyautogui.moveTo(x, y)
        pyautogui.click(x, y)
        await asyncio.sleep(0.1)
        pyautogui.doubleClick(x, y)
        await asyncio.sleep(0.1)
        return True
    else:
        await error_message(f'채널 {selected_channel}에 대한 좌표가 정의되지 않았습니다.')
        return None

async def channel_bug():
    """ok 이미지가 보이는 동안 최대 2번 반복. ok 감지 시 ok 클릭 → back 클릭 → neko 더블클릭 → channel_click 호출. ok가 안 보이면 즉시 종료"""
    try:
        # 최대 2번 반복 체크
        for i in range(2):
            # ok.png를 0.1초 간격으로 체크 (미감지시 에러메시지 없음)
            result = await image_search('ok', time=5, delay=0.1)
            if result[0]:
                # ok.png 인식시 클릭
                await image_click('ok', time=30, delay=0.1, click_type="single")
                pyautogui.click(970, 430)
                await asyncio.sleep(0.1)
                
                # back.png 클릭
                await image_click('back', time=30, delay=0.1, click_type="single")
                pyautogui.click(970, 430)
                await asyncio.sleep(1)
                
                # neko.png 더블클릭
                await image_click('neko', time=30, delay=0.1, click_type="double")
                pyautogui.click(970, 430)
                # 3초 지연
                await asyncio.sleep(2)
                
                # channel_click으로 상태전역변수에 따른 클릭 처리
                await channel_click()
                
                # 1초 대기 후 다음 체크
                await asyncio.sleep(1)
            else:
                # ok.png가 안 보이면 즉시 함수 종료
                return True
        
        # 2번 모두 완료시 함수 종료
        return True
            
    except Exception as e:
        # 예외 발생시 에러메시지 없이 처리
        return False

async def server_bug():
    """start 이미지가 보이는 동안 최대 10번 반복. start 감지 시 back 클릭 → 2초 대기 → neko 더블클릭. start가 안 보이면 즉시 종료"""
    try:
        # 최대 10번 반복 체크
        for i in range(10):
            # start.png를 0.1초 간격으로 체크 (미감지시 에러메시지 없음)
            result = await image_search('start', time=30, delay=0.1)
            if result[0]:
                # back.png 클릭
                await image_click('back', time=30, delay=0.1, click_type="single")
                await asyncio.sleep(0.1)
                
                # 2초 지연
                await asyncio.sleep(2)
                
                # neko.png 더블클릭
                await image_click('neko', time=30, delay=0.1, click_type="double")
                await asyncio.sleep(0.1)
                
                # 1초 대기 후 다음 체크
                await asyncio.sleep(1)
            else:
                # start.png가 안 보이면 즉시 함수 종료
                return True
        
        # 10번 모두 완료시 함수 종료
        return True
            
    except Exception as e:
        # 예외 발생시 에러메시지 없이 처리
        return False



async def tahwa():
    """cheat 모드에서만 skill~skill3 이미지를 순차 클릭. 그 외 모드는 즉시 반환."""
    if run_mode != "cheat":
        return True
    try:
        # 클릭할 이미지 목록
        skills = ['skill', 'skill1', 'skill2', 'skill3']
        
        for skill_name in skills:
            # 이미지 클릭 시도 (에러메시지 없음)
            result = await image_search(skill_name, time=1, delay=0.1)
            if result[0]:
                # 이미지가 감지되면 클릭
                await image_click(skill_name, time=1, delay=0.1, click_type="single")
            
            # 1초 지연 (마지막 이미지가 아닌 경우)
            if skill_name != 'skill3':
                await asyncio.sleep(1)
        
        return True
            
    except Exception as e:
        # 예외 발생시 에러메시지 없이 처리
        return False

# =============================================================================
# 3. 실질적인 행동 함수들
# =============================================================================

async def check_game():
    """게임 상태 확인. cheat+DayNight: KST 프로필이 바뀌면 !m cheat와 동일 순서(game·exe 종료 → DLL 정리 → cheat off → day|night 템플릿에서 PC·VM 패치 후 OptionIniPath 전체 기록) 후 False(복구 루프 유도). 그 외 game.exe·오류·check·cheaton 등 검사."""
    global cheat_active_profile
    error_images = ["error", "135", "rerror", "dll", "report"]
    channel_obj = bot.get_channel(channel_id)

    if (
        run_mode == "cheat"
        and daynight_enabled
        and os.path.isfile(cheat_ini_day_path)
        and os.path.isfile(cheat_ini_night_path)
    ):
        want = desired_profile_kst()
        if want != cheat_active_profile:
            await kill_game_exe_only()
            await dismiss_temp_exe_via_ui_click()
            try:
                await cheat_config("off")
            except Exception:
                pass
            apply_cheat_disk_from_templates(want)
            return False

    # 1. game.exe 또는 귀혼 프로세스가 실행 중인지 확인
    # 작업 관리자에서 "game(32비트)(2)" 또는 "귀혼(32비트)(2)"로 보이지만 실제 프로세스 이름은 "game.exe"입니다
    game_running = False
    for proc in psutil.process_iter():
        try:
            proc_name = proc.name().lower()
            # game.exe 프로세스 확인 (작업 관리자에서는 "(32비트)(2)" 같은 표시가 추가되지만 실제 이름은 "game.exe")
            if proc_name == "game.exe":
                game_running = True
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    if not game_running:
        return False  # 조기 반환
    
    # 2. 오류 이미지 검사
    for img in error_images:
        result = await image_search(img, 1)
        found = result[0]
        if found:
            return False  # 조기 반환

    # 3. check.png 체크 (연속 감지 시 문제로 판단)
    if not (await image_search("check", 1))[0]:
        # 두 번째 검사 - 60초 동안 1초마다 1번씩 처리
        if not (await image_search("check", time=20, delay=1))[0]:
            return False  # 조기 반환
        
    # 4. cheaton 이미지 체크
    if not (await image_search("cheaton", 1))[0]:
        return False  # 조기 반환
    
    # 5. cheatupdate 이미지 체크
    if (await image_search("cheatupdate", 1))[0]:
        pyautogui.doubleClick(755, 17)
        return False  # 조기 반환
    
    # 모든 검사를 통과하면 True 반환
    return True


async def check_death():
    """death 이미지 감지 시 RGB 변화 검사. 영역(960~1400, y=948)을 5초 간격으로 3회 캡처. 3회 모두 동일하면 death와 ok 클릭 후 종료, 하나라도 다르면 정상으로 판단하여 종료"""
    channel_obj = bot.get_channel(channel_id)
    
    # death 이미지 한 번이라도 감지되면 진행
    if (await image_search("death", time=1))[0]:
        # 10초 간격으로 3회 캡처 (가로 960~1400, 세로 한 줄 y=948)
        captures = []
        for i in range(3):
            img = np.array(ImageGrab.grab(bbox=(960, 948, 1400, 949)))
            captures.append(img)
            if i < 2:
                await asyncio.sleep(5)
        
        # 세 장이 모두 동일하면 문제로 판단하여 후속 처리, 하나라도 다르면 정상으로 간주하고 반환
        if np.array_equal(captures[0], captures[1]) and np.array_equal(captures[1], captures[2]):
            # death 및 ok 클릭 후, 이후 처리는 check_map에 위임
            await image_click('death', time=600, delay=0.1, click_type="single")
            await image_click('ok', time=600, delay=0.1, click_type="single")
            await asyncio.sleep(5)
            return
        else:
            return
    return



CHEAT_STATUS_PIXEL_XY = (280, 426)
CHEAT_STATUS_RGB = (66, 150, 250)


def _cheat_status_pixel_rgb() -> Optional[Tuple[int, int, int]]:
    x, y = CHEAT_STATUS_PIXEL_XY
    try:
        im = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
        p = im.getpixel((0, 0))
    except Exception:
        return None
    if len(p) >= 3:
        return int(p[0]), int(p[1]), int(p[2])
    return None


async def cheat_config(mode: str) -> None:
    """(280,426) 픽셀이 RGB(66,150,250)이면 치트 UI 켜진 상태로 본다.
    on: 그 색이면 아무 것도 안 함, 아니면 F2. off: 그 색이면 F2, 아니면 아무 것도 안 함."""
    low = (mode or "").strip().lower()
    if low not in ("on", "off"):
        return
    if keyboard_controller is None:
        return
    rgb = await _run_sync_in_executor(_cheat_status_pixel_rgb)
    if rgb is None:
        return
    active = rgb == CHEAT_STATUS_RGB
    if low == "on":
        if active:
            return
    else:
        if not active:
            return
    keyboard_controller.press(Key.f2)
    await asyncio.sleep(0.1)
    keyboard_controller.release(Key.f2)
    await asyncio.sleep(0.1)

async def exp_mode_direction_wiggle():
    """exp 모드: 방향키 왼쪽 1초, 오른쪽 1초."""
    if keyboard_controller is None:
        return
    kc = keyboard_controller
    kc.press(Key.left)
    await asyncio.sleep(1)
    kc.release(Key.left)
    kc.press(Key.right)
    await asyncio.sleep(1)
    kc.release(Key.right)

async def gaming():
    """매크로 메인 루프. macro가 True인 동안 반복: check_game 실패 시 cleangame → access → cheat_config → cheat일 때만 tahwa(skill) → 120초 대기. check_death. exp면 30초마다 방향키 좌우."""
    global macro, exp_wiggle_last
    channel_obj = bot.get_channel(channel_id)
    exp_wiggle_last = 0.0

    if run_mode == "exp":
        await cheat_config("off")
    else:
        await cheat_config("on")

    try:
        while macro:
            try:
                if not await check_game():
                    await cleangame()
                    if run_mode == "exp":
                        await access(cheat_after_chrome="off")
                        await cheat_config("off")
                    else:
                        await access(cheat_after_chrome="on")
                        await cheat_config("on")
                    await tahwa()
                    await asyncio.sleep(120)
                else:
                    if run_mode == "exp":
                        now = time.monotonic()
                        if now - exp_wiggle_last >= 30:
                            exp_wiggle_last = now
                            await exp_mode_direction_wiggle()
                await check_death()
                await asyncio.sleep(1)

            except Exception as e:
                await asyncio.sleep(5)

    except asyncio.CancelledError:
        macro = False
        return

async def cheat():
    dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher.dll")
    if not os.path.exists(dll_path):
        return None
    cmd = ['rundll32', dll_path, 'Silent']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    await image_search('cheatlogin', time=1000, delay=0.1)
    # 기존 행동: cheatlogin 클릭
    await image_click('cheatlogin', time=100, delay=0.1, click_type="single")


def clear_chrome_history_and_cache_preserving_startup():
    """방문기록·일반 캐시·자동완성(Web Data)·저장 로그인(Login Data)만 삭제.

    유지(초기화하지 않음): Preferences·Secure Preferences(시작 페이지·사이트별 허용·실행/팝업 관련),
    User Data\\Local State, Network(쿠키), Local Storage, Session Storage, IndexedDB,
    Service Worker, blob_storage(게임/런처 ‘항상 실행’·팝업 닫기 등 웹 상태).
    """
    local = os.environ.get("LOCALAPPDATA", "")
    if not local:
        return
    user_data = os.path.join(local, "Google", "Chrome", "User Data")
    if not os.path.isdir(user_data):
        return

    def rm_rf(path: str) -> None:
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
        except OSError:
            pass

    history_files = (
        "History",
        "History-journal",
        "History-wal",
        "History-shm",
        "Archived History",
        "Archived History-journal",
        "Visited Links",
        "Visited Links-journal",
        "Top Sites",
        "Top Sites-journal",
        "Top Sites-wal",
        "Top Sites-shm",
        "Favicons",
        "Favicons-journal",
    )
    # 아이디/비번 입력 흔적·드롭다운(자동완성·저장된 비밀번호)
    autofill_login_files = (
        "Web Data",
        "Web Data-journal",
        "Web Data-wal",
        "Web Data-shm",
        "Login Data",
        "Login Data-journal",
        "Login Data-wal",
        "Login Data-shm",
        "Login Data For Account",
        "Login Data For Account-journal",
        "Account Web Data",
        "Account Web Data-journal",
    )
    # Service Worker·blob_storage 는 삭제하지 않음(웹 런처 팝업/실행 허용 상태가 리셋될 수 있음)
    cache_dirs = (
        "Cache",
        "Code Cache",
        "GPUCache",
        "DawnGraphiteCache",
        "DawnWebGPUCache",
        "ShaderCache",
        "GrShaderCache",
        "Media Cache",
    )

    try:
        for name in os.listdir(user_data):
            prof = os.path.join(user_data, name)
            if not os.path.isdir(prof):
                continue
            if not os.path.isfile(os.path.join(prof, "Preferences")):
                continue
            for fn in history_files:
                rm_rf(os.path.join(prof, fn))
            for fn in autofill_login_files:
                rm_rf(os.path.join(prof, fn))
            for d in cache_dirs:
                rm_rf(os.path.join(prof, d))
    except OSError:
        pass


async def cleangame():
    # 크롬 브라우저 강제 종료 (복구 메시지 방지). access() 등 전체 정리용. 모드 전환은 kill_game_exe_only 우선.
    try:
        subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True, timeout=5)
    except Exception as e:
        pass

    await asyncio.sleep(1)
    clear_chrome_history_and_cache_preserving_startup()

    try:
        subprocess.run(["taskkill", "/f", "/im", "game.exe"], capture_output=True, timeout=5)
    except Exception as e:
        pass

    await asyncio.sleep(3)

async def login():
    """로그인 처리. web에 따라 login 이미지와 좌표 결정. id_value가 "google"이면 google 클릭, "naver"이면 naver 클릭, "save"이면 login 버튼만 클릭, 기타는 ID/PW를 클립보드로 입력. mgame은 최대 3회 재시도, hangame은 1회만. loginerror 감지 시 재시도"""
    global web, id_value, pw_value
    
    try:
        # web 상태에 따라 로그인 이미지 및 입력 좌표 결정
        if web == 'hangame':
            login_image = 'hlogin'
            id_pos = (1080, 240)
            pw_pos = (1080, 320)
            max_retry = 1  # hangame은 재시도 없음
        else:
            login_image = 'mlogin'
            id_pos = (750, 440)
            pw_pos = (750, 510)
            max_retry = 3  # mgame은 최대 3회 재시도
        
        # 로그인 이미지 검색 (access에서 이미 본 경우가 많아 실패 시 알림 생략)
        login_result = await image_search(
            login_image, time=30, delay=0.1, alert_on_miss=False
        )
        if not login_result[0]:
            return False
        
        # id_value에 따른 처리
        if id_value == "google":
            # google.png 클릭
            await image_click('google', time=10, delay=0.1, click_type="single")
        elif id_value == "naver":
            # naver.png 클릭
            await image_click('naver', time=10, delay=0.1, click_type="single")
        elif id_value == "save":
            # 저장된 정보로 로그인 버튼만 클릭
            await image_click(login_image, time=10, delay=0.1, click_type="single")
        else:
            # 기존 방식: ID/PW 입력
            if id_value is None or pw_value is None:
                return False
            
            for attempt in range(max_retry):
                # ID 입력 (클립보드 사용 - 한글 및 특수문자 지원)
                pyautogui.click(*id_pos)
                await asyncio.sleep(0.5)
                pyautogui.hotkey('ctrl', 'a')
                await asyncio.sleep(0.2)
                pyautogui.press('delete')
                await asyncio.sleep(0.2)
                # 클립보드에 ID 복사 후 붙여넣기
                pyperclip.copy(str(id_value))
                pyautogui.hotkey('ctrl', 'v')
                await asyncio.sleep(0.5)
                
                # PW 입력 (클립보드 사용 - 한글 및 특수문자 지원)
                pyautogui.click(*pw_pos)
                await asyncio.sleep(0.5)
                pyautogui.hotkey('ctrl', 'a')
                await asyncio.sleep(0.2)
                pyautogui.press('delete')
                await asyncio.sleep(0.2)
                # 클립보드에 PW 복사 후 붙여넣기
                pyperclip.copy(str(pw_value))
                pyautogui.hotkey('ctrl', 'v')
                await asyncio.sleep(0.5)
                
                # 로그인 버튼 클릭
                await image_click(login_image, time=10, delay=0.1, click_type="single")
                await asyncio.sleep(2)
                
                # mgame일 때 loginerror.png 예외처리
                if web == 'mgame':
                    error_result = await image_search(
                        "loginerror", time=3, delay=0.5, alert_on_miss=False
                    )
                    if error_result[0]:
                        pyautogui.click(1130, 210)
                        await asyncio.sleep(1)
                        continue  # 다시 시도
                # hangame 또는 mgame에서 에러가 없으면 성공
                return True
            return False
        
        await asyncio.sleep(2)  # 로그인 처리 대기
        return True
        
    except Exception as e:
        return False

async def access(ch: Optional[Union[int, str]] = None, *, cheat_after_chrome: str = "off"):
    """게임 접속 프로세스. … 크롬 종료 후 neko 직전에 cheat_config(cheat_after_chrome): !3(game)는 off, !1·매크로 복구는 on 권장."""
    global channel, web, game_access_running
    
    # 1. cleangame 실행
    await cleangame()
    
    # 2. 시간 동기화 (times.windows.com) - 오류 무시
    try:
        subprocess.run(["w32tm", "/resync"], shell=True, capture_output=True, timeout=10)
    except Exception as e:
        pass

    # 3. Temp에 .exe가 없을 때만 cheat (런처/치트 쪽이 아직 안 뜬 것으로 간주)
    if not local_temp_has_any_exe():
        await cheat()
    
    # 4. 크롬 실행
    if web == 'mgame':
        chrome_url = "https://msign.mgame.com/login/?tu=https://hon.mgame.com/"
    else:  # hangame
        chrome_url = "https://accounts.hangame.com/sign-in?inflow=PC&nextUrl=https%3A%2F%2Fhon.hangame.com"
    
    subprocess.Popen([
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "--start-maximized",
        "--new-window",
        "--disable-features=TranslateUI",
        "--disable-extensions",
        "--disable-default-apps",
        "--disable-popup-blocking",
        "--disable-notifications",
        "--disable-component-update",
        "--no-first-run",
        "--no-default-browser-check",
        chrome_url
    ])
    await asyncio.sleep(2)
    
    # 5. 로그인 버튼이 보일 때만 로그인; 세션 유지 등으로 안 보이면 로그인 생략 후 아래에서 게임 URL로 이동
    prefix = 'm' if web == 'mgame' else 'h'
    login_image = 'mlogin' if web == 'mgame' else 'hlogin'
    login_visible = (
        await image_search(login_image, time=30, delay=0.1, alert_on_miss=False)
    )[0]
    if login_visible:
        await login()
    # 6. 로그인 후(또는 로그인 생략 시) 플랫폼에 따라 게임 페이지로 이동
    await asyncio.sleep(3)  # 로그인 완료 대기
    try:
        if web == 'mgame':
            # mgame일 때 hon.mgame.com으로 이동 (기존 탭)
            subprocess.run([
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                "https://hon.mgame.com"
            ])
        else:  # hangame
            # hangame일 때 hon.hangame.com으로 이동 (기존 탭)
            subprocess.run([
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                "https://hon.hangame.com"
            ])
        await asyncio.sleep(2)  # 페이지 로딩 대기
    except Exception as e:
        pass

    # E.png — 없어도 아래 webstart 는 반드시 진행 (알림/예외로 access 중단 방지)
    e_hit = (await image_search("e", time=10, delay=0.1, alert_on_miss=False))[0]
    if e_hit:
        await asyncio.sleep(0.5)
        pyautogui.moveTo(1594, 180)
        pyautogui.mouseDown(1594, 180)
        await asyncio.sleep(0.1)
        pyautogui.mouseUp(1594, 180)
        await asyncio.sleep(3)
    # 7. mwebstart/hwebstart — 이미지 실패해도 흐름 유지, 재시도는 그레이+낮은 threshold
    ws = await image_click(
        f"{prefix}webstart",
        time=200,
        delay=0.1,
        click_type="single",
        threshold=0.9,
        alert_on_fail=False,
    )
    if not ws:
        await image_click(
            f"{prefix}webstart",
            time=120,
            delay=0.15,
            click_type="single",
            threshold=0.72,
            use_grayscale=True,
            alert_on_fail=False,
        )

    # 7. lancherstart 버튼 클릭 (패치 완료 후 정상 상태에서만 클릭)
    # 패치 중에는 클릭하지 않고, 정상적인 이미지와 색상이 같아질 때까지 대기
    # threshold=0.9로 설정하여 정상 상태의 이미지만 인식하고 클릭
    await image_click(
        "lancherstart",
        time=50,
        delay=0.1,
        click_type="single",
        threshold=0.9,
        use_grayscale=False,
        alert_on_fail=False,
    )
    await asyncio.sleep(2)

    # 16. 크롬 브라우저 강제 종료 → 방문기록·캐시만 삭제(시작 페이지 설정 유지)
    subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True)
    await asyncio.sleep(1)
    clear_chrome_history_and_cache_preserving_startup()
    await asyncio.sleep(5)

    cc = (cheat_after_chrome or "off").strip().lower()
    if cc in ("on", "off"):
        await cheat_config(cc)

    # 10. neko 버튼 클릭
    await image_click('neko', time=180, delay=1, click_type="double")

        
    # 11. 2pw 값이 설정되어 있으면 password 함수 호출
    if pw2_value is not None:
        await password(pw2_value)
    await server_bug()
    
    # 13. channel_click() 실행 (선택적 채널 인자 전달)
    await channel_click(ch)
    await channel_bug()
    
    
    # 17. cheaton 이미지 서칭 (180초 동안 0.1초 간격)
    result = await image_search('cheaton', time=180, delay=0.1)
    if not result[0]:
        await cleangame()
        return
    
    # 18. start 버튼 클릭
    await image_click('start', time=100, delay=0.1, click_type="double")
    
    # 19. check 이미지 서칭 (60초 동안 1초 간격)
    result = await image_search('check', time=60, delay=1)
    if result[0]:
        return  # access 함수 종료
    else:
        await cleangame()

async def lancherstart():
    global web
    prefix = 'm' if web == 'mgame' else 'h'
    await asyncio.sleep(10)
    while True:
        result = await image_search(
            "lancherstart", time=50, delay=0.1, alert_on_miss=False
        )

        # 이미지가 인식될 때 → 복구 로직 실행
        if result[0] == True:
            pyautogui.click(1320, 265)
            await asyncio.sleep(1)
            await image_click(
                f"{prefix}webstart",
                time=50,
                delay=0.1,
                click_type="single",
                threshold=0.9,
                use_grayscale=False,
                alert_on_fail=False,
            )
            await image_click(
                "lancherstart",
                time=50,
                delay=0.1,
                click_type="single",
                threshold=0.9,
                use_grayscale=False,
                alert_on_fail=False,
            )
            await asyncio.sleep(10)
        else:
            # 이미지가 인식 안 될 때 → 함수 종료
            return

async def _full_daynight_switch_impl(profile: str) -> bool:
    """game.exe 종료 → DLL UI → cheat off → !m cheat와 동일하게 settings·day|night 템플릿 재빌드·OptionIniPath → 런처·access. 매크로였으면 gaming 재시작."""
    global macro, tasks
    was_macro_running = macro
    if macro:
        macro = False
        for task in list(tasks):
            task.cancel()
        tasks.clear()
        try:
            await cheat_config("on")
        except Exception:
            pass
    await kill_game_exe_only()
    await dismiss_temp_exe_via_ui_click()
    try:
        await cheat_config("off")
    except Exception:
        pass
    if not apply_cheat_disk_from_templates(profile):
        return False
    if not local_temp_has_any_exe():
        await cheat()
    await access(cheat_after_chrome="on")
    if was_macro_running:
        macro = True
        tasks.append(asyncio.create_task(gaming()))
    return True

async def run_daynight_switch_pipeline(profile: str) -> bool:
    global daynight_async_lock
    lock = daynight_async_lock
    if lock is not None:
        async with lock:
            return await _full_daynight_switch_impl(profile)
    return await _full_daynight_switch_impl(profile)

async def ensure_daynight_aligned_for_macro(channel_obj) -> bool:
    if run_mode != "cheat":
        return True
    if not daynight_enabled:
        return True
    want = desired_profile_kst()
    if not os.path.isfile(cheat_ini_day_path) or not os.path.isfile(cheat_ini_night_path):
        return True
    if option_ini_matches_profile(want) and cheat_active_profile == want:
        return True
    if language:
        await send_message(channel_obj, "Day/Night 설정 적용 및 재접속 중...")
    else:
        await send_message(channel_obj, "Applying Day/Night profile and reconnecting...")
    return await run_daynight_switch_pipeline(want)

def daynight_scheduler_loop():
    """예전: 45초마다 Day/Night 전환. 이제 KST 전환은 check_game에서 처리하므로 스레드를 시작하지 않음."""
    while True:
        time.sleep(3600)

# =============================================================================
# 4. 디스코드 봇 명령어들
# =============================================================================

@bot.command(aliases=['w'])
async def web_cmd(ctx, value: Optional[str] = None):
    """web 전역변수 설정/조회. value 없으면 현재 값 표시, "m"이면 mgame, "h"이면 hangame으로 설정하고 ini 저장"""
    global web, grow, language
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # 값이 없으면 현재 설정 표시
    if value is None:
        if language:
            await send_message(channel_obj, f"현재 web 값은 {web} 입니다.")
        else:
            await send_message(channel_obj, f"Current web value is {web}.")
        return
    
    # 설정 변경
    if value.lower() == "m":
        web = "mgame"
        save_settings()
        if language:
            await send_message(channel_obj, "web 값이 mgame(으)로 변경되었습니다.")
        else:
            await send_message(channel_obj, "web value has been changed to mgame.")
    elif value.lower() == "h":
        web = "hangame"
        save_settings()
        if language:
            await send_message(channel_obj, "web 값이 hangame(으)로 변경되었습니다.")
        else:
            await send_message(channel_obj, "web value has been changed to hangame.")
    else:
        if language:
            await send_message(channel_obj, "m(엠게임) 또는 h(한게임)만 입력 가능합니다.")
        else:
            await send_message(channel_obj, "Only m(mgame) or h(hangame) can be entered.")

@bot.command(aliases=['c'])
async def channel_cmd(ctx, x: Optional[int] = None):
    """channel 전역변수 설정/조회. x 없으면 현재 값 표시. 1~8 또는 10~88(2자릿수)만 허용. 2자릿수는 첫 자릿수 1~8, 두 자릿수 0~8 검증. 설정 후 ini 저장"""
    global channel, grow, language
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # 값이 없으면 현재 설정 표시
    if x is None:
        if language:
            await send_message(channel_obj, f"현재 채널값은 {channel} 입니다.")
        else:
            await send_message(channel_obj, f"Current channel value is {channel}.")
        return
    
    # 3자릿수 이상 채널 값 검증 (변경하지 않음)
    if x >= 100:
        if language:
            await send_message(channel_obj, "채널값은 1~8 또는 10~88 사이의 숫자만 입력 가능합니다.")
        else:
            await send_message(channel_obj, "Channel value must be between 1~8 or 10~88.")
        return
    
    # 2자릿수 채널 값 검증
    if 10 <= x <= 99:
        channel_str = str(x)
        first_digit = int(channel_str[0])
        second_digit = int(channel_str[1])
        
        # 첫 번째 자릿수가 0인 경우
        if first_digit == 0:
            if language:
                await send_message(channel_obj, "첫 번째 자릿수는 0이 될 수 없습니다.")
            else:
                await send_message(channel_obj, "The first digit cannot be 0.")
            return
        
        # 첫 번째 자릿수가 9 이상인 경우
        if first_digit >= 9:
            if language:
                await send_message(channel_obj, "첫 번째 자릿수는 8 이하여야 합니다.")
            else:
                await send_message(channel_obj, "The first digit must be 8 or less.")
            return
        
        # 두 번째 자릿수가 9 이상인 경우
        if second_digit >= 9:
            if language:
                await send_message(channel_obj, "두 번째 자릿수는 8 이하여야 합니다.")
            else:
                await send_message(channel_obj, "The second digit must be 8 or less.")
            return
        
        # 검증 통과 - 저장 및 상태 전역변수 변경
        channel = x
        save_settings()
        if language:
            await send_message(channel_obj, f"채널값이 {x}으로 변경되었습니다.")
        else:
            await send_message(channel_obj, f"Channel value has been changed to {x}.")
    
    # 1자릿수 채널 값 검증 (기존 로직)
    elif 1 <= x <= 8:
        channel = x
        save_settings()
        if language:
            await send_message(channel_obj, f"채널값이 {x}으로 변경되었습니다.")
        else:
            await send_message(channel_obj, f"Channel value has been changed to {x}.")
    else:
        if language:
            await send_message(channel_obj, "채널값은 1~8 또는 10~88 사이의 숫자만 입력 가능합니다.")
        else:
            await send_message(channel_obj, "Channel value must be between 1~8 or 10~88.")    

@bot.command(aliases=['2pw'])
async def pw2_cmd(ctx, value: Optional[str] = None):
    """pw2_value 전역변수 설정/조회. value 없으면 현재 값 표시, "none"이면 None으로 설정, 숫자면 해당 값으로 설정. 설정 후 ini 저장"""
    global pw2_value, grow, language
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # 값이 없으면 현재 설정 표시
    if value is None:
        current_value = "None" if pw2_value is None else pw2_value
        if language:
            await send_message(channel_obj, f"현재 2pw 값은 {current_value} 입니다.")
        else:
            await send_message(channel_obj, f"Current 2pw value is {current_value}.")
        return
    
    # 설정 변경
    if value.lower() == "none":
        pw2_value = None
        save_settings()
        if language:
            await send_message(channel_obj, "2pw 값이 None으로 변경되었습니다.")
        else:
            await send_message(channel_obj, "2pw value has been changed to None.")
    else:
        # 숫자인지 확인
        try:
            int(value)  # 숫자로 변환 가능한지 테스트
            pw2_value = value
            save_settings()
            if language:
                await send_message(channel_obj, f"2pw 값이 {value}으로 변경되었습니다.")
            else:
                await send_message(channel_obj, f"2pw value has been changed to {value}.")
        except ValueError:
            if language:
                await send_message(channel_obj, "2pw 값은 숫자 또는 'none'만 입력 가능합니다.")
            else:
                await send_message(channel_obj, "2pw value must be a number or 'none'.")

@bot.command(aliases=['name'])
async def name_cmd(ctx, value: Optional[str] = None):
    """name 전역변수 설정/조회. value 없으면 현재 값 표시, "none"이면 None으로 설정, 기타 값이면 해당 값으로 설정. 설정 후 ini 저장"""
    global name, grow, language
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # 값이 없으면 현재 설정 표시
    if value is None:
        current_value = "None" if name is None else name
        if language:
            await send_message(channel_obj, f"현재 name 값은 {current_value} 입니다.")
        else:
            await send_message(channel_obj, f"Current name value is {current_value}.")
        return
    
    # 설정 변경
    if value.lower() == "none":
        name = None
        save_settings()
        if language:
            await send_message(channel_obj, "name 값이 None으로 변경되었습니다.")
        else:
            await send_message(channel_obj, "name value has been changed to None.")
    else:
        name = value
        save_settings()
        if language:
            await send_message(channel_obj, f"name 값이 {value}으로 변경되었습니다.")
        else:
            await send_message(channel_obj, f"name value has been changed to {value}.")

@bot.command(aliases=['id'])
async def id_cmd(ctx, value: Optional[str] = None):
    """id_value 전역변수 설정/조회. value 없으면 현재 값 표시, "none"이면 None으로 설정, 기타 값이면 해당 값으로 설정. 설정 후 ini 저장"""
    global id_value, grow, language
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # 값이 없으면 현재 설정 표시
    if value is None:
        current_value = "None" if id_value is None else id_value
        if language:
            await send_message(channel_obj, f"현재 id 값은 {current_value} 입니다.")
        else:
            await send_message(channel_obj, f"Current id value is {current_value}.")
        return
    
    # 설정 변경
    if value.lower() == "none":
        id_value = None
        save_settings()
        if language:
            await send_message(channel_obj, "id 값이 None으로 변경되었습니다.")
        else:
            await send_message(channel_obj, "id value has been changed to None.")
    else:
        id_value = value
        save_settings()
        if language:
            await send_message(channel_obj, f"id 값이 {value}으로 변경되었습니다.")
        else:
            await send_message(channel_obj, f"id value has been changed to {value}.")

@bot.command(aliases=['pw'])
async def pw_cmd(ctx, value: Optional[str] = None):
    """pw_value 전역변수 설정/조회. value 없으면 현재 값 표시, "none"이면 None으로 설정, 기타 값이면 해당 값으로 설정. 설정 후 ini 저장"""
    global pw_value, grow, language
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # 값이 없으면 현재 설정 표시
    if value is None:
        current_value = "None" if pw_value is None else pw_value
        if language:
            await send_message(channel_obj, f"현재 pw 값은 {current_value} 입니다.")
        else:
            await send_message(channel_obj, f"Current pw value is {current_value}.")
        return
    
    # 설정 변경
    if value.lower() == "none":
        pw_value = None
        save_settings()
        if language:
            await send_message(channel_obj, "pw 값이 None으로 변경되었습니다.")
        else:
            await send_message(channel_obj, "pw value has been changed to None.")
    else:
        pw_value = value
        save_settings()
        if language:
            await send_message(channel_obj, f"pw 값이 {value}으로 변경되었습니다.")
        else:
            await send_message(channel_obj, f"pw value has been changed to {value}.")

@bot.command(name='pc')
async def pc_cmd(ctx, value: Optional[str] = None):
    """pc 번호 1~14 설정/조회. cheat 모드에서 option.ini·name 반영."""
    global pc, grow, language, run_mode

    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return

    channel_obj = bot.get_channel(channel_id)

    if value is None:
        if language:
            await send_message(channel_obj, f"현재 pc 값은 {pc} 입니다.")
        else:
            await send_message(channel_obj, f"Current pc is {pc}.")
        return

    try:
        n = int(value)
        if 1 <= n <= 14:
            pc = n
            sync_display_name_from_pc_vm()
            if run_mode == "cheat":
                apply_run_mode_option_and_name()
            refresh_macro_gui()
            if language:
                await send_message(channel_obj, f"pc 값이 {n}으로 변경되었습니다.")
            else:
                await send_message(channel_obj, f"pc has been changed to {n}.")
        else:
            if language:
                await send_message(channel_obj, "pc 값은 1~14 사이만 가능합니다.")
            else:
                await send_message(channel_obj, "pc must be between 1 and 14.")
    except ValueError:
        if language:
            await send_message(channel_obj, "pc 값은 1~14 숫자로 입력해주세요.")
        else:
            await send_message(channel_obj, "Enter pc as a number 1~14.")

@bot.command(aliases=['v'])
async def vm_cmd(ctx, value: Optional[str] = None):
    """vm 전역변수 설정/조회. value 없으면 현재 값 표시, 1~4 숫자만 허용. 설정 후 ini 저장"""
    global vm, grow, language, run_mode
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # 값이 없으면 현재 설정 표시
    if value is None:
        if language:
            await send_message(channel_obj, f"현재 vm 값은 {vm} 입니다.")
        else:
            await send_message(channel_obj, f"Current vm value is {vm}.")
        return
    
    # 설정 변경
    try:
        vm_num = int(value)
        if 1 <= vm_num <= 4:
            vm = vm_num
            sync_display_name_from_pc_vm()
            if run_mode == "cheat":
                apply_run_mode_option_and_name()
            refresh_macro_gui()
            if language:
                await send_message(channel_obj, f"vm 값이 {vm_num}으로 변경되었습니다.")
            else:
                await send_message(channel_obj, f"vm value has been changed to {vm_num}.")
        else:
            if language:
                await send_message(channel_obj, "vm 값은 1~4 사이의 숫자만 입력 가능합니다.")
            else:
                await send_message(channel_obj, "vm value must be between 1~4.")
    except ValueError:
        if language:
            await send_message(channel_obj, "vm 값은 1~4 사이의 숫자만 입력 가능합니다.")
        else:
            await send_message(channel_obj, "vm value must be between 1~4.")

@bot.command(name='lang')
async def lang_cmd(ctx):
    """language 전역변수 토글. True(한국어)와 False(영어)를 전환하고 ini 저장"""
    global language, grow
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # language 토글
    language = not language
    save_settings()
    
    if language:
        await send_message(channel_obj, f"언어가 한국어로 설정되었습니다. (현재: {language})")
    else:
        await send_message(channel_obj, f"Language has been set to English. (Current: {language})")

def _run_mode_reply_text(m: str) -> Tuple[str, str]:
    """(한글, 영어) 안내 문구."""
    if m == "cheat":
        return (
            "cheat 모드: ini\\day.ini·night.ini 템플릿 전체를 읽어 PC·VM(mob·맵링크·채널·레벨리밋)만 [config]에서 패치 → OptionIniPath(기본 C:\\\\option.ini) 기존 삭제 후 전체 반영. 평일 주간↔야간 전환은 매크로 루프의 check_game에서 처리.",
            "Cheat: load ini/day.ini or night.ini, patch [config] for PC/VM, delete & rewrite OptionIniPath. Day/night at check_game (KST).",
        )
    if m == "normal":
        return (
            "normal 모드: NormalIniPath(기본 normal.ini) 전체가 OptionIniPath로 복사됩니다. 시간대 자동 전환 없음.",
            "Normal mode: full NormalIniPath (default normal.ini) is copied to OptionIniPath; no schedule switch.",
        )
    return (
        "exp 모드: ExpIniPath(기본 exp.ini) 전체가 OptionIniPath로 복사되고, 게임 정상 시 30초마다 방향키(←1초 →1초) 입력.",
        "Exp mode: full ExpIniPath copied to OptionIniPath; while game OK, every 30s Left 1s then Right 1s.",
    )

@bot.command(aliases=['m'])
async def mode_cmd(ctx, ch: Optional[str] = None):
    """!m [cheat|normal|exp] 설정 또는 인자 없으면 순환. !m [1~8]은 채널 이동."""
    global run_mode, vm, grow, language

    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return

    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return

    if ch is not None:
        low = ch.strip().lower()
        if low in ("cheat", "normal", "exp"):
            prev = run_mode
            if low == prev:
                ko, en = _run_mode_reply_text(run_mode)
                await notify_discord_command_channels(ctx, ko if language else en)
                return
            run_mode = low
            ko, en = _run_mode_reply_text(run_mode)
            busy_ko = "\n(게임 정리·INI 반영 진행 중…)"
            busy_en = "\n(Cleanup and INI apply in progress…)"
            await notify_discord_command_channels(
                ctx, (ko if language else en) + (busy_ko if language else busy_en)
            )
            _mode_switch_timeout = 240.0
            try:
                ok, _err = await asyncio.wait_for(
                    after_run_mode_changed(ctx, language=language),
                    timeout=_mode_switch_timeout,
                )
            except asyncio.TimeoutError:
                ok = False
                await notify_discord_command_channels(
                    ctx,
                    (
                        f"[모드전환·타임아웃] {_mode_switch_timeout:.0f}초 초과. "
                        "마지막 '[모드전환·디버그]' 줄 다음 단계에서 멈춤 — 동기 블로킹(캡처·입력·프로세스) 의심."
                        if language
                        else f"[mode timeout] {_mode_switch_timeout:.0f}s — stuck after last debug line; sync block suspected."
                    ),
                )
            if ok:
                await notify_discord_command_channels(
                    ctx, "모드 적용 완료." if language else "Mode change complete."
                )
            else:
                await notify_discord_command_channels(
                    ctx,
                    (
                        "모드 적용이 오류·타임아웃으로 끝까지 가지 못했습니다. 위 디버그·오류 메시지를 확인하세요."
                        if language
                        else "Mode apply did not finish; see debug/error messages above."
                    ),
                )
            return

        delay = vm_delay_seconds_integrated_only(ctx.channel.id, vm)
        if delay > 0:
            if language:
                await notify_discord_command_channels(
                    ctx, f"vm={vm}에 따라 {delay}초 후 이동을 시작합니다."
                )
            else:
                await notify_discord_command_channels(
                    ctx, f"Starting move in {delay} seconds according to vm={vm}."
                )
            await asyncio.sleep(delay)

        try:
            ch_num = int(ch)
        except Exception:
            if language:
                await notify_discord_command_channels(
                    ctx, "채널은 1~8 또는 모드 cheat/normal/exp 를 입력하세요."
                )
            else:
                await notify_discord_command_channels(
                    ctx, "Use channel 1~8 or mode: cheat, normal, exp."
                )
            return

        if 1 <= ch_num <= 8:
            if language:
                await notify_discord_command_channels(
                    ctx, f"채널 {ch_num} 접속을 시도합니다."
                )
            else:
                await notify_discord_command_channels(
                    ctx, f"Attempting to connect to channel {ch_num}."
                )
            await cleangame()
            await access(ch_num, cheat_after_chrome="off")
            await keyboard_controller.press(Key.f3)
            await asyncio.sleep(0.1)
            await keyboard_controller.release(Key.f3)
            if language:
                await notify_discord_command_channels(ctx, "이동완료")
            else:
                await notify_discord_command_channels(ctx, "Move completed")
        else:
            if language:
                await notify_discord_command_channels(
                    ctx, "채널 번호는 1~8 사이여야 합니다."
                )
            else:
                await notify_discord_command_channels(
                    ctx, "Channel number must be between 1~8."
                )
        return

    order = ("cheat", "normal", "exp")
    try:
        i = order.index(run_mode)
    except ValueError:
        i = 0
    prev = run_mode
    run_mode = order[(i + 1) % len(order)]
    ko, en = _run_mode_reply_text(run_mode)
    if prev != run_mode:
        busy_ko = "\n(게임 정리·INI 반영 진행 중…)"
        busy_en = "\n(Cleanup and INI apply in progress…)"
        await notify_discord_command_channels(
            ctx, (ko if language else en) + (busy_ko if language else busy_en)
        )
        _mode_switch_timeout = 240.0
        try:
            ok, _err = await asyncio.wait_for(
                after_run_mode_changed(ctx, language=language),
                timeout=_mode_switch_timeout,
            )
        except asyncio.TimeoutError:
            ok = False
            await notify_discord_command_channels(
                ctx,
                (
                    f"[모드전환·타임아웃] {_mode_switch_timeout:.0f}초 초과. "
                    "마지막 디버그 줄 이후 단계에서 정지한 것으로 추정."
                    if language
                    else f"[mode timeout] {_mode_switch_timeout:.0f}s — stalled after last debug line."
                ),
            )
        if ok:
            await notify_discord_command_channels(
                ctx, "모드 적용 완료." if language else "Mode change complete."
            )
        else:
            await notify_discord_command_channels(
                ctx,
                (
                    "모드 적용이 오류·타임아웃으로 끝까지 가지 못했습니다. 위 디버그·오류 메시지를 확인하세요."
                    if language
                    else "Mode apply did not finish; see debug/error messages above."
                ),
            )
    else:
        await notify_discord_command_channels(ctx, ko if language else en)

@bot.command(aliases=['g'])
async def grow_cmd(ctx):
    """grow 전역변수 토글. True와 False를 전환하고 ini 저장. grow가 True일 때 integrated_channel_id에서는 명령어 무시"""
    global grow
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # grow 토글
    grow = not grow
    save_settings()
    
    if language:
        status = "활성화" if grow else "비활성화"
        await send_message(channel_obj, f"grow가 {status}되었습니다. (현재: {grow})")
    else:
        status = "enabled" if grow else "disabled"
        await send_message(channel_obj, f"grow has been {status}. (Current: {grow})")

@bot.command(aliases=['d'])
async def delete_cmd(ctx, value: Optional[str] = None):
    """delete 전역변수 설정/조회(메모용). value 없으면 현재 값 표시, 있으면 해당 값으로 설정. 설정 후 ini 저장"""
    global delete, grow, language
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # 값이 없으면 현재 설정 표시
    if value is None:
        current_value = "None" if delete is None else delete
        if language:
            await send_message(channel_obj, f"현재 delete 값은 {current_value} 입니다.")
        else:
            await send_message(channel_obj, f"Current delete value is {current_value}.")
        return
    
    # 설정 변경
    delete = value
    save_settings()
    if language:
        await send_message(channel_obj, f"delete 값이 {value}으로 변경되었습니다.")
    else:
        await send_message(channel_obj, f"delete value has been changed to {value}.")


@bot.command(aliases=['e'])
async def clean_cmd(ctx):
    """cleangame 함수 호출하여 게임 정리"""
    global grow

    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    if language:
        await send_message(channel_obj, "게임 정리 시작")
    else:
        await send_message(channel_obj, "Starting game cleanup")
    pyautogui.doubleClick(755, 17)
    await cleangame()
    
    if language:
        await send_message(channel_obj, "게임 정리 완료")
    else:
        await send_message(channel_obj, "Game cleanup completed")

@bot.event
async def on_ready():
    """봇 로그인 성공 시 호출. Discord 채널에 "매크로 준비완료" 메시지 전송"""
    global discord_loop, daynight_async_lock, _daynight_scheduler_started
    discord_loop = asyncio.get_running_loop()
    if daynight_async_lock is None:
        daynight_async_lock = asyncio.Lock()
    _daynight_scheduler_started = True

    channel_obj = bot.get_channel(channel_id)
    
    if channel_obj is None:
        return
    
    if channel_obj and isinstance(channel_obj, discord.TextChannel):
        try:
            await channel_obj.send("매크로 준비완료")
        except Exception as e:
            pass
@bot.command(aliases=['1'])
async def start(ctx):
    """매크로 시작. 통합채널에서만 vm 지연(2:5s,3:10s,4:15s). 일반 채널은 지연 없음."""
    global macro, vm, grow, language
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    delay = vm_delay_seconds_integrated_only(ctx.channel.id, vm)
    if delay > 0:
        if language:
            await send_message(channel_obj, f"vm={vm}에 따라 {delay}초 후 시작합니다.")
        else:
            await send_message(channel_obj, f"Starting in {delay} seconds according to vm={vm}.")
        await asyncio.sleep(delay)
    
    # 매크로가 이미 실행 중이 아니면 시작
    if not macro:
        if not await ensure_daynight_aligned_for_macro(channel_obj):
            if language:
                await send_message(channel_obj, "Day/Night 전환 실패 — 매크로를 시작하지 않았습니다.")
            else:
                await send_message(channel_obj, "Day/Night switch failed; macro not started.")
            return
        macro = True
        # gaming 함수를 asyncio 작업으로 시작
        tasks.append(asyncio.create_task(gaming()))
        if language:
            await send_message(channel_obj, "시작")
        else:
            await send_message(channel_obj, "Started")

@bot.command(aliases=['도움말', 'guide'])
async def help_cmd(ctx):
    """사용 가능한 명령어 목록을 language 설정에 따라 한국어 또는 영어로 표시"""
    # 채널 권한 확인 (channel_id에서만 허용)
    if ctx.channel.id != channel_id:
        return
    
    channel_obj = bot.get_channel(channel_id)
    if language:
        help_text = (
            "**[명령어 목록]**\n"
            "**매크로 제어**\n"
            "`!start` (`1`) : 매크로 시작 (통합채널에서만 vm 지연)\n"
            "`!stop` (`2`) : 매크로 중단\n"
            "`!game` (`3`) [채널] : 게임 접속 (통합채널에서만 vm 지연)\n"
            "`!move` [채널] : 채널 이동 (vm 지연 없음)\n"
            "`!m` : 모드 순환 또는 `!m cheat|normal|exp` / 통합채널에서만 `!m [1~8]` 시 vm 지연\n"
            "`!exit` (`4`) : 프로그램 종료 및 설정 저장\n"
            "\n"
            "**설정 관리**\n"
            "`!web [m/h]` (`w`) : 게임사(mgame/한게임) 설정\n"
            "`!channel [숫자]` (`c`) : 채널 번호(1~8) 설정\n"
            "`!pc [1~14]` : PC 번호 (cheat 모드 option/name 반영)\n"
            "`!vm [1~4]` (`v`) : vm 값 (통합채널에서 !1·!3·!m[1~8] 시 지연: 1즉시/2·5s/3·10s/4·15s)\n"
            "`!lang` : 언어 설정 토글 (한국어/영어)\n"
            "\n"
            "**로그인 설정**\n"
            "`!id [아이디/google/naver/save]` : ID 설정 (google/naver/save 지원)\n"
            "`!pw [비밀번호/none]` : PW 설정\n"
            "`!2pw [숫자/none]` : 2차 비밀번호 설정\n"
            "`!name [이름]` : 이름 설정\n"
            "\n"
            "**기타**\n"
            "`!clean` (`e`) : 게임 정리 (cleangame 호출)\n"
            "`!l` (`5`) : 현재 화면 전송\n"
        )
    else:
        help_text = (
            "**[Command List]**\n"
            "**Macro Control**\n"
            "`!start` (`1`) : Start macro (vm delay only in integrated channel)\n"
            "`!stop` (`2`) : Stop macro\n"
            "`!game` (`3`) [channel] : Connect (vm delay only in integrated channel)\n"
            "`!move` [channel] : Move channel (no vm delay)\n"
            "`!m` : Cycle mode or `!m cheat|normal|exp` / vm delay only on `!m [1~8]` from integrated channel\n"
            "`!exit` (`4`) : Exit program and save settings\n"
            "\n"
            "**Settings**\n"
            "`!web [m/h]` (`w`) : Game platform (mgame/hangame) setting\n"
            "`!channel [number]` (`c`) : Channel number (1~8) setting\n"
            "`!pc [1~14]` : PC index (cheat mode option/name)\n"
            "`!vm [1~4]` (`v`) : Vm index (delay on !1/!3/!m[1~8] in integrated channel only)\n"
            "`!lang` : Toggle language (Korean/English)\n"
            "\n"
            "**Login Settings**\n"
            "`!id [id/google/naver/save]` : ID setting (google/naver/save supported)\n"
            "`!pw [password/none]` : PW setting\n"
            "`!2pw [number/none]` : 2nd password setting\n"
            "`!name [name]` : Name setting\n"
            "\n"
            "**Others**\n"
            "`!clean` (`e`) : Game cleanup (cleangame call)\n"
            "`!l` (`5`) : Send current screen\n"
        )
    await send_message(channel_obj, help_text)
    
@bot.command(aliases=['3'])
async def game(ctx, ch: Optional[str] = None):
    """게임 접속. 통합채널에서만 vm 지연. 일반 채널은 지연 없음."""
    global game_access_running, vm, grow, language
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    delay = vm_delay_seconds_integrated_only(ctx.channel.id, vm)
    if delay > 0:
        if language:
            await send_message(channel_obj, f"vm={vm}에 따라 {delay}초 후 접속을 시작합니다.")
        else:
            await send_message(channel_obj, f"Starting connection in {delay} seconds according to vm={vm}.")
        await asyncio.sleep(delay)
    
    # 인자 검증 및 access 호출
    if ch is not None:
        try:
            ch_num = int(ch)
        except Exception:
            if language:
                await send_message(channel_obj, "채널 번호는 1~8 숫자로 입력해주세요.")
            else:
                await send_message(channel_obj, "Please enter a channel number between 1~8.")
            return
        if 1 <= ch_num <= 8:
            if language:
                await send_message(channel_obj, f"채널 {ch_num} 접속을 시도합니다.")
            else:
                await send_message(channel_obj, f"Attempting to connect to channel {ch_num}.")
            await access(ch_num, cheat_after_chrome="off")
            if language:
                await send_message(channel_obj, "접속완료")
            else:
                await send_message(channel_obj, "Connection completed")
        else:
            if language:
                await send_message(channel_obj, "채널 번호는 1~8 사이여야 합니다.")
            else:
                await send_message(channel_obj, "Channel number must be between 1~8.")
    else:
        # 숫자가 없으면 상태전역변수 channel 값을 사용
        if language:
            await send_message(channel_obj, f"채널 {channel} 접속을 시도합니다.")
        else:
            await send_message(channel_obj, f"Attempting to connect to channel {channel}.")
        await access(cheat_after_chrome="off")
        if language:
            await send_message(channel_obj, "접속완료")
        else:
            await send_message(channel_obj, "Connection completed")

@bot.command(name='move')
async def move_cmd(ctx, ch: Optional[str] = None):
    """채널 이동. vm 지연 없음. cleangame → access → F4."""
    global vm, grow, language
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # !move 는 일반/통합 모두 VM 지연 없음 (!1·!3·!m 채널 이동만 통합채널에서 지연)
    
    # 인자 검증 및 access 호출
    if ch is not None:
        try:
            ch_num = int(ch)
        except Exception:
            if language:
                await send_message(channel_obj, "채널 번호는 1~8 숫자로 입력해주세요.")
            else:
                await send_message(channel_obj, "Please enter a channel number between 1~8.")
            return
        if 1 <= ch_num <= 8:
            if language:
                await send_message(channel_obj, f"채널 {ch_num} 접속을 시도합니다.")
            else:
                await send_message(channel_obj, f"Attempting to connect to channel {ch_num}.")
            await cleangame()            
            await access(ch_num, cheat_after_chrome="off")
            await keyboard_controller.press(Key.f4)
            await asyncio.sleep(0.1)
            await keyboard_controller.release(Key.f4)   
            if language:
                await send_message(channel_obj, "이동완료")
            else:
                await send_message(channel_obj, "Move completed")
            # market 재탐색 및 이동완료 메시지 전송 제거 (요청사항)
            
        else:
            if language:
                await send_message(channel_obj, "채널 번호는 1~8 사이여야 합니다.")
            else:
                await send_message(channel_obj, "Channel number must be between 1~8.")
    else:
        if language:
            await send_message(channel_obj, "사용법: !move [1~8]")
        else:
            await send_message(channel_obj, "Usage: !move [1~8]")
    
    # !move는 지정 채널 접속만 처리하고 여기서 추가적인 공용 접속 흐름은 실행하지 않습니다.

@bot.command(aliases=['2'])
async def stop(ctx):
    """매크로 중단. macro를 False로 설정, cheat_config(on) 호출, 모든 백그라운드 태스크 취소 및 리스트 비움"""
    global macro, grow, language
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    channel_obj = bot.get_channel(channel_id)
    
    # 매크로가 실행 중이면 중단
    if macro:
        macro = False
        # 진행 중인 모든 작업을 취소
        await cheat_config("on")
        for task in tasks:
            task.cancel()
            tasks.clear()  # 작업 리스트를 비움
        if language:
            await send_message(channel_obj, "중단")
        else:
            await send_message(channel_obj, "Stopped")

@bot.command(aliases=['6'])
async def l(ctx):
    """
    레벨 확인 명령어
    - 현재 화면을 캡처하여 전송
    - 캡처 후 임시 파일 삭제
    """
    global grow
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    # 화면 캡처
    screen = np.array(ImageGrab.grab(bbox=(0, 0, 1920, 1080)))
    screen = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
    level_path = os.path.join(script_dir, "level.png")
    cv2.imwrite(level_path, screen)
    
    # 이미지 전송
    channel_obj = bot.get_channel(channel_id)
    if channel_obj and isinstance(channel_obj, discord.TextChannel):
        await channel_obj.send(file=discord.File(level_path))
    
    # 임시 파일 삭제
    try:
        os.unlink(level_path)
    except Exception:
        pass

@bot.command(aliases=['4'])
async def exit(ctx):
    """설정 저장 후 프로그램 종료(os._exit)"""
    global grow
    
    # 채널 권한 확인
    if ctx.channel.id != channel_id and ('intergrated_channel_id' not in globals() or ctx.channel.id != intergrated_channel_id):
        return
    
    # grow가 true이고 integrated_channel_id에서 명령어를 받았으면 무시
    if grow and ('intergrated_channel_id' in globals() and ctx.channel.id == intergrated_channel_id):
        return
    
    await ctx.send("프로그램 종료")
    save_settings()
    os._exit(0)

# =============================================================================
# 2. GUI 클래스
# =============================================================================

class MacroGUI:
    """매크로 GUI 클래스. 우측 상단에 위치, 항상 맨 위 표시, 상태 표시 및 5초마다 상태 업데이트"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("귀혼")
        self.root.geometry("320x280")
        self.root.resizable(False, False)
        
        # 항상 맨 위에 표시
        self.root.attributes('-topmost', True)
        
        # 윈도우 스타일 설정 (Windows에서 더 깔끔하게)
        try:
            self.root.attributes('-alpha', 0.95)  # 약간 투명도
        except:
            pass
        
        # 우측 꼭짓점이 (1920, 0)이 되도록 위치 설정
        window_width = 320
        window_height = 320
        x = 1920 - window_width  # 우측 꼭짓점이 1920이 되도록
        y = 0  # 상단 꼭짓점이 0이 되도록
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 스타일 설정
        self.setup_styles()
        
        # GUI 요소 생성
        self.create_widgets()
        
        # 이전 상태 저장 변수들
        self.prev_macro = None
        self.prev_game_access_running = None
        self.prev_web = None
        self.prev_id_value = None
        self.prev_pw_value = None
        self.prev_pw2_value = None
        self.prev_channel = None
        self.prev_name = None
        self.prev_vm = None
        self.prev_delete = None
        self.prev_run_mode = None
        self.prev_pc = None

        # 상태 업데이트 시작
        self.update_status()
    
    def setup_styles(self):
        """GUI 스타일 및 색상 테마 설정"""
        style = ttk.Style()
        
        # 테마 설정
        style.theme_use('clam')
        
        # 커스텀 색상 - 더 눈에 잘 들어오도록 개선
        self.colors = {
            'bg_primary': '#1a1a2e',      # 더 진한 배경
            'bg_secondary': '#16213e',     # 더 진한 카드 배경
            'accent': '#0f3460',           # 진한 파란색 액센트
            'success': '#00b894',          # 밝은 초록색 (성공)
            'warning': '#fdcb6e',          # 밝은 주황색 (경고)
            'danger': '#e17055',           # 밝은 빨간색 (위험)
            'text_primary': '#ffffff',     # 흰색 텍스트 (더 선명)
            'text_secondary': '#dfe6e9',   # 밝은 회색 텍스트
            'border': '#636e72'            # 테두리 색상
        }
        
        # 프레임 스타일
        style.configure('Main.TFrame', background=self.colors['bg_primary'])
        style.configure('Card.TFrame', background=self.colors['bg_secondary'])
        
        # 라벨 스타일
        style.configure('Title.TLabel', 
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 14, 'bold'))
        
        style.configure('Status.TLabel', 
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 12, 'bold'))
        
        style.configure('Info.TLabel', 
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_secondary'],
                       font=('Segoe UI', 9))
        

        
        # 루트 윈도우 배경색 설정
        self.root.configure(bg=self.colors['bg_primary'])
    
    def create_widgets(self):
        """GUI 위젯(제목 라벨, 상태 카드, 정보 라벨) 생성 및 배치"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, style='Main.TFrame', padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 그리드 가중치 설정
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 제목 라벨 - name 값으로 동적 표시
        self.title_label = ttk.Label(main_frame, text="", style='Title.TLabel')
        self.title_label.grid(row=0, column=0, pady=(0, 10))
        
        # 상태 카드 프레임
        status_frame = ttk.Frame(main_frame, style='Card.TFrame', padding="15")
        status_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        # 상태 표시 라벨
        self.status_label = ttk.Label(status_frame, text="Status: Stopped", style='Status.TLabel')
        self.status_label.grid(row=0, column=0, pady=(0, 10))
        
        # 정보 표시 라벨들
        self.info_label = ttk.Label(status_frame, text="", style='Info.TLabel', justify='left')
        self.info_label.grid(row=1, column=0, sticky="w")
        
        # 버전 표시 라벨 (맨 밑 하단)
        global version
        version_text = f"v {version}"
        self.version_label = ttk.Label(main_frame, text=version_text, style='Info.TLabel')
        self.version_label.grid(row=2, column=0, pady=(10, 0), sticky="s")
        

    
    def update_status(self):
        """전역변수 상태를 확인하여 변경사항이 있을 때만 GUI 업데이트. 5초마다 재호출"""
        global macro, game_access_running, web, pw2_value, channel, name, id_value, pw_value, vm, delete, run_mode, pc

        # 현재 상태값들
        current_macro = macro
        current_game_access_running = game_access_running
        current_web = web
        current_id_value = id_value
        current_pw_value = pw_value
        current_pw2_value = pw2_value
        current_channel = channel
        current_name = name
        current_vm = vm
        current_delete = delete
        current_run_mode = run_mode
        current_pc = pc

        # 변경사항 확인
        has_changes = (
            self.prev_macro != current_macro or
            self.prev_game_access_running != current_game_access_running or
            self.prev_web != current_web or
            self.prev_id_value != current_id_value or
            self.prev_pw_value != current_pw_value or
            self.prev_pw2_value != current_pw2_value or
            self.prev_channel != current_channel or
            self.prev_name != current_name or
            self.prev_vm != current_vm or
            self.prev_delete != current_delete or
            self.prev_run_mode != current_run_mode or
            self.prev_pc != current_pc
        )
        
        # 변경사항이 있을 때만 GUI 업데이트
        if has_changes:
            # 상태 업데이트
            if current_game_access_running:
                status_text = "Status: Connecting"
                status_color = self.colors['warning']
            elif current_macro:
                status_text = "Status: Hunting"
                status_color = self.colors['success']
            else:
                status_text = "Status: Stopped"
                status_color = self.colors['text_secondary']
            
            self.status_label.config(text=status_text)
            
            # 제목 업데이트 - name 값으로 표시
            title_display = str(current_name) if current_name is not None else "None"
            self.title_label.config(text=title_display)
            
            # 정보 업데이트
            pw2_display = str(current_pw2_value) if current_pw2_value is not None else "None"
            id_display = str(current_id_value) if current_id_value is not None else "None"
            pw_display = str(current_pw_value) if current_pw_value is not None else "None"
            
            # delete 상태 표시
            delete_display = str(current_delete) if current_delete is not None else "None"
            
            info_text = f"mode: {current_run_mode}\npc: {current_pc}\nvm: {current_vm}\nPlatform: {current_web}\nID: {id_display}\nPW: {pw_display}\n2pw: {pw2_display}\nchannel: {current_channel}\ndelete: {delete_display}"
            self.info_label.config(text=info_text)
            
            # 이전 상태값들 업데이트
            self.prev_macro = current_macro
            self.prev_game_access_running = current_game_access_running
            self.prev_web = current_web
            self.prev_id_value = current_id_value
            self.prev_pw_value = current_pw_value
            self.prev_pw2_value = current_pw2_value
            self.prev_channel = current_channel
            self.prev_name = current_name
            self.prev_vm = current_vm
            self.prev_delete = current_delete
            self.prev_run_mode = current_run_mode
            self.prev_pc = current_pc

        # 5초마다 상태 확인 (자원 소모 감소)
        self.root.after(5000, self.update_status)
    

    
    def run(self):
        """GUI 메인 루프 실행"""
        self.root.mainloop()

def create_gui():
    """GUI 생성 및 실행"""
    global gui_root, status_label
    
    gui = MacroGUI()
    gui_root = gui.root
    status_label = gui.status_label
    
    return gui

# =============================================================================
# 5. 프로그램 실행
# =============================================================================

# 전역 변수 초기화
keyboard_controller = None
executor = None
gui = None

try:
    # 키보드 컨트롤러 초기화
    keyboard_controller = Controller()
    executor = ThreadPoolExecutor(max_workers=5)

    # GUI 시작
    gui = create_gui()
    
    # GUI 관련 전역 변수
    gui_root = None
    status_label = None

    # 프로그램 시작 시간
    start_time = datetime.datetime.now()

    async def main():
        await bot.start(token)

    if __name__ == "__main__":
        # 봇을 별도 스레드에서 실행하고 GUI를 메인 스레드에서 실행
        def run_bot():
            try:
                asyncio.run(main())
            except Exception as e:
                pass
        
        # 봇을 백그라운드에서 실행
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        # GUI를 메인 스레드에서 실행
        gui.run()
        
except Exception as e:
    save_settings()
