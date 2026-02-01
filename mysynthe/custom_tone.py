from pyxel import Tone, sin
import json

class CustomTone:
    '''PyxelのToneクラスを取り込んだ拡張クラス'''

    def __init__(self):
# from 14_synthesize.py
# [(mode, sample_bits, wavetable, gain), (mode, sample_bits, wavetable, gain), ...]
# 'mode' corresponds to:
#  0 for wavetable, 1 for short-period noise, 2 for long-period noise.
# 'wavetable' can be any length, but all are 32 elements in this example.
# 'wavetable' value range depends on 'sample_bits'. For 4 bits, the range is 0-15.
        self._entity = Tone()
        self._mode: int = 0 # for wavetable
        self._gain: float = 1.0
        self._sample_bits: int = 6 # 6 bits -> volume range 0-63
        self.set_parameter()

        # 事前定義波形データ
        self._waveform_dicts: dict[str,list[int]] = {
            "sign": [], # サインカーブは後から関数で導出
            "triangle": [32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 62]+
                    [63, 61, 59, 57, 55, 53, 51, 49, 47, 45, 43, 40, 38, 36, 34, 32]+
                    [30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2, 0]+
                    [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31],
            "square": [63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63]+
                    [63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63]+
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]+
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "pulse": [63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63, 63]+
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]+
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]+
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "saw": [63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48]+
                    [47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32]+ 
                    [31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16]+
                    [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
            "saw4": [63, 58, 54, 49, 45, 40, 36, 32, 28, 24, 20, 16, 12, 8, 4, 3]+
                    [62, 58, 54, 49, 45, 40, 36, 32, 28, 24, 20, 16, 12, 8, 4, 2]+
                    [61, 58, 54, 49, 45, 40, 36, 32, 28, 24, 20, 16, 12, 8, 4, 1]+
                    [60, 58, 54, 49, 45, 40, 36, 32, 28, 24, 20, 16, 12, 8, 4, 0],
            }
        # サインカーブ生成
        width = 64
        center_y = 32
        amplitude = 32
        waveform: list = []
        for x in range(width):
            angle = (x / width) * 360
            waveform.append(min((2 ** self._sample_bits) - 1,
                                int(sin(angle) * amplitude + center_y)))
        self._waveform_dicts["sign"] = waveform.copy()

        self.update_wavetable(self._waveform_dicts["sign"])

    def set_parameter(self, mode: int | None = None, gain: float | None = None,
                      sample_bits: int | None = None):
        '''Toneクラス用パラメータをカスタムクラスのプロパティから反映'''
        self._entity.mode = mode if mode is not None else self._mode
        self._entity.gain = gain if gain is not None else self._gain
        self._entity.sample_bits = sample_bits if sample_bits is not None else self._sample_bits

    def update_wavetable(self, waveform_volumes: list[int]):
        '''波形データを変更'''
        self._entity.wavetable.from_list(waveform_volumes) # type: ignore

    def get_wavetable(self) -> list:
        return self._entity.wavetable.to_list() # type: ignore

    def read_json(self, filename: str):
        '''jsonファイルの読み込み'''
        with open(filename, "r", encoding = "UTF-8") as f:
            data = json.load(f)
        return data

    def write_json(self, filename: str, data: str):
        '''jsonファイルの書き込み'''
        with open(filename, "w") as f:
            f.write(data)

    def load_parameter(self, filename: str) -> str:
        '''jsonファイルからパラメータを読み込み、クラス変数に反映'''
        try:
            data = self.read_json(filename)

            self._mode = data.get("mode", 0)
            self._gain = data.get("gain", 1.0)
            self._sample_bits = data.get("sample_bits", 6)
            self.set_parameter()
            self._entity.wavetable.from_list(data.get("waveform_volumes", [])) # type: ignore
            return f"Loaded: {filename}"
        except FileNotFoundError:
            return f"Error: {filename} not found."

    def save_parameter(self, filename: str) -> str:
        '''現在のパラメータをjsonファイルとして保存'''
        data = {
            "mode": self._mode,
            "gain": self._gain,
            "sample_bits": self._sample_bits,
            "waveform_volumes": self._entity.wavetable.to_list() # type: ignore
        }
        # json.dumpsで文字列化して、既存のwrite_jsonを利用
        json_str = json.dumps(data, indent=4)
        self.write_json(filename, json_str)
        return f"Saved: {filename}"

