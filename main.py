import numpy as np
import utils
from models import SynthesizerTrn
import torch
from torch import no_grad, LongTensor
from text import text_to_sequence
import commons
import wave
import fastapi
import requests
import io
import alkana
import re
model_path = "./OUTPUT_MODEL/G_Amitaro.pth"
config_path = "./OUTPUT_MODEL/config.json"
length = 1.0
device='cpu'
def get_text(text, hps, is_symbol):
    text_norm = text_to_sequence(text, hps.symbols, [] if is_symbol else hps.data.text_cleaners)
    if hps.data.add_blank:
        text_norm = commons.intersperse(text_norm, 0)
    text_norm = LongTensor(text_norm)
    return text_norm

def to_kana(text):
    # extract [a-zA-Z]

    texts=[]
    cursor=0
    while cursor<len(text):
        if text[cursor] in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
            # extract
            end_of_word=re.search("[^a-zA-Z']",text[cursor:])
            assert end_of_word is not None and end_of_word.start()!=0
            if end_of_word is None:
                end_of_word=len(text)
            else:
                end_of_word=end_of_word.start()+cursor
            word=text[cursor:end_of_word]
            # convert
            kana=alkana.get_kana(word)
            if kana is None:
                kana=word
            texts.append(text[cursor:end_of_word])
            cursor=end_of_word
        else:
            texts.append(text[cursor])
            cursor+=1
    return "".join(texts)



def get_vits_array(text):
    hps = utils.get_hparams_from_file(config_path)
    net_g = SynthesizerTrn(
        len(hps.symbols),
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        n_speakers=hps.data.n_speakers,
        **hps.model).to(device)
    _ = net_g.eval()
    _ = utils.load_checkpoint(model_path, net_g, None)

    speaker_ids = hps.speakers

    # text = "[JA]" + text + "[JA]"
    speaker_id = 0
    stn_tst = get_text(text, hps, False)
    with no_grad():
        x_tst = stn_tst.unsqueeze(0).to(device)
        x_tst_lengths = LongTensor([stn_tst.size(0)]).to(device)
        sid = LongTensor([speaker_id]).to(device)
        audio = net_g.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=.667, noise_scale_w=0.6,
                            length_scale=1.0 / length)[0][0, 0].data.cpu().float().numpy()
    del stn_tst, x_tst, x_tst_lengths, sid

    return (hps.data.sampling_rate, audio)

app = fastapi.FastAPI()

redirect_to="http://localhost:50021/"
@app.post("/audio_query")
async def audio_query(req:fastapi.Request):
    speaker=int(req.query_params["speaker"])
    text=req.query_params["text"]
    if speaker<1000:
        # proxy
        remain_params = {}

        # to dict
        for k in req.query_params.keys():
            remain_params[k] = req.query_params[k]

        btext = to_kana(text)
        remain_params["text"]=btext
        # urldecode
        r=requests.post(redirect_to+"audio_query",params=remain_params)
        return r.json()

    else:
        return {"text":text,"speaker":speaker}
@app.post("/synthesis")
async def synthesis(req:fastapi.Request):
    body=await req.json()
    speaker = int(req.query_params["speaker"])
    if speaker<1000:
        # proxy
        remain_params = {}

        # to dict
        for k in req.query_params.keys():
            remain_params[k]=  req.query_params[k]

        r=requests.post(redirect_to+"synthesis",params=remain_params,json=body)
        # return as bytes
        return fastapi.Response(content=r.content,media_type="audio/wav")

    else:
        text=body["text"]
        text= to_kana(text)
        samplerate, audio = get_vits_array(text)
        b=io.BytesIO()
        # save
        with wave.open(b, mode="wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(samplerate)
            audio = audio * 32767
            # trim
            if len(audio)>2000:
                audio=audio[1000:-1000]
            f.writeframesraw(audio.astype(np.int16))
        return fastapi.Response(content=b.getvalue(),media_type="audio/wav")

# proxy get and post
@app.get("/{url}")
async def get(url:str):
    r=requests.get(redirect_to+url)
    return fastapi.Response(content=r.content)

@app.post("/{url}")
async def post(url:str):
    body=await fastapi.Request.json()
    r=requests.post(redirect_to+url,params=body)
    return fastapi.Response(content=r.content)

if __name__ == '__main__':
    samplerate,audio=get_vits_array("こんにちは")

    # save
    with wave.open("output.wav", mode="wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(samplerate)
        print(samplerate)
        audio=audio*32767
        f.writeframesraw(audio.astype(np.int16))
