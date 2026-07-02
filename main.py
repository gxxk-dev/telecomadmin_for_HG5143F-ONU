# coding=utf-8

# AGPLv3+ License. By Gxxk(Frez79).
# 全自动获取 电信网关 HG5143F(ONU) 的超管密码.

from __future__ import annotations

import argparse
import base64
import hashlib
import ipaddress
import json
import platform
import re
import socket
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

try:
    import requests
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.padding import PKCS7
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError("请执行 uv sync 后再运行脚本") from exc

try:
    import pyperclip

    CLIPBOARD_AVAILABLE = True
except ModuleNotFoundError:
    CLIPBOARD_AVAILABLE = False


DEFAULT_IP = "192.168.1.1"
FH_TOOL_PATH = "/fh_tool/api"


@dataclass(frozen=True)
class FHToolCrypto:
    key: bytes
    iv: bytes
    digest: str


class FHToolError(RuntimeError):
    pass


def normalize_ip(value: str) -> str:
    try:
        ip = ipaddress.ip_address(value.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("不符规范的 IP 地址") from exc
    if ip.version != 4:
        raise argparse.ArgumentTypeError("目前只支持 IPv4 网关地址")
    return str(ip)


def normalize_mac(value: str) -> str:
    mac = value.strip().upper().replace(":", "").replace("-", "")
    if not re.fullmatch(r"[A-F0-9]{12}", mac):
        raise ValueError("不符规范的 MAC 地址，应为 AABBCCDDEEFF 格式")
    return mac


def detect_default_gateway() -> str | None:
    system = platform.system()
    commands: list[list[str]] = []

    if system == "Windows":
        commands = [["route", "print", "-4", "0.0.0.0"]]
    elif system == "Darwin":
        commands = [["route", "-n", "get", "default"]]
    else:
        commands = [["ip", "-4", "route", "show", "default"], ["route", "-n"]]

    for command in commands:
        try:
            output = subprocess.check_output(
                command,
                stderr=subprocess.DEVNULL,
            ).decode("utf-8", errors="ignore")
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

        if system == "Darwin":
            match = re.search(r"gateway:\s*(\d{1,3}(?:\.\d{1,3}){3})", output)
            if match:
                return normalize_ip(match.group(1))
            continue

        if command[:2] == ["ip", "-4"]:
            match = re.search(r"\bdefault\s+via\s+(\d{1,3}(?:\.\d{1,3}){3})", output)
            if match:
                return normalize_ip(match.group(1))
            continue

        for line in output.splitlines():
            line = line.strip()
            if not line or "0.0.0.0" not in line:
                continue
            parts = line.split()
            candidates = [part for part in parts if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", part)]
            for candidate in candidates:
                if candidate != "0.0.0.0":
                    return normalize_ip(candidate)

    return None


def format_mac(mac: str) -> str:
    return ":".join(mac[i : i + 2] for i in range(0, 12, 2))


def get_mac_address(ip: str) -> str | None:
    """从本机 ARP 表获取网关 MAC。失败时返回 None，交给用户手动输入。"""
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(
                f"arp -a {ip}",
                shell=True,
                stderr=subprocess.DEVNULL,
            ).decode("utf-8", errors="ignore")
            match = re.search(r"([A-Fa-f0-9]{2}(?:-[A-Fa-f0-9]{2}){5})", output)
        else:
            output = subprocess.check_output(
                ["arp", "-n", ip],
                stderr=subprocess.DEVNULL,
            ).decode("utf-8", errors="ignore")
            match = re.search(r"([A-Fa-f0-9]{2}(?::[A-Fa-f0-9]{2}){5})", output)
        if match:
            return normalize_mac(match.group(1))
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def prompt_mac(ip: str, quiet: bool = False) -> str:
    detected = get_mac_address(ip)
    if detected:
        if not quiet:
            print(f"网关 MAC: {format_mac(detected)}")
        return detected

    print("无法从 ARP 表自动获取网关 MAC。")
    manual = input("请手动输入网关 MAC(AABBCCDDEEFF): ")
    return normalize_mac(manual)


def derive_crypto(mac: str) -> FHToolCrypto:
    digest = hashlib.sha256(mac.encode("ascii")).hexdigest()
    key = "".join(digest[2 * i + 2] for i in range(16)).encode("ascii")
    iv = "".join(digest[3 * i + 3] for i in range(16)).encode("ascii")
    return FHToolCrypto(key=key, iv=iv, digest=digest)


def pkcs7_pad(data: bytes) -> bytes:
    padder = PKCS7(128).padder()
    return padder.update(data) + padder.finalize()


def pkcs7_unpad(data: bytes) -> bytes:
    unpadder = PKCS7(128).unpadder()
    return unpadder.update(data) + unpadder.finalize()


def encrypt_payload(payload: dict[str, Any], crypto: FHToolCrypto) -> str:
    plaintext = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    encryptor = Cipher(
        algorithms.AES(crypto.key),
        modes.CBC(crypto.iv),
    ).encryptor()
    ciphertext = encryptor.update(pkcs7_pad(plaintext)) + encryptor.finalize()
    return base64.b64encode(ciphertext).decode("ascii")


def decrypt_payload(body: str, crypto: FHToolCrypto) -> dict[str, Any]:
    raw = base64.b64decode(body.strip())
    decryptor = Cipher(
        algorithms.AES(crypto.key),
        modes.CBC(crypto.iv),
    ).decryptor()
    plaintext = pkcs7_unpad(decryptor.update(raw) + decryptor.finalize())
    return json.loads(plaintext.decode("utf-8"))


def fh_tool_call(
    ip: str,
    mac: str,
    payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    crypto = derive_crypto(mac)
    encrypted = encrypt_payload(payload, crypto)
    url = f"http://{ip}:8080{FH_TOOL_PATH}"
    try:
        response = requests.post(
            url,
            data=encrypted,
            headers={
                "Content-Type": "text/plain",
                "Connection": "close",
            },
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise FHToolError(f"无法连接 {url}: {exc}") from exc

    if response.status_code != 200:
        raise FHToolError(
            f"{FH_TOOL_PATH} 返回 HTTP {response.status_code}，设备可能不支持该接口"
        )

    try:
        return decrypt_payload(response.text, crypto)
    except Exception as exc:
        raise FHToolError("响应解密失败，MAC 可能不匹配或固件协议不同") from exc


def tcp_open(ip: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def copy_password(password: str, disabled: bool) -> None:
    if disabled or not CLIPBOARD_AVAILABLE:
        return
    try:
        pyperclip.copy(password)
    except Exception:
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="通过 fh_tool/api 获取 HG5143F(ONU) 超级管理员密码。",
    )
    parser.add_argument(
        "--ip",
        type=normalize_ip,
        help=f"网关 IPv4 地址；不传则自动探测 default gateway，失败后使用 {DEFAULT_IP}",
    )
    parser.add_argument(
        "--mac",
        help="网关 MAC，支持 AABBCCDDEEFF / AA:BB:CC:DD:EE:FF / AA-BB-CC-DD-EE-FF",
    )
    parser.add_argument(
        "--enable-telnet",
        action="store_true",
        help="获取超密后调用 TelnetEnable=1，并检查 23/tcp 是否打开",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP/TCP timeout 秒数，默认 5",
    )
    parser.add_argument(
        "--no-clipboard",
        action="store_true",
        help="不尝试复制超密到剪贴板",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 machine-readable JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ip = args.ip or detect_default_gateway() or DEFAULT_IP

    try:
        mac = normalize_mac(args.mac) if args.mac else prompt_mac(ip, args.json)
    except ValueError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2

    if not args.json:
        print(60 * "H")
        print("全自动获取 电信网关 HG5143F(ONU) 的超管密码.")
        print("当前路径: fh_tool/api -> GetAdminAccount")
        print(f"网关 IP: {ip}")
        print(f"网关 MAC: {format_mac(mac)}")
        print(60 * "H")

    result: dict[str, Any] = {
        "ip": ip,
        "mac": format_mac(mac),
        "get_admin_account": None,
        "telnet_enable": None,
        "telnet_port_open": None,
    }

    try:
        admin_response = fh_tool_call(
            ip,
            mac,
            {"index": "1", "func": "GetAdminAccount"},
            args.timeout,
        )
        result["get_admin_account"] = admin_response
    except FHToolError as exc:
        print(f"获取超密失败: {exc}", file=sys.stderr)
        return 1

    admin_name = admin_response.get("adminname")
    admin_pwd = admin_response.get("adminpwd")
    ok = admin_response.get("result") == 0 and admin_name and admin_pwd

    if ok:
        copy_password(str(admin_pwd), args.no_clipboard)
    else:
        print(f"接口返回异常: {admin_response}", file=sys.stderr)
        return 1

    if args.enable_telnet:
        try:
            telnet_response = fh_tool_call(
                ip,
                mac,
                {"index": "1", "func": "TelnetEnable", "telnet": "1"},
                args.timeout,
            )
            result["telnet_enable"] = telnet_response
            result["telnet_port_open"] = tcp_open(ip, 23, args.timeout)
        except FHToolError as exc:
            result["telnet_enable"] = {"error": str(exc)}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    clipboard_note = "，已复制到剪贴板" if CLIPBOARD_AVAILABLE and not args.no_clipboard else ""
    print(f"获取成功{clipboard_note}:")
    print(f"  username: {admin_name}")
    print(f"  password: {admin_pwd}")

    if args.enable_telnet:
        print(f"TelnetEnable 响应: {result['telnet_enable']}")
        print(f"23/tcp open: {result['telnet_port_open']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
