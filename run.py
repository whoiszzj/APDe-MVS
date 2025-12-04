import os
import multiprocessing as mp
import argparse
import glob
from tools.run_SAM import SAMRunner

#####################################################################################################
# args:
parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', type=str, default='/home/ubuntu/Data/DTU/test')
parser.add_argument('--APD_path', type=str, default='./build/APD')
parser.add_argument('--resume', action='store_true', default=False)
parser.add_argument('--gpu_num', type=int, default=1)
parser.add_argument('--work_num', type=int, default=1)
parser.add_argument('--scans', type=str, nargs='+', default=[])
parser.add_argument('--reservation', type=str, default=None, help='reservation for the server, e.g. 3h30m10s')
parser.add_argument('--only_fuse', action='store_true', default=False)
parser.add_argument('--no_fuse', action='store_true', default=False)
parser.add_argument('--memory_cache', action='store_true', default=False)
parser.add_argument('--no_sam', action='store_true', default=False)
parser.add_argument('--no_impetus', action='store_true', default=False)
parser.add_argument('--no_weak_filter', action='store_true', default=False)
parser.add_argument('--no_color', action='store_true', default=False)
parser.add_argument('--flush', action='store_true', default=False)
parser.add_argument('--dry_run', action='store_true', default=False)
parser.add_argument('--backup_code', action='store_true', default=False)
parser.add_argument('--ETH3D_train', action='store_true', default=False)
parser.add_argument('--ETH3D_test', action='store_true', default=False)
parser.add_argument('--TaT_intermediate', action='store_true', default=False)
parser.add_argument('--TaT_advanced', action='store_true', default=False)
parser.add_argument('--export_anchor', action='store_true', default=False)
parser.add_argument('--export_curve', action='store_true', default=False)
args = parser.parse_args()
#####################################################################################################


def init(pp, ll):
    global positions, lock
    positions = pp
    lock = ll


def worker(scan):
    scan_dir = os.path.join(args.data_dir, scan)
    if not os.path.isdir(scan_dir):
        print('{} is not a dir'.format(scan_dir))
        return

    ########################################################
    # acquire a position
    pos_index = 0
    lock.acquire()
    for j in range(len(positions)):
        if positions[j] == 0:
            positions[j] = 1
            pos_index = j
            break
    lock.release()
    ########################################################
    gpu_index = pos_index // args.work_num
    dataset = 'General'
    if args.data_dir.find('DTU') != -1:
        dataset = 'DTU'
    elif args.data_dir.find('TaT') != -1:
        if scan in ['Auditorium', 'Ballroom', 'Courtroom', 'Museum', 'Palace', 'Temple']:
            dataset = 'TaT_a'
        else:
            dataset = 'TaT_i'
    elif args.data_dir.find('ETH3D') != -1:
        dataset = 'ETH3D'

    if not args.no_sam:
        mask_folder = os.path.join(scan_dir, 'sa_masks')
        if not os.path.exists(mask_folder):
            sam_runner = SAMRunner(args.data_dir, [scan], max_size=2560)
            sam_runner.run()

    APD_path = os.path.join(scan_dir, 'APD')
    if not os.path.exists(APD_path):
        os.makedirs(APD_path)

    call_APD_cmd = \
         '{} --dense_folder {} --gpu_index {} --dataset {} ' \
         '--only_fuse {} --no_fuse {}  --use_sa {} --memory_cache {} --flush {} ' \
         '--export_anchor {} --export_curve {} --export_color {} --use_impetus {} --weak_filter {}'.format(
            args.APD_path, scan_dir, gpu_index, dataset,
            'true' if args.only_fuse else 'false',
            'true' if args.no_fuse else 'false',
            'false' if args.no_sam else 'true',
            'true' if args.memory_cache else 'false',
            'true' if args.flush else 'false',
            'true' if args.export_anchor else 'false',
            'true' if args.export_curve else 'false',
            "false" if args.no_color else "true",
            "false" if args.no_impetus else "true",
            "false" if args.no_weak_filter else "true"
        )

    log_path = os.path.join(APD_path, 'log.txt')
    if os.path.exists(log_path):
        call_APD_cmd += ' >> ' + log_path
    else:
        call_APD_cmd += ' > ' + log_path

    if args.resume:
        APD_ply_path = os.path.join(scan_dir, 'APD', 'APD.ply')
        if not os.path.exists(APD_ply_path):
            print(call_APD_cmd)
            if not args.dry_run:
                os.system(call_APD_cmd)
        else:
            print('APD result exists for {}'.format(scan_dir))
    else:
        print(call_APD_cmd)
        if not args.dry_run:
            os.system(call_APD_cmd)
    if  args.backup_code:
        # get current path
        current_path = os.path.dirname(os.path.abspath(__file__))
        code_list = glob.glob(os.path.join(current_path, '*.cpp'))
        code_list += glob.glob(os.path.join(current_path, '*.cu'))
        code_list += glob.glob(os.path.join(current_path, '*.cuh'))
        code_list += glob.glob(os.path.join(current_path, '*.h'))
        code_list += glob.glob(os.path.join(current_path, '*.sh'))
        ver_id = os.popen('git rev-parse --short HEAD').read().strip()
        dst_path = os.path.join(APD_path, 'code_{}'.format(ver_id))
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
        for code_path in code_list:
            os.system('cp {} {}'.format(code_path, dst_path))
        print('backup code to {}'.format(dst_path))

    # sleep_time = random.randint(8, 12)
    # time.sleep(sleep_time)
    ########################################################
    # release the position
    lock.acquire()
    positions[pos_index] = 0
    lock.release()
    ########################################################


if __name__ == "__main__":
    print(args)
    if args.reservation is not None:
        # sleep for reservation
        print('sleep for reservation: {}'.format(args.reservation))
        os.system('sleep {}'.format(args.reservation))
        print('sleep done')

    if args.ETH3D_train:
        scans = ['courtyard', 'delivery_area', 'electro', 'facade', 'kicker', 'meadow', 'office', 'pipes', 'playground', 'relief', 'relief_2', 'terrace', 'terrains']
    elif args.ETH3D_test:
        scans = ['botanical_garden', 'boulders', 'bridge', 'door', 'exhibition_hall', 'lecture_room', 'living_room', 'lounge', 'observatory', 'old_computer', 'statue', 'terrace_2']
    elif args.TaT_intermediate:
        scans = ['Family', 'Francis', 'Horse', 'Lighthouse', 'M60', 'Panther', 'Playground']
    elif args.TaT_advanced:
        scans = ['Auditorium', 'Ballroom', 'Courtroom', 'Museum', 'Palace', 'Temple']
    else:
        if args.scans:
            scans = args.scans
        else:
            scans = os.listdir(args.data_dir)
            scans.sort()

    scans = [{'scan': scan, 'img': 0} for scan in scans]
    for scan in scans:
        scan_dir = os.path.join(args.data_dir, scan['scan'])
        if not os.path.isdir(scan_dir):
            print('{} is not a dir'.format(scan_dir))
            continue
        scan['img'] = len(os.listdir(os.path.join(scan_dir, 'images')))
    # sort by img number
    scans.sort(key=lambda x: -x['img'])
    scans = [scan['scan'] for scan in scans]
    print('scans: {}'.format(scans))
    print('scans size: {}'.format(len(scans)))
    total_work_num = min(args.work_num * args.gpu_num, len(scans))
    print('total_work_num: {}'.format(total_work_num))
    positions = mp.Array('i', [0] * total_work_num)
    lock = mp.Lock()
    pool = mp.Pool(processes=total_work_num, initializer=init, initargs=(positions, lock))
    for scan in scans:
        pool.apply_async(worker, args=(scan,))
    pool.close()
    pool.join()
    print('done')
