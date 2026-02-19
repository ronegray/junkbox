# input.py
import pyxel as px
from typing import Literal, Callable
# 型指定
InputMode = Literal["once", "keep", "hold"]
TargetDevice = Literal["pad", "kbd"]
type InputHandler = Callable[[InputMode], bool]

# 入力関連定数
ANALOG_THRESHOLD_XY = 0x3FFF # アナログレバー閾値
ANALOG_THRESHOLD_TRIGGER = 0x00FF # トリガーボタン閾値
GAME_FPS = 30 # 実際の組み込み時はシステム共通設定等外部から取得する
WAIT_SEC_KEYREPEAT = 0.5
INTERVAL_SEC_KEYREPEAT = 0.1
ASSIGNABLE_KEYS =(
px.KEY_ESCAPE,px.KEY_F1,px.KEY_F2,px.KEY_F3,px.KEY_F4,px.KEY_F5,px.KEY_F6,px.KEY_F7,px.KEY_F8,px.KEY_F9,px.KEY_F10,px.KEY_F11,px.KEY_F12,px.KEY_PRINTSCREEN,px.KEY_SCROLLLOCK,px.KEY_PAUSE,

px.KEY_1,px.KEY_2,px.KEY_3,px.KEY_4,px.KEY_5,px.KEY_6,px.KEY_7,px.KEY_8,px.KEY_9,px.KEY_0,px.KEY_MINUS,px.KEY_CARET,px.KEY_BACKSLASH,px.KEY_BACKSPACE,px.KEY_INSERT,px.KEY_HOME,px.KEY_PAGEUP,

px.KEY_TAB,px.KEY_Q,px.KEY_W,px.KEY_E,px.KEY_R,px.KEY_T,px.KEY_Y,px.KEY_U,px.KEY_I,px.KEY_O,px.KEY_P,px.KEY_AT,px.KEY_LEFTBRACKET,px.KEY_RETURN,px.KEY_DELETE,px.KEY_END,px.KEY_PAGEDOWN,

px.KEY_CAPSLOCK,px.KEY_A,px.KEY_S,px.KEY_D,px.KEY_F,px.KEY_G,px.KEY_H,px.KEY_J,px.KEY_K,px.KEY_L,px.KEY_SEMICOLON,px.KEY_COLON,px.KEY_RIGHTBRACKET,

px.KEY_LSHIFT,px.KEY_Z,px.KEY_X,px.KEY_C,px.KEY_V,px.KEY_B,px.KEY_N,px.KEY_M,px.KEY_COMMA,px.KEY_PERIOD,px.KEY_SLASH,px.KEY_BACKSLASH,px.KEY_RSHIFT,px.KEY_UP,

px.KEY_LCTRL,px.KEY_LALT,px.KEY_SPACE,px.KEY_RALT,px.KEY_MENU,px.KEY_RCTRL,px.KEY_LEFT,px.KEY_DOWN,px.KEY_RIGHT,

px.KEY_NUMLOCKCLEAR,px.KEY_KP_DIVIDE,px.KEY_KP_MULTIPLY,px.KEY_KP_MINUS,px.KEY_KP_7,px.KEY_KP_8,px.KEY_KP_9,px.KEY_KP_PLUS,px.KEY_KP_4,px.KEY_KP_5,px.KEY_KP_6,px.KEY_KP_1,px.KEY_KP_2,px.KEY_KP_3,px.KEY_KP_ENTER,px.KEY_KP_0,px.KEY_KP_PERIOD
)


# デフォルトキーマップ
DEFAULT_BINDS_PAD: dict[str, int] = { # パッド
    "up": px.GAMEPAD1_BUTTON_DPAD_UP,
    "down": px.GAMEPAD1_BUTTON_DPAD_DOWN,
    "left": px.GAMEPAD1_BUTTON_DPAD_LEFT,
    "right": px.GAMEPAD1_BUTTON_DPAD_RIGHT,
    "decide": px.GAMEPAD1_BUTTON_A,
    "cancel": px.GAMEPAD1_BUTTON_B,
    "other1": px.GAMEPAD1_BUTTON_X,
    "other2": px.GAMEPAD1_BUTTON_Y,
    "LS": px.GAMEPAD1_BUTTON_LEFTSHOULDER,
    "RS": px.GAMEPAD1_BUTTON_RIGHTSHOULDER
}
DEFAULT_BINDS_KBD: dict[str, int] = { # キーボード
    "up": px.KEY_UP,
    "down": px.KEY_DOWN,
    "left": px.KEY_LEFT,
    "right": px.KEY_RIGHT,
    "decide": px.KEY_Z,
    "cancel": px.KEY_X,
    "other1": px.KEY_C,
    "other2": px.KEY_V,
    "LS": px.KEY_LSHIFT,
    "RS": px.KEY_RSHIFT
}

# --- 内部状態（モジュール変数） ---
# アクション：入力判定関数
_action_keymap_pad: dict[str, InputHandler] = {}
_action_keymap_kbd: dict[str, InputHandler] = {}
# アクション：[キーコード、入力正負]
_key_assign_map_pad: dict[str, dict[str, int]] = {}
_key_assign_map_kbd: dict[str, dict[str, int]] = {}


def _wrap_analog_input(key_code: int, input_sign: int=1,hold_sec: float=WAIT_SEC_KEYREPEAT,
                       repeat_sec: float=INTERVAL_SEC_KEYREPEAT) -> InputHandler:
    '''アナログ入力btnvでbtn/btnp/btnp-repeatを再現する為のラッパー'''
    frame_count = 0 # 0: 離している / 1以上: 倒し続けているフレーム数
    # btnp-repeat再現用パラメータ
    hold_frame = _sec_to_frames(hold_sec)
    repeat_frame = _sec_to_frames(repeat_sec)

    # 入力閾値　レバーとトリガーで別設定
    if key_code in (px.GAMEPAD1_AXIS_LEFTX,px.GAMEPAD1_AXIS_LEFTY,
                    px.GAMEPAD1_AXIS_RIGHTX,px.GAMEPAD1_AXIS_RIGHTY):
        threshold = ANALOG_THRESHOLD_XY
    elif key_code in (px.GAMEPAD1_AXIS_TRIGGERLEFT,px.GAMEPAD1_AXIS_TRIGGERRIGHT):
        threshold = ANALOG_THRESHOLD_TRIGGER

    def check(mode: InputMode ="once") -> bool:
        nonlocal frame_count  # 外側の変数を書き換えるために必要
        # 現在のアナログ値を取得
        val = px.btnv(key_code)
        is_active = (val * input_sign) > threshold

        # keep(押しっぱなし) 単に閾値を超えているか返すだけ
        if mode == "keep":
            return is_active

        # once(一回性),hold(長押し繰り返し)の判定
        if is_active:
            frame_count += 1
            # 1フレーム目はどちらもTrue
            if frame_count == 1:
                return True
            # once：2フレーム目以降は常にFalse
            if mode == "once":
                return False
            # hold：hold期間を超え、かつrepeat間隔ごとにTrueを返す
            if mode == "hold" and frame_count > hold_frame:
                if (frame_count - hold_frame) % repeat_frame == 0:
                    return True
        else:
            # キー入力停止（閾値を下回る）でリセット
            frame_count = 0

        return False

    return check


def _generate_handler(key_code: int, input_sign: int=1) -> InputHandler:
    '''入力コードに応じた適切な判定関数（クロージャ）を生成する'''
    # アナログ軸（スティック・トリガー）の場合
    if key_code in (px.GAMEPAD1_AXIS_LEFTX, px.GAMEPAD1_AXIS_LEFTY,
                    px.GAMEPAD1_AXIS_RIGHTX, px.GAMEPAD1_AXIS_RIGHTY,
                    px.GAMEPAD1_AXIS_TRIGGERLEFT, px.GAMEPAD1_AXIS_TRIGGERRIGHT):
        return _wrap_analog_input(key_code, input_sign)
    # それ以外の全てのデジタルキー・ボタンの場合
    else:
        return lambda mode="once": (
            px.btn(key_code) if mode == "keep" else
            px.btnp(key_code) if mode == "once" else
            px.btnp(key_code, hold=15, repeat=5) if mode == "hold" else
            False
        )


def keybind(action_name: str, key_code: int, input_sign: int=1, bind_target: TargetDevice="pad") -> bool:
    '''行動名に対してキーコード設定済入力判定クロージャおよびセーブロード用辞書を設定'''
    match bind_target:
        case "pad":
            # rust>pyxel-platform>key.rsより
            if key_code < px.GAMEPAD1_AXIS_LEFTX:
                print(f"Warning: {action_name} to {key_code} is not a valid Pad code.") 
                return False
            target_actmap = _action_keymap_pad
            target_assign = _key_assign_map_pad
        case "kbd":
            if key_code >= px.MOUSE_POS_X:
                print(f"Warning: {action_name} to {key_code} is not a valid keyboard code.") 
                return False
            target_actmap = _action_keymap_kbd
            target_assign = _key_assign_map_kbd
        case _:
            return False

    target_actmap[action_name] = _generate_handler(key_code, input_sign)
    target_assign[action_name] = {"code": key_code, "input_sign": input_sign}

    return True


def _bind_all_actions(bind_target: TargetDevice, key_assign_map: dict|None=None):
    '''定義済データの一括反映'''
    if key_assign_map is None:
        if bind_target == "pad":
            key_assign_map = DEFAULT_BINDS_PAD.copy()
        elif bind_target == "kbd":
            key_assign_map = DEFAULT_BINDS_KBD.copy()
        else:
            print(f"Warning: No default bindmap for bind_target:{bind_target}") 
            return False

    for action, key in key_assign_map.items():
        if type(key) is dict:
            sign = key["input_sign"]
            keycode = key["code"]
        else:
            sign = 1
            keycode = key
        keybind(action, keycode, sign, bind_target)


def init():
    '''初期化時に一括でバインドする'''
    _bind_all_actions("pad")
    _bind_all_actions("kbd")


def listener(listen_target: TargetDevice="pad") -> tuple[int, int]|None:
    if listen_target == "pad":
        # キーパッドの判定(アナログ入力)
        for keycode in range(px.GAMEPAD1_AXIS_LEFTX, px.GAMEPAD1_AXIS_RIGHTY+1):
            input_val = px.btnv(keycode)
            if abs(input_val) > ANALOG_THRESHOLD_XY: # 1以上、とかだと遊びの範囲で超反応するケースあり
                input_sign = int(px.sgn(input_val))
                return keycode, input_sign
        for keycode in range(px.GAMEPAD1_AXIS_TRIGGERLEFT, px.GAMEPAD1_AXIS_RIGHTY+1):
            input_val = px.btnv(keycode)
            if abs(input_val) > ANALOG_THRESHOLD_TRIGGER:
                return keycode, 1

        # キーパッドの判定(デジタル入力)
        for keycode in range(px.GAMEPAD1_BUTTON_A, px.GAMEPAD1_BUTTON_DPAD_RIGHT+1):
            if px.btnp(keycode):
                return keycode, 1

    elif listen_target == "kbd":
        for keycode in ASSIGNABLE_KEYS:
            if px.btnp(keycode):
                return keycode, 1
            
    return None


def is_pressed(action_name: str, mode: InputMode="once") -> bool:
    '''アクションに該当する入力の有無を判定する'''
    # パッド
    func_pad = _action_keymap_pad.get(action_name)
    is_pad = func_pad(mode) if func_pad else False
    # キーボード
    func_kbd = _action_keymap_kbd.get(action_name) 
    is_kbd = func_kbd(mode) if func_kbd else False

    return (is_pad or is_kbd)


def get_keymap(target: TargetDevice):
    '''本モジュール利用側へキーマップ情報を提供'''
    match target:
        case "pad":
            keymap = _key_assign_map_pad
        case "kbd":
            keymap = _key_assign_map_kbd

    return keymap

# ----------------------------------
# のちのち共通関数等に切り出す部分の為敢えてここに記述
# ----------------------------------
import json
from pathlib import Path
# 設定ファイルの保存先（Python標準のpathlibを使うと安全です）
CONFIG_PATH = Path("keyconfig.json")
def save_config():
    '''jsonファイルとして設定を保存'''
    key_config_data = {
        "pad": _key_assign_map_pad,
        "kbd": _key_assign_map_kbd
        }

    # 実際の組み込み時は共通関数のjson書き込みを呼び出す
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        # indent=4 を入れると、人間がテキストエディタで読みやすい形式になります
        json.dump(key_config_data, f, indent=4)


def load_config():
    '''jsonファイルからキーコードのマッピングを呼び出し、判定関数を再生成'''
    if not CONFIG_PATH.exists():
            init()  # ファイルがなければデフォルトで初期化
            return

    try:
        #　実際の組み込み時は共通関数のjson読み込みを呼び出す
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
           
        # デフォルト値をベースに、JSONにある設定だけを上書き（安全なマージ）
        key_assign_map = {}
        for action in DEFAULT_BINDS_PAD.keys():
            # JSONにキーがあればその値を、無ければデフォルト値を取得
            key_assign_map[action] = loaded_data["pad"].get(action, DEFAULT_BINDS_PAD[action])
        # アクション：[キーコード、入力正負]の辞書データから入力判定関数と保存用データを再生成
        _bind_all_actions("pad",key_assign_map)
        
        for action in DEFAULT_BINDS_KBD.keys():
            # JSONにキーがあればその値を、無ければデフォルト値を取得
            key_assign_map[action] = loaded_data["kbd"].get(action, DEFAULT_BINDS_KBD[action])
        _bind_all_actions("kbd",key_assign_map)

    except json.JSONDecodeError:
        # ファイルが壊れていた場合はデフォルト設定のまま進行
        print("設定ファイルが破損しているため、デフォルト値を使用します。")
    

def _sec_to_frames(seconds):
    # Pyxelのデフォルトは30ですが、将来的に可変にするならここを調整
    return int(seconds * 30)