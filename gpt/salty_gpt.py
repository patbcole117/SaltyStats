import os
import pickle
from contextlib import nullcontext
import torch
from gpt.model import GPTConfig, GPT

# -----------------------------------------------------------------------------
max_new_tokens = 1 # number of tokens generated in each sample
temperature = 0.8 # 1.0 = no change, < 1.0 = less random, > 1.0 = more random, in predictions
top_k = 2 # retain only the top_k most likely tokens, clamp others to have 0 probability
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

class SaltyGPT:
    def __init__(self, out_dir, num_samples=5000):
        self.num_samples = num_samples
        self.preds = []
        self.pred = 0
        self.confidence = 0.0
        self.out_dir = out_dir
        self.ready = False
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

    def predict(self, prompt):
        start_ids = self.encode(prompt)
        x = (torch.tensor(start_ids, dtype=torch.long, device=device)[None, ...])

        # run generation
        with torch.no_grad():
            with ctx:
                for k in range(self.num_samples):
                    y = self.model.generate(x, max_new_tokens, temperature=temperature, top_k=top_k)
                    self.preds.append(int((self.decode(y[0].tolist())[-1])))
                self.pred = max(set(self.preds), key=self.preds.count)
                self.confidence = float((self.preds.count(self.pred))) / float(len(self.preds))
                self.ready = True
        
    def flush(self):
        self.preds = []
        self.confidence = 0.0
        self.ready = False
    