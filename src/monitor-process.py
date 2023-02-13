import subprocess
import shlex
import re
import argparse
import time

cgroup_path = ''
postmaster_pids = []
username = ''
dbname = ''

saved = {}

def run_command(command, hook=None):
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    count = 0

    while True:
        output = process.stdout.readline()
        if not output and process.poll() is not None:
            break

        if output:
            if hook:
                hook(output, count)
            count = count + 1

def parse_forkstat(line, line_num):
    if line_num == 1:
        return
    r = re.match(r" *(?P<pid>\d{1,}) postgres: *\d+, %s %s .*" % (username, dbname), str(line, encoding='utf8').strip())
    if r:
        pid = r['pid']

        if pid in saved.keys():
            return

        with open(cgroup_path, "w") as f:
            f.write(str(pid) + '\n')
            saved[pid] = True
            print(str(pid) + " write to " + cgroup_path)

def parse_postmaster(line, line_numer):
    if line_numer == 1:
        return
    r = re.match(r" *(?P<pid>\d+) /.* -D /.* -p", str(line, encoding="utf8").strip())
    if r:
        postmaster_pids.append(r['pid'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Provide username and db name')
    parser.add_argument('username', type=str,
                    help='user of db')
    parser.add_argument('dbname', type=str,
                    help='db name')

    parser.add_argument('cgpath', type=str,
                    help='cgroup path')
    args = parser.parse_args()

    cgroup_path = args.cgpath + "/cgroup.procs"
    username = args.username
    dbname = args.dbname

    run_command(f"ps -u {args.username} -o pid,command", parse_postmaster)
    print(postmaster_pids)

    while True:
        run_command(f"ps -o pid,command --ppid {','.join(postmaster_pids)}", parse_forkstat)
        time.sleep(1)

