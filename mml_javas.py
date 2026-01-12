import pyxel as px

class App():
    def __init__(self):
        px.init(128,128,title=__file__.split("\\")[-1])
        self.JPFONT = px.Font("umplus_j10r.bdf")
        ch_max = 8
        track_length = 8

        track:list[list[str]] = [["" for _ in range(track_length)] for _ in range(ch_max)]

        channels:list[px.Channel] = []
        for _ in range(ch_max):
            channel = px.Channel()
            channel.gain = 0.5/8
            channel.detune = 0
            channels.append(channel)
        px.channels.from_list(channels)

        ext_tone = px.Tone()
        EXT_TONE_ENV = (  # Saw Wave
                0, 4,
                [15, 15, 14, 14, 13, 13, 12, 12, 11, 11, 10, 10, 9, 9, 8, 8]
                + [7, 7, 6, 6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 0, 0],
                1.0,
            )
        ext_tone.mode = EXT_TONE_ENV[0]
        ext_tone.sample_bits = EXT_TONE_ENV[1]
        ext_tone.wavetable.from_list(EXT_TONE_ENV[2])
        ext_tone.gain = EXT_TONE_ENV[3]
        # px.tones[0] = ext_tone

        '''
        '''


        #index0は定義データ
        track[0][0]="T76 V98 Q99 @1 O5 L16"
        track[1][0]="T76 V66 Q93 @1 O4 L16"
        track[2][0]="T76 V85 Q99 @0 O3 L8"
        track[3][0]="T76 V19 Q99 @1 O5 L16 Y3"
        track[4][0]=""
        track[5][0]=""
        track[6][0]=""
        track[7][0]=""

        #index1以降は楽譜
        track[0][1]="e8defedc&c8r8 <b8Q90a8Q99a8g#ab8ab>c8<b>cd8cd"
        track[0][2]="e8degedc&c8r8. defa8r<aa8 r4.r ab>cd8r4cd"
        track[0][3]="e8defedc&c8r8 <b8a8a8g#ab8ab>c8<b>cd8cd"
        track[0][4]="e8degedc&c8r8. defa8r<aa8 r4.r ab>cc8r4. <b8>r8. dc<b>c2<b2>c4r8cd"

        track[1][1]="cg>ec< <b>gd<b> <a>ec<a> <g8f8> dfa>c< egb>d< fa>cf< gb>dg<"
        track[1][2]="cg>ec< <b>gd<b> <a>ec<a> <a>ec<a> [<f>caf]4 [<b>g>d<b]2"
        track[1][3]="cg>ec< <b>gd<b> <a>ec<a> <g8f8> dfa>c< egb>d< fa>cf< gb>dg<"
        track[1][4]="cg>ec< <b>gd<b> <a>ec<a> <a>ec<a> [<f>caf]4 [<b>g>d<b]2"
        track[1][5]="[<b>g>d<b]2 [<f>caf]2 [<b>g>d<b]2 [cg>ec<]2"

        track[2][1]=">c<rbr16a16&aref >drerfrgr"
        track[2][2]=" c<rbr16a16&ar4. [f16r16]8 [g16r16]4"
        track[2][3]=">c<rbr16a16&aref >drerfrgr"
        track[2][4]=" c<rbr16a16&ar4. [f16r16]8 [g16r16]4"
        track[2][5]="[g16r16]4 [f16r16]4 [g16r16]4 >[c16r16]3 r"

        track[3][1]="r96e8defedc&c8r8 <b8Q90a8Q99a8g#ab8ab>c8<b>cd8cd"
        track[3][2]="e8degedc&c8r8. defa8r<aa8 r4.r ab>cd8r4cd"
        track[3][3]="e8defedc&c8r8 <b8a8a8g#ab8ab>c8<b>cd8cd"
        track[3][4]="e8degedc&c8r8. defa8r<aa8 r4.r ab>cc8r4. <b8>r8. dc<b>c2<b2>c4r8cd"

        #トラック（＝チャンネル）データをMMLとして登録（1TR=1Ch：1sound)
        for i,tdata in enumerate(track):
            if tdata[0]:
                mmltext = ""
                for data in tdata:
                    mmltext += data
                px.sounds[i].mml(mmltext)



        #定義データの再生
        self.flg_loop = True

        # まとめてミュージックで鳴らす場合
        px.musics[0].set([0],[1],[2],[3],[4],[5],[6],[7])
        # px.playm(0,loop=True)

        # #本当に多チャンネルでエラー起きず鳴らせてるかの確認
        # for ch,_ in enumerate(track):
        #     px.play(ch, ch, loop=True)

        #Pyxel実行
        # px.show()
        px.run(self.update, self.draw)

    def update(self):
        if px.btnp(px.KEY_SPACE):
            px.playm(0,loop=self.flg_loop)
    
    def draw(self):
        px.cls(0)
        soundtitle="古代伝説"
        px.text(px.width//2-self.JPFONT.text_width(soundtitle)//2,px.height//2-4,
                soundtitle,px.frame_count%16,self.JPFONT)
App()
