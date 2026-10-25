import time
# -*- coding: utf-8 -*-
# ===================================================================
#  ANURAG SINGH
# ===================================================================
import sys, asyncio, httpx, random, json, socket, struct, time, os, uuid
# This must be configured before importing any google.protobuf module.
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
import itertools, secrets, traceback, base64
import requests, hmac, string, hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

import warnings
warnings.filterwarnings("ignore")
try:
    import urllib3
    urllib3.disable_warnings()
except Exception:
    pass

from google_play_scraper import app as play_scraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from protobuf_decoder.protobuf_decoder import Parser
from message_ids import MESSAGE_ID_TO_NAME
import Aksingh_pb2
import Anuragsingh_pb2
import get_login_data_pb2
import MajoRLoGinrEq_pb2
from MajorLoginRes_pb2 import MajorLoginRes

try:
    import reqClan_pb2
    _CLAN_PB_AVAILABLE = True
except Exception:
    _CLAN_PB_AVAILABLE = False

# web dashboard HATA DIYA - local no-op stub
class _StubState:
    def __init__(self):
        self.accounts = {}
        self.account_workers = {}
        self.account_credentials = {}
        self.refresh_callbacks = {}
        self.logs = []
    def log(self, *a, **k): pass
    def register_account(self, **k): pass
    def update_status(self, *a, **k): pass
    def update_exp(self, *a, **k): pass
    def increment_match(self, *a, **k): pass
    def is_paused(self, *a): return False
    def toggle_pause(self, *a): return False

bot_state = _StubState()

async def start_web_dashboard(*a, **k):
    return None

# =========================== CONFIG ===========================
WEB_HOST = "0.0.0.0"
WEB_PORT = 20333
ACCOUNTS_FILE = "accounts.json"
TOKEN_CACHE_FILE = "token_cache.json"
DEVICES_FILE = "devices.json"
TOKEN_CACHE_TTL = 4500

START_MATCH_INTERVAL    = 1.0
NEW_MATCH_DELAY         = 1.0
MAX_CONCURRENT_MATCHES  = 20
MAX_MATCH_DURATION      = 70000
MATCH_IDLE_TIMEOUT      = 12.0
EXP_REFRESH_INTERVAL    = 30.0
EXP_REFRESH_AFTER_MATCH_DELAY = 5.0
MAX_CONSECUTIVE_PARSE_FAILURES = 5
NON_MATCH_RECONNECT_DELAY      = 0.5

#  Only Battle Royale
BR_MODE_ID             = 1  # Clasificatoria / Ranked BR
BR_MAP_ID              = 1

ANTI_AFK_MIN_INTERVAL  = 1.8
ANTI_AFK_MAX_INTERVAL  = 3.5

MATCH_SEARCH_TIMEOUT   = 90.0
MATCH_WATCHDOG_CHECK   = 15.0
REGION_ROTATION_LIST   = ["IND"]  # replaced at startup by user selection
REGION_ROTATE_EVERY_N  = 2
MAX_SEARCH_ATTEMPTS    = 999999

SAFE_PLAY_MODE        = True
BYPASS_TIMING_JITTER  = True
BYPASS_PACKET_JITTER  = True
BYPASS_HELLO_DELAY    = True
BYPASS_KA_JITTER      = True

ENABLE_SPEED_MOVEMENT       = True    # movement every 30 seconds
MOVEMENT_SPEED_MIN          = 1.0
MOVEMENT_SPEED_MAX          = 1.4
MOVEMENT_PATTERN            = "circle"
MOVEMENT_TICK_MS            = 30000
MOVEMENT_RADIUS             = 180
MOVEMENT_UPDATE_SPEED_EVERY = 4.0
MOVEMENT_STATE_IDLE_CHANCE   = 0.10
MOVEMENT_STATE_WALK_CHANCE   = 0.28
MOVEMENT_STATE_RUN_CHANCE    = 0.32
MOVEMENT_STATE_SPRINT_CHANCE = 0.10
MOVEMENT_STATE_JUMP_CHANCE   = 0.08
MOVEMENT_STATE_CROUCH_CHANCE = 0.06
MOVEMENT_STATE_PRONE_CHANCE  = 0.06

ENABLE_HTTP_PING = True
PING_INTERVAL    = 20.0
PING_TIMEOUT     = 8.0
PING_URL         = "https://loginbp.ppmainecoonghj.com/Ping"
PING_REAL_IP     = "103.109.214.211"

FALLBACK_UID = ""
FALLBACK_PASSWORD = ""

# =========================== SQUAD CONFIG ===========================
TEAM_MODE               = False
TEAM_SIZE               = 4          # total squad (bots + captain)
TEAM_BOTS               = 4          #  menu se set: normal=4, captain-mode=3
USER_GAME_UID           = ""         #  menu se set (option 1)
CLAN_ID                 = ""         #  menu se clan UID
CLAN_STATE_FILE         = "clan_state.json"
AUTO_JOIN_CLAN          = False
TEAM_PEER_WAIT_TIMEOUT  = 355.0
TEAM_CREATE_WAIT        = 1.0
TEAM_INVITE_CYCLE_WAIT  = 1.0
TEAM_INVITE_MAX_TIME    = 45.0
TEAM_HEARTBEAT_INTERVAL = 2.0
TEAM_IDLE_ITERS_TEAM    = 120
TEAM_MEMBER_START_DELAY = 3.0
TEAM_FINAL_WAIT         = 1.0
TEAM_READY_DELAY = 1.0
_accept_friend_request = True
DEBUG_TEAM_PACKETS      = False      #  debug kam

# =========================== ANTI-BAN ===========================
def bypass_jitter(base, spread=0.35):
    if not (SAFE_PLAY_MODE and BYPASS_TIMING_JITTER): return base
    return max(0.05, base + random.uniform(-spread, spread))

def bypass_packet_jitter(base, spread_ratio=0.35):
    if not (SAFE_PLAY_MODE and BYPASS_PACKET_JITTER): return base
    return max(0.1, base + random.uniform(-base * spread_ratio, base * spread_ratio))

def bypass_hello_delay():
    if not (SAFE_PLAY_MODE and BYPASS_HELLO_DELAY): return 0.0
    return random.uniform(0.01, 0.10)

def bypass_ka_jitter(base=3.0):
    if not (SAFE_PLAY_MODE and BYPASS_KA_JITTER): return base
    return max(2.0, base + random.uniform(-0.5, 0.8))

def bypass_human_reconnect_delay(attempt):
    if not (SAFE_PLAY_MODE and BYPASS_TIMING_JITTER): return min(attempt * 0.5, 2.0)
    return max(0.05, min(attempt * 0.5, 2.0) + random.uniform(-0.4, 0.7))

# =========================== GUEST GEN (FYT_) ===========================
GEN_uVer = "2018.4.12f1"
GEN_GameVer = "2.132.4"
GEN_ReleaseVer = "OB55"
GEN_UaUnity = f"UnityPlayer/{GEN_uVer} (UnityWebRequest/1.0, libcurl/8.5.0-DEV)"
GEN_Hkey = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
GEN_Akey = GEN_Hkey.encode()

GEN_SharedCookie = (
    "datadome=nmP601L~4DvFBNemgIhE2d3Y~tR68_GHUaV8WhUdKLhjg74S_YsRWpOCnYL8cNtz"
    "58Olr_SEm1GSttQImpJO1j15k2AGGY~bFDp0hfrk6p0Dv_JZSGXJUGhhY_QsQ~5H"
)

GEN_UserAgents = [
    "GarenaMSDK/4.0.42(RMX3710 ;Android 15;hi;IND;app 2.132.1 2019118525;)",
    "GarenaMSDK/4.0.42(RMX3085 ;Android 13;hi;IND;app 2.132.1 2019118525;)",
    "GarenaMSDK/4.0.42(SM-A546E ;Android 14;hi;IND;app 2.132.1 2019118525;)",
    "GarenaMSDK/4.0.42(SM-A235F ;Android 13;hi;IND;app 2.132.1 2019118525;)",
    "GarenaMSDK/4.0.42(CPH2449 ;Android 14;hi;IND;app 2.132.1 2019118525;)",
    "GarenaMSDK/4.0.42(V2307 ;Android 14;hi;IND;app 2.132.1 2019118525;)",
    "GarenaMSDK/4.0.42(Pixel 6 ;Android 13;hi;IND;app 2.132.1 2019118525;)",
    "GarenaMSDK/4.0.42(2201117TG  ;Android 14;hi;IND;app 2.132.1 2019118525;)",
    "GarenaMSDK/4.0.42(NTH-NX9 ;Android 13;hi;IND;app 2.132.1 2019118525;)",
    "GarenaMSDK/4.0.42(X6836 ;Android 13;hi;IND;app 2.132.1 2019118525;)",
]

GEN_GgreBlob = bytes.fromhex(
    "47475245010101006d020000832363e79711efb391707fad6381be1acaef57ae198e95d7005ec74d16dd406b7d5356f25b38699671436eb29e6c5ffc6107073ea5fbe9795714af5661bed317bb90d6962420a1edb389ad19115a1b6eeb5205173fd7804b7d23418697ed1c288f66acf0701640c7a613ae69464d9404e38b24d595be1c97c4eac6772952fccbc6714a9472629d0609aeb5de0afb1c078390195a8b6cf96f30b27d7c5120f43af278a150830d3e91f9fa89098d0be519e3802b826e67640293352402ad27479581fcf6e5997f4fc7709bdcb129dc803d1c254b8d5bca4cff1a3d021f169b4e133aca832f1c227baaa2f78ff0ce59b9934af15724766aba47d99de62dc3232f04920cc9dabc292bee3ad4c342f3c7aa94021f7b468417a21eb57bb45b23c27de9e3c5c972012cccfc4e4794d0a6d5368bfcbec8a8ba327815d20f9df47c7eb3c99a18e6747cc3ceb1823a8fcf57afcd5aaf3ca536b76a77c3c218c8dc1860a22fcb87a5a9f8c017745e523a1a4ab8a836993515b6040a33936c39f07b2641885cc90e218555c9539ba541896fdca071175a8cbd8157615b788efeca65bb5b81aeb5cdb5f0712d6e1a50016656d6409e1888546c40fd2f01aab95a05da798b48c1bb9fa01b28d949f903bf3428be1506bb724b13b8e04469bda807ca56d5cdd7d78bd804e9041ebef8e992ff41d441196430efb5ce5ebc4c09f08abd966019132e24cfb54d89fb48d84042963501640b6eec1658d8b1455887cbeae2884cd441ffe0ee1d25b353e83668bc870c9ce8e91991a737e962f8d411d08537352b6fb50c1f65596c9faf1262d9a38e9fb509ecc036b3b0e410b7ef100006c692ca3ba025cda9a13dc649d883bee4c68b051161067d432d080e9e6907e11d895aae0d9e2aa9ebe945e3dee4392bfc353fe98f99895b3bbc69f4"
)

GEN_LoginDataApi = "http://148.113.25.200:2849/getlogindata"


def _gen_veraddr():
    r = httpx.get(
        "https://version.ggwhitehawk.com/live/ver.php",
        params={
            "version": "1.132.3",
            "lang": "hi",
            "device": "android",
            "channel": "android",
            "appstore": "googleplay",
            "region": "IND",
            "whitelist_version": "1.3.0",
            "whitelist_sp_version": "1.0.0",
        },
        timeout=15, verify=False,
    )
    d = r.json()
    Ob = d["remote_version"]
    Ver = d["latest_release_version"]
    LoginBp = d["server_url"].replace("https://", "").replace("http://", "").rstrip("/")
    return Ver, Ob, LoginBp


GEN_NAME_PREFIX = "vxt-bot_"        #  naye accounts is prefix se banenge


def _gen_name():
    chars = string.ascii_lowercase + string.digits
    return GEN_NAME_PREFIX + ''.join(random.choices(chars, k=4))


def _gen_pwd():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=64))


def _gen_sig(payload):
    return hmac.new(GEN_Akey, payload.encode(), hashlib.sha256).hexdigest()


def _gen_reg(app_ver):
    Pwd = _gen_pwd()
    UaStr = random.choice(GEN_UserAgents)
    Url = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
    Data = {"app_id": 100067, "client_type": 2, "password": Pwd, "source": 2}
    Text = json.dumps(Data, separators=(',', ':'))
    Sig = _gen_sig(Text)
    Hdr = {
        "User-Agent": UaStr,
        "Authorization": f"Signature {Sig}",
        "Cookie": GEN_SharedCookie,
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Host": "100067.connect.garena.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
    }
    r = requests.post(Url, headers=Hdr, data=Text, verify=False, timeout=25)
    j = r.json()
    if "data" in j and "uid" in j["data"]:
        return j["data"]["uid"], Pwd, Sig
    raise Exception(f"Reg failed: {j}")


def _gen_accs(uid, pwd, app_ver):
    UaStr = random.choice(GEN_UserAgents)
    Url = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
    Hdr = {
        "User-Agent": UaStr,
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Host": "100067.connect.garena.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
    }
    Prm = {
        "client_id": 100067,
        "client_secret": GEN_Hkey,
        "client_type": 2,
        "device_id": "",
        "password": pwd,
        "response_type": "token",
        "uid": uid
    }
    payload = json.dumps(Prm, separators=(',', ':'))
    r = requests.post(Url, headers=Hdr, data=payload, verify=False, timeout=25)
    j = r.json()
    if "data" in j and "access_token" in j["data"]:
        return j["data"]["access_token"], j["data"]["open_id"]
    raise Exception(f"Token grant failed: {j}")


def _gen_crvr(n):
    if n < 0: return b''
    H = []
    while True:
        S = n & 0x7F
        n >>= 7
        if n: S |= 0x80
        H.append(S)
        if not n: break
    return bytes(H)


def _gen_f_vint(f, v):
    return _gen_crvr((f << 3) | 0) + _gen_crvr(v)


def _gen_f_str(f, s):
    enc = s.encode() if isinstance(s, str) else s
    return _gen_crvr((f << 3) | 2) + _gen_crvr(len(enc)) + enc


def _gen_f_bytes(f, b):
    return _gen_crvr((f << 3) | 2) + _gen_crvr(len(b)) + b


def _gen_enaes(hex_data):
    key = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
    iv = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(bytes.fromhex(hex_data), AES.block_size)).hex()


def _gen_encode_open_id(open_id):
    ks = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,
          0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]
    return ''.join(chr(ord(c) ^ ks[i % len(ks)]) for i, c in enumerate(open_id)).encode('latin1')


def _gen_majreg(nick, access_tok, open_id, pwd, host, ob):
    Url = f"https://{host}/MajorRegister"
    fields = {
        1:  nick,
        2:  access_tok,
        3:  open_id,
        5:  102000007,
        6:  4,
        7:  1,
        13: 1,
        14: _gen_encode_open_id(open_id),
        15: "hi",
        16: 2,
        20: GEN_GameVer,
        21: 1,
        22: GEN_GgreBlob,
    }
    body = b''
    for k, v in fields.items():
        if isinstance(v, int):
            body += _gen_f_vint(k, v)
        elif isinstance(v, bytes):
            body += _gen_f_bytes(k, v)
        else:
            body += _gen_f_str(k, v)
    Payload = bytes.fromhex(_gen_enaes(body.hex()))
    Hdr = {
        "User-Agent": GEN_UaUnity,
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Authorization": "Bearer",
        "X-GA": "v1 1",
        "X-GA-SV": str(int(time.time())),
        "ReleaseVersion": GEN_ReleaseVer,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": GEN_uVer,
        "Host": host,
        "Connection": "Keep-Alive",
    }
    return requests.post(Url, headers=Hdr, data=Payload, verify=False, timeout=25)


def _gen_check_active(uid, pwd):
    try:
        r = requests.get(
            GEN_LoginDataApi,
            params={"uid": uid, "pass": pwd},
            timeout=20, verify=False,
        )
        return r.json()
    except Exception:
        return {}


def _gen_save_account(uid, pwd):
    filename = ACCOUNTS_FILE
    accounts = []
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    accounts = data
        except Exception:
            accounts = []
    for acc in accounts:
        if str(acc.get("uid")) == str(uid):
            return
    accounts.append({"uid": str(uid), "password": str(pwd)})
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=2)
    except Exception as e:
        print(f"  Save error: {e}")


def _gen_one_account(ver, ob, host):
    """Sync: garena reg + token grant + MajorRegister. Returns (uid, pwd, nick, reg_ok).
    BR_ACCOUNT_DIRTY_NAME aane pe naam ke alag formats try karta hai."""
    Uid, Pwd, Sig = _gen_reg(ver)
    AccessTok, OpenId = _gen_accs(Uid, Pwd, ver)

    sfx = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    tag = GEN_NAME_PREFIX.strip().rstrip("_")   # "FYT"
    candidates = [
        f"{tag}_{sfx}",      # FYT_1e47   direct ye (server accept karta hai)
        f"{tag}{sfx}",       # FYT1e47   (fallback)
        f"vai_{sfx}",        # fallback (proven)
    ]

    reg_ok = False
    Nick = candidates[-1]
    for cand in candidates:
        Resp = _gen_majreg(cand, AccessTok, OpenId, Pwd, host, ob)
        if Resp.status_code == 200:
            Nick = cand
            reg_ok = True
            break
        try:
            err_txt = Resp.text[:100]
        except Exception:
            err_txt = "<no body>"
        print(f"  MajReg    => {Resp.status_code} | {err_txt} | rejected: '{cand}'")
        # naam ke alawa koi aur error (version/config) -> aage retry bekaar hai
        if "DIRTY_NAME" not in err_txt.upper():
            break
    return Uid, Pwd, Nick, reg_ok


async def auto_generate_accounts(count=4):
    print_info(f"GEN: {count} accounts ({GEN_NAME_PREFIX}xxxx)")
    loop = asyncio.get_running_loop()
    try:
        Ver, Ob, Host = await loop.run_in_executor(None, _gen_veraddr)
    except Exception as e:
        print_error(f"version config fail: {e}")
        return 0
    saved = 0
    for i in range(count):
        try:
            Uid, Pwd, Nick, reg_ok = await loop.run_in_executor(None, _gen_one_account, Ver, Ob, Host)
        except Exception as e:
            print_error(f"[{i+1}/{count}] err: {e}")
            continue
        print_success(f"UID => {Uid}")
        print_success(f"PASS => {Pwd}")
        acc = await process_account_uid_pass(str(Uid), str(Pwd))
        if acc:
            saved += 1
            _gen_save_account(str(Uid), str(Pwd))
        else:
            print_error(f"[{i+1}/{count}] login fail")
    print_success(f"GEN done: {saved}/{count} saved")
    return saved


# =========================== GLORY COUNTER (persisted) ===========================
GLORY_FILE = "glory_count.json"

def _load_glory() -> int:
    try:
        with open(GLORY_FILE, "r", encoding="utf-8") as f:
            return int(json.load(f).get("glory", 0))
    except Exception:
        return 0

def _save_glory(n: int) -> None:
    try:
        with open(GLORY_FILE, "w", encoding="utf-8") as f:
            json.dump({"glory": n}, f)
    except Exception:
        pass

GLORY_COUNT = _load_glory()
_glory_lock = asyncio.Lock()

async def add_glory(n: int = 1) -> int:
    global GLORY_COUNT
    async with _glory_lock:
        GLORY_COUNT += n
        _save_glory(GLORY_COUNT)
        total = GLORY_COUNT
    print_success(f"GLORY +{n} => TOTAL: {total}")
    return total

# ============================== DEVICE ==============================
def get_device_for_account(account_identifier):
    devices = {}
    if os.path.exists(DEVICES_FILE):
        try:
            with open(DEVICES_FILE, "r", encoding="utf-8") as f:
                devices = json.load(f)
        except Exception: pass
    key = str(account_identifier)
    if key in devices: return devices[key]
    dev_list = [
        ("Samsung", "SM-G998B", "Adreno (TM) 660", "Android OS 12 / API-31"),
        ("Xiaomi", "2201122G", "Adreno (TM) 730", "Android OS 13 / API-33"),
        ("Realme", "RMX3700", "Mali-G710", "Android OS 14 / API-34"),
        ("OnePlus", "CPH2451", "Adreno (TM) 740", "Android OS 13 / API-33"),
        ("OPPO", "CPH2611", "Adreno (TM) 720", "Android OS 14 / API-34"),
    ]
    brand, model, gpu, os_ver = random.choice(dev_list)
    dev = {
        "unique_device_id": f"Google|{uuid.uuid4()}",
        "brand": brand, "model": model, "gpu_renderer": gpu, "system_software": os_ver,
        "screen_width": random.choice([1080, 1440, 720]),
        "screen_height": random.choice([2400, 3200, 1600]),
        "screen_dpi": str(random.randint(300, 420)),
        "memory": random.randint(2800, 6500),
        "processor_details": f"ARM64 FP ASIMD AES | {random.randint(2200, 3200)} | {random.randint(6, 12)}",
        "client_ip": f"{random.randint(103, 223)}.{random.randint(10, 250)}.{random.randint(10, 250)}.{random.randint(10, 250)}",
    }
    devices[key] = dev
    try:
        with open(DEVICES_FILE, "w", encoding="utf-8") as f:
            json.dump(devices, f, indent=2)
    except Exception: pass
    return dev

# =========================== DNS ===========================
_DNS_CACHE: Dict[str, Tuple[str, float]] = {}
_DNS_CACHE_TTL = 300.0

async def resolve_host_cloudflare(hostname):
    if not hostname: return hostname
    parts = hostname.split('.')
    if len(parts) == 4 and all(p.isdigit() for p in parts): return hostname
    now = time.time()
    if hostname in _DNS_CACHE:
        ip, exp = _DNS_CACHE[hostname]
        if now < exp: return ip
    try:
        loop = asyncio.get_running_loop()
        info = await loop.getaddrinfo(hostname, None, family=socket.AF_INET)
        if info:
            ip = info[0][4][0]
            _DNS_CACHE[hostname] = (ip, now + _DNS_CACHE_TTL)
            return ip
    except Exception: pass
    return hostname

def optimize_tcp_socket(sock):
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
    except Exception: pass

def optimize_udp_socket(sock):
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 131072)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 131072)
    except Exception: pass

# =========================== HTTP CLIENT ===========================
client = httpx.AsyncClient(verify=False, timeout=10.0,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=50))
headers = {
    'User-Agent': 'UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
    'Connection': 'Keep-Alive', 'Accept-Encoding': 'gzip',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Unity-Version': '2018.4.12f1', 'X-GA-SV': '1789535859',
    'X-GA': 'v1 1', 'ReleaseVersion': 'OB55'
}

AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV  = b'6oyZDr22E3ychjM%'

CRC7_TABLE = bytes([
    0,9,18,27,36,45,54,63,72,65,90,83,108,101,126,119,25,16,11,2,61,52,47,38,
    81,88,67,74,117,124,103,110,50,59,32,41,22,31,4,13,122,115,104,97,94,87,76,69,
    43,34,57,48,15,6,29,20,99,106,113,120,71,78,85,92,100,109,118,127,64,73,82,91,
    44,37,62,55,8,1,26,19,125,116,111,102,89,80,75,66,53,60,39,46,17,24,3,10,
    86,95,68,77,114,123,96,105,30,23,12,5,58,51,40,33,79,70,93,84,107,98,121,112,
    7,14,21,28,35,42,49,56,65,72,83,90,101,108,119,126,9,0,27,18,45,36,63,54,
    88,81,74,67,124,117,110,103,16,25,2,11,52,61,38,47,115,122,97,104,87,94,69,76,
    59,50,41,32,31,22,13,4,106,99,120,113,78,71,92,85,34,43,48,57,6,15,20,29,
    37,44,55,62,1,8,19,26,109,100,127,118,73,64,91,82,60,53,46,39,24,17,10,3,
    116,125,102,111,80,89,66,75,23,30,5,12,51,58,33,40,95,86,77,68,123,114,105,96,
    14,7,28,21,42,35,56,49,70,79,84,93,98,107,112,121,
])
_DELTA = 0x9E3779B9
_ROUNDS = 16
_FIELD_SIZES = {0:1, 1:2, 2:2, 3:1, 4:2}
_FIELD_NAMES = {0:"sendOption", 1:"cmd", 2:"orderId", 3:"flags", 4:"length"}

# =========================== LOG ===========================
class Colors:
    GREEN=FAIL=WARNING=CYAN=MAGENTA=WHITE=HEADER=ENDC=''

def _pb(tag, t):
    try: print(f"\033[1m》》 {tag} {t}\033[0m")
    except Exception: pass

def print_colored(t, c=None):
    _pb("", t)

def print_success(t):
    _pb("[+]", t)

def print_error(t):
    _pb("[-]", t)

def print_warning(t):
    _pb("[!]", t)

def print_info(t):
    _pb("[i]", t)

def get_proto_field(d, key, default=None):
    if not d or not isinstance(d, dict): return default
    if key in d:
        v = d[key].get('data'); return v if v is not None else default
    if str(key) in d:
        v = d[str(key)].get('data'); return v if v is not None else default
    return default

# =========================== MATCH COUNTER ===========================
_match_counters: Dict[str, int] = {}
_match_counter_lock = asyncio.Lock()

async def _inc_match(uid):
    async with _match_counter_lock:
        _match_counters[uid] = _match_counters.get(uid, 0) + 1
        return _match_counters[uid]

async def _dec_match(uid):
    async with _match_counter_lock:
        if uid in _match_counters and _match_counters[uid] > 0:
            _match_counters[uid] -= 1
        return _match_counters.get(uid, 0)

async def _get_match_count(uid):
    async with _match_counter_lock:
        return _match_counters.get(uid, 0)

async def _get_total_match_count():
    async with _match_counter_lock:
        return sum(_match_counters.values())

# =========================== SQUAD STATE ===========================
_team_state = {
    "peers": {},
    "leader_uid": None,
    "team_code": None,
    "pk_code": None,
    "members": set(),
    "members_lock": asyncio.Lock(),
    "lock": asyncio.Lock(),
}

async def _team_member_join(uid):
    uid = str(uid)
    async with _team_state["members_lock"]:
        before = len(_team_state["members"])
        _team_state["members"].add(uid)
        after = len(_team_state["members"])
    if after != before:
        print_success(f"[TEAM]  In team ({after}/{TEAM_SIZE}) | joined: {uid}")
        try:
            for p_uid in list(_team_state["peers"].keys()):
                role = "LEADER" if _team_state["leader_uid"] == p_uid else "MEMBER"
                joined = p_uid in _team_state["members"]
                tag = f"IN_TEAM ({after}/{TEAM_SIZE}) [{role}]" if joined else f"JOINING ({after}/{TEAM_SIZE}) [{role}]"
                bot_state.update_status(p_uid, tag, 0)
        except Exception: pass
    return after

async def _team_member_leave(uid):
    async with _team_state["members_lock"]:
        _team_state["members"].discard(str(uid))

async def _team_member_count():
    async with _team_state["members_lock"]:
        return len(_team_state["members"])

async def _team_member_reset(keep_leader=True):
    async with _team_state["members_lock"]:
        _team_state["members"].clear()
        if keep_leader and _team_state["leader_uid"]:
            _team_state["members"].add(_team_state["leader_uid"])

# =========================== TOKEN CACHE ===========================
_token_cache_memo = {}
_token_cache_memo_time = 0.0
_TOKEN_CACHE_MEMO_TTL = 5.0

def _json_serializer(obj):
    if isinstance(obj, (bytes, bytearray)): return {"__bytes_hex__": bytes(obj).hex()}
    raise TypeError(f"not serializable: {type(obj)}")

def _json_deserializer(obj):
    if isinstance(obj, dict):
        if "__bytes_hex__" in obj and len(obj) == 1:
            try: return bytes.fromhex(obj["__bytes_hex__"])
            except Exception: return b""
        return {k: _json_deserializer(v) for k, v in obj.items()}
    if isinstance(obj, list): return [_json_deserializer(x) for x in obj]
    return obj

def _load_token_cache():
    global _token_cache_memo, _token_cache_memo_time
    now = time.time()
    if _token_cache_memo and (now - _token_cache_memo_time) < _TOKEN_CACHE_MEMO_TTL:
        return _token_cache_memo
    if not os.path.exists(TOKEN_CACHE_FILE): return {}
    try:
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content: return {}
        data = json.loads(content)
        if not isinstance(data, dict): raise ValueError("root must be dict")
        parsed = _json_deserializer(data)
        _token_cache_memo = parsed; _token_cache_memo_time = now
        return parsed
    except Exception as e:
        print_error(f"Token cache corrupt -> delete: {e}")
        try: os.remove(TOKEN_CACHE_FILE)
        except Exception: pass
        return {}

def _save_token_cache(cache):
    global _token_cache_memo, _token_cache_memo_time
    try:
        tmp = TOKEN_CACHE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, default=_json_serializer)
        os.replace(tmp, TOKEN_CACHE_FILE)
        _token_cache_memo = cache; _token_cache_memo_time = time.time()
    except Exception as e: print_error(f"Cache save: {e}")

def cache_get(uid):
    cache = _load_token_cache()
    e = cache.get(str(uid))
    if not e: return None
    if time.time() - e.get("cached_at", 0) > TOKEN_CACHE_TTL:
        cache_invalidate(uid); return None
    if str(e.get("account_id", "")).isdigit(): e["account_id"] = int(e["account_id"])
    if not isinstance(e.get("login_payload_data"), (bytes, bytearray)):
        cache_invalidate(uid); return None
    return e

def cache_set(uid, data):
    cache = _load_token_cache()
    e = dict(data); e["cached_at"] = time.time()
    cache[str(uid)] = e; _save_token_cache(cache)
    print_success(f"[CACHE] Saved UID {uid}")

def cache_invalidate(uid):
    cache = _load_token_cache()
    if str(uid) in cache:
        del cache[str(uid)]; _save_token_cache(cache)

def _update_cache_profile(data, level, exp):
    try:
        keys = []
        if data.get('auth_uid'): keys.append(str(data['auth_uid']))
        if data.get('auth_token'): keys.append(f"tok_{data['auth_token'][:20]}")
        if not keys: return
        cache = _load_token_cache(); ch = False
        for k in keys:
            if k in cache and isinstance(cache[k], dict):
                cache[k]['level'] = level; cache[k]['exp'] = exp; ch = True
        if ch: _save_token_cache(cache)
    except Exception: pass

# =========================== ENCRYPTION ===========================
async def aes_encrypt(payload, key, iv):
    return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(payload, AES.block_size))

async def get_playstore_version():
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, lambda: play_scraper('com.dts.freefireth', lang='hi', country='id'))
    return res.get("version")

async def version_config():
    app_version = await get_playstore_version()
    url = ("https://version.ggwhitehawk.com/live/ver.php"
           f"?version={app_version}&lang=hi&device=android&channel=android"
           "&appstore=googleplay&region=ID&whitelist_version=1.3.0&whitelist_sp_version=1.0.0")
    try:
        r = await client.get(url); r.raise_for_status()
        d = r.json()
        su = d.get("server_url"); rv = d.get("remote_version"); lr = d.get("latest_release_version")
        if not su or not rv or not lr: return None
        return lr, rv, su
    except Exception: return None

async def get_access_token(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    hdrs = {
        "Host": "100067.connect.garena.com",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; SM-G998B)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br", "Connection": "close"
    }
    data = {
        "uid": uid, "password": password, "response_type": "token", "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"
    }
    for attempt in range(5):
        try:
            r = await client.post(url, headers=hdrs, data=data)
            if r.status_code == 200:
                d = r.json()
                oid = d.get("open_id"); at = d.get("access_token"); pf = d.get("platform", 4)
                if oid and at: return oid, at, pf
            if r.status_code == 429: await asyncio.sleep(1); continue
        except Exception: pass
        await asyncio.sleep(0.5)
    return None

async def parse_results(parsed):
    out = {}
    for r in parsed:
        fd = {"wire_type": r.wire_type}
        if r.wire_type in ("varint", "string", "bytes"): fd["data"] = r.data
        elif r.wire_type == "length_delimited":
            fd["data"] = await parse_results(r.data.results)
        out[r.field] = fd
    return out

async def decode_protobuf(data):
    parsed = Parser().parse(data)
    return json.dumps(await parse_results(parsed))

def decode_protobuf_dict_safe(data):
    try:
        parsed = Parser().parse(data)
        return _recursive_dict(parsed)
    except Exception: return {}

def _recursive_dict(results):
    out = {}
    for r in results:
        fd = {"wire_type": r.wire_type}
        if r.wire_type in ("varint", "string", "bytes"): fd["data"] = r.data
        elif r.wire_type == "length_delimited":
            if hasattr(r.data, "results"): fd["data"] = _recursive_dict(r.data.results)
            elif isinstance(r.data, list): fd["data"] = _recursive_dict(r.data)
            else: fd["data"] = str(r.data)
        out[str(r.field)] = fd
    return out

def _decode_proto_manual(data):
    """Manual protobuf decode (fallback)."""
    result = {}; offset = 0; data_len = len(data)
    while offset < data_len:
        header = 0; shift = 0
        while offset < data_len:
            b = data[offset]; offset += 1
            header |= (b & 0x7F) << shift
            if not (b & 0x80): break
            shift += 7
            if shift > 28: break
        if header == 0: break
        fn = header >> 3; wt = header & 0x7
        if fn == 0: break
        if wt == 0:
            v = 0; shift = 0
            while offset < data_len:
                b = data[offset]; offset += 1
                v |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
                if shift > 63: break
            result[fn] = v
        elif wt == 2:
            length = 0; shift = 0
            while offset < data_len:
                b = data[offset]; offset += 1
                length |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
                if shift > 28: break
            if length > data_len - offset: break
            value = data[offset:offset+length]; offset += length
            try:
                s = value.decode('utf-8')
                if s and all(31 < ord(c) < 127 or ord(c) in (9,10,13) for c in s):
                    result[fn] = s
                else:
                    nested = _decode_proto_manual(value)
                    result[fn] = nested if nested else value.hex()
            except UnicodeDecodeError:
                nested = _decode_proto_manual(value)
                result[fn] = nested if nested else value.hex()
        elif wt == 5: offset += 4
        elif wt == 1: offset += 8
        else: break
    return result

# =========================== MANUAL PROTOBUF ENCODE ===========================
def encode_varint(n):
    if n < 0: return b''
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        if n: b |= 0x80
        out.append(b)
        if not n: break
    return bytes(out)

def build_proto(fields):
    parts = []
    for k, v in fields.items():
        if isinstance(v, dict):
            nested = build_proto(v)
            parts.append(encode_varint((k << 3) | 2) + encode_varint(len(nested)) + nested)
        elif isinstance(v, int):
            parts.append(encode_varint((k << 3) | 0) + encode_varint(v))
        elif isinstance(v, (str, bytes)):
            ev = v.encode() if isinstance(v, str) else v
            parts.append(encode_varint((k << 3) | 2) + encode_varint(len(ev)) + ev)
    return b''.join(parts)

def encrypt_api(plain_hex):
    return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(
        pad(bytes.fromhex(plain_hex), AES.block_size)).hex()

def encrypt_api_bytes(plain_bytes):
    return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(plain_bytes, AES.block_size))

# =========================== SQUAD PROTOBUF BUILDERS ===========================
def _pb_varint(fn, val): return encode_varint((fn << 3) | 0) + encode_varint(val)
def _pb_length(fn, val):
    enc = val.encode('utf-8') if isinstance(val, str) else val
    return encode_varint((fn << 3) | 2) + encode_varint(len(enc)) + enc

def create_proto(fields):
    packet = bytearray()
    for field, value in fields.items():
        if isinstance(field, str): field = int(field)
        if isinstance(value, dict):
            packet.extend(_pb_length(field, bytes(create_proto(value))))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    packet.extend(_pb_length(field, bytes(create_proto(item))))
                elif isinstance(item, str): packet.extend(_pb_length(field, item))
                elif isinstance(item, (bytes, bytearray)): packet.extend(_pb_length(field, bytes(item)))
                elif isinstance(item, bool): packet.extend(_pb_varint(field, 1 if item else 0))
                elif isinstance(item, int): packet.extend(_pb_varint(field, item))
        elif isinstance(value, bool): packet.extend(_pb_varint(field, 1 if value else 0))
        elif isinstance(value, int): packet.extend(_pb_varint(field, value))
        elif isinstance(value, str): packet.extend(_pb_length(field, value))
        elif isinstance(value, (bytes, bytearray)): packet.extend(_pb_length(field, bytes(value)))
    return bytes(packet)

def create_packet(Pk, N, K, V):
    if isinstance(K, str): K = bytes.fromhex(K) if len(K) == 32 else K.encode()
    if isinstance(V, str): V = bytes.fromhex(V) if len(V) == 32 else V.encode()
    PkEnc = AES.new(K, AES.MODE_CBC, V).encrypt(pad(bytes.fromhex(Pk), 16)).hex()
    L = len(PkEnc) // 2
    hexlen = hex(L)[2:]
    if len(hexlen) % 2 != 0: hexlen = '0' + hexlen
    pad_len = 12 - len(N) - len(hexlen)
    if pad_len < 0: pad_len = 0
    return bytes.fromhex(N + ('0' * pad_len) + hexlen + PkEnc)

# =========== SQUAD PACKETS ===========
def _sq_prefix(base, region="ID"):
    reg = str(region).upper() if region else "ID"
    if reg == "IND":
        return base + "14"
    return base + "15"   # ID/default - capture-verified

def create_team(key, iv, game_version="1.132.9"):
    fields = {
        1: 1, 2: {2: bytes.fromhex("01"), 3: 1, 4: 3, 5: "en",
            8: {1: "IDC3", 2: 123, 3: "ID"}, 9: 1,
            10: bytes.fromhex("01090a0b1219202729"), 11: 2, 13: 1,
            14: {1: "08FBA33B4BABE2790205390333330000009700050092005F72697EB2134DCBB2467625142201040e38e848dc0e748c3f6aa04d81000000ff1113090dcacfa16d",
                 2: 478, 3: "7e585d55", 4: "y[Z]", 6: 12, 7: "15686677735a7506101c",
                 8: str(game_version), 9: 3, 10: 1, 11: "03626253513637754174"},
            19: 329, 21: bytes.fromhex("374f521955"), 24: {1: 21},
            27: "a_6534489873065906362"}}
    return create_packet(create_proto(fields).hex(), "0515", key, iv)

def team_fresh(account_id, key, iv):
    return create_packet(create_proto({1: 72, 2: {1: int(account_id)}}).hex(), "0515", key, iv)

def invite_player_in_team(target_uid, key, iv, region="ID"):
    return create_packet(create_proto({1: 2, 2: {1: int(target_uid), 2: region, 4: 1}}).hex(),
                         _sq_prefix("05", region), key, iv)

def accept_team_invite(target_uid, group_id, key, iv, region="ID"):
    fields = {1: 4, 2: {1: int(target_uid), 3: int(target_uid),
        4: bytes.fromhex("0107090a0b120f19202729"), 8: 1,
        9: {1: "08FBA33B0522052002041B0222220007000C00010004000547E265AE1080779546762514110104076fa2e8770e748c3f6a68ed75000000ff08080500cacfa16d",
            2: 235, 3: {14: 80, 11: 86}, 4: "{Y\\R", 6: 13, 7: {2: 4},
            8: "1.132.9", 9: 2, 10: 1, 11: "0362625351"},
        10: str(group_id),
        11: {"1": "IDC3", "2": 107, "3": "ID"}, 13: "en", 16: "374f5219",
        20: {1: 21}, 23: "a_6534489873065906362",
        24: "https://dl-sg-production.freefiremobile.com/",
        27: {1: 2, 2: 4}}}
    return create_packet(create_proto(fields).hex(), _sq_prefix("05", region), key, iv)

def start_match_team(account_id, key, iv, region="ID"):
    fields = {1: 9, 2: {1: int(account_id), 7: {1: "IDC3", 2: 410, 3: region}}}
    return create_packet(create_proto(fields).hex(), _sq_prefix("05", region), key, iv)

def ready_for_game(uid, key, iv):
    return create_packet(create_proto({1: 15, 2: {1: uid, 2: 1}}).hex(), "0519", key, iv)

# =========================== MAJORLOGIN / GETLOGIN ===========================
async def build_majorlogin_payload(open_id, access_token, platform, client_version, device_info):
    """
    Dono flows ke liye — Guest (platform=4) aur Token (3/4/8/11).
    """
    try:
        try:
            platform_int = int(platform)
        except (ValueError, TypeError):
            platform_int = 4
        platform_str = str(platform_int)

        print_info(f"[MAJORLOGIN] platform={platform_str}")

        major_login = MajoRLoGinrEq_pb2.MajorLogin()
        major_login.open_id = open_id
        major_login.access_token = access_token
        major_login.client_version = client_version
        major_login.event_time = str(datetime.now())[:-7]
        major_login.game_name = "free fire"
        major_login.platform_id = 1
        major_login.system_software = "Android OS 10 / API-29 (QP1A.190711.020/V12.0.26.0.QCDINXM)"
        major_login.system_hardware = "Handheld"
        major_login.telecom_operator = "Ncell"
        major_login.network_type = "WIFI"
        major_login.screen_width = 1600
        major_login.screen_height = 720
        major_login.screen_dpi = "320"
        major_login.processor_details = "ARMv7 VFPv3 NEON | 2001 | 8"
        major_login.memory = 3790
        major_login.gpu_renderer = "PowerVR Rogue GE8320"
        major_login.gpu_version = "OpenGL ES 3.2 build 1.11@5425693"
        major_login.unique_device_id = "Google|00000000-0000-0000-0000-000000000000"
        major_login.client_ip = "111.119.38.133"
        major_login.language = "en"

        # ✅ DYNAMIC #1
        major_login.open_id_type = platform_str

        major_login.device_type = "Handheld"
        major_login.device_model = "Xiaomi M2006C3LII"
        major_login.country_code = "BD"
        major_login.platform_sdk_id = 1
        major_login.network_operator_a = "Ncell"
        major_login.network_type_a = "WIFI"
        major_login.client_using_version = "1ac4b80ecf0478a44203bf8fac6120f5"
        major_login.external_storage_total = 53041
        major_login.external_storage_available = 7291
        major_login.internal_storage_total = 2176
        major_login.game_disk_storage_available = 7395
        major_login.game_disk_storage_total = 53041
        major_login.external_sdcard_avail_storage = 7395
        major_login.external_sdcard_total_storage = 53041
        major_login.field_70 = 4
        major_login.login_by = 2
        major_login.library_path = "/data/app/com.dts.freefireth-yAPXAhp2RyIlrtNAM0VzKQ==/lib/arm"
        major_login.reg_avatar = 1
        major_login.library_token = "066a589fa3f5658377634fe7b1d88556|/data/app/com.dts.freefireth-yAPXAhp2RyIlrtNAM0VzKQ==/base.apk"
        major_login.channel_type = 6
        major_login.cpu_type = 1
        major_login.cpu_architecture = "32"
        major_login.client_version_code = "2019121227"
        major_login.field_85 = 3
        major_login.graphics_api = "OpenGLES2"
        major_login.supported_astc_bitset = 3071
        major_login.login_open_id_type = 4
        major_login.loading_time = 9329
        major_login.release_channel = "3rd_party"
        major_login.extra_info = "KqsHT3r+fXQIu/dyZrEa8fJBhbJ5uqDES7YsAUfu+Mck9A+Bly6lFfYk7Q7Nj68pqI8I3g4Oz3gLxWef6Eh/jKyzHug="
        major_login.android_engine_init_flag = 111207
        major_login.field_96 = json.dumps({"cur_rate": None, "support_etc2": False}, separators=(',', ':'))
        major_login.if_push = 1

        # ✅ DYNAMIC #2 & #3
        major_login.origin_platform_type = platform_str
        major_login.primary_platform_type = platform_str

        major_login.field_102 = bytes.fromhex("42 54 4c 10 53 0e 5b 04 30")
        major_login.field_104 = 47591
        major_login.field_105 = 1
        major_login.field_106 = "https://dl-bs.ggpolarbear.com/live/ABHotUpdates/|https://core-bs.ggpolarbear.com/live/ABHotUpdates/|1c2462939e53942fc995400436a3dc7b"
        major_login.field_107 = "c8e41b7a93f02d56e1a94c7b8203f5d1"
        string = major_login.SerializeToString()
        return encrypt_api_bytes(string)
    except Exception as e:
        print_error(f"build_majorlogin_payload: {type(e).__name__}: {e}")
        return None




class _PaidLoginAdapter:
    def __init__(self, response):
        self._response = response
        self.account_id = response.account_id
        self.token = response.token
        self.url = response.server_url
        self.region = response.lock_region
        self.kts = response.kts
        self.ak = response.ak
        self.aiv = response.aiv
        # Legacy guild caller expects these names; Paid ANURAG SINGH uses kts/ak/aiv.
        raw_ts = response.kts
        try:
            self.server_time = int(raw_ts)
            if self.server_time > 10**11:  # milliseconds -> seconds
                self.server_time //= 1000
            if self.server_time <= 0:
                raise ValueError("invalid server timestamp")
        except (ValueError, TypeError, OverflowError):
            self.server_time = int(time.time())
        self.aes_ak = response.ak
        self.iv_i = response.aiv
    def __getattr__(self, key):
        return getattr(self._response, key)

def _adapt_paid_login(response):
    return _PaidLoginAdapter(response)

async def send_majorlogin(data, release_version, server_url):
    try:
        url = f"{server_url.rstrip('/')}/MajorLogin"
        req_headers = headers.copy()
        req_headers["ReleaseVersion"] = release_version
        response = await client.post(url, headers=req_headers, data=data)
        if response.status_code != 200:
            print_error(f"MajorLogin HTTP {response.status_code}: {response.text[:200]}")
            return None
        response_content = response.content
        if len(response_content) < 40:
            return None
        proto_payload = response_content[64:] if len(response_content) > 64 else response_content

        res_proto = MajorLoginRes()
        try:
            res_proto.ParseFromString(proto_payload)
            if res_proto.lock_region and res_proto.token:
                return _adapt_paid_login(res_proto)
        except Exception:
            pass

        for offset in range(min(128, len(proto_payload))):
            try:
                candidate = MajorLoginRes()
                candidate.ParseFromString(proto_payload[offset:])
                if candidate.lock_region and candidate.token:
                    return _adapt_paid_login(candidate)
            except Exception:
                pass

        print_error("MajorLogin parse failed at all offsets")
        return None
    except Exception as e:
        print_error(f"send_majorlogin EXC: {type(e).__name__}: {e}")
        return None



async def send_getlogin(data, base_url, token, release_version):
    try:
        url = f"{base_url.rstrip('/')}/GetLoginData"
        hdrs = headers.copy()
        hdrs["ReleaseVersion"] = release_version
        hdrs["X-GA-SV"] = str(int(time.time()))
        hdrs['Authorization'] = f"Bearer {token}"
        try:
            from urllib.parse import urlparse as _urlp
            hdrs['Host'] = (_urlp(base_url).hostname or "clientbp.ppmainecoonghj.com")
        except Exception:
            hdrs['Host'] = "clientbp.ppmainecoonghj.com"
        r = await client.post(url, headers=hdrs, data=data)
        if r.status_code != 200: return None
        c = r.content
        rp = get_login_data_pb2.GetLoginDataRes()
        ok = False
        try:
            rp.ParseFromString(c)
            if rp.functional_addrs or rp.informational_addrs: ok = True
        except Exception: pass
        if not ok:
            for off in range(min(128, len(c))):
                try:
                    cand = get_login_data_pb2.GetLoginDataRes(); cand.ParseFromString(c[off:])
                    if cand.functional_addrs or cand.informational_addrs:
                        rp = cand; break
                except Exception: continue
        dd = {}
        try:
            parsed = Parser().parse(c.hex())
            dd = await parse_results(parsed)
        except Exception: pass
        return rp, dd
    except Exception: return None

# =========================== HTTP PING ===========================
async def send_ping(account_id, token, release_version, ping_url=None):
    try:
        try: acc = int(account_id)
        except Exception: acc = 0
        now_ms = int(time.time() * 1000)
        payload = struct.pack("<Q", acc & 0xFFFFFFFFFFFFFFFF) + struct.pack("<Q", now_ms & 0xFFFFFFFFFFFFFFFF)
        req_id = secrets.token_urlsafe(18)[:22]
        hdrs = {
            'accept': '*/*', 'accept-encoding': 'deflate, gzip',
            'authorization': f'Bearer {token}',
            'content-type': 'application/x-www-form-urlencoded',
            'releaseversion': release_version,
            'user-agent': 'UnityPlayer/2018.4.12f1',
            'x-ga': 'v1 1', 'x-ga-sv': str(int(time.time())),
            'x-railway-edge': 'sin1', 'x-railway-request-id': req_id,
            'x-real-ip': PING_REAL_IP, 'x-request-start': str(now_ms),
            'x-unity-version': '2018.4.12f1',
        }
        r = await client.post(str(ping_url or PING_URL), headers=hdrs, content=payload, timeout=PING_TIMEOUT)
        return r.status_code == 200
    except Exception: return False

async def ping_worker(account_id, token, release_version, region="ID", ping_url=None):
    if not ENABLE_HTTP_PING: return
    _purl = str(ping_url or PING_URL)
    uid_str = str(account_id); ok_count = 0; fails = 0
    try:
        await asyncio.sleep(5.0 + random.uniform(0, 2.0))
        while True:
            ok = await send_ping(uid_str, token, release_version, _purl)
            if ok:
                ok_count += 1; fails = 0
                if ok_count % 10 == 0: print_info(f"[PING] {uid_str} OK total={ok_count}")
            else:
                fails += 1
                if fails <= 3: print_warning(f"[PING] {uid_str} fail #{fails}")
            await asyncio.sleep(max(5.0, PING_INTERVAL + random.uniform(-3.0, 3.0)))
    except asyncio.CancelledError: pass
    finally: print_info(f"[PING] Stopped {uid_str} OK={ok_count}")

# =========================== TCP STARTUP ===========================
async def build_tcp_startup_packet(account_id, token, server_time, key, iv, region="ID", typ='OnLine'):
    uid_hex = f"{int(account_id):016x}"
    ts_hex = f"{int(server_time):08x}"
    enc = (await aes_encrypt(token.encode(), key, iv)).hex()
    enc_len = f"{len(enc)//2:08x}"
    reg = str(region).upper() if region else "ID"
    if typ == 'OnLine':
        pfx = '7119' if reg == 'ID' else ('7114' if reg == 'IND' else '7115')
        return f"{pfx}{uid_hex}{ts_hex}00000000{enc_len}{enc}"
    pfx = '9219' if reg == 'ID' else ('9214' if reg == 'IND' else '9215')
    return f"{pfx}{uid_hex}{ts_hex}{enc_len}{enc}"

async def send_keep_alive(region="ID"):
    try:
        reg = str(region).upper() if region else "ID"
        return bytes.fromhex("0219" if reg == "ID" else ("0214" if reg == "IND" else "0215"))
    except Exception:
        return bytes.fromhex("0219")

# =========================== MATCH SEARCH PACKETS ===========================
BR_HEX = (
    "080112800a0a010110013a110a044944433110aa011a064555524f50453a100a044944433210311a064555524f5045"
    "40014a0801090a0b1219202758016291090a80013038384638324246303241393637363730323031303130303030"
    "30303030303030303031363030303130303135303030323232463937454545304630303030303034363736323531"
    "34303030303030303030303030303030303030303030303030303030303030303030303030306666303030303030"
    "3030636163666131366410241afb02735d5e571400024a775d45414d1a041b1c001f11010449715f4243481a001e"
    "1d071c1703004b1a4066785c524570735c51486775421b5c5a4c07504042685a63610816054e19025e7519600147"
    "7c015165406370195f5547404e4550640103020f1304064863754268676c755f65576e40467e5f0a417a4701026d"
    "675d6e73670b1108495a4c6a0b78470b740065645e525a057258425f584a447d4e6759440c11044e7c596d7f4b62"
    "5f7d04055a47505c4e1d6b5b4107447d7201057d7f0f14084e430457674f7e517d72015172415d027473577c4d61"
    "5f79535256780911030f4d5e027a797f614165067806505d53777750475e75064257076500460817014e741e7e50"
    "78487e7a7c465e7669767153497064605a7376677773550d160148037e18675966787f4c42607a645f577e7b44"
    "1b460776026b18685d0b110205490060020f70676175654674706671797f41067346677c4e06585e780f15074c57"
    "047b40517075415f6364027259674b5b0166407f7340600407770a22047a5d5c52300b3a0a167305067162727516"
    "134208312e3133302e3232480350015ae90403626253513635686e556f4e36416456324b796f566c636f47777648"
    "4f624e56526c4d727073504b4f43654177616848494176795556497273743752737149734a7a786b324752526837"
    "7a2f637664626d504f6a73552f79626d38547a4c69586d2f474351696d494b53486833447955726f39515152756c"
    "34545350626d6d624b7949565937545671577059455372323646572f59624578507338514f706d317372785455736c"
    "30796a434144444d4f34616a654b615753366361496c554b4963797a494e396d52516f715277687939797257476d"
    "337a644345337a6a61436f492f5a585233656f65365a42647a64677654636b6b665733356e4d4c6a6a56507256"
    "4b6433523172756174394e50514150724a5546627859696c4c5a3859707336654d5447666b6649793574666a526c"
    "314d4648706b51774c6373374439656378566c41636f374e664f6d2b30654756466c443474447870677138553359"
    "5973587645384842502f70666c767a737138316a32524f4d7857437556445442492f684735625462773166456e42"
    "49725162762b636144775147696f74554e316d4c4b77734379456f4766706746614251457645672b736a764c4c78"
    "704743334c304a5344532f74526169504354553344374e6249306547516651622f5a466f4c36455630775a324d6f"
    "583932414c572f5049752f56634663584e70596b356f7966326151416a536971486a2f363276354843644f525551"
    "303578754e6171795251625653704654303137655237675255636b4966366c6f447476342b514e4a4670766d7475"
    "7077707774396a5a5974437a4b56743657726d6e36785837706658456251555434684f3758a201050803108703a2"
    "01050804108103a20105080510c001a20105081d10cc01a2010408161078a20105080e10af01a201020815"
)

async def start_game_battle_royale(region, client_version, writer, key, iv):
    packet = bytes.fromhex(BR_HEX)
    try:
        proto = Anuragsingh_pb2.StartMatch(); proto.ParseFromString(packet)
        if hasattr(proto.main, 'region_list') and len(proto.main.region_list) > 0:
            proto.main.region_list[0].region = region
            if len(proto.main.region_list) > 1: proto.main.region_list[1].region = region
        if hasattr(proto.main, 'client_version'):
            proto.main.client_version.remote_version = client_version
        packet = proto.SerializeToString()
    except Exception: pass
    enc = (await aes_encrypt(packet, key, iv)).hex()
    plen = len(enc) // 2
    hl = hex(plen)[2:]
    hl = hl if len(hl) > 1 else "0" + hl
    reg = str(region).upper() if region else "BD"
    pfx = "031500" if reg == "ID" else ("031400" if reg == "IND" else "031500")
    final = pfx + "0" * (6 - len(hl)) + hl + enc
    writer.write(bytes.fromhex(final)); await writer.drain()
    print_info(f"[BR] search sent ({plen}B) R={reg}")

async def start_game_lone_wolf_solo(region, client_version, writer, key, iv):
    packet = bytes.fromhex("080112800a0a010b102b3a110a044944433110aa011a064555524f50453a100a044944433210311a064555524f504540014a0801090a0b1219202758016291090a8001303838463832424630324139363736373032303130313030303030303030303030303136303030313030313530303032323246393745454530463030303030303436373632353134303030303030303030303030303030303030303030303030303030303030303030303030303066663030303030303030636163666131366410241afb02735d5e571400024a775d45414d1a041b1c001f11010449715f4243481a001e1d071c1703004b1a4066785c524570735c51486775421b5c5a4c07504042685a63610816054e19025e75196001477c015165406370195f5547404e4550640103020f1304064863754268676c755f65576e40467e5f0a417a4701026d675d6e73670b1108495a4c6a0b78470b740065645e525a057258425f584a447d4e6759440c11044e7c596d7f4b625f7d04055a47505c4e1d6b5b4107447d7201057d7f0f14084e430457674f7e517d72015172415d027473577c4d615f79535256780911030f4d5e027a797f614165067806505d53777750475e75064257076500460817014e741e7e5078487e7a7c465e7669767153497064605a7376677773550d160148037e18675966787f4c42607a645f577e7b441b460776026b18685d0b110205490060020f70676175654674706671797f41067346677c4e06585e780f15074c57047b40517075415f6364027259674b5b0166407f7340600407770a22047a5d5c52300b3a0a167305067162727516134208312e3133302e3232480350015ae90403626253513635686e556f4e36416456324b796f566c636f477776484f624e56526c4d727073504b4f43654177616848494176795556497273743752737149734a7a786b3247525268377a2f637664626d504f6a73552f79626d38547a4c69586d2f474351696d494b53486833447955726f39515152756c34545350626d6d624b7949565937545671577059455372323646572f59624578507338514f706d317372785455736c30796a434144444d4f34616a654b615753366361496c554b4963797a494e396d52516f715277687939797257476d337a644345337a6a61436f492f5a585233656f65365a42647a64677654636b6b665733356e4d4c6a6a565072564b6433523172756174394e50514150724a5546627859696c4c5a3859707336654d5447666b6649793574666a526c314d4648706b51774c6373374439656378566c41636f374e664f6d2b30654756466c4434744478706771385533595973587645384842502f70666c767a737138316a32524f4d7857437556445442492f684735625462773166456e4249725162762b636144775147696f74554e316d4c4b77734379456f4766706746614251457645672b736a764c4c78704743334c304a5344532f74526169504354553344374e6249306547516651622f5a466f4c36455630775a324d6f583932414c572f5049752f56634663584e70596b356f7966326151416a536971486a2f363276354843644f525551303578754e6171795251625653704654303137655237675255636b4966366c6f447476342b514e4a4670766d74757077707774396a5a5974437a4b56743657726d6e36785837706658456251555434684f3758a201050803108703a201050804108103a20105080510c001a20105081d10cc01a2010408161078a20105080e10af01a201020815")
    proto = Anuragsingh_pb2.StartMatch()
    proto.ParseFromString(packet)
    if hasattr(proto.main, 'region_list') and len(proto.main.region_list) > 0:
        proto.main.region_list[0].region = region
        if len(proto.main.region_list) > 1:
            proto.main.region_list[1].region = region
    if hasattr(proto.main, 'client_version'):
        proto.main.client_version.remote_version = client_version
    packet = proto.SerializeToString()
    encrypted_packet = (await aes_encrypt(packet, key, iv)).hex()
    packet_length = len(encrypted_packet) // 2
    hex_length = hex(packet_length)[2:]
    hex_length = hex_length if len(hex_length) > 1 else "0" + hex_length
    reg = str(region).upper() if region else "BD"
    reg_prefix = "031900" if reg == "BD" else ("031400" if reg == "IND" else "031500")
    final_packet = reg_prefix + "0" * (6 - len(hex_length)) + hex_length + encrypted_packet
    writer.write(bytes.fromhex(final_packet))
    await writer.drain()

# =========================== UDP HELPERS ===========================
async def has_ssan_zig(n):
    z = (n << 1) & 0xFFFFFFFFFFFFFFFF
    out = bytearray()
    while z >= 0x80: out.append((z & 0x7F) | 0x80); z >>= 7
    out.append(z); return bytes(out)

async def uleb_encode(n):
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        if n: b |= 0x80
        out.append(b)
        if not n: break
    return bytes(out)

async def zigzag_encode_signed(n):
    try: n = int(n)
    except Exception: n = 0
    zz = (n << 1) ^ (n >> 63)
    if zz < 0: zz = -zz
    out = bytearray()
    while True:
        b = zz & 0x7F; zz >>= 7
        if zz: b |= 0x80
        out.append(b)
        if not zz: break
    return bytes(out)

async def tea_enc(v0, v1, k0, k1, k2, k3):
    s = 0
    for _ in range(_ROUNDS):
        s = (s + _DELTA) & 0xFFFFFFFF
        v0 = (v0 + (((((v1<<4)&0xFFFFFFFF)+k0)&0xFFFFFFFF ^ ((v1+s)&0xFFFFFFFF) ^ (((v1>>5)+k1)&0xFFFFFFFF)))) & 0xFFFFFFFF
        v1 = (v1 + (((((v0<<4)&0xFFFFFFFF)+k2)&0xFFFFFFFF ^ ((v0+s)&0xFFFFFFFF) ^ (((v0>>5)+k3)&0xFFFFFFFF)))) & 0xFFFFFFFF
    return v0, v1

async def tea_dec(v0, v1, k0, k1, k2, k3):
    s = (_DELTA * _ROUNDS) & 0xFFFFFFFF
    for _ in range(_ROUNDS):
        v1 = (v1 - (((((v0<<4)&0xFFFFFFFF)+k2)&0xFFFFFFFF ^ ((v0+s)&0xFFFFFFFF) ^ (((v0>>5)+k3)&0xFFFFFFFF)))) & 0xFFFFFFFF
        v0 = (v0 - (((((v1<<4)&0xFFFFFFFF)+k0)&0xFFFFFFFF ^ ((v1+s)&0xFFFFFFFF) ^ (((v1>>5)+k1)&0xFFFFFFFF)))) & 0xFFFFFFFF
        s = (s - _DELTA) & 0xFFFFFFFF
    return v0, v1

async def tea_cbc_encrypt(padded, key_bytes):
    k0,k1,k2,k3 = (struct.unpack_from("<I", key_bytes, o)[0] for o in (0,4,8,12))
    out = bytearray(len(padded)); pc = bytearray(8); pi = bytearray(8)
    for i in range(0, len(padded), 8):
        x = bytearray(8)
        for j in range(8): x[j] = padded[i+j] ^ pc[j]
        e0,e1 = await tea_enc(struct.unpack_from("<I", x, 0)[0],
                              struct.unpack_from("<I", x, 4)[0], k0,k1,k2,k3)
        enc = bytearray(8)
        struct.pack_into("<I", enc, 0, e0); struct.pack_into("<I", enc, 4, e1)
        for j in range(8): out[i+j] = enc[j] ^ pi[j]
        pc[:] = out[i:i+8]; pi[:] = x
    return bytes(out)

async def tea_cbc_decrypt(body, key_bytes):
    k0,k1,k2,k3 = (struct.unpack_from("<I", key_bytes, o)[0] for o in (0,4,8,12))
    out = bytearray(len(body)); pi = bytearray(8); pc = bytearray(8)
    x = bytearray(8); dec = bytearray(8)
    for i in range(0, len(body), 8):
        for j in range(8): x[j] = body[i+j] ^ pi[j]
        d0,d1 = await tea_dec(struct.unpack_from("<I", x, 0)[0],
                              struct.unpack_from("<I", x, 4)[0], k0,k1,k2,k3)
        struct.pack_into("<I", dec, 0, d0); struct.pack_into("<I", dec, 4, d1)
        for j in range(8): out[i+j] = dec[j] ^ pc[j]
        pc[:] = body[i:i+8]; pi[:] = dec
    return bytes(out)

async def build_padded(content):
    pad_len = (8 - (len(content) + 10) % 8) % 8
    return bytes([pad_len, 0, 0]) + b"\x00" * pad_len + content + b"\x00" * 7

async def encode_header(layout, so, cmd, oid, flags, length, k, v80):
    out = bytearray()
    for code in layout:
        val = {0:so, 1:cmd, 2:oid, 3:flags, 4:length}[code]
        if _FIELD_SIZES[code] == 1: out.append((val & 0xFF) ^ k)
        else:
            v = ((val & 0xFFFF) ^ v80) & 0xFFFF
            out.append(v & 0xFF); out.append((v >> 8) & 0xFF)
    return bytes(out)

async def crc7_buff(crc, buf):
    c = crc & 0x7F
    for b in buf: c = CRC7_TABLE[((2*(c & 0xFF)) ^ (b & 0xFF)) & 0xFF] & 0x7F
    return c & 0x7F

async def sv_frame(msg_key, layout, so, cmd, oid, flags, content, key, encrypted=True):
    k = key[0]; v80 = ((k << 8) | k) & 0xFFFF
    body = await tea_cbc_encrypt(await build_padded(content), key) if encrypted else content
    hdr = bytearray([msg_key, 0]) + await encode_header(layout, so, cmd, oid, flags, len(body), k, v80)
    pkt = bytearray(hdr + body)
    pkt[1] = await crc7_buff(0, bytes(pkt[2:])) & 0x7F
    return bytes(pkt)

async def build_packet(msg_key, layout, so, cmd, oid, flags, content, key, encrypted=True):
    k = key[0]; v80 = ((k << 8) | k) & 0xFFFF
    body = await tea_cbc_encrypt(await build_padded(content), key) if encrypted else content
    hdr = bytearray([msg_key, 0])
    for code in layout:
        val = {0:so, 1:cmd, 2:oid, 3:flags, 4:len(body)}[code]
        if _FIELD_SIZES[code] == 1: hdr.append((val & 0xFF) ^ k)
        else:
            v = ((val & 0xFFFF) ^ v80) & 0xFFFF
            hdr.append(v & 0xFF); hdr.append((v >> 8) & 0xFF)
    pkt = bytearray(hdr + body)
    pkt[1] = await crc7_buff(0, bytes(pkt[2:])) & 0x7F
    return bytes(pkt)

async def layouts_from_mask(mask):
    ru = [int(c) for c in str(mask).strip()]
    nr = [c for c in ru if c != 2]
    return ru, nr

async def build_hello_packet(text, key, layout):
    data = text.encode("utf-8")
    if len(data) > 25: raise ValueError("too long")
    content = b"\x10\x00\x00\x00" + data + b"\x00" * (29 - 4 - len(data))
    k = key[0] if key else 10
    v80 = ((k << 8) | k) & 0xFFFF
    layout = [int(c) for c in str(layout).strip()] if isinstance(layout, str) else list(layout)
    padded = await build_padded(content)
    enc_body = await tea_cbc_encrypt(padded, key)
    hdr = await encode_header(layout, 1, 1, 0, 1, len(enc_body), k, v80)
    pkt = bytearray([0x63, 0x00]) + hdr + enc_body
    pkt[1] = await crc7_buff(0, pkt[2:]) & 0x7F
    return bytes(pkt).hex()

async def classify(frame):
    cmd = frame["cmd"]
    name = MESSAGE_ID_TO_NAME.get(cmd, f"UNKNOWN_{cmd}")
    if name == "UDP_HELLO": return "HELLO"
    if name == "UDP_ACK": return "ACK"
    if name == "UDP_PING": return "PING"
    if name == "RUDP_JOIN_MATCH": return "JOIN_MATCH"
    if name.startswith("RUDP_"): return name
    if name.startswith("UDP_"): return name
    return "DATA"

async def reply_for(frame, key, mask, ack_key=0x68, ping_key=0x6D, hello_key=0x5B, ack_style="short"):
    _, nr = await layouts_from_mask(mask)
    typ = await classify(frame)
    if typ == "HELLO":
        if ack_style == "echo":
            content = frame["content"] if frame["content"] else b"\x10\x00\x00\x00"
            return typ, await build_packet(hello_key, nr, 1, 1, None, 1, content, key)
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, b"\x01\x00", key)
    if typ == "ACK":
        content = frame["content"] if frame["content"] else b"\x01\x00"
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, content, key)
    if typ == "PING":
        c = frame["content"]
        counter = c[:4] if len(c) >= 4 else c
        return typ, await build_packet(ping_key, nr, 0, 3, None, 0, counter + b"\x00\x00\x00", key, encrypted=False)
    if typ == "JOIN_MATCH":
        return typ, await build_packet(ack_key, nr, 0, 2, None, 1, b"\x02\x00", key)
    return typ, None

async def keepalive_ping(sock, ip, port, key_bytes, mask, stop_event):
    nr = (await layouts_from_mask(mask))[1]
    ping_keys = [0x66, 0x6D, 0x69, 0x6C, 0x6B, 0x6E, 0x6F, 0x70]
    loop = asyncio.get_event_loop(); i = 0
    while not stop_event.is_set():
        pk = ping_keys[i % len(ping_keys)]
        counter = int(time.time() * 1000) & 0xFFFFFFFF
        pkt = await build_packet(pk, nr, 0, 3, None, 0, struct.pack("<I", counter) + b"\x00\x00\x00",
                                 key_bytes, encrypted=False)
        try: await loop.sock_sendto(sock, pkt, (ip, port))
        except Exception: pass
        i += 1
        try: await asyncio.wait_for(stop_event.wait(), timeout=bypass_packet_jitter(3.0, 0.4))
        except asyncio.TimeoutError: pass

async def try_header(buf, layout, k, v80):
    off = 2; out = {}
    for code in layout:
        size = _FIELD_SIZES[code]
        if off + size > len(buf): return None
        out[_FIELD_NAMES[code]] = ((buf[off] ^ k) if size == 1
                                    else ((buf[off] | (buf[off+1] << 8)) ^ v80) & 0xFFFF)
        off += size
    out["headerLen"] = off
    return out

async def oicq_unpad(padded):
    if not padded or len(padded) < 8: return None
    if not all(padded[-1-i] == 0 for i in range(7)): return None
    pad_len = padded[0] & 0x07
    s = 3 + pad_len; e = len(padded) - 7
    return padded[s:e] if s < e else b""

async def decode_packet(packet, key, mask=None):
    data = bytes(packet) if isinstance(packet, bytes) else bytes.fromhex(packet)
    if len(data) < 8: return None
    k = key[0]; v80 = ((k << 8) | k) & 0xFFFF
    crc_ok = (data[1] & 0x7F) == await crc7_buff(0, data[2:])
    candidates = []
    if mask:
        ru, nr = await layouts_from_mask(mask)
        layouts = [("RUDP", ru), ("nonRUDP", nr)]
    else:
        layouts = [("RUDP", list(p)) for p in itertools.permutations([0,1,2,3,4])]
        layouts += [("nonRUDP", list(p)) for p in itertools.permutations([0,1,3,4])]
    for kind, layout in layouts:
        f = await try_header(data, layout, k, v80)
        if not f: continue
        if f["flags"] > 7 or f["sendOption"] > 7: continue
        if f["length"] != len(data) - f["headerLen"]: continue
        body = data[f["headerLen"]:f["headerLen"]+f["length"]]
        content = None
        if f["flags"] & 1:
            if len(body) < 8 or len(body) % 8 != 0: continue
            padded = await tea_cbc_decrypt(body, key)
            content = await oicq_unpad(padded)
            if content is None: continue
        else: content = body
        score = (1 if crc_ok else 0) + (1 if content is not None else 0)
        candidates.append({"kind":kind, "layout":layout, "headerLen":f["headerLen"],
            "msgKey":data[0], "cmd":f["cmd"], "flags":f["flags"],
            "sendOption":f["sendOption"], "orderId":f.get("orderId"),
            "length":f["length"], "content":content, "crcOk":crc_ok,
            "score":score, "total":len(data)})
    if not candidates: return None
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[0]

async def build_match_startup_packets(token, udp_key, match_code, account_id, block_val,
                                      server_ip="", region="ID", client_version="1.132.6",
                                      client_version_code="2019121229", access_token="",
                                      mode_id=BR_MODE_ID, map_id=BR_MAP_ID):
    token = token.strip()
    udp_key = bytes.fromhex(udp_key)
    match_code = [int(ch) for ch in str(match_code).strip()]
    thunder_jwt = token[:660] if len(token) > 660 else token
    sharma_jwt = token[660:] if len(token) > 660 else ""
    eth = thunder_jwt.encode() if isinstance(thunder_jwt, str) else thunder_jwt
    esh = sharma_jwt.encode() if isinstance(sharma_jwt, str) else sharma_jwt
    garena420 = await has_ssan_zig(len(eth)) + eth
    reg = str(region).upper() if region else "ID"
    csoversea_block = bytes.fromhex(
        "ca0163736f7665727365612e7374726f6e67686f6c642e66726565666972656d6f62696c652e636f6d"
        "3b302e302e302e303b33342e3132362e37362e34353b33342e38372e3137372e31343b33342e38372e"
        "3137302e3233303b33352e3138352e3138332e35370000000000000100000000000000000000000001"
        "00000800000100000000000100a8a2d7bebd8d8bdf110200")
    mid = bytes.fromhex('0000000001000102030101') + await has_ssan_zig(len(reg)) + reg.encode()
    mid += bytes.fromhex('0001030003000004')
    mid += await has_ssan_zig(len(client_version)) + client_version.encode()
    mid += await has_ssan_zig(len(client_version_code)) + client_version_code.encode()
    mid += csoversea_block
    clean_ip = server_ip.split(':')[0] if server_ip else "0.0.0.0"
    mid += await has_ssan_zig(len(clean_ip)) + clean_ip.encode()
    if access_token:
        clean_acc = access_token.strip()
        mid += await has_ssan_zig(len(clean_acc)) + clean_acc.encode()
    mid += await has_ssan_zig(len(esh)) + esh
    tg = (await uleb_encode(int(account_id)) + await uleb_encode(int(block_val)) +
          await uleb_encode(1) + await uleb_encode(int(mode_id)) +
          await uleb_encode(int(block_val)) + await uleb_encode(int(map_id)) + mid)
    process = await sv_frame(0x5E, match_code, 2, 447, 0, 1, garena420, udp_key)
    loading = await sv_frame(0x5A, match_code, 2, 448, 1, 1, tg, udp_key)
    return process.hex(), loading.hex()

# =========================== MOVEMENT 2001 ===========================
async def build_movement_packet_2001(key_bytes, msg_key, player_state, x, y, z,
                                     tick, counter, move_state, account_uid,
                                     room_code, phase="arena"):
    if phase == "game":
        TAIL = (b"\x00"*7 + b"\x93\xca\xd5\xf9\x0b" + b"\x8e\xfe\xfc\xf7\x0b"
                + b"\xf4\xe0\xfe\xf7\x03" + b"\x00\x00")
    else:
        TAIL = (b"\x00"*7 + b"\xbd\xb6\xe1\xf3\x03" + b"\x00"
                + b"\xc4\xb6\xe1\xfb\x0b" + b"\x00\x00")
    body = bytearray()
    body += await uleb_encode(int(account_uid))
    body += await uleb_encode(int(player_state))
    body += await zigzag_encode_signed(int(x))
    body += await zigzag_encode_signed(int(y))
    body += await zigzag_encode_signed(int(z))
    body += b"\x00"
    body += await uleb_encode(int(move_state))
    body += TAIL
    body += await uleb_encode(int(tick))
    body += b"\x00\x00\x00"
    body += await uleb_encode(int(counter))
    body = bytes(body)
    k = key_bytes[0]; v80 = ((k << 8) | k) & 0xFFFF
    h = bytearray()
    h.append(msg_key & 0xFF); h.append(0x00); h.append(0x00 ^ k)
    h += ((2001 ^ v80) & 0xFFFF).to_bytes(2, "little")
    h += ((len(body) ^ v80) & 0xFFFF).to_bytes(2, "little")
    h.append(0x00 ^ k)
    h[1] = (await crc7_buff(0, bytes(h[2:]) + body)) & 0x7F
    return bytes(h) + body

class MovementTracker:
    PLAYER_STATE = {"idle":0, "walk":1, "run":2, "sprint":3, "jump":4, "crouch":5, "prone":6}
    def __init__(self, pattern="circle", radius=180):
        self.pattern = pattern; self.radius = int(radius)
        self.tick = 0; self.counter = 0
        self.angle = random.uniform(0, 6.2832)
        self.speed_multiplier = 1.0; self.dir_flip = 1
        self._next_speed_roll = time.time()
        self.state = "walk"; self.state_start = time.time()
        self.state_duration = random.uniform(2.0, 4.0)
        self._roll_new_speed()
    def _roll_new_speed(self):
        try:
            lo, hi = float(MOVEMENT_SPEED_MIN), float(MOVEMENT_SPEED_MAX)
            if hi < lo: lo, hi = hi, lo
            self.speed_multiplier = round(random.uniform(lo, hi), 2)
        except Exception: self.speed_multiplier = 1.0
        self._next_speed_roll = time.time() + MOVEMENT_UPDATE_SPEED_EVERY
    def _pick_next_state(self):
        r = random.random()
        ci = MOVEMENT_STATE_IDLE_CHANCE
        cw = ci + MOVEMENT_STATE_WALK_CHANCE
        cr = cw + MOVEMENT_STATE_RUN_CHANCE
        cs = cr + MOVEMENT_STATE_SPRINT_CHANCE
        cj = cs + MOVEMENT_STATE_JUMP_CHANCE
        cc = cj + MOVEMENT_STATE_CROUCH_CHANCE
        if r < ci: return "idle", random.uniform(0.6, 1.6)
        elif r < cw: return "walk", random.uniform(1.6, 3.0)
        elif r < cr: return "run", random.uniform(2.0, 4.0)
        elif r < cs: return "sprint", random.uniform(1.2, 2.5)
        elif r < cj: return "jump", random.uniform(0.35, 0.65)
        elif r < cc: return "crouch", random.uniform(1.2, 2.5)
        else: return "prone", random.uniform(1.5, 3.5)
    def _generate_movement(self):
        p = (self.pattern or "circle").lower()
        x = y = z = 0; ms = 0
        if p == "circle":
            self.angle += 0.35 * self.dir_flip
            if self.angle > 6.2832: self.angle -= 6.2832
            elif self.angle < 0: self.angle += 6.2832
            x = int(self.radius * random.uniform(0.9, 1.1) * (1.0 if self.angle % 3.14 < 1.57 else -1.0))
            y = int(self.radius * random.uniform(0.4, 0.6))
            z = int(self.radius * random.uniform(0.9, 1.1) * (1.0 if self.angle % 6.28 < 3.14 else -1.0))
            ms = 0x0F
        else:
            x = random.randint(-self.radius, self.radius)
            y = random.randint(-40, 40)
            z = random.randint(-self.radius, self.radius)
            ms = random.choice([0x01, 0x02, 0x04, 0x08, 0x0F])
        return x, y, z, ms
    def next(self):
        now = time.time()
        if now >= self._next_speed_roll: self._roll_new_speed()
        if now - self.state_start > self.state_duration:
            old = self.state
            self.state, self.state_duration = self._pick_next_state()
            self.state_start = now
            if old != self.state:
                print_info(f"[MOVE] {old} -> {self.state} ({self.state_duration:.2f}s)")
        self.tick = (self.tick + 1) & 0xFFFFFFFF
        self.counter = (self.counter + 1) & 0xFFFFFFFF
        ps = self.PLAYER_STATE.get(self.state, 1)
        if self.state in ("idle", "crouch", "prone"): x = y = z = 0; move_state = 0
        else: x, y, z, move_state = self._generate_movement()
        return ps, x, y, z, move_state, self.tick, self.counter, self.speed_multiplier, self.state

SOLO_COMPLETED_MATCHES = {}
SELECTED_REGION = "IND"

def solo_mode_for_level(level):
    """Always Clasificatoria (ranked BR)."""
    return "BR"

LIVE_MATCH_LOCK = asyncio.Lock()  # legacy; solo matches do not acquire this global lock

async def movement_worker(sock, ip, port, udp_key_bytes, match_code, account_id, stop_event, match_index):
    loop = asyncio.get_event_loop(); addr = (ip, port)
    tracker = MovementTracker(pattern=MOVEMENT_PATTERN, radius=MOVEMENT_RADIUS)
    sent = 0
    try:
        await asyncio.sleep(30.0)
        while not stop_event.is_set():
            try:
                ps, x, y, z, ms, tick, cnt, sm, st = tracker.next()
                pkt = await build_movement_packet_2001(udp_key_bytes, 0x6B, ps, x, y, z, tick, cnt, ms,
                                                       account_id, match_code, phase="arena")
                await loop.sock_sendto(sock, pkt, addr); sent += 1
                if sent % 30 == 0: print_info(f"[MOVE] #{match_index} sent={sent} {st}({ps}) rate={sm}x")
                base = MOVEMENT_TICK_MS / 1000.0
                try: smx = max(0.7, min(float(sm), 1.6))
                except Exception: smx = 1.0
                wait = 30.0
                try: await asyncio.wait_for(stop_event.wait(), timeout=wait); break
                except asyncio.TimeoutError: pass
            except asyncio.CancelledError: break
            except Exception: await asyncio.sleep(0.5)
    except asyncio.CancelledError: pass
    finally: print_info(f"[MOVE] #{match_index} stopped sent={sent}")

async def send_anti_afk_fire(sock, addr, udp_key_bytes, match_code, account_id):
    try:
        _, nr = await layouts_from_mask(match_code)
        try: pid = int(account_id)
        except Exception: pid = 0
        ts = int(time.time() * 1000) & 0xFFFFFFFF
        wid = random.choice([101, 102, 103, 201, 202])
        fire = struct.pack("<IIHB", pid & 0xFFFFFFFF, ts, wid, 1)
        fp = await build_packet(0x68, nr, 0, 104, None, 0, fire, udp_key_bytes, encrypted=False)
        loop = asyncio.get_event_loop()
        await loop.sock_sendto(sock, fp, addr)
        await asyncio.sleep(bypass_jitter(random.uniform(0.15, 0.30), 0.05))
        stop = struct.pack("<IIHB", pid & 0xFFFFFFFF, ts + 200, wid, 0)
        sp = await build_packet(0x68, nr, 0, 105, None, 0, stop, udp_key_bytes, encrypted=False)
        await loop.sock_sendto(sock, sp, addr)
        return True
    except Exception: return False

async def anti_afk_worker(sock, ip, port, udp_key_bytes, match_code, account_id, stop_event, match_index):
    addr = (ip, port); fires = 0
    try:
        await asyncio.sleep(bypass_jitter(2.5, 0.5))
        while not stop_event.is_set():
            try:
                if await send_anti_afk_fire(sock, addr, udp_key_bytes, match_code, account_id): fires += 1
                w = random.uniform(ANTI_AFK_MIN_INTERVAL, ANTI_AFK_MAX_INTERVAL)
                w = bypass_packet_jitter(w, 0.25)
                try: await asyncio.wait_for(stop_event.wait(), timeout=w); break
                except asyncio.TimeoutError: pass
            except asyncio.CancelledError: break
            except Exception: await asyncio.sleep(1.0)
    except asyncio.CancelledError: pass
    finally:
        if fires > 0: print_info(f"[AFK] #{match_index} Fires={fires}")

# =========================== PLAY GAME ===========================
async def play_game(server_ip_port, thunder, sharma, udp_key, match_code,
                    account_id, player_region, client_version, key, iv,
                    match_index, on_match_complete=None):
    t0 = time.time()
    ping_task = anti_task = move_task = None
    sock = None
    ping_stop = asyncio.Event(); anti_stop = asyncio.Event(); move_stop = asyncio.Event()
    uid_str = str(account_id); completed = False
    try:
        ip, port = server_ip_port.split(":"); port = int(port)
        rip = await resolve_host_cloudflare(ip)
        loop = asyncio.get_event_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try: sock.bind(('0.0.0.0', 0))
        except Exception: pass
        optimize_udp_socket(sock); sock.setblocking(False)
        udp_key_bytes = bytes.fromhex(udp_key)
        await asyncio.sleep(bypass_hello_delay())
        hello = await build_hello_packet(f"{account_id}_2585", udp_key_bytes, match_code)
        await loop.sock_sendto(sock, bytes.fromhex(hello), (rip, port))
        ack_state = "waiting_for_hello_reply"
        thunder_sent = False; join_match_rcv = False; local_closed = False
        send_lock = asyncio.Lock(); anti_started = False
        ping_task = asyncio.create_task(keepalive_ping(sock, rip, port, udp_key_bytes, match_code, ping_stop))
        last_activity = time.time()
        print_colored(f"[MATCH #{match_index}] UDP -> {server_ip_port} (DNS:{rip})", Colors.MAGENTA)

        async def start_workers():
            nonlocal anti_task, move_task, anti_started
            if anti_started: return
            anti_started = True
            anti_task = asyncio.create_task(anti_afk_worker(sock, rip, port, udp_key_bytes, match_code,
                                                            account_id, anti_stop, match_index))
            print_success(f"[AFK] Worker #{match_index}")
            if ENABLE_SPEED_MOVEMENT:
                move_task = asyncio.create_task(movement_worker(sock, rip, port, udp_key_bytes, match_code,
                                                                account_id, move_stop, match_index))
                print_success(f"[MOVE] Worker #{match_index} | {MOVEMENT_PATTERN}")

        async def send_startup():
            nonlocal ack_state, thunder_sent
            if thunder_sent: return
            async with send_lock:
                if thunder_sent: return
                try:
                    await loop.sock_sendto(sock, bytes.fromhex(thunder), (rip, port))
                    thunder_sent = True
                    await asyncio.sleep(bypass_jitter(0.1, 0.05))
                    _, nr = await layouts_from_mask(match_code)
                    ack = await build_packet(0x68, nr, 0, 2, None, 1, b"\x01\x00", udp_key_bytes)
                    await loop.sock_sendto(sock, ack, (rip, port))
                    await asyncio.sleep(bypass_jitter(0.2, 0.05))
                    await loop.sock_sendto(sock, bytes.fromhex(sharma), (rip, port))
                    ack_state = "thunder_sharma_sent"
                    print_success(f"[MATCH #{match_index}] Startup delivered")
                    await start_workers()
                except Exception as e: print_error(f"[MATCH #{match_index}] startup: {e}")

        while not local_closed:
            if time.time() - t0 > MAX_MATCH_DURATION: break
            try:
                resp, saddr = await asyncio.wait_for(loop.sock_recvfrom(sock, 65535), timeout=1.5)
                if resp:
                    last_activity = time.time()
                    frame = await decode_packet(resp, udp_key_bytes, match_code)
                    if frame:
                        pt = await classify(frame)
                        if frame['cmd'] in [103, 107]:
                            print_success(f"[MATCH #{match_index}] END cmd={frame['cmd']}")
                            try: await add_glory(1)
                            except Exception: pass
                            completed = True; local_closed = True; continue
                        if frame['cmd'] == 101:
                            try:
                                _, nr = await layouts_from_mask(match_code)
                                a = await build_packet(0x68, nr, 0, 2, None, 1, b"\x01\x00", udp_key_bytes)
                                await loop.sock_sendto(sock, a, saddr)
                            except Exception: pass
                            continue
                        if pt in ["ACK", "PING", "HELLO", "JOIN_MATCH"]:
                            if pt == "HELLO" and ack_state == "waiting_for_hello_reply":
                                _, r = await reply_for(frame, udp_key_bytes, match_code, ack_style="short")
                                if r: await loop.sock_sendto(sock, r, saddr)
                                ack_state = "ack_sent_waiting"
                            elif pt == "ACK":
                                if ack_state == "waiting_for_hello_reply":
                                    _, r = await reply_for(frame, udp_key_bytes, match_code)
                                    if r: await loop.sock_sendto(sock, r, saddr)
                                    ack_state = "ready_to_send_thunder"
                                elif ack_state == "ack_sent_waiting":
                                    ack_state = "ready_to_send_thunder"
                                else:
                                    _, r = await reply_for(frame, udp_key_bytes, match_code)
                                    if r: await loop.sock_sendto(sock, r, saddr)
                            elif pt == "PING":
                                _, r = await reply_for(frame, udp_key_bytes, match_code)
                                if r: await loop.sock_sendto(sock, r, saddr)
                            elif pt == "JOIN_MATCH" and not join_match_rcv:
                                _, r = await reply_for(frame, udp_key_bytes, match_code)
                                if r: await loop.sock_sendto(sock, r, saddr); join_match_rcv = True
            except asyncio.TimeoutError:
                if ack_state == "ready_to_send_thunder" and not thunder_sent:
                    await send_startup()
                elif ack_state == "waiting_for_hello_reply":
                    if (time.time() - last_activity) > 3.0:
                        try:
                            hp = await build_hello_packet(f"{account_id}_2585", udp_key_bytes, match_code)
                            await loop.sock_sendto(sock, bytes.fromhex(hp), (rip, port))
                        except Exception: pass
                        last_activity = time.time()
                    if (time.time() - t0) > 12.0:
                        print_warning(f"[MATCH #{match_index}] Handshake timeout"); break
                elif ack_state == "thunder_sharma_sent":
                    if (time.time() - last_activity) > MATCH_IDLE_TIMEOUT:
                        print_success(f"[MATCH #{match_index}] Finished naturally")
                        completed = True; break
                continue
            except BlockingIOError: await asyncio.sleep(0.05)
            except OSError: await asyncio.sleep(0.5); continue
            except Exception: await asyncio.sleep(0.5); continue
            if ack_state == "ready_to_send_thunder" and not thunder_sent:
                await start_startup_safe(send_startup)
        return f"match #{match_index} finished"
    except Exception as e:
        print_error(f"[MATCH #{match_index}] {e}"); return f"match #{match_index} error"
    finally:
        if completed:
            try: bot_state.increment_match(uid_str)
            except Exception: pass
            if on_match_complete:
                try: asyncio.create_task(on_match_complete())
                except Exception: pass
        anti_stop.set(); move_stop.set()
        for t in (anti_task, move_task):
            if t:
                try: await asyncio.wait_for(t, timeout=2.0)
                except Exception:
                    t.cancel()
                    try: await t
                    except Exception: pass
        ping_stop.set()
        if ping_task:
            ping_task.cancel()
            try: await ping_task
            except asyncio.CancelledError: pass
        if sock:
            try: sock.close()
            except Exception: pass
        rem = await _dec_match(uid_str)
        total = await _get_total_match_count()
        print_info(f"[MATCH #{match_index}] Closed. UID:{rem} Total:{total}")
        try: bot_state.update_status(uid_str, "IN_MATCH" if rem > 0 else "ONLINE", rem)
        except Exception: pass

async def start_startup_safe(fn):
    try: await fn()
    except Exception: pass

# =========================== CLAN JOIN (dedup) ===========================
def _get_region_from_jwt(jwt_token):
    try:
        p = jwt_token.split('.')[1]
        p += '=' * (-len(p) % 4)
        d = json.loads(base64.urlsafe_b64decode(p))
        return (d.get('lock_region') or d.get('noti_region') or 'ID').upper()
    except Exception:
        return "ID"

def _get_region_url(region):
    r = str(region).upper()
    if r == "IND": return "https://client.ind.freefiremobile.com"
    if r in ("BR", "US", "NA"): return "https://client.us.freefiremobile.com"
    return "https://clientbp.ggpolarbear.com"

def _create_clan_payload(clan_id):
    try:
        raw = encode_varint(0x08) + encode_varint(int(clan_id))   # field 1 varint - no pb2 needed
        return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(raw, AES.block_size))
    except Exception:
        return None

async def join_clan(jwt_token, clan_id):
    try:
        region = _get_region_from_jwt(jwt_token)
        base_url = _get_region_url(region)
        payload = _create_clan_payload(clan_id)
        if not payload: return False, "payload build failed"
        hdrs = {
            "Expect": "100-continue",
            "Authorization": f"Bearer {jwt_token}",
            "X-Unity-Version": "2018.4.11f1", "X-GA": "v1 1",
            "ReleaseVersion": "OB55", "Content-Type": "application/octet-stream",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F Build/RP1A.200720.012)",
            "Host": base_url.replace("https://", ""),
            "Connection": "Keep-Alive", "Accept-Encoding": "gzip",
        }
        r = await client.post(base_url.rstrip("/") + "/RequestJoinClan", headers=hdrs,
                              content=payload, timeout=15.0)
        print_info(f"[CLAN] Join status: {r.status_code} | Region: {region}")
        if r.status_code == 200:
            print_success(f"[CLAN] Join request sent for clan {clan_id}")
            return True, ""
        return False, r.text.strip()[:120]
    except Exception as e:
        print_error(f"[CLAN] Join error: {e}")
        return False, str(e)


# =========================== FRIEND REQUEST ===========================
async def _process_social_packet(raw_bytes, account_data, tag="MAIN"):
    try:
        hex_data = raw_bytes.hex()
        candidates = []
        if len(raw_bytes) >= 6:
            plen = raw_bytes[4]
            if 0 < plen <= (len(raw_bytes) - 5):
                try:
                    inner = bytes(raw_bytes[5:5 + plen])
                    d0 = decode_protobuf_dict_safe(inner) or _wrap_manual(inner)
                    if d0: candidates.append((5, d0))
                except Exception: pass
        for off in [5, 6, 10, 8, 12, 4, 0]:
            if off >= len(hex_data): continue
            try: inner = bytes.fromhex(hex_data[off:])
            except Exception: continue
            decoded = decode_protobuf_dict_safe(inner) or _wrap_manual(inner)
            if decoded: candidates.append((off, decoded))
        if not candidates: return
        candidates.sort(key=lambda x: len(x[1]) if isinstance(x[1], dict) else 0, reverse=True)
        best_off, decoded = candidates[0]
        def _v(c, k):
            if not isinstance(c, dict): return None
            v = c.get(k) if k in c else c.get(str(k))
            if isinstance(v, dict) and "data" in v: return v["data"]
            return v
        f5w = decoded.get("5") or decoded.get(5) if isinstance(decoded, dict) else None
        f5 = f5w["data"] if isinstance(f5w, dict) and "data" in f5w else f5w
        target = None
        if isinstance(f5, dict):
            for fk in [1, 2, 3, 4, 6]:
                c = _v(f5, fk)
                if c and str(c).isdigit() and 6 <= len(str(c)) <= 15:
                    target = str(c); break
        if not target: return
        own = str(account_data.get('account_id', '')) if account_data else ''
        if own and target == own: return
        if not _accept_friend_request or not account_data: return
        jwt = account_data.get('token'); srv = account_data.get('server_url')
        rel = account_data.get('release_version'); own_id = account_data.get('account_id')
        if not (jwt and srv and rel and own_id): return
        url = f"{srv.rstrip('/')}/ConfirmFriendRequest"
        fields = {"1": int(target), "2": int(own_id)}
        try:
            payload = bytes.fromhex(encrypt_api(create_proto(fields).hex()))
            hdrs = {
                "authorization": f"Bearer {jwt}",
                "host": srv.replace("https://", "").replace("http://", "").split("/")[0],
                "x-ga": "v1 1", "content-type": "application/x-www-form-urlencoded",
                "accept-encoding": "deflate, gzip", "releaseversion": f"{rel}",
                "user-agent": "UnityPlayer/2022.3.47f1", "accept": "*/*",
                "x-unity-version": "2022.3.47f1",
            }
            async with httpx.AsyncClient(verify=False, timeout=8.0) as s:
                r = await s.post(url, headers=hdrs, content=payload)
                if r.status_code == 200 and len(r.content) > 0:
                    print_success(f"[FRIEND-{tag}]  {target}")
        except Exception: pass
    except Exception: pass

def _wrap_manual(inner):
    try:
        alt = _decode_proto_manual(inner)
        if alt and len(alt) > 0:
            return {str(k): {"data": v} for k, v in alt.items()}
    except Exception: pass
    return None

def _raw_fields_multi(data: bytes) -> dict:
    out = {}
    offset = 0; data_len = len(data)
    while offset < data_len:
        header = 0; shift = 0
        while offset < data_len:
            b = data[offset]; offset += 1
            header |= (b & 0x7F) << shift
            if not (b & 0x80): break
            shift += 7
            if shift > 28: break
        if header == 0: break
        fn = header >> 3; wt = header & 0x7
        if wt == 0:
            v = 0; shift = 0
            while offset < data_len:
                b = data[offset]; offset += 1
                v |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
        elif wt == 2:
            ln = 0; shift = 0
            while offset < data_len:
                b = data[offset]; offset += 1
                ln |= (b & 0x7F) << shift
                if not (b & 0x80): break
                shift += 7
            if ln > data_len - offset: break
            v = bytes(data[offset:offset+ln]); offset += ln
        elif wt == 5: v = bytes(data[offset:offset+4]); offset += 4
        elif wt == 1: v = bytes(data[offset:offset+8]); offset += 8
        else: break
        out.setdefault(fn, []).append(v)
    return out


def _parse_team_roster(inner: bytes):
    """0500 team state -> (team_code, member_uids). Captain ka join yahi se detect hota hai."""
    team_code = None
    uids = set()
    try:
        for f5 in _raw_fields_multi(inner).get(5, []):
            if not isinstance(f5, (bytes, bytearray)): continue
            mf = _raw_fields_multi(bytes(f5))
            for code_b in mf.get(11, []):
                if isinstance(code_b, (bytes, bytearray)):
                    s = bytes(code_b).decode("utf-8", "ignore").strip()
                    if s.isdigit() and len(s) == 7: team_code = s
            for m in mf.get(6, []):
                if isinstance(m, (bytes, bytearray)):
                    mm = _raw_fields_multi(bytes(m))
                    for v in mm.get(1, []):
                        if isinstance(v, int) and v > 1000:
                            uids.add(str(v)); break
    except Exception:
        pass
    return team_code, uids


# =========================== TEAM INVITE HANDLER ===========================
async def _handle_team_invite(hex_data, pl, uid_str, current_account_data,
                              current_key, current_iv, writer):
    try:
        if DEBUG_TEAM_PACKETS:
            print_info(f"[TEAM-IN {uid_str}] len={pl} hex={hex_data[:80]}")

        #  server roster (member list + code) — captain join yahi se detect hota hai
        try:
            for _roff in (10, 8, 6):
                if len(hex_data) <= _roff + 8: continue
                try:
                    _tc, _uids = _parse_team_roster(bytes.fromhex(hex_data[_roff:]))
                except Exception:
                    continue
                if _tc:
                    async with _team_state["lock"]:
                        if not _team_state.get("team_code"):
                            _team_state["team_code"] = _tc
                for _u in _uids:
                    await _team_member_join(_u)
                if _tc or _uids:
                    break
        except Exception:
            pass

        candidates = []
        for off in [10, 8, 6, 12, 14, 4, 16, 0, 20, 2]:
            if off >= len(hex_data) or len(hex_data) - off < 4: continue
            try: inner = bytes.fromhex(hex_data[off:])
            except Exception: continue

            dec = decode_protobuf_dict_safe(inner)
            if dec and isinstance(dec, dict) and len(dec) > 0:
                candidates.append((off, "parser", dec)); continue

            alt = _decode_proto_manual(inner)
            if alt and len(alt) > 0:
                candidates.append((off, "manual", {str(k): {"data": v} for k, v in alt.items()}))

        if not candidates:
            return False

        candidates.sort(key=lambda x: len(x[2]) if isinstance(x[2], dict) else 0, reverse=True)
        best_off, decoder, dec = candidates[0]
        print_info(f"[TEAM-IN {uid_str}] decoded@{best_off}/{decoder} fields={list(dec.keys())[:20]}")

        def _unwrap(d, keys):
            if not isinstance(d, dict): return None
            for k in keys:
                v = d.get(k) if k in d else d.get(str(k))
                if isinstance(v, dict) and "data" in v: return v["data"]
                if isinstance(v, dict): return v
            return None

        target_dict = None
        for kp in [["5"], ["4"], ["6"], ["2"], ["1"]]:
            u = _unwrap(dec, kp)
            if isinstance(u, dict) and len(u) >= 3:
                target_dict = u
                print_info(f"[TEAM-IN {uid_str}] nested@{kp[0]}")
                break
        if target_dict is None: target_dict = dec

        def _g(d, k):
            if not isinstance(d, dict): return None
            v = d.get(k) if k in d else d.get(str(k))
            if isinstance(v, dict) and "data" in v: return v["data"]
            if isinstance(v, dict):
                for kk in ["1","2","3","4","5","6","7","8"]:
                    vv = v.get(kk) if kk in v else v.get(int(kk))
                    if isinstance(vv, dict) and "data" in vv: return vv["data"]
            return v

        group_id = None
        for k in list(target_dict.keys()):
            c = _g(target_dict, k)
            if isinstance(c, str) and 20 <= len(c) <= 40:
                group_id = c
                print_success(f"[TEAM-IN {uid_str}]  group_id@f{k}: {c[:24]}...")
                break
        if not group_id:
            for k in list(dec.keys()):
                c = _g(dec, k)
                if isinstance(c, str) and 20 <= len(c) <= 40:
                    group_id = c
                    print_success(f"[TEAM-IN {uid_str}]  group_id@root.f{k}: {c[:24]}...")
                    break

        own_acc = str(current_account_data.get('account_id')) if current_account_data else None
        inviter = None
        all_f = list(target_dict.keys()) + list(dec.keys())
        for k in all_f:
            c = _g(target_dict, k) or _g(dec, k)
            if c and str(c).isdigit() and 6 <= len(str(c)) <= 15:
                if str(c) != uid_str and str(c) != own_acc:
                    inviter = str(c)
                    print_success(f"[TEAM-IN {uid_str}]  inviter@f{k}: {c}")
                    break

        tc = None
        for k in all_f:
            c = _g(target_dict, k) or _g(dec, k)
            if c and str(c).isdigit() and len(str(c)) == 7:
                tc = str(c); break
        if tc:
            async with _team_state["lock"]:
                _team_state["team_code"] = tc
            print_success(f"[TEAM-IN {uid_str}]  Team Code: {tc}")

        is_member = (_team_state["leader_uid"] != uid_str)
        if inviter and group_id and is_member:
            async with _team_state["members_lock"]:
                already = uid_str in _team_state["members"]
            if already:
                return True
            print_success(f"[TEAM-IN {uid_str}]  ACCEPT: inviter={inviter} group={group_id[:16]}...")
            accepted = False
            for attempt in range(3):
                try:
                    _reg = str(current_account_data.get('region', 'ID')) if isinstance(current_account_data, dict) else 'ID'
                    acc = accept_team_invite(int(inviter), group_id, current_key, current_iv, region=_reg)
                    if writer and not writer.is_closing():
                        writer.write(acc); await writer.drain()
                        print_success(f"[TEAM-IN {uid_str}]  accept #{attempt+1} ({len(acc)}B)")
                        accepted = True; break
                except Exception as e:
                    print_warning(f"[TEAM-IN {uid_str}] accept err #{attempt+1}: {e}")
                await asyncio.sleep(0.4)
            if accepted:
                await _team_member_join(uid_str)
            return True
        return False
    except Exception as e:
        print_warning(f"[TEAM-IN {uid_str}] error: {e}")
        return False

# =========================== FUNCTIONAL (MAIN) — BATTLE ROYALE ONLY ===========================
async def functional_battle_royale(addrs, starter_packet, account_region, client_version,
                                    key, iv, account_id="", account_data=None,
                                    account_level=2, max_reconnects=10):
    reconnects = 0
    ip, port = addrs.split(":")
    play_matches: List[asyncio.Task] = []
    no_response_count = 0
    search_attempts = 0
    last_start_time = 0.0
    uid_str = str(account_id)
    current_level = int(account_level or 2)
    consecutive_parse_failures = 0
    current_token = starter_packet
    current_key = key; current_iv = iv
    current_account_data = account_data
    reconnect_count_total = 0
    region_index = 0
    current_search_region = SELECTED_REGION
    _writer_ref = {"w": None}
    _team_active = {"flag": True}

    async def trigger_post_match_refresh():
        await asyncio.sleep(EXP_REFRESH_AFTER_MATCH_DELAY)
        try:
            cd = bot_state.account_credentials.get(uid_str)
            if cd: await refresh_account_profile(cd)
        except Exception: pass

    # =========== LEADER: create  invite-loop  ready  start ===========
    async def _team_coordinator():
        try:
            deadline = time.time() + TEAM_PEER_WAIT_TIMEOUT
            while time.time() < deadline:
                async with _team_state["lock"]:
                    n = len(_team_state["peers"])
                if n >= TEAM_BOTS: break
                if bot_state.is_paused(uid_str): return
                await asyncio.sleep(0.5)

            async with _team_state["lock"]:
                n = len(_team_state["peers"])
                is_leader = (_team_state["leader_uid"] == uid_str)
                peers_snapshot = dict(_team_state["peers"])

            if not is_leader:
                print_info(f"[TEAM] {uid_str} waiting as member...")
                return

            # parallel-match gate - wait while the account is at MAX
            while True:
                _am = await _get_match_count(uid_str)
                if _am < MAX_CONCURRENT_MATCHES: break
                if bot_state.is_paused(uid_str): return
                print_info(f"[TEAM] {uid_str} active matches {_am}/{MAX_CONCURRENT_MATCHES} - hold")
                await asyncio.sleep(3.0)
            if n < TEAM_BOTS:
                print_warning(f"[TEAM] Only {n}/{TEAM_BOTS} bot peers")
            else:
                print_success(f"[TEAM]  All {n} bot peers online")

            await asyncio.sleep(TEAM_READY_DELAY)
            print_success(f"[TEAM]  {uid_str} creating team...")

            async with _team_state["lock"]:
                _team_state["team_code"] = None
                _team_state["pk_code"] = None

            own_id_num = None
            if current_account_data: own_id_num = current_account_data.get('account_id')
            if not own_id_num:
                try: own_id_num = int(uid_str)
                except Exception: own_id_num = 0

            try:
                pkt = create_team(current_key, current_iv, client_version)
                if _writer_ref["w"] and not _writer_ref["w"].is_closing():
                    _writer_ref["w"].write(pkt); await _writer_ref["w"].drain()
                    print_info(f"[TEAM] create_team sent ({len(pkt)}B)")
                    await _team_member_reset(keep_leader=False)
                    await _team_member_join(uid_str)
            except Exception as e:
                print_error(f"[TEAM] create_team: {e}")

            await asyncio.sleep(TEAM_CREATE_WAIT)

            peer_uids = []
            for peer_uid, info in peers_snapshot.items():
                if peer_uid == uid_str: continue
                pa = None
                try: pa = info["data"].get("account_id")
                except Exception: pass
                if not pa: pa = peer_uid
                peer_uids.append(int(pa))
            invite_targets = list(peer_uids)
            if USER_GAME_UID:
                invite_targets.append(int(USER_GAME_UID))
            print_info(f"[TEAM] Will invite {len(invite_targets)}: {invite_targets}")

            heartbeat_stop = asyncio.Event()
            async def heartbeat_loop():
                while not heartbeat_stop.is_set():
                    try:
                        if _writer_ref["w"] and not _writer_ref["w"].is_closing():
                            pkt = team_fresh(int(own_id_num), current_key, current_iv)
                            _writer_ref["w"].write(pkt); await _writer_ref["w"].drain()
                    except Exception: pass
                    try: await asyncio.wait_for(heartbeat_stop.wait(), timeout=TEAM_HEARTBEAT_INTERVAL)
                    except asyncio.TimeoutError: pass
            hb_task = asyncio.create_task(heartbeat_loop())

            print_success(f"[TEAM]  Invite-loop start (max {int(TEAM_INVITE_MAX_TIME)}s)")
            invite_start = time.time()
            cycle = 0
            while time.time() - invite_start < TEAM_INVITE_MAX_TIME:
                if not _team_active["flag"]: break
                if bot_state.is_paused(uid_str): break
                cnt = await _team_member_count()
                if cnt >= TEAM_SIZE:
                    print_success(f"[TEAM]  Full team ({cnt}/{TEAM_SIZE})!")
                    break
                cycle += 1
                for i, tuid in enumerate(invite_targets):
                    async with _team_state["members_lock"]:
                        joined = str(tuid) in _team_state["members"]
                    if joined: continue
                    try:
                        inv = invite_player_in_team(tuid, current_key, current_iv, region=account_region)
                        if _writer_ref["w"] and not _writer_ref["w"].is_closing():
                            _writer_ref["w"].write(inv); await _writer_ref["w"].drain()
                            print_success(f"[TEAM]  invite {tuid} cycle#{cycle}")
                    except Exception as e:
                        print_warning(f"[TEAM] invite err: {e}")
                    await asyncio.sleep(0.2)
                try: await asyncio.wait_for(heartbeat_stop.wait(), timeout=TEAM_INVITE_CYCLE_WAIT)
                except asyncio.TimeoutError: pass

            final_cnt = await _team_member_count()
            print_colored(f"[TEAM] == FINAL: In team ({final_cnt}/{TEAM_SIZE}) ==", Colors.MAGENTA)

            if final_cnt < TEAM_SIZE:
                print_warning(f"[TEAM] Partial squad ({final_cnt}/{TEAM_SIZE}); proceeding with available members")

            await asyncio.sleep(TEAM_FINAL_WAIT)
            heartbeat_stop.set()
            try: hb_task.cancel(); await asyncio.gather(hb_task, return_exceptions=True)
            except Exception: pass

            print_success(f"[TEAM]  {uid_str} loop: ready  1s  start (every 5s) - partial squad allowed")
            while _team_active["flag"]:
                try:
                    if bot_state.is_paused(uid_str): break
                    async with _team_state["lock"]:
                        if _team_state["leader_uid"] != uid_str: break
                    _tcnt = await _team_member_count()
                    if _tcnt < 1:
                        await asyncio.sleep(2.0)
                        continue
                    oid = current_account_data.get('account_id', own_id_num) if current_account_data else own_id_num
                    try:
                        rdy = ready_for_game(int(oid), current_key, current_iv)
                        if _writer_ref["w"] and not _writer_ref["w"].is_closing():
                            _writer_ref["w"].write(rdy); await _writer_ref["w"].drain()
                    except Exception as e: print_warning(f"[TEAM] ready err: {e}")
                    await asyncio.sleep(1.0)
                    sm = start_match_team(int(oid), current_key, current_iv, region=account_region)
                    if _writer_ref["w"] and not _writer_ref["w"].is_closing():
                        _writer_ref["w"].write(sm); await _writer_ref["w"].drain()
                except Exception as e: print_warning(f"[TEAM] start err: {e}")
                try: await asyncio.wait_for(asyncio.sleep(5.0), timeout=5.5)
                except asyncio.TimeoutError: pass
        except asyncio.CancelledError: raise
        except Exception as e:
            print_error(f"[TEAM] coordinator: {e}")
            traceback.print_exc()

    async def _member_match_trigger():
        try:
            await asyncio.sleep(TEAM_READY_DELAY + TEAM_MEMBER_START_DELAY)
            async with _team_state["lock"]:
                if _team_state["leader_uid"] == uid_str: return
            # parallel-match gate
            while _team_active["flag"]:
                _am = await _get_match_count(uid_str)
                if _am < MAX_CONCURRENT_MATCHES: break
                await asyncio.sleep(3.0)
            if not _team_active["flag"]: return
            print_success(f"[TEAM]  Member {uid_str}: passive (READY only, no START)")
            my_id = current_account_data.get('account_id', uid_str) if current_account_data else uid_str
            while _team_active["flag"]:
                try:
                    if bot_state.is_paused(uid_str): break
                    #  members never start - only leader cmd 1:9; READY only when full team
                    if await _team_member_count() < 1:
                        await asyncio.sleep(2.0)
                        continue
                    if _writer_ref["w"] and not _writer_ref["w"].is_closing():
                        try:
                            rdy = ready_for_game(int(my_id), current_key, current_iv)
                            _writer_ref["w"].write(rdy); await _writer_ref["w"].drain()
                        except Exception as e: print_warning(f"[TEAM] member ready err: {e}")
                except Exception as e: print_warning(f"[TEAM] member trigger: {e}")
                try: await asyncio.wait_for(asyncio.sleep(5.0), timeout=5.5)
                except asyncio.TimeoutError: pass
        except asyncio.CancelledError: raise
        except Exception as e: print_warning(f"[TEAM] member outer: {e}")

    try:
        while True:
            writer = None; gateway_ping_task = None
            team_coord_task = None; member_trigger_task = None
            try:
                if current_account_data:
                    fresh = None
                    if current_account_data.get('auth_type') == 'guest' and current_account_data.get('auth_uid'):
                        fresh = cache_get(str(current_account_data['auth_uid']))
                    elif current_account_data.get('auth_type') == 'token' and current_account_data.get('auth_token'):
                        fresh = cache_get(f"tok_{current_account_data['auth_token'][:20]}")
                    if fresh:
                        current_account_data = fresh
                        current_key = fresh['aes_ak']; current_iv = fresh['iv_i']
                        current_token = await build_tcp_startup_packet(
                            fresh['account_id'], fresh['token'], fresh['server_time'],
                            current_key, current_iv,
                            region=fresh.get('region', account_region), typ='OnLine')
                        try:
                            lv = int(fresh.get('level', current_level) or current_level)
                            if lv != current_level: current_level = lv
                        except Exception: pass
                    else:
                        print_warning(f"[FUNC] Cache miss {uid_str} -> re-login")
                        try:
                            if current_account_data.get('auth_uid'):
                                cache_invalidate(str(current_account_data['auth_uid']))
                            if current_account_data.get('auth_token'):
                                cache_invalidate(f"tok_{current_account_data['auth_token'][:20]}")
                        except Exception: pass
                        raise ConnectionError("Cache expired")

                try:
                    if uid_str in bot_state.accounts:
                        ll = int(bot_state.accounts[uid_str].get('level', current_level) or current_level)
                        if ll != current_level:
                            print_info(f"[LEVEL] {uid_str}: {current_level} -> {ll}")
                            current_level = ll
                except Exception: pass

                rip = await resolve_host_cloudflare(ip)
                reader, writer = await asyncio.open_connection(rip, int(port))
                _writer_ref["w"] = writer
                raw_sock = writer.get_extra_info('socket')
                if raw_sock: optimize_tcp_socket(raw_sock)
                await asyncio.sleep(bypass_hello_delay())
                writer.write(bytes.fromhex(current_token)); await writer.drain()
                try:
                    ka = await send_keep_alive(account_region)
                    if ka and not writer.is_closing():
                        writer.write(ka); await asyncio.wait_for(writer.drain(), timeout=3)
                except Exception: pass

                async def func_gateway_keepalive():
                    ka_bytes = await send_keep_alive(account_region)
                    while True:
                        await asyncio.sleep(bypass_ka_jitter(3.0))
                        try:
                            if writer and not writer.is_closing():
                                writer.write(ka_bytes); await writer.drain()
                        except Exception: break
                gateway_ping_task = asyncio.create_task(func_gateway_keepalive())

                connection_start_time = asyncio.get_running_loop().time()
                last_watchdog_check = connection_start_time
                search_attempts = 0
                # Fixed region for the entire process: never rotate on reconnect.
                current_search_region = SELECTED_REGION

                print_success(f"[FUNC] TCP connected {uid_str} (DNS:{rip} Lvl:{current_level} R:{current_search_region})")
                reconnects = 0; no_response_count = 0; last_start_time = 0.0

                async with _team_state["lock"]:
                    _team_state["peers"][uid_str] = {
                        "writer": writer, "data": current_account_data,
                        "key": current_key, "iv": current_iv}
                    # deterministic leader = lowest uid (no split-team race on reconnect)
                    if _team_state["leader_uid"] is None or uid_str < str(_team_state["leader_uid"]):
                        _team_state["leader_uid"] = uid_str
                        print_success(f"[TEAM]  {uid_str} is leader")

                if TEAM_MODE:
                    team_coord_task = asyncio.create_task(_team_coordinator())
                    member_trigger_task = asyncio.create_task(_member_match_trigger())
                else:
                    # Each account searches independently. First completed match is BR,
                    # subsequent matches are LW. This is per-account, not global.
                    if solo_mode_for_level(current_level) == "BR":
                        print_info("[MODE] CLASIFICATORIA BR"); await start_game_battle_royale(current_search_region, client_version, writer, current_key, current_iv)
                    else:
                        await start_game_lone_wolf_solo(current_search_region, client_version, writer, current_key, current_iv)

                while True:
                    play_matches[:] = [m for m in play_matches if not m.done()]
                    active = await _get_match_count(uid_str)
                    try: bot_state.update_status(uid_str, "ONLINE" if active == 0 else "IN_MATCH", active)
                    except Exception: pass

                    now = asyncio.get_running_loop().time()
                    if now - last_watchdog_check >= MATCH_WATCHDOG_CHECK:
                        last_watchdog_check = now
                        search_attempts += 1
                        sd = now - connection_start_time
                        if sd > 30: print_warning(f"[WATCHDOG] {uid_str} searching {int(sd)}s att={search_attempts}")
                        if sd > MATCH_SEARCH_TIMEOUT or search_attempts >= MAX_SEARCH_ATTEMPTS:
                            raise ConnectionError("Search watchdog")
                    if search_attempts >= MAX_SEARCH_ATTEMPTS:
                        raise ConnectionError("Max attempts")

                    try:
                        data = await asyncio.wait_for(reader.read(8192), timeout=0.3)
                    except asyncio.TimeoutError:
                        no_response_count += 1
                        if TEAM_MODE:
                            if no_response_count > TEAM_IDLE_ITERS_TEAM:
                                raise ConnectionError("Team idle timeout")
                        else:
                            if no_response_count > 80: raise ConnectionError("idle")
                        continue

                    if not data: raise ConnectionError("closed")
                    hex_data = data.hex()
                    pl = len(data)
                    no_response_count = 0

                    if DEBUG_TEAM_PACKETS and not hex_data.startswith("0300") and not hex_data.startswith("0600"):
                        print_info(f"[RAW-IN {uid_str}] len={pl} prefix={hex_data[:24]}")

                    if hex_data.startswith("0600") and pl > 20:
                        await _process_social_packet(data, current_account_data, tag="MAIN")
                        continue

                    if hex_data.startswith("05") and pl > 10:
                        await _handle_team_invite(hex_data, pl, uid_str, current_account_data,
                                                  current_key, current_iv, writer)
                        continue

                    if hex_data.startswith("0300") and 10 < pl < 30:
                        continue

                    if hex_data.startswith("0300") and pl >= 300:
                        print_success("MATCH FOUND - UDP connect ho raha hai")

                        for tk in (team_coord_task, member_trigger_task):
                            if tk and not tk.done():
                                tk.cancel()
                                try: await tk
                                except asyncio.CancelledError: pass
                        team_coord_task = None; member_trigger_task = None
                        _team_active["flag"] = False

                        try:
                            res = json.loads(await decode_protobuf(hex_data[10:]))
                            token = udp_key = match_code = server_ip_port = None
                            match_account_id = block_val = None
                            if '42' in res and 'data' in res['42']:
                                match_code = res['42']['data']
                            if '5' in res and 'data' in res['5']:
                                r5 = res['5']['data']
                                server_ip_port = r5.get('2', {}).get('data')
                                udp_key = r5.get('3', {}).get('data')
                                token = r5.get('4', {}).get('data')
                                if '42' in r5: match_code = r5['42']['data']
                            if '1' in res and 'data' in res['1']:
                                match_account_id = res['1']['data']
                            if '5' in res and 'data' in res['5']:
                                block_val = res['5']['data'].get('1', {}).get('data')

                            effective = match_account_id or account_id or "BD_BOT"
                            if token and udp_key and match_code and server_ip_port:
                                try:
                                    async with _team_state["lock"]:
                                        _team_state["pk_code"] = str(match_code)
                                        _team_state["team_code"] = str(match_code)
                                    print_colored(f"[PK]  Room Code: {match_code}", Colors.MAGENTA)
                                    print_colored(f"[PK]  Server: {server_ip_port}", Colors.MAGENTA)
                                    print_colored(f"[PK]  UDP Key: {udp_key}", Colors.MAGENTA)
                                except Exception: pass

                                acc_tok = current_account_data.get('access_token', '') if current_account_data else ""
                                mode = solo_mode_for_level(current_level)
                                mid, mp = (BR_MODE_ID, BR_MAP_ID) if mode == "BR" else (11, 1)
                                tag = "CLASIFICATORIA" if mode == "BR" else "LONE_WOLF"
                                print_info(f"[TARGET] {tag} mid={mid} mp={mp}")
                                thunder, sharma = await build_match_startup_packets(
                                    token, udp_key, match_code, effective, block_val or 0,
                                    server_ip=server_ip_port, region=account_region,
                                    client_version=client_version, access_token=acc_tok,
                                    mode_id=mid, map_id=mp)
                                match_index = await _inc_match(uid_str)
                                total = await _get_total_match_count()
                                print_colored(f"[MATCH #{match_index}] UDP -> {server_ip_port} ({tag})", Colors.CYAN)

                                # Match is foreground/awaited; no second live match starts until this ends.
                                if True:  # per-account foreground, no global cross-account lock
                                    await play_game(
                                        server_ip_port, thunder, sharma, udp_key, match_code,
                                        effective, current_search_region, client_version,
                                        current_key, current_iv,
                                        match_index=match_index, on_match_complete=trigger_post_match_refresh)
                                SOLO_COMPLETED_MATCHES[uid_str] = SOLO_COMPLETED_MATCHES.get(uid_str, 0) + 1
                                consecutive_parse_failures = 0
                                active_now = await _get_match_count(uid_str)
                                print_info(f"[MATCH] #{match_index} live for {uid_str} (active={active_now})")

                                # prior match finished; now reconnect for next match
                                try: writer.close(); await writer.wait_closed()
                                except Exception: pass
                                await asyncio.sleep(NEW_MATCH_DELAY)
                                reconnect_count_total += 1
                                break
                            else:
                                consecutive_parse_failures += 1
                                print_warning(f"[FUNC] Non-match big pkt #{consecutive_parse_failures}")
                                if consecutive_parse_failures >= MAX_CONSECUTIVE_PARSE_FAILURES:
                                    consecutive_parse_failures = 0
                                try: writer.close(); await writer.wait_closed()
                                except Exception: pass
                                await asyncio.sleep(NON_MATCH_RECONNECT_DELAY)
                                break
                        except Exception as e:
                            print_error(f"[FUNC] Match parse: {e}")
                            consecutive_parse_failures += 1
                            try: writer.close(); await writer.wait_closed()
                            except Exception: pass
                            await asyncio.sleep(NON_MATCH_RECONNECT_DELAY)
                            break

                    if 30 <= pl <= 40: continue

            except asyncio.CancelledError:
                print_warning(f"[FUNC] Cancelled — cancel {len(play_matches)} UDP")
                for m in play_matches:
                    if not m.done(): m.cancel()
                if play_matches:
                    await asyncio.gather(*play_matches, return_exceptions=True)
                play_matches.clear()
                if gateway_ping_task: gateway_ping_task.cancel()
                async with _team_state["lock"]:
                    _team_state["peers"].pop(uid_str, None)
                    if _team_state["leader_uid"] == uid_str:
                        _team_state["leader_uid"] = min(_team_state["peers"].keys()) if _team_state["peers"] else None
                        if _team_state["leader_uid"]:
                            print_info(f"[TEAM] new leader: {_team_state['leader_uid']}")
                await _team_member_leave(uid_str)
                raise
            except Exception as e:
                if gateway_ping_task: gateway_ping_task.cancel()
                print_error(f"[FUNC] TCP state {uid_str}: {e}")
                play_matches[:] = [m for m in play_matches if not m.done()]
                if writer:
                    try: writer.close(); await writer.wait_closed()
                    except Exception: pass
                if "Cache expired" in str(e):
                    print_warning(f"[FUNC] re-login {uid_str}")
                    break
                reconnect_count_total += 1
                reconnects += 1
                if reconnects > max_reconnects:
                    reconnects = 0
                    await asyncio.sleep(3)
                    continue
                await asyncio.sleep(bypass_human_reconnect_delay(reconnects))
            finally:
                _team_active["flag"] = False
                for tk in (team_coord_task, member_trigger_task):
                    if tk and not tk.done():
                        tk.cancel()
                        try: await tk
                        except (asyncio.CancelledError, Exception): pass
                if gateway_ping_task: gateway_ping_task.cancel()
                if writer:
                    try: writer.close(); await writer.wait_closed()
                    except Exception: pass
                async with _team_state["lock"]:
                    _team_state["peers"].pop(uid_str, None)
                    if _team_state["leader_uid"] == uid_str:
                        _team_state["leader_uid"] = min(_team_state["peers"].keys()) if _team_state["peers"] else None
                        if _team_state["leader_uid"]:
                            print_info(f"[TEAM] new leader: {_team_state['leader_uid']}")
                await _team_member_leave(uid_str)
                _team_active["flag"] = True
    except asyncio.CancelledError:
        for m in play_matches:
            if not m.done(): m.cancel()
        if play_matches: await asyncio.gather(*play_matches, return_exceptions=True)
        play_matches.clear()
        raise

# =========================== INFORMATIONAL ===========================
async def informational(addrs, starter_packet, key, iv, region="ID", max_reconnects=3):
    reconnects = 0
    ip, port = addrs.split(":")
    while True:
        writer = None; ping_task = None
        try:
            rip = await resolve_host_cloudflare(ip)
            reader, writer = await asyncio.open_connection(rip, int(port))
            rs = writer.get_extra_info('socket')
            if rs: optimize_tcp_socket(rs)
            writer.write(bytes.fromhex(starter_packet)); await writer.drain()
            reconnects = 0
            try:
                ka = await send_keep_alive(region)
                if ka and not writer.is_closing():
                    writer.write(ka); await asyncio.wait_for(writer.drain(), timeout=3)
            except Exception: pass
            async def info_ka():
                ka = await send_keep_alive(region)
                while True:
                    await asyncio.sleep(bypass_ka_jitter(3.0))
                    try:
                        if writer and not writer.is_closing():
                            writer.write(ka); await writer.drain()
                    except Exception: break
            ping_task = asyncio.create_task(info_ka())
            while True:
                data = await reader.read(8192)
                if not data: raise ConnectionError("closed")
        except asyncio.CancelledError:
            if ping_task: ping_task.cancel()
            if writer:
                try: writer.close(); await writer.wait_closed()
                except Exception: pass
            raise
        except Exception:
            if ping_task: ping_task.cancel()
            if writer:
                try: writer.close(); await writer.wait_closed()
                except Exception: pass
            reconnects += 1
            if reconnects > max_reconnects:
                await asyncio.sleep(3); reconnects = 0
            else: await asyncio.sleep(1)

# =========================== ACCOUNT HELPERS ===========================
def _register_credentials(ad):
    try:
        acc_id = str(ad['account_id'])
        bot_state.account_credentials[acc_id] = ad
        if ad.get('auth_uid'): bot_state.account_credentials[str(ad['auth_uid'])] = ad
        if ad.get('auth_token'): bot_state.account_credentials[f"tok_{ad['auth_token'][:20]}"] = ad
    except Exception: pass

async def refresh_account_profile(ad_or_uid):
    try:
        if isinstance(ad_or_uid, str):
            uid = str(ad_or_uid); ad = bot_state.account_credentials.get(uid)
        else:
            ad = ad_or_uid; uid = str(ad.get('account_id')) if ad else "?"
        if not ad: return
        url = ad.get('server_url'); token = ad.get('token')
        rel = ad.get('release_version'); payload = ad.get('login_payload_data')
        if not (url and token and rel and payload): return
        res = await send_getlogin(payload, url, token, rel)
        if not res: return
        rp, dd = res
        def _si(v, d):
            try:
                if v is None or v == "": return d
                return int(v)
            except Exception: return d
        level = _si(get_proto_field(dd, 6, None), None)
        exp = _si(get_proto_field(dd, 7, None), None)
        likes = _si(get_proto_field(dd, 8, None), None)
        try: nick = rp.nickname or get_proto_field(dd, 4, "") or ""
        except Exception: nick = ""
        if level is None and exp is None: return
        level = level if level is not None else 1
        exp = exp if exp is not None else 0
        likes = likes if likes is not None else 0
        acc_id = str(ad['account_id'])
        old_lv = 0; old_ex = 0
        try:
            if acc_id in bot_state.accounts:
                old_lv = int(bot_state.accounts[acc_id].get('level', 0) or 0)
                old_ex = int(bot_state.accounts[acc_id].get('exp', 0) or 0)
        except Exception: pass
        try: bot_state.update_exp(acc_id, exp, level)
        except Exception: pass
        if likes > 0 and acc_id in bot_state.accounts:
            bot_state.accounts[acc_id]["likes"] = likes
        if nick and acc_id in bot_state.accounts:
            bot_state.accounts[acc_id]["nickname"] = nick
        _update_cache_profile(ad, level, exp)
        ad['level'] = level; ad['exp'] = exp
        if likes > 0: ad['likes'] = likes
        if nick: ad['nickname'] = nick
        pass
    except Exception: pass

async def process_account_uid_pass(uid, password):
    cached = cache_get(uid)
    if cached:
        print_success(f"[CACHE] {uid} loaded")
        acc_id = str(cached['account_id'])
        bot_state.register_account(uid=acc_id,
            nickname=cached.get('nickname', f"Player_{acc_id}"),
            region=cached.get('region', 'ID'),
            level=cached.get('level', 1), exp=cached.get('exp', 0),
            likes=cached.get('likes', 0))
        _register_credentials(cached); return cached
    print_info(f"[LOGIN] UID {uid}...")
    try:
        vc = await version_config()
        if not vc: return None
        rel, cv, su = vc
        tg = await get_access_token(uid, password)
        if not tg: return None
        oid, at, pf = tg
        dev = get_device_for_account(uid)
        lpd = await build_majorlogin_payload(oid, at, pf, cv, dev)
        if not lpd: return None
        mresp = await send_majorlogin(lpd, rel, su)
        if mresp is None: return None
        gl = await send_getlogin(lpd, mresp.url, mresp.token, rel)
        if gl is None: return None
        rp, dd = gl
        acc_id = str(mresp.account_id)
        level = int(get_proto_field(dd, 6, 1) or 1)
        exp = int(get_proto_field(dd, 7, 0) or 0)
        likes = int(get_proto_field(dd, 8, 0) or 0)
        nick = rp.nickname or get_proto_field(dd, 4, f"Player_{acc_id}")
        region = mresp.region or get_proto_field(dd, 3, "ID")
        bot_state.register_account(uid=acc_id, nickname=nick, region=region,
                                    level=level, exp=exp, likes=likes)
        print_success(f"[OK] {acc_id} | {nick} | Lvl{level} | BATTLE ROYALE")
        ad = {
            'account_id': mresp.account_id, 'nickname': nick, 'region': region,
            'level': level, 'exp': exp, 'likes': likes,
            'open_id': oid, 'access_token': at, 'platform': str(pf),
            'token': mresp.token, 'server_time': mresp.server_time,
            'aes_ak': mresp.aes_ak, 'iv_i': mresp.iv_i,
            'functional_addrs': rp.functional_addrs or get_proto_field(dd, 14),
            'informational_addrs': rp.informational_addrs or get_proto_field(dd, 32),
            'release_version': rel, 'client_version': cv, 'server_url': mresp.url,
            'login_host': str(su),
            'login_payload_data': lpd,
            'auth_type': 'guest', 'auth_uid': uid, 'auth_password': password,
        }
        _register_credentials(ad); cache_set(uid, ad); return ad
    except Exception as e:
        print_error(f"process_account_uid_pass: {e}")
        traceback.print_exc(); return None

async def process_account_token(access_token):
    cache_key = f"tok_{access_token[:20]}"
    cached = cache_get(cache_key)
    if cached:
        acc_id = str(cached['account_id'])
        bot_state.register_account(uid=acc_id,
            nickname=cached.get('nickname', f"Player_{acc_id}"),
            region=cached.get('region', 'ID'),
            level=cached.get('level', 1), exp=cached.get('exp', 0),
            likes=cached.get('likes', 0))
        _register_credentials(cached); return cached
    print_info("[LOGIN] Token...")
    try:
        vc = await version_config()
        if not vc: return None
        rel, cv, su = vc
        import requests
        url = f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}"
        hdrs = {"User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)"}
        resp = await asyncio.to_thread(requests.get, url, headers=hdrs, timeout=10)
        d = resp.json()
        if 'error' in d: return None
        oid = d.get('open_id'); pf = d.get('platform', 4)
        if not oid: return None
        dev = get_device_for_account(oid)
        lpd = await build_majorlogin_payload(oid, access_token, str(pf), cv, dev)
        if not lpd: return None
        mresp = await send_majorlogin(lpd, rel, su)
        if mresp is None: return None
        gl = await send_getlogin(lpd, mresp.url, mresp.token, rel)
        if gl is None: return None
        rp, dd = gl
        acc_id = str(mresp.account_id)
        level = int(get_proto_field(dd, 6, 1) or 1)
        exp = int(get_proto_field(dd, 7, 0) or 0)
        likes = int(get_proto_field(dd, 8, 0) or 0)
        nick = rp.nickname or get_proto_field(dd, 4, f"Player_{acc_id}")
        region = mresp.region or get_proto_field(dd, 3, "ID")
        bot_state.register_account(uid=acc_id, nickname=nick, region=region,
                                    level=level, exp=exp, likes=likes)
        ad = {
            'account_id': mresp.account_id, 'nickname': nick, 'region': region,
            'level': level, 'exp': exp, 'likes': likes,
            'open_id': oid, 'access_token': access_token, 'platform': str(pf),
            'token': mresp.token, 'server_time': mresp.server_time,
            'aes_ak': mresp.aes_ak, 'iv_i': mresp.iv_i,
            'functional_addrs': rp.functional_addrs or get_proto_field(dd, 14),
            'informational_addrs': rp.informational_addrs or get_proto_field(dd, 32),
            'release_version': rel, 'client_version': cv, 'server_url': mresp.url,
            'login_payload_data': lpd,
            'auth_type': 'token', 'auth_token': access_token,
        }
        _register_credentials(ad); cache_set(cache_key, ad); return ad
    except Exception as e:
        print_error(f"process_account_token: {e}"); return None

async def run_account_worker(ad, label):
    acc_id = str(ad['account_id'])
    info_task = None; exp_task = None; ping_task = None
    try:
        reg = ad.get('region', 'ID')
        # A region selection cannot transfer an account to a different home server.
        if str(reg).upper() not in (SELECTED_REGION, 'ID' if SELECTED_REGION == 'IND' else SELECTED_REGION):
            print_warning(f"[REGION] Skipping {acc_id}: account region {reg} != selected {SELECTED_REGION}")
            return
        reg = SELECTED_REGION
        ad['region'] = reg
        tcp_online = await build_tcp_startup_packet(
            ad['account_id'], ad['token'], ad['server_time'],
            ad['aes_ak'], ad['iv_i'], region=reg, typ='OnLine')
        tcp_chat = await build_tcp_startup_packet(
            ad['account_id'], ad['token'], ad['server_time'],
            ad['aes_ak'], ad['iv_i'], region=reg, typ='ChaT')

        cap_task = None
        if AUTO_JOIN_CLAN and CLAN_ID:
            #  dedup: pehle se clan mein ho toh request mat bhejo
            _auid = str(ad.get('auth_uid') or acc_id)
            _done = set()
            if os.path.exists(CLAN_STATE_FILE):
                try:
                    with open(CLAN_STATE_FILE, "r", encoding="utf-8") as _cf:
                        _done = set(json.load(_cf))
                except Exception:
                    _done = set()
            if _auid in _done:
                print_info(f"[CLAN] {_auid} already in clan (saved) - skip")
            else:
                _okj = False
                for _ct in range(2):
                    try:
                        await asyncio.sleep(1.0 if _ct == 0 else 15.0)
                        _okj, _errj = await join_clan(ad['token'], CLAN_ID)
                        if _okj: break
                        if "ALREADY_IN" in str(_errj).upper():
                            print_info(f"[CLAN] {_auid} already in a clan - done")
                            _okj = True; break
                    except Exception as _ce:
                        print_warning(f"[CLAN] {_ce}")
                if _okj:
                    _done.add(_auid)
                    try:
                        with open(CLAN_STATE_FILE, "w", encoding="utf-8") as _cf:
                            json.dump(sorted(_done), _cf)
                    except Exception:
                        pass

        if USER_GAME_UID:
            #  captain ki friend request har 20s auto-accept (invite tabhi deliver hota hai)
            async def _cap_friend_loop():
                while True:
                    await asyncio.sleep(20)
                    try:
                        _url = f"{ad['server_url'].rstrip('/')}/ConfirmFriendRequest"
                        _pl = bytes.fromhex(encrypt_api(create_proto({"1": int(USER_GAME_UID), "2": int(acc_id)}).hex()))
                        _hd = {
                            "authorization": f"Bearer {ad['token']}",
                            "host": ad['server_url'].replace("https://", "").split("/")[0],
                            "x-ga": "v1 1", "content-type": "application/x-www-form-urlencoded",
                            "accept-encoding": "deflate, gzip",
                            "releaseversion": str(ad['release_version']),
                            "user-agent": "UnityPlayer/2022.3.47f1", "accept": "*/*",
                            "x-unity-version": "2022.3.47f1",
                        }
                        await client.post(_url, headers=_hd, content=_pl, timeout=8.0)
                    except Exception:
                        pass
            cap_task = asyncio.create_task(_cap_friend_loop())
        info_task = asyncio.create_task(informational(ad['informational_addrs'], tcp_chat,
                                                      ad['aes_ak'], ad['iv_i'], region=reg))
        if ENABLE_HTTP_PING:
            _phost = str(ad.get('login_host') or PING_URL).rstrip('/')
            _purl = _phost if _phost.endswith('/Ping') else (_phost + '/Ping')
            ping_task = asyncio.create_task(ping_worker(acc_id, ad['token'], ad['release_version'], region=reg, ping_url=_purl))
            print_success(f"[PING] Started {acc_id}")

        async def exp_refresher():
            try:
                f = bot_state.account_credentials.get(acc_id)
                if f: await refresh_account_profile(f)
            except Exception: pass
            while True:
                await asyncio.sleep(EXP_REFRESH_INTERVAL + random.uniform(-3.0, 3.0))
                try:
                    f = bot_state.account_credentials.get(acc_id)
                    if f: await refresh_account_profile(f)
                except Exception: pass
        exp_task = asyncio.create_task(exp_refresher())
        #  Always Battle Royale
        await functional_battle_royale(ad['functional_addrs'], tcp_online, ad['region'], ad['client_version'],
            ad['aes_ak'], ad['iv_i'], account_id=acc_id, account_data=ad,
            account_level=int(ad.get('level', 2) or 2))
    except asyncio.CancelledError: raise
    except Exception as e: print_error(f"run_account_worker {label}: {e}")
    finally:
        for t in (info_task, exp_task, ping_task, cap_task):
            if t and not t.done(): t.cancel()
        for t in (info_task, exp_task, ping_task, cap_task):
            if t:
                try: await t
                except Exception: pass

async def account_loop_guest(uid, password):
    while True:
        try:
            print_info(f"[LOGIN] Guest {uid}...")
            try: bot_state.update_status(str(uid), "CONNECTING")
            except Exception: pass
            ad = await process_account_uid_pass(uid, password)
            if not ad:
                print_error(f"Login failed {uid}, retry 15s")
                try: bot_state.update_status(str(uid), "ERROR")
                except Exception: pass
                await asyncio.sleep(15); continue
            await run_account_worker(ad, uid)
            print_warning(f"Session end {uid}, reconnect 3s")
            await asyncio.sleep(3)
        except asyncio.CancelledError:
            print_warning(f"Worker {uid} stopped")
            try: bot_state.update_status(str(uid), "OFFLINE")
            except Exception: pass
            break
        except Exception as e:
            print_error(f"Error {uid}: {e}, retry 10s")
            await asyncio.sleep(10)

async def account_loop_token(token):
    label = token[:10]
    while True:
        try:
            ad = await process_account_token(token)
            if not ad:
                print_error("Login token fail, retry 15s")
                await asyncio.sleep(15); continue
            acc_id = str(ad['account_id'])
            await run_account_worker(ad, acc_id)
            await asyncio.sleep(3)
        except asyncio.CancelledError:
            print_warning(f"Token {label} stopped"); break
        except Exception as e:
            print_error(f"Token error: {e}, retry 10s")
            await asyncio.sleep(10)

def load_accounts():
    accounts = []
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list): accounts = data
        except Exception as e: print_error(f"load: {e}")
    if not accounts and FALLBACK_UID and FALLBACK_PASSWORD:
        accounts.append({"uid": FALLBACK_UID, "password": FALLBACK_PASSWORD})
    return accounts

# =========================== MAIN ===========================

# Developer Zone localhost dashboard (configuration only; not live match telemetry)
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import json as _dashboard_json
dashboard_state = {"region":"Not selected", "bots":0, "guild":"Not selected", "parallel_per_bot":1}



def _vextu_base():
    return os.path.dirname(os.path.abspath(__file__))

def _write_engine_status(data: dict):
    try:
        path = os.path.join(_vextu_base(), "engine_status.json")
        data = dict(data)
        data["ts"] = int(time.time())
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def _append_engine_log(msg: str):
    try:
        path = os.path.join(_vextu_base(), "engine.log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S") + " " + str(msg) + "\n")
    except Exception:
        pass

async def main():
    global TEAM_BOTS, USER_GAME_UID, CLAN_ID, AUTO_JOIN_CLAN, GEN_NAME_PREFIX, SELECTED_REGION, MAX_CONCURRENT_MATCHES
    print_colored("VEXTU ANDROID | BOT ENGINE")
    base = _vextu_base()
    db_path = os.path.join(base, "vextu.db")
    queue_path = os.path.join(base, "launch_queue.json")
    global ACCOUNTS_FILE, CLAN_STATE_FILE
    ACCOUNTS_FILE = os.path.join(base, "accounts.json")
    CLAN_STATE_FILE = os.path.join(base, "clan_state.json")
    active_launches = {}

    print_info(f"DB: {db_path}")
    print_info(f"Accounts: {ACCOUNTS_FILE}")
    _write_engine_status({"online": True, "mode": "starting", "msg": "starting"})
    _append_engine_log("engine start")

    def db_connect():
        import sqlite3
        if not os.path.exists(db_path):
            return None
        con = sqlite3.connect(db_path, timeout=10)
        con.row_factory = sqlite3.Row
        return con

    def fetch_pending():
        items = []
        now = int(time.time())
        try:
            con = db_connect()
            if con is not None:
                cur = con.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bot_queue'")
                if cur.fetchone():
                    # pending always
                    cur.execute("SELECT * FROM bot_queue WHERE status='pending' ORDER BY created_at ASC LIMIT 20")
                    for row in cur.fetchall():
                        items.append({
                            "id": row["id"],
                            "region": row["region"],
                            "guild_id": row["guild_id"],
                            "bots": row["bots"],
                            "hours": row["hours"],
                            "status": row["status"],
                            "source": "db",
                            "resume": False,
                        })
                    # running but still inside 8h window -> resume on restart
                    cur.execute("SELECT * FROM bot_queue WHERE status='running' ORDER BY created_at ASC LIMIT 20")
                    for row in cur.fetchall():
                        started = int(row["started_at"] or row["created_at"] or 0)
                        hours = max(1, int(row["hours"] or 8))
                        ends = started + hours * 3600
                        if started > 0 and now < ends:
                            left_h = max(0.05, (ends - now) / 3600.0)
                            items.append({
                                "id": row["id"],
                                "region": row["region"],
                                "guild_id": row["guild_id"],
                                "bots": row["bots"],
                                "hours": left_h,
                                "status": "running",
                                "source": "db-resume",
                                "resume": True,
                                "ends_at": ends,
                            })
                        elif started > 0 and now >= ends:
                            try:
                                cur.execute("UPDATE bot_queue SET status='done', finished_at=? WHERE id=?", (now, row["id"]))
                            except Exception:
                                pass
                    con.commit()
                con.close()
        except Exception as e:
            print_warning(f"db queue: {e}")
            _append_engine_log(f"db queue error: {e}")

        # 2) JSON fallback
        if not items:
            try:
                if os.path.exists(queue_path):
                    with open(queue_path, "r", encoding="utf-8") as f:
                        raw = f.read().strip()
                    if raw:
                        data = json.loads(raw)
                        if isinstance(data, list):
                            for it in data:
                                if str(it.get("status")) == "pending":
                                    it = dict(it)
                                    it["source"] = "json"
                                    items.append(it)
            except Exception as e:
                print_warning(f"json queue: {e}")
        return items

    def mark_queue(qid, status, progress=None, stage=None, msg=None):
        try:
            con = db_connect()
            if con is not None:
                cur = con.cursor()
                # ensure columns exist (older dbs)
                try:
                    cur.execute("ALTER TABLE bot_queue ADD COLUMN progress INTEGER NOT NULL DEFAULT 0")
                except Exception:
                    pass
                try:
                    cur.execute("ALTER TABLE bot_queue ADD COLUMN stage TEXT DEFAULT ''")
                except Exception:
                    pass
                try:
                    cur.execute("ALTER TABLE bot_queue ADD COLUMN msg TEXT DEFAULT ''")
                except Exception:
                    pass
                if status == "running":
                    cur.execute("UPDATE bot_queue SET status=?, started_at=? WHERE id=?", (status, int(time.time()), qid))
                elif status == "done":
                    cur.execute("UPDATE bot_queue SET status=?, finished_at=?, progress=100, stage=?, msg=? WHERE id=?",
                                (status, int(time.time()), stage or "ready", msg or "Listo", qid))
                else:
                    cur.execute("UPDATE bot_queue SET status=? WHERE id=?", (status, qid))
                if progress is not None or stage is not None or msg is not None:
                    cur.execute(
                        "UPDATE bot_queue SET progress=COALESCE(?,progress), stage=COALESCE(?,stage), msg=COALESCE(?,msg) WHERE id=?",
                        (progress, stage, msg, qid)
                    )
                con.commit()
                con.close()
        except Exception as e:
            print_warning(f"db mark: {e}")
        # json mirror
        try:
            if not os.path.exists(queue_path):
                return
            with open(queue_path, "r", encoding="utf-8") as f:
                raw = f.read().strip()
            data = json.loads(raw) if raw else []
            if not isinstance(data, list):
                return
            for it in data:
                if str(it.get("id")) == str(qid):
                    it["status"] = status
                    if status == "running":
                        it["started_at"] = int(time.time())
                    if status == "done":
                        it["finished_at"] = int(time.time())
            with open(queue_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    async def ensure_accounts(need: int, launch_id: str = ""):
        print_info(f"[GEN] always creating {need} NEW accounts")
        _append_engine_log(f"creating {need} new accounts")
        before = {str(a.get("uid")) for a in load_accounts() if a.get("uid")}
        created_uids = []
        for i in range(need):
            _write_engine_status({
                "online": True,
                "mode": "generating",
                "stage": "creating_account",
                "current": i + 1,
                "total": need,
                "launch_id": launch_id,
                "msg": f"Creando cuenta {i+1}/{need}",
                "progress": int(((i) / max(need, 1)) * 70),
            })
            if launch_id:
                mark_queue(launch_id, "running", progress=int(((i) / max(need, 1)) * 70), stage="creating_account", msg=f"Creando cuenta {i+1}/{need}")
            print_info(f"[GEN] account {i+1}/{need}")
            try:
                n = await auto_generate_accounts(1)
            except Exception as e:
                print_error(f"[GEN] {i+1}: {e}")
                _append_engine_log(f"gen error {i+1}: {e}")
                traceback.print_exc()
                n = 0
            after = load_accounts()
            for a in after:
                uid = str(a.get("uid") or "")
                if uid and uid not in before and uid not in created_uids:
                    created_uids.append(uid)
                    before.add(uid)
            print_success(f"[GEN] progress created={len(created_uids)}/{need}")
        # return only newly created when possible
        all_accs = load_accounts()
        new_accs = [a for a in all_accs if str(a.get("uid")) in created_uids]
        if len(new_accs) >= need:
            return new_accs[:need]
        return all_accs[-need:] if len(all_accs) >= need else all_accs

    async def run_launch(item: dict):
        global TEAM_BOTS, USER_GAME_UID, CLAN_ID, AUTO_JOIN_CLAN, GEN_NAME_PREFIX, SELECTED_REGION, MAX_CONCURRENT_MATCHES
        lid = str(item.get("id") or "")
        region = str(item.get("region") or "IND").upper().strip()
        guild = str(item.get("guild_id") or "").strip()
        bots = max(1, min(50, int(item.get("bots") or 4)))
        try:
            hours = float(item.get("hours") or 8)
        except Exception:
            hours = 8.0
        hours = max(0.05, min(24.0, hours))
        is_resume = bool(item.get("resume"))

        SELECTED_REGION = region
        CLAN_ID = guild
        AUTO_JOIN_CLAN = bool(guild)
        TEAM_BOTS = bots
        USER_GAME_UID = ""
        GEN_NAME_PREFIX = "vxt-bot"
        MAX_CONCURRENT_MATCHES = 20
        dashboard_state["region"] = region
        dashboard_state["bots"] = bots
        dashboard_state["guild"] = guild or "—"
        print_success(f"[LAUNCH {lid[:8]}] src={item.get('source')} region={region} guild={guild} bots={bots} hours={hours}")
        _append_engine_log(f"launch {lid[:8]} {region} {guild} bots={bots}")
        _write_engine_status({"online": True, "mode": "launching", "launch_id": lid, "region": region, "guild": guild, "bots": bots})

        if is_resume:
            print_info(f"[RESUME] launch {lid[:8]} remaining ~{hours:.2f}h")
            _append_engine_log(f"resume {lid[:8]} hours_left={hours:.2f}")
            accs = load_accounts()
            if len(accs) > bots:
                accs = accs[-bots:]
            if not accs:
                accs = await ensure_accounts(bots, lid)
        else:
            accs = await ensure_accounts(bots, lid)

        if not accs:
            print_error("[LAUNCH] no accounts")
            _write_engine_status({"online": True, "mode": "error", "msg": "no accounts"})
            return

        _write_engine_status({
            "online": True,
            "mode": "starting",
            "stage": "starting_workers",
            "launch_id": lid,
            "region": region,
            "guild": guild,
            "bots": bots,
            "current": 0,
            "total": len(accs),
            "progress": 85,
            "msg": "Iniciando bots y uniéndose al clan...",
        })
        mark_queue(lid, "running", progress=85, stage="starting_workers", msg="Iniciando bots y uniéndose al clan...")
        workers = []
        for idx, acc in enumerate(accs):

            try:
                if acc.get("uid") and acc.get("password"):
                    u = str(acc["uid"]); pw = str(acc["password"])
                    print_info(f"[START] guest {u}")
                    t = asyncio.create_task(account_loop_guest(u, pw))
                    bot_state.account_workers[u] = t
                    workers.append((u, t))
                elif acc.get("token"):
                    tok = str(acc["token"])
                    t = asyncio.create_task(account_loop_token(tok))
                    bot_state.account_workers[tok[:10]] = t
                    workers.append((tok[:10], t))
            except Exception as e:
                print_error(f"[START] {e}")

        print_success(f"[LAUNCH {lid[:8]}] workers={len(workers)}")
        _write_engine_status({
            "online": True,
            "mode": "running",
            "stage": "ready",
            "launch_id": lid,
            "region": region,
            "guild": guild,
            "bots": bots,
            "workers": len(workers),
            "accounts": len(accs),
            "current": bots,
            "total": bots,
            "progress": 100,
            "msg": "Listo: cuentas creadas, clan y bots en marcha",
            "left_min": hours * 60,
            "ends_at": int(time.time()) + hours * 3600,
        })
        mark_queue(lid, "running", progress=100, stage="ready", msg="Listo: cuentas creadas, clan y bots en marcha")

        if item.get("ends_at"):
            end_at = float(item.get("ends_at"))
        else:
            end_at = time.time() + hours * 3600
        try:
            while time.time() < end_at:
                alive = sum(1 for _, t in workers if not t.done())
                _write_engine_status({
                    "online": True, "mode": "running", "launch_id": lid,
                    "region": region, "guild": guild, "bots": bots,
                    "workers": alive, "accounts": len(accs),
                    "left_min": max(0, int((end_at - time.time()) / 60)),
                    "msg": f"running {alive} workers"
                })
                if alive == 0:
                    print_warning("all workers stopped")
                    break
                await asyncio.sleep(15)
        except asyncio.CancelledError:
            pass

        for key, t in workers:
            if not t.done():
                t.cancel()
            bot_state.account_workers.pop(key, None)
        if workers:
            await asyncio.gather(*[t for _, t in workers], return_exceptions=True)
        _write_engine_status({"online": True, "mode": "idle", "msg": "waiting for launches"})
        print_success(f"[LAUNCH {lid[:8]}] finished")

    if os.environ.get("VEXTU_AUTO") == "1":
        item = {
            "id": "env-" + str(int(time.time())),
            "region": os.environ.get("VEXTU_REGION", "IND"),
            "guild_id": os.environ.get("VEXTU_GUILD", ""),
            "bots": int(os.environ.get("VEXTU_BOTS", "4")),
            "hours": int(os.environ.get("VEXTU_HOURS", "8")),
            "source": "env",
        }
        await run_launch(item)
        return

    print_info("Daemon: reading bot_queue from vextu.db (and json fallback)")
    if not os.path.exists(db_path):
        print_warning("vextu.db not found yet. Open the panel once so PHP creates it in THIS folder.")
    _write_engine_status({"online": True, "mode": "idle", "msg": "waiting for launches"})

    while True:
        try:
            pending = fetch_pending()
            for item in pending:
                lid = str(item.get("id") or "")
                if not lid or lid in active_launches:
                    continue
                if lid in active_launches and not active_launches[lid].done():
                    continue
                mark_queue(lid, "running")
                print_success(f"[QUEUE] picked {lid[:8]} from {item.get('source')}")
                _append_engine_log(f"picked {lid[:8]} from {item.get('source')}")

                async def _wrap(_item=item, _lid=lid):
                    try:
                        await run_launch(_item)
                    except Exception as e:
                        print_error(f"launch: {e}")
                        traceback.print_exc()
                    finally:
                        mark_queue(_lid, "done")
                        active_launches.pop(_lid, None)

                active_launches[lid] = asyncio.create_task(_wrap())

            alive = len([t for t in active_launches.values() if not t.done()])
            _write_engine_status({
                "online": True,
                "mode": "running" if alive else "idle",
                "active": alive,
                "msg": f"{alive} active" if alive else "waiting for launches",
                "db_exists": os.path.exists(db_path),
            })
            await asyncio.sleep(2)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print_error(f"daemon: {e}")
            traceback.print_exc()
            await asyncio.sleep(5)

    for t in list(active_launches.values()):
        t.cancel()
    if active_launches:
        await asyncio.gather(*active_launches.values(), return_exceptions=True)
    _write_engine_status({"online": False, "mode": "stopped"})
    print_success("Engine stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_warning("stopped")