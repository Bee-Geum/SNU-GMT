# run examples
# python3 2_f_list_files.py ais AIS0601-0630.zip AIS0701-0730.zip AIS0801-0830.zip AIS0901-0930.zip AIS1001-1030.zip AIS1101-1118.zip AIS1119-1130.zip
# python3 2_f_list_files.py ltem LTEM1101-1118.zip LTEM1119-1130.zip
# python3 2_f_list_files.py vpass VPASS0701-1231.zip


# =================================================== #
#                                                     #
#               2024. 01. 10 금비가 수정함              #
#                                                     #
# =================================================== #


import utils as ut
import sys, os, zipfile, pickle, csv, codecs


def process():
    hcol = {}
    h    = {}
    # cnt  = 0
    
    with open(f"3_f_make_grid_{NET}.sh", 'w') as sh_file:
        for zip_file_name in sorted(ZIP_FILE_NAMES):
            zip_file = zipfile.ZipFile(f"{DATAFD}/{zip_file_name}", 'r')
            files    = sorted([file for file in zip_file.namelist() if file.endswith('.csv')])

            for file in files:
                # cnt += 1

                # 여기 python 파일 이름 바꿈
                sh_file.write(f"time python3 3_f_make_grid.py {NET} {zip_file_name} {file}\n")

                if len(file.split('_')) == 5:
                    cur  = csv.reader(codecs.iterdecode(zip_file.open(files[0]), "UTF-8"))
                    head = next(cur)

                    LA, LO, SOG, RECPTN_DT, SHIP_ID = [head.index(v) for v in HSTUBS]

                    h          = dict(LA=LA, LO=LO, SOG=SOG, RECPTN_DT=RECPTN_DT, SHIP_ID=SHIP_ID)
                    hcol[file] = h
                elif len(file.split('_')) == 6:
                    if len(h) == 0:
                        raise ValueError(f"Header row is not found for {file} in {zip_file_name}.")
                    hcol[file] = h
                else:
                    raise ValueError("Filenames should contain only 4 or 5 '_' characters.")
    
    
    os.chmod(f'3_f_make_grid_{NET}.sh', 0o755)

    with open(f'header_{NET}.pickle', 'wb') as pfile:
        pickle.dump(hcol, pfile)



def get_info():
    # 읽기 전용은 const 전역변수로 설정
    global DATAFD
    global NET
    global ZIP_FILE_NAMES
    global HSTUBS

    DATAFD   = ut.env['datafd']
    gridtime = int(ut.env['gridtime'])
    cores    = int(ut.env['cores'])
    args     = sys.argv[1:]
    NET      = args[0]

    ZIP_FILE_NAMES = args[1:]

    print(f'CPU cores identified: {ut.cpus}')
    print(f'{cores} CPU cores are requested.')
    print(f'Processing the following files: {ZIP_FILE_NAMES}')
    
    if NET == 'ais': 
        HSTUBS = 'LA LO SOG RECPTN_DT MMSI'.split()
    elif NET == 'ltem': 
        HSTUBS = 'LA LO SOG RECPTN_DT SHIP_MRN'.split()
    elif NET == 'vpass':
        HSTUBS = 'LA LO SOG RECPTN_DT VPASS_RFID'.split()
    else: 
        raise ValueError('Only ais, ltem, vpass networks are supported.')


def main():
    get_info()
    process()


if __name__ == "__main__":
    main()