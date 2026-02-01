import pyxel as px
import custom_tone

# 音色編集中に鳴らす楽譜のサンプル（１ｃｈ分のみ）
MMLSTAT: str = "@0" # tone0に対して設定している為音色番号は0必須
MMLCODE: str = "cdefgab>c"
# MMLSTAT: str = "T132 @0 Q99 O2 L16"
# MMLCODE: str = "[[drdd]4 [frff]2 [grgg]2]2 [a#ra#a#]4 [araa]8"


# ADSR編集用オブジェクト(4つ生成)
class Knob:
    MAXVOL: int = 127
    RADIUS: int = 4
    LABEL_OFFSET: dict[str,int] = {"x": -1, "y": -2}

    def __init__(self, app: "App", label: str, x: float, y: float):
        self.parent: App = app
        self.label: str = label
        self.x: float = x
        self.y: float = Knob.MAXVOL - y
        self.is_move: bool = False
        self.color: int = px.COLOR_BROWN
        match self.label:
            case "A":
                self.color = px.COLOR_RED
            case "D":
                self.color = px.COLOR_ORANGE
            case "S":
                self.color = px.COLOR_GREEN
            case "R":
                self.color = px.COLOR_DARK_BLUE

    def update(self):
        if px.btn(px.MOUSE_BUTTON_LEFT):
            dx = self.parent.DRAW_OFFSET_E["x"] + self.x - px.mouse_x
            dy = self.parent.DRAW_OFFSET_E["y"] + self.y - px.mouse_y
            if dx**2 + dy**2 < Knob.RADIUS**2:
                self.is_move = True
        else:
            self.is_move = False
            
        if self.is_move:
            self.x = px.mouse_x - self.parent.DRAW_OFFSET_E["x"]
            self.y = px.mouse_y - self.parent.DRAW_OFFSET_E["y"]
            match self.label:
                case "A":
                    self.x = min(max(self.parent.ENVELOPE_BOX["u"], self.x),
                                 self.parent.adsr["D"].x)
                    self.y = 0
                case "D":
                    self.x = min(max(self.x, self.parent.adsr["A"].x), self.parent.ENVELOPE_BOX["w"])
                    self.y = self.parent.adsr["S"].y
                case "S":
                    self.x = self.parent.ENVELOPE_BOX["w"] + Knob.RADIUS
                    self.y = min(Knob.MAXVOL, max(0, self.y))
                    self.parent.adsr["D"].y = self.y
                case "R":
                    self.x = min(self.parent.RELEASE_BOX["u"]+self.parent.RELEASE_BOX["w"],
                                 max(self.parent.RELEASE_BOX["u"], self.x))
                    self.y = Knob.MAXVOL

    def draw(self):
        px.circ(self.x, self.y, Knob.RADIUS, self.color)
        px.text(self.x + Knob.LABEL_OFFSET["x"], self.y + Knob.LABEL_OFFSET["y"],
                self.label, px.COLOR_WHITE)


# wavetable編集用(64個生成)
class Slider:
    MAXVOL: int = 63
    MINVOL: int = 0

    def __init__(self, app: "App", bit: int, vol: int):
        self.parent: App = app
        self.bit: int = bit
        self.vol: int = vol
        self.size: int = 3
        self.is_move: bool = False
        self.color: int = px.COLOR_LIGHT_BLUE

    def update(self):
        if px.btn(px.MOUSE_BUTTON_LEFT) and (
            self.parent.DRAW_OFFSET_W["x"] + self.bit * 4 + 2
            <= px.mouse_x <=
            self.parent.DRAW_OFFSET_W["x"] + self.bit * 4 + 2 + self.size
        ) and (
            self.parent.DRAW_OFFSET_W["y"] + self.parent.WAVETABLE_BOX["v"]
            <= px.mouse_y <=
            self.parent.DRAW_OFFSET_W["y"] + self.parent.WAVETABLE_BOX["v"] + self.parent.WAVETABLE_BOX["h"]
        ):
            self.is_move = True
        else:
            self.is_move = False

        if self.is_move:
            self.vol = max(0, min(63, 64 - ((px.mouse_y - self.parent.DRAW_OFFSET_W["y"]) // 2)))

    def draw(self):
        color = px.COLOR_RED if self.is_move else self.color
        left = self.bit * 4 + 2
        top = 128 - (self.vol * 2) - 1

        px.rect(left, top + self.size, self.size, (self.vol * 2), px.COLOR_NAVY)
        px.rect(left, top, self.size, self.size, color)


# 画面等メイン部分
class App:
    DRAW_OFFSET_E: dict[str, int] = {"x": 8, "y": 16}
    ENVELOPE_BOX: dict[str, int] = {"u": 0, "v":0, "w":64, "h":128}
    RELEASE_BOX: dict[str, int] = {"u": ENVELOPE_BOX["w"] + Knob.RADIUS * 2 + 1,
                                   "v": 0, "w": 32, "h": 128}
    DRAW_OFFSET_W: dict[str, int] = {"x": 136, "y": 16}
    WAVETABLE_BOX: dict[str, int] = {"u": 0, "v":0, "w":259, "h":131}

    def __init__(self):
        # 波形編集時のマウス位置のトラッキング精度の為FPSを240に設定
        px.init(416, 192, title=__file__.split("\\")[-1], fps=240) 
        px.load("mysynthe.pyxres")
        self.msgtxt: str = ""

        # 主要要素事前定義
        self.init_env()
        self.init_wav()

        # テストサウンド定義
        self.mmlstat: str = MMLSTAT
        self.mmlcode: str = MMLCODE
        self.env_string: str = ""

        # 視聴用サウンドの設定
        px.sounds[0].mml(self.mmlstat + self.mmlcode)

        px.mouse(True) # マウスカーソル表示
        px.run(self.update, self.draw)

    def init_env(self):
        '''エンベロープパラメータ初期化'''
        self.adsr: dict[str,Knob] = {
            "A": Knob(self, "A", 0, 127),
            "D": Knob(self, "D", 16, 96),
            "S": Knob(self, "S", App.ENVELOPE_BOX["w"] + Knob.RADIUS, 96),
            "R": Knob(self, "R", App.RELEASE_BOX["u"] + App.RELEASE_BOX["w"], 0),
        }

    def init_wav(self):
        '''波形パラメータ初期化'''
        self.custom_tone = custom_tone.CustomTone()

        # スライダの生成（デフォルト値は拡張トーンクラスのデフォルト波形＝正弦波）
        self.waveform_sliders: list[Slider] = [ # list[Slider.vol]->Tone.wavetable.from_list()
            Slider(self, bit, vol) for bit, vol 
            in enumerate(self.custom_tone.get_wavetable())] 

        # 一括設定ボタン用設定
        x = self.DRAW_OFFSET_W["x"] + self.WAVETABLE_BOX["u"]
        y = self.DRAW_OFFSET_W["y"] + self.WAVETABLE_BOX["h"] + 2
        offset = 30 # ボタンの描画間隔
        self.waveform_button_dicts: dict[str,list[int]] = {
            "sign": [x, y, 18, 10],
            "triangle": [x + offset * 1, y, 18, 10],
            "square": [x + offset * 2, y, 18, 10],
            "pulse": [x + offset * 3, y, 18, 10],
            "saw": [x + offset * 4, y, 18, 10],
            }
        self.file_button_dicts: dict[str,list[int]] = {
            "save": [x + offset * 5, y, 18, 10],
            "load": [x + offset * 6, y, 18, 10]
        }

        # 標準トーン0番を書き換え（14_synthesizer.pyに倣って4ch以上に拡張してもOK）
        px.tones[0] = self.custom_tone._entity

        # 編集中フラグの初期値定義
        self.is_editing_wavetable: bool = False

    def update_slider(self, wavetable: list):
        '''全スライダーのボリューム設定を更新'''
        for i, vol in enumerate(wavetable):
            self.waveform_sliders[i].vol = vol

    def update(self):
        '''アプリケーション更新'''
        # サウンド再生・停止
        if px.btnp(px.KEY_SPACE):
            if px.play_pos(0) is None:
                px.play(0, 0, loop=True)
            else:
                px.stop()

        # エンベロープつまみ操作
        for obj_e in self.adsr.values():
            obj_e.update()
            if obj_e.is_move:
                self.msgtxt = ""
                break
        # エンベロープ文字列生成
        attack = self.adsr["A"].x
        decay = self.adsr["D"].x - self.adsr["A"].x
        sustain = 127 - self.adsr["S"].y
        release = self.adsr["R"].x - self.RELEASE_BOX["u"]
        env = f"@ENV1{{0,{attack},127,{decay},{sustain},{release},0}}"
        # 変更があった時は再生音に反映
        if self.env_string != env:
            self.env_string = env
            px.sounds[0].mml(self.mmlstat + self.env_string + self.mmlcode)

        # 波形スライダー操作
        for obj_w in self.waveform_sliders:
            obj_w.update()
            if obj_w.is_move:
                self.msgtxt = ""
                self.is_editing_wavetable = True
                break
        # 波形スライダー編集結果の反映
        if self.is_editing_wavetable and px.btnr(px.MOUSE_BUTTON_LEFT):
            self.is_editing_wavetable = False
            wavetable = [slider.vol for slider in self.waveform_sliders]
            self.custom_tone.update_wavetable(wavetable)

        # ボタンクリック（波形、セーブ／ロード）
        if px.btnp(px.MOUSE_BUTTON_LEFT):
            self.msgtxt = ""
            for key, box in self.waveform_button_dicts.items():
                if (box[0] <= px.mouse_x <= box[0]+box[2]
                    and box[1] <= px.mouse_y <= box[1]+box[3]
                ):
                    wavetable = self.custom_tone._waveform_dicts[key].copy()
                    # for i, vol in enumerate(wavetable):
                    #     self.waveform_sliders[i].vol = vol
                    self.update_slider(wavetable)
                    self.custom_tone.update_wavetable(wavetable)
            for key, box in self.file_button_dicts.items():
                if (box[0] <= px.mouse_x <= box[0]+box[2]
                    and box[1] <= px.mouse_y <= box[1]+box[3]
                ):
                    match key:
                        case "save":
                            self.msgtxt = self.custom_tone.save_parameter("waveform.json")
                        case "load":
                            self.msgtxt = self.custom_tone.load_parameter("waveform.json")
                            self.update_slider(self.custom_tone.get_wavetable())

    def draw_env(self):
        '''エンベロープ表示'''
        px.camera(-App.DRAW_OFFSET_E["x"],-App.DRAW_OFFSET_E["y"])

        # 枠
        px.rectb(*App.ENVELOPE_BOX.values(), px.COLOR_WHITE) # type: ignore
        px.rectb(*App.RELEASE_BOX.values(), px.COLOR_NAVY) # type: ignore
        for x in range(0, App.ENVELOPE_BOX["w"], 2):
            px.pset(x, App.ENVELOPE_BOX["h"]//2, px.COLOR_WHITE)

        # 線
        # 0 to A
        px.line(App.ENVELOPE_BOX["u"], App.ENVELOPE_BOX["h"] - 1,
                self.adsr["A"].x, self.adsr["A"].y, self.adsr["A"].color)
        # A to D
        px.line(self.adsr["A"].x, self.adsr["A"].y,
                self.adsr["D"].x, self.adsr["D"].y, self.adsr["D"].color)
        # S
        px.line(App.ENVELOPE_BOX["u"], self.adsr["S"].y,
                self.adsr["S"].x, self.adsr["S"].y, self.adsr["S"].color)
        # R
        px.line(self.adsr["S"].x + self.adsr["S"].RADIUS, self.adsr["S"].y,
                self.adsr["R"].x, self.adsr["R"].y, self.adsr["R"].color)
        # つまみ
        for obj in self.adsr.values():
            obj.draw()

        # @ENV文字列
        px.text(0, -11, self.env_string, px.COLOR_CYAN)

        # カメラ戻し
        px.camera()
    
    def draw_wave(self):
        '''波形フォーム表示'''
        px.camera(-App.DRAW_OFFSET_W["x"],-App.DRAW_OFFSET_W["y"])

        # 枠
        px.rectb(*App.WAVETABLE_BOX.values(), px.COLOR_WHITE) # type: ignore
        # 横軸
        for y in (32,96):
            for x in range(-1, App.WAVETABLE_BOX["w"]+1, 4):
                px.pset(x, y, px.COLOR_PEACH)
        for x in range(-1, App.WAVETABLE_BOX["w"]+1, 2):
            px.pset(x, 64, px.COLOR_PEACH)
        px.text(-10, -2, "31", px.COLOR_WHITE)
        px.text(-10, 30, "15", px.COLOR_WHITE)
        px.text(-5, 62, "0", px.COLOR_WHITE)
        px.text(-14, 94, "-16", px.COLOR_WHITE)
        px.text(-14, 126, "-32", px.COLOR_WHITE)
        # 縦軸
        for x in (65,193):
            px.line(x, 0, x, App.WAVETABLE_BOX["h"]-1, px.COLOR_GRAY)
        px.line(129, 0, 129, App.WAVETABLE_BOX["h"]-1, px.COLOR_LIME)

        # スライダー
        for obj in self.waveform_sliders:
            obj.draw()

        # カメラ戻し
        px.camera()

    def draw(self):
        '''アプリケーション描画'''
        px.cls(0)
        self.draw_env()  # エンベロープ領域
        self.draw_wave() # 波形領域

        # 波形ボタン
        # クリック時の座標判定にカメラのズレを含めたくないので、draw_waveではなくここで描画
        # sign
        px.rectb(*self.waveform_button_dicts["sign"], px.COLOR_ORANGE) # type: ignore
        px.blt(self.waveform_button_dicts["sign"][0] + 1, self.waveform_button_dicts["sign"][1] + 1,
               0, 0, 0, 16, 8)
        # tri
        px.rectb(*self.waveform_button_dicts["triangle"], px.COLOR_ORANGE) # type: ignore
        px.blt(self.waveform_button_dicts["triangle"][0] + 1, self.waveform_button_dicts["triangle"][1] + 1,
               0, 0, 8, 16, 8)
        # square
        px.rectb(*self.waveform_button_dicts["square"], px.COLOR_ORANGE) # type: ignore
        px.blt(self.waveform_button_dicts["square"][0] + 1, self.waveform_button_dicts["square"][1] + 1,
               0, 0, 16, 16, 8)
        # pulse
        px.rectb(*self.waveform_button_dicts["pulse"], px.COLOR_ORANGE) # type: ignore
        px.blt(self.waveform_button_dicts["pulse"][0] + 1, self.waveform_button_dicts["pulse"][1] + 1,
               0, 0, 24, 16, 8)
        # saw
        px.rectb(*self.waveform_button_dicts["saw"], px.COLOR_ORANGE) # type: ignore
        px.blt(self.waveform_button_dicts["saw"][0] + 1, self.waveform_button_dicts["saw"][1] + 1,
               0, 0, 32, 16, 8)

        # セーブ
        px.rectb(*self.file_button_dicts["save"], px.COLOR_GREEN) # type: ignore
        px.blt(self.file_button_dicts["save"][0] + 1, self.file_button_dicts["save"][1] + 1,
               0, 0, 40, 16, 8)
        # ロード
        px.rectb(*self.file_button_dicts["load"], px.COLOR_RED) # type: ignore
        px.blt(self.file_button_dicts["load"][0] + 1, self.file_button_dicts["load"][1] + 1,
               0, 0, 48, 16, 8)
        
        px.text(4, px.height - 9, "Hit Space Key to ON/OFF sound", px.COLOR_LIGHT_BLUE)
        px.text(px.width - len(self.msgtxt) * 5, px.height - 9, self.msgtxt, px.COLOR_LIGHT_BLUE)

App()

