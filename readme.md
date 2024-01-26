# altvoicevox
[Lycoris53/Vits-TTS-Japanese-Only-Amitaro](https://huggingface.co/Lycoris53/Vits-TTS-Japanese-Only-Amitaro)をVoicevoxの代わりに使用するためのプログラムです。  
VoicevoxスピーカIDを1000番以降にすると使用できます。1000番未満の場合はhttp://localhost:50021/ にリダイレクトします。
リダイレクト機能は[LMMChat](https://github.com/ebisuke/LMMChat)ように設計していますので、それ以外の用途での保証は致しません。
# 使い方
- 本プロジェクトをクローンします。
```
git clone https://github.com/ebisuke/altvoicevox.git
cd altvoicevox
```
- モデルをクローンします。
```
git lfs install
git clone https://huggingface.co/Lycoris53/Vits-TTS-Japanese-Only-Amitaro OUTPUT_MODEL
```
- `pip install -r requirements.txt`で必要なライブラリをインストールします。
- monotonic_alignをインストールします。
```
cd monotonic_align
pip install -e .
cd ..
```
- `uvicorn --host 0.0.0.0 --port 18021 main:app`などで起動します。ポート番号はローカルのVoicevoxと被らないようにしてください。
- LMMChatで使用する場合は、`voicevoxbaseurl`を修正してください。

# 使用ライブラリ
- [Lycoris53/Vits-TTS-Japanese-Only-Amitaro](https://huggingface.co/Lycoris53/Vits-TTS-Japanese-Only-Amitaro)
- [(Spaces) Lycoris53/VITS-TTS-Japanese-Only-Amitaro](https://huggingface.co/spaces/Lycoris53/VITS-TTS-Japanese-Only-Amitaro/tree/main)