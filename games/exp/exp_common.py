import os
from datetime import datetime


def setup_dir(game_name):
    dt = datetime.today()
    dt = str(dt).split(' ')[0]
    res_dir = '../../results/stats/' + game_name  +'/'+  dt.replace(":", "_").replace(" ", "_") + '/'
    if not os.path.exists(res_dir):
        os.mkdir(res_dir)
    return res_dir
