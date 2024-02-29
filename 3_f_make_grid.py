# sleep 0 && ./3_make_grid_ais.sh
# sleep 1800 && ./3_make_grid_ltem.sh
# sleep 3000 && ./3_make_grid_vpass.sh


# =================================================== #
#                                                     #
#               2024. 01. 10 금비가 수정함              #
#                                                     #
# =================================================== #


import os
import csv
import sys
import pickle
import zipfile
import codecs
import numpy as np
import utils as ut
from scipy import sparse


def proc(args):
    i, zip_file_name, file = args

    zip_file = zipfile.ZipFile(f"{DATAFD}/{zip_file_name}", 'r')
    cursor   = csv.reader(codecs.iterdecode(zip_file.open(file), "UTF-8"))
    
    if len(file.split("_")) == 5:
        head = next(cursor)

    LA, LO, SOG, RECPTN_DT, SHIP_ID = [HCOL[file][v] for v in 'LA LO SOG RECPTN_DT SHIP_ID'.split()]
    total, counted = 0, 0

    matdict = {}

    for v in ut.matlist:
        matdict[v] = sparse.lil_matrix((H*M, W*M), dtype=np.float32)
    
    for j, line in enumerate(cursor):
        if j % 1000000 == 0:
            print(f"FILE {i}: {file} -- ROW {j}")
        total += 1

        try:
            lat, lon, sog      = [float(line[v]) for v in [LA, LO, SOG]]
            recptn_dt, ship_id = line[RECPTN_DT], line[SHIP_ID]
            thisd              = recptn_dt.split()[0].replace('-', '')
            thish              = int(recptn_dt.split()[1].split(':')[0])
        except:
            print("######", [i, file, j, line])
            continue
        
        if (not (BD['minlat'] < lat < BD['maxlat'])) \
            or (not (BD['minlon']< lon < BD['maxlon'])) \
            or sog < BD['minsog'] or sog > BD['maxsog']: 
            continue
        
        counted += 1

        rc = ut.ll2idx(lat, lon)
        matdict['CMAT'][rc] += 1
        matdict['SMAT'][rc] += sog

        tiderc = ut.ll2tiderc(lat, lon)

        if ship_id in TTD:
            thistype = 'NB' if TTD[ship_id][0][0]!='B' else 'B'
            this_ton = ut.proc_ton(float(TTD[ship_id][1]), thistype)
        else:
            thistype, this_ton = None, None
        
        if not (0 <= tiderc[0] < 17 and \
                0 <= tiderc[1] < 17):
            thistide = list('LMH')
        else:
            if thisd not in DTD:
                thistide = list('LMH')
            else:
                rawt = DTD[thisd][thish][tiderc]

                if np.isnan(rawt): 
                    thistide = list('LMH')
                else:
                    if int(rawt) == 1: 
                        thistide = ['H']
                    elif int(rawt) == 0: 
                        thistide = ['M']
                    elif int(rawt) == -1: 
                        thistide = ['L']
                    else: 
                        raise ValueError('Tide should be -1, 0, or +1.')

        for t in thistide:
            matdict[f'CMAT_{t}'][rc] += 1
            matdict[f'SMAT_{t}'][rc] += sog
        if (thistype != None) and (this_ton != None):
            matdict[f'CMAT_{t}_{thistype}_{this_ton}'][rc] += 1
            matdict[f'SMAT_{t}_{thistype}_{this_ton}'][rc] += sog          
            
    return (total, counted, matdict)


def main():
    global M
    global W
    global H
    global DATAFD
    global BD
    global HCOL
    global TTD
    global DTD

    net      = sys.argv[1]
    zip_file = sys.argv[2]
    file     = sys.argv[3]
    fstub    = file.replace(".csv", '').split('/')[-1]

    M      = int(ut.env['gridsize'])     # 2000
    DATAFD = ut.env['datafd']            # 데이터 경로
    tempfd = "/data/GMT/geum_tempgrid"   # 이건 내 공간으로 임시 설정함
    BD     = {k: int(ut.env[k]) for k in 'minlat maxlat minlon maxlon minsog maxsog'.split()}
    W      = BD['maxlon'] - BD['minlon'] # 8
    H      = BD['maxlat'] - BD['minlat'] # 8

    # daily_tide_dict.pickle로 수정
    with open(f"daily_tide_dict.pickle", 'rb') as file1, \
        open(f"header_{net}.pickle", 'rb') as file2, \
        open(f"typeton_{net}.pickle", 'rb') as file3:

        DTD  = pickle.load(file1)
        HCOL = pickle.load(file2)
        TTD  = pickle.load(file3)
    
    lines = open(f"3_f_make_grid_{net}.sh").readlines()

    for i, line in enumerate(lines):
        if f"{net} {zip_file} {file}" in line:
            break

    out = proc((i, zip_file, file))

    os.makedirs(F"{tempfd}/{net}", exist_ok=True)
    csv.writer(open(f"{tempfd}/{net}/{file}", 'w')).writerow([out[:2]])

    print(f'FILE {i}: saving matrix for {net} {zip_file} {file}...')

    for v in ut.matlist:
        sparse.save_npz(f"{tempfd}/{net}/{fstub}_{v}.npz", out[2][v].tocsr())


if __name__ == "__main__":
    main()