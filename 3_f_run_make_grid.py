# time python3 3_f_run_make_grid.py
# takes about 1.5 hours with 120 cores


# =================================================== #
#                                                     #
#               2024. 01. 08 금비가 수정함              #
#                                                     #
# =================================================== #


import subprocess
import multiprocessing
import os
import utils as ut


def run(cmd):
    subprocess.run(cmd, shell=True)


def main():
    commands = []

    for net in "ais ltem vpass".split():
        file = f"3_f_make_grid_{net}.sh"

        if os.path.exists(file):
            commands += [line.strip() for line in open(f'3_f_make_grid_{net}.sh').readlines()]

    p = multiprocessing.Pool(processes=int(ut.env['cores']))
    p.map(run, commands)


if __name__ == "__main__":
    main()