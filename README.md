# SaltyStats - A Salty Bet analysis and automation toolset.

SaltyStats is the third iteration of my Salty Bet analysis program. Major changes have been made this iteration including swapping out SQL for MongoDB, adding verbose logging and error handling, simplified architecture, and some HUGE new features like automaticly recording matches via Streamlink, and a Prediction Module which uses GPTs trained on a large dataset to predict match outcomes.

# What is Salty Bet?
Salty Bet is akin to a virtual version of The Ultimate Fighting Championship. At www.SaltyBet.com is a live stream of virtual, AI-controlled, fan-made characters duking it out 24/7. Thousands of spectators tune in daily to watch fights and bet fake-money, known as " salt " , on their  favorite characters. There are thousands of characters ( I have gathered stats on over 10k so far! ). 

If you’re familiar with fighting games like Mortal Kombat, Street Fighter, or Tekken, Salty Bet will look quite familiar.  Salty Bet is built on the 2D fighting game engine Mugen. Released in 1999 by Elecbyte, Mugen gained notoriety by allowing players to create and import their own fighters. At some point Salty Bet's creator, Salty, saw the potential in Mugen’s community and created the website Salty Bet where the Mugen community could compare each other’s custom fighters in front of a live audience and definitively prove who is the best fighter.




# Installation

**You will need to edit app.py and remove all predictors except elo. GPTs must be trained and added yourself.** 
CHANGE THIS: 
```
pmodels = [pf.create_predictor('Elo', 'Elo'), pf.create_predictor('Gpt', '20240223_salty_gpt_full'), pf.create_predictor('Gpt', '20240223_salty_gpt_names'), pf.create_predictor('Gpt', '20240223_salty_gpt_noelo')]
```
TO THIS:
```
pmodels = [pf.create_predictor('Elo', 'Elo')]
```
### Automatic Installation ( with some tweaking )
```bash
git clone https://github.com/patbcole117/SaltyStats
```
Inside the utils folder is a bash script **UpdateSaltyStats.sh** this can be edited and used to quickly setup the environment. It may need minor tweaking depending on your system and whether you opt to train your own GPTs for predictions.

### Manual Installation ( no CUDA version )
```
git clone https://github.com/patbcole117/SaltyStats
python3 -m venv SaltyStats/.venv
SaltyStats/.venv/bin/pip install torch torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
SaltyStats/.venv/bin/pip install -r requirements.txt
cp SaltyStats/utils/conf.example SaltyStats/saltystat.conf

** Now you need to edit the config ( SaltyStats/saltystat.conf ) **
vi SaltyStats/saltystat.conf
```
The only information which needs to be added to the config is MongoDB information under the [DATABASE] section. MONGO_URL is only the unique part of your mongo url connection string. It does NOT include the prefix protocol information or the suffix static url information. See below for an example.

If you wish to use a local MongoDB server simply chance LOCALE to LOCAL. The MONGO_URL should be the entire connection string in this case. For example : mongodb://localhost:27017/

```

EXAMPLE IMAGE HERE.


```

### GPTs and other Predictiors

By default the only prediction method is an Elo Ranking picker. It is NOT a GPT and simply predicts the winner based on Elo rankings. Obviously this will not work very well if you do nto have a lot of matches ( 500,000+ ) since Elo takes time to become valuable. However SaltyStats supports a framework for adding your own GPTs.

You should have some understanding on how GPTs work before attempting to configure them. I reccomend watching some of the content on https://www.youtube.com/@AndrejKarpathy/videos before proceding. 

GitHub file limits do not permit me to upload my trained GPTs. You will have to train your own. I configured CUDA and used a fork of https://github.com/karpathy/nanoGPT to create a training program. You will have to create your own aswell if you plan to use GPTs.

**The GPT must only output a 1 or 2 depending on if RED or BLUE wins the match. If your GPT emits an answer that is not 1 or 2  it will fail. If you do not know how to tailor the output of your GPT go do some research.**

```
1. Learn how https://github.com/karpathy/nanoGPT works.

2. Feed nanoGPT some data from SaltyStats ( this can be formatted however you wish ) to train a model. This will be output as a ckpt.pt and meta.pkl file.

3. Create a folder in the SaltyStats/gpt directory and place both files ( ckpt.pt and meta.pkl ) into the folder.

4. Edit app.py, there is a list variable named pmodels. Instantiate your new GPT in the list like so: 
    pf.create_predictor('Gpt', 'FOLDER_NAME_OF_YOUR_GPT')
```
SaltyStats will now use your model every match to predict the outcome.

You can train models many different ways and run them simultaneously. I am presently using 4 models, 3 GPTs and one which simply picked based on elo.

## Features

* Elo Ranking system for " dumb " predictions.

* GPT support using nanoGPT ( https://github.com/karpathy/nanoGPT )

* Record live matches in individual mp4 files using Streamlink and FFMPEG.

* Uses MongoDB ( Use MongoDB Atlas for EASY graphs and charts and free storage. )

## Future Features
* Favorate Fighter Alerts.

