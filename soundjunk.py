import pyxel as px
px.init(128,128,title=__file__.split("\\")[-1])

track:list[list[str]] = [["" for _ in range(16)] for _ in range(8)]

track[0][0]="@2 @ENV1{63,12,96,36,127} @VIB1{40,13,25} @VIB2{36,9,50} Q100 O4 L4 "
track[1][0]="@2 @ENV1{63,12,96,36,127} Q80 O4 L4 Y10 V96"
# track[1][0]="T112 V60 L16 @2 O4" #DQ序曲の残骸
track[2][0]="@0 V127 O2 L8 Q50 @ENV1{127,8,32} "
track[3][0]="@3 Q60 @ENV1{108,8,0} O6 L16 "
track[4][0]="@3 V127 Q60 @ENV2{48,8,0} O7 L16 "
track[5][0]="@3 Q50 @ENV3{96,48,0} O7 L16 "

track[0][1]=" @VIB1 @ENV0 ccggaag2 ffeeddc2 ggffeed2 @VIB1 ggffeed2 ccggaag2 ffeeddc2"
track[1][1]="r32 @ENV1 ccggaag2 ffeeddc2 ggffeed2 @VIB1 ggffeed2 ccggaag2 ffeeddc2"
# track[1][1]="c8rff8 c8c8c8<a8> c8f8g8f8 c8f8g8a8 a#8>d8<a#8a8 g8f8c8.c c8f8.ff8 f8<a8>f8c1&4"#DQ序曲の残骸

# track[2][1]="[[Q90c >c16c16<]4 [Q90<b-> b-16b-16< ]4]2" #もともとの譜面
track[2][1]="[Q90c >c16c16<]8 [Q90<f> f16f16< ]4 >[Q90c >c16c16<]4"
track[2][2]="[Q90<f> f16f16< ]4 [Q90e >e16e16<]4 >[Q90<f> f16f16< ]4 [Q90g >g16g16<]4 >"
track[2][3]="[Q90c >c16c16<]8 [Q90<f> f16f16< ]4 >[Q90c >c16c16<]4"

track[3][1]="[ar rr r8 rr [a r]2 r8 rr]4"
track[4][1]="[rr aa r8 aa [r a]2 r8 aa]4"
track[5][1]="[rr rr a8 rr [r r]2 a8 rr]4"

for i,tdata in enumerate(track):
    if tdata[0]:
        mmltext = ""
        for data in tdata:
            mmltext += data
        px.sounds[i].mml(mmltext)

ext_tone = px.Tone()
EXT_TONE_ENV = (  # Saw Wave
        0, 4,
        [15, 15, 14, 14, 13, 13, 12, 12, 11, 11, 10, 10, 9, 9, 8, 8]
        + [7, 7, 6, 6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 0, 0],
        1.0,
    )
ext_tone.mode = EXT_TONE_ENV[0]
ext_tone.sample_bits = EXT_TONE_ENV[1]
ext_tone.waveform.from_list(EXT_TONE_ENV[2])
ext_tone.gain = EXT_TONE_ENV[3]
px.tones[0] = ext_tone

channels:list[px.Channel] = []
for _ in range(8):
    channel = px.Channel()
    channel.gain = 0.5/8
    channel.detune = 0
    channels.append(channel)
px.channels.from_list(channels)

#まとめてミュージックで鳴らす場合
# px.musics[0].set([0],[1],[2],[3],[4],[5],[6],[7],[8])
# px.playm(0,loop=True)

#本当に多チャンネルでエラー起きず鳴らせてるかの確認
for ch,_ in enumerate(track):
    px.play(ch, ch, loop=True)

px.show()
