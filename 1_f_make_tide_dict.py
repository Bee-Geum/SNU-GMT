# =================================================== #
#                                                     #
#               2024. 01. 05 금비가 수정함              #
#                                                     #
# =================================================== #


import numpy as np
import utils as ut
import h5py
import os
import datetime
import pickle


# Function to call: make tide label dictionary {date: (24hours, i, j ) 3d array} 
def make_day_grid_hour_label_dict(date, grid_name):
    dt          = date
    grid        = grid_name
    temp_pro_dt = datetime.datetime.strptime(dt, '%Y%m%d') + datetime.timedelta(days=1)
    pro_dt      = temp_pro_dt.strftime('%Y') + temp_pro_dt.strftime('%m') + temp_pro_dt.strftime('%d')

    # mat_51_list: each element is (51 x 51) points in 1 grid on 1 day
    mat_51_list = []

    file1 = h5py.File(f'{WATER_LEVEL_FOLDER}/{dt}/104KR00KR4_{grid}.h5', 'r')
    for group_idx in [i for i in '10,11,12,13,14,15,16,17,18,19,20,21,22,23,24'.split(',')]:
        # group010 is 0 o'clock of dt, group23 is 14 o'clock of dt
        mat_51 = file1.get(f'WaterLevel/WaterLevel.01/Group_0{group_idx}/values')[()]
        mat_51_list.append(mat_51)

    file2 = h5py.File(f'{WATER_LEVEL_FOLDER}/{pro_dt}/104KR00KR4_{grid}.h5', 'r')
    for group_idx in [i for i in '01,02,03,04,05,06,07,08,09'.split(',')]:
        # group001 is 15 o'clock of dt(a day before pro_dt), group009 is 23 o'clock of dt(a day before pro_dt)
        mat_51 = file2.get(f'WaterLevel/WaterLevel.01/Group_0{group_idx}/values')[()]
        mat_51_list.append(mat_51)

    mat_51_array           = np.array(mat_51_list)                # 3d array (24 x 51 x 51), each table index means o'clock of dt
    mat_2601_array         = np.reshape(mat_51_array, (24, 2601)) # 2d array (24 x 2601)   , each table index means o'clock of dt
    day_grid_hourly_avg_wl = np.nanmean(mat_2601_array, axis=1)   # 1d array (24,)         , each index means o'clock of dt

    # figure out high/mid/low tide hours with (24, ) 1d array

    # prev_diff : prev_diff[i] = arr[i-1] - arr[i], prev_diff[0] is 0
    prev_diff = np.insert(np.flip(np.diff(np.flip(day_grid_hourly_avg_wl))), 0 , 0)
    # pro_diff : pro_diff[i] = arr[i+1] - arr[i], prev_diff[23] is 0
    pro_diff  = np.insert(np.diff(day_grid_hourly_avg_wl), (len(day_grid_hourly_avg_wl)-1), 0)

    temp_low  = np.intersect1d(np.where(prev_diff > 0), np.where(pro_diff > 0))
    temp_high = np.intersect1d(np.where(prev_diff < 0), np.where(pro_diff < 0))

    low_hours  = []
    high_hours = []

    for i in temp_low:
        low_hours.append(i-1)
        low_hours.append(i)
        low_hours.append(i+1)

    for i in temp_high:
        high_hours.append(i-1)
        high_hours.append(i)
        high_hours.append(i+1)

    grid_hour_label_dict = {} # (24 x 1 x 1) of cube

    for hour in range(24):
        if hour in high_hours:
            grid_hour_label_dict[hour] =  1
        elif hour in low_hours:
            grid_hour_label_dict[hour] = -1
        else:
            grid_hour_label_dict[hour] =  0

    return grid_hour_label_dict


def make_tide_label(): 
    # 5. execute main to make tide label dictionary

    print('5. Making tide label dictionary ...')

    except_date_list = []

    for date in NONEXIST_DATE_FOLDER:
        temp_prev_dt = datetime.datetime.strptime(date, '%Y%m%d') - datetime.timedelta(days=1)
        prev_dt      = temp_prev_dt.strftime('%Y') + temp_prev_dt.strftime('%m') + temp_prev_dt.strftime('%d')

        except_date_list.append(prev_dt)

    # result is {date: (24hours, i, j ) 3d array} 
    result = {}

    for date in DAYLIST:
        if date in except_date_list: 
            continue
        # cube is 3d array. 
        # 24 layers means 24 hours, and an element in each (17 x 17) matrix is the tide label of a grid 
        cube = np.full((24,17,17), np.nan)

        for grid in GRID_NAME_LIST:
            grid_hour_label_dict = make_day_grid_hour_label_dict(date, grid)


            for hour in grid_hour_label_dict.keys():
                cube[hour, GRID_NAME_IDX_DICT[grid][0], GRID_NAME_IDX_DICT[grid][1]] = grid_hour_label_dict[hour]
        
        result[date] = cube

    # save result as pickle
    
    name = 'daily_tide_dict'
    with open(f"{name}.pickle", "wb") as file:
        pickle.dump(result, file, protocol=pickle.HIGHEST_PROTOCOL)

    if os.path.exists(f"{name}.pickle"): 
        print(f'{name} has been saved!')
    else: 
        print(f'{name} is NOT saved.')


def make_grid():
    # 4. make grid : index in (17 x 17 matrix) dictionary 

    gidx_north_dict = {}
    gidx_west_dict  = {}

    for grid_name in GRID_NAME_LIST:
        target_path = os.path.join(WATER_LEVEL_FOLDER, str(DAYLIST[0]), "104KR00KR4_" + grid_name + ".h5")

        file        = h5py.File(target_path, 'r')

        north_bound_lat = file.attrs['northBoundLatitude']
        west_bound_lon  = file.attrs['westBoundLongitude']

        gidx_north_dict[grid_name] = north_bound_lat
        gidx_west_dict[grid_name]  = west_bound_lon

    sorted_gidx_north_dict = {k: v for k, v in sorted(gidx_north_dict.items(), key=lambda item: item[1], reverse=True)}
    sorted_gidx_west_dict  = {k: v for k, v in sorted(gidx_west_dict.items(), key=lambda item: item[1])}

    grid_name_row_dict = {k: int((39.0-v)*2)  for k, v in sorted_gidx_north_dict.items()}
    grid_name_col_dict = {k: int((v-124.0)*2) for k, v in sorted_gidx_west_dict.items()}


    # 읽기만 할꺼라서 const 전역변수 설정
    global GRID_NAME_IDX_DICT

    # GRID_NAME_IDX_DICT is {grid_name: (i, j)}


    GRID_NAME_IDX_DICT = {}
    for name in grid_name_row_dict.keys():
        GRID_NAME_IDX_DICT[name] = [grid_name_row_dict[name], grid_name_col_dict[name]]

    if len(GRID_NAME_IDX_DICT) == 108:
        print("3. Make grid:index dictionary is done!")
    else:
        print("Error: the number of grids must be 108")


def make_grid_name_list():
    # list h5 filenames in one day folder under the 'water' folder

    file_list    = []
    target_path  = os.path.join(WATER_LEVEL_FOLDER, str(DAYLIST[0]))

    for path, _, files in os.walk(target_path):
        for file in files:
            if '.h5' in file:
                file_list.append(os.path.join(path, file))

    # 읽기만 할꺼라서 const 전역변수 선언
    global GRID_NAME_LIST

    GRID_NAME_LIST = []
    for file_name in file_list:
        grid_name = file_name.split('/')[-1][11:16]
        GRID_NAME_LIST.append(grid_name)

    if len(GRID_NAME_LIST) == 108:
        print("2. Make grid name list is done!")
    else:
        print("Error: the number of grids must be 108")


def make_day_list():
    # 읽기만 할꺼라서 const 전역변수 선언
    global DAYLIST

    DAYLIST  = []
    mon_list = list(MONTH_DAYS_DICT.keys())

    for month in mon_list:
        for day in range(1, MONTH_DAYS_DICT[month]+1):
            DAYLIST.append(f'{TARGET_YEAR}{month:02d}{day:02d}')

    for non_date in NONEXIST_DATE_FOLDER:
        DAYLIST.remove(non_date)

    if len(DAYLIST) != 0:
        print("1. Make day list is done!")
    else:
        print('No date in day list')


def config():
    datafd = ut.env['datafd']

    os.makedirs(f"{datafd}/water", exist_ok=True)

    # 읽기만 할꺼라서 const 전역변수 선언
    global WATER_LEVEL_FOLDER
    global TARGET_YEAR
    global MONTH_DAYS_DICT
    global NONEXIST_DATE_FOLDER

    WATER_LEVEL_FOLDER   = os.path.join(datafd, 'water')

    TARGET_YEAR          = '2022'
    MONTH_DAYS_DICT      = {6:30, 7:31, 8:31, 9:30, 10:31, 11:30}
    NONEXIST_DATE_FOLDER = ['20220719']


def main():
    config()
    make_day_list()
    make_grid_name_list()
    make_grid()
    make_tide_label()


if __name__ == "__main__":
    main()