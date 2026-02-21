import gzip
from pyxel import Image
from hashlib import sha256
from pathlib import Path
from struct import pack, unpack

def check_file(filepath, chk_mode: str="r") -> Path|None:
    '''ファイル操作前の存在のチェック'''
    # チェックモードの確認
    if chk_mode not in ("r","w"):
        return None

    # 対象ファイルと親ディレクトリのパスを取得
    path = Path(filepath)
    parent = path.parent

    if chk_mode == "r": # read時は指定ファイルの有無
        if not path.exists():
            return None
    elif chk_mode == "w": # write時は出力先の有無
        if not parent.exists():
            return None
        if not parent.is_dir():
            return None
    
    return path


def read_bin(filepath: Path) -> bytes:
    '''バイナリファイルを読み込んでバイナリデータを返す'''
    with open(filepath, "rb") as f:
        bin_data: bytes = f.read()
    return bin_data


def write_bin(filepath: Path, bin_data: bytes):
    '''バイナリデータのファイル出力'''
    with open(filepath, "wb") as f:
        f.write(bin_data)


def convert_bmp(filename: str) -> bool:
    '''指定された画像ファイルに画像サイズとハッシュを付けてgzip保存する'''
    # ファイル存在チェック
    filepath = check_file(filename, "r")
    if not filepath:
        return False

    # 1. いったん普通にBMPを読み込む
    img = Image.from_image(filename)
    # 2. Pyxelのメモリから「純粋なピクセルデータ」をbytesとして取り出す
    pixel_data = img.data_ptr()
    raw_pixel_data = bytes(pixel_data)
    # 3. 展開時に利用する画像サイズ情報を付与してピクセルデータを圧縮する
    sizeheader = pack("!HH", img.width, img.height)
    compressed = gzip.compress(sizeheader + raw_pixel_data)
    # 4. ハッシュ計算
    hash_value = sha256(compressed).digest()
    # 5. データファイルの出力
    writepath = check_file(filepath.with_suffix(".bdt"), "w")
    if not writepath:
        return False
    write_bin(writepath, hash_value + compressed)

    return True

def load_dat_bmp(filename: str) -> Image|None:
    '''変換済ビットマップファイルを読み込んでImageオブジェクトを生成'''
    # ファイル存在チェック
    filepath = check_file(filename, "r")
    if not filepath:
        return None

    # データファイル読込
    bin_data = read_bin(filepath)
    # ハッシュデータと分離
    hash_value = bin_data[:32]  # SHA-256ハッシュ（32バイト）
    compressed = bin_data[32:]
    # ハッシュチェック
    if sha256(compressed).digest() != hash_value:  # ハッシュ一致
        return None

    # 復元処理
    decompressed = gzip.decompress(compressed)
    sizeheader = decompressed[:4]
    raw_pixel_data = decompressed[4:]
    img_width, img_height = unpack("!HH", sizeheader)

    pixel_image = Image(img_width, img_height)
    pixel_data = pixel_image.data_ptr()
    pixel_data[:] = raw_pixel_data

    return pixel_image