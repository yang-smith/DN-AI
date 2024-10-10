from pymem import Pymem


ADDRS = [0x3A70FD4, 0x3A878DC, 0x3AA0508, 0x3AC85F0, 0x3ACF3D8, 0x3AD1908]


def fix_version(pm: Pymem):
    WeChatWindll_base = 0
    for m in list(pm.list_modules()):
        path = m.filename
        if path.endswith("WeChatWin.dll"):
            WeChatWindll_base = m.lpBaseOfDll
            break

    for offset in ADDRS:
        addr = WeChatWindll_base + offset
        v = pm.read_uint(addr)
        if v == 0x63090A13:  # 已经修复过了
            continue
        elif v != 0x63090551:  # 不是 3.9.5.81 修复也没用
            raise Exception("别修了，版本不对，修了也没啥用。")

        pm.write_uint(addr, 0x63090A13)

    print("好了，可以扫码登录了")


if __name__ == "__main__":
    try:
        pm = Pymem("WeChat.exe")
        fix_version(pm)
    except Exception as e:
        print(f"{e}，请确认微信程序已经打开！")