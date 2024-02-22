from abc import ABC, abstractmethod 
import os
import pickle
from contextlib import nullcontext
import torch
from gpt.model import GPTConfig, GPT

# -----------------------------------------------------------------------------
seed = 1337
device = 'cpu' # examples: 'cpu', 'cuda', 'cuda:0', 'cuda:1', etc.
dtype = 'bfloat16' if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else 'float16' # 'float32' or 'bfloat16' or 'float16'
# -----------------------------------------------------------------------------

torch.manual_seed(seed)
torch.cuda.manual_seed(seed)
torch.backends.cuda.matmul.allow_tf32 = True # allow tf32 on matmul
torch.backends.cudnn.allow_tf32 = True # allow tf32 on cudnn
device_type = 'cuda' if 'cuda' in device else 'cpu' # for later use in torch.autocast
ptdtype = {'float32': torch.float32, 'bfloat16': torch.bfloat16, 'float16': torch.float16}[dtype]
ctx = nullcontext() if device_type == 'cpu' else torch.amp.autocast(device_type=device_type, dtype=ptdtype)

class Predictor(ABC):
    def __init__(self, param):
        self.preds = []
        self.pred = 0
        self.confidence = 0.0
        self.ready = False
        self.name = param

    @abstractmethod
    def predict(prediction_data):
        pass

    def flush(self):
        self.preds = []
        self.pred = 0
        self.confidence = 0.0
        self.ready = False

class Gpt(Predictor):
    def __init__(self, param):
        super().__init__(param)

        self.num_samples=5000
        self.temperature = 0.8
        self.max_new_tokens = 1
        self.top_k = 2
        self.out_dir = self.name

        ckpt_path = os.path.join('gpt', self.out_dir, 'ckpt.pt')
        checkpoint = torch.load(ckpt_path, map_location=device)
        gptconf = GPTConfig(**checkpoint['model_args'])
        self.model = GPT(gptconf)

        state_dict = checkpoint['model']
        unwanted_prefix = '_orig_mod.'
        for k,v in list(state_dict.items()):
            if k.startswith(unwanted_prefix):
                state_dict[k[len(unwanted_prefix):]] = state_dict.pop(k)
        self.model.load_state_dict(state_dict)
        self.model.eval()
        self.model.to(device)

        # look for the meta pickle in case it is available in the dataset folder
        load_meta = False
        meta_path = os.path.join('gpt', self.out_dir, 'meta.pkl')
        load_meta = os.path.exists(meta_path)
        if load_meta:
            with open(meta_path, 'rb') as f:
                meta = pickle.load(f)
            stoi, itos = meta['stoi'], meta['itos']
            self.encode = lambda s: [stoi[c] for c in s]
            self.decode = lambda l: ''.join([itos[i] for i in l])
        
    def predict(self, prediction_data):
        csv = f'{prediction_data["p1name"]}'
        for k, v in prediction_data.items():
            if k != "p1name":
                csv += f',{v}'
            #print(csv)
        csv+=','

        start_ids = self.encode(csv)
        x = (torch.tensor(start_ids, dtype=torch.long, device=device)[None, ...])
        with torch.no_grad():
            with ctx:
                for k in range(self.num_samples):
                    y = self.model.generate(x, self.max_new_tokens, temperature=self.temperature, top_k=self.top_k)
                    self.preds.append(int((self.decode(y[0].tolist())[-1])))
                self.pred = max(set(self.preds), key=self.preds.count)
                self.confidence = float((self.preds.count(self.pred))) / float(len(self.preds)) * 100
                self.ready = True

class Elo(Predictor):
    def __init__(self, param):
        super().__init__(param)
    
    def predict(self, prediction_data):
        self.confidence = 100.00
        if prediction_data["p1elo"] > prediction_data["p2elo"]:
            self.pred = 1
        elif prediction_data["p1elo"] < prediction_data["p2elo"]:
            self.pred = 2
        else:
            self.pred = 1
            self.confidence = 50.00
        self.ready = True

class PredictorFactory():
    def create_predictor(self, ptype: str, param: str) -> Predictor:
        obj = ptype.capitalize()
        return globals()[ptype](param)
