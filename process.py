#!/usr/bin/env python

import datetime
import errno
import filecmp
import os
import os.path
import shutil
import subprocess
import tempfile
import zipfile
import pytz
from contextlib import contextmanager

OUT_DIR = "./extracted-repo"
DEMO_GAME_DIR = "DemoQuest"
TZ = pytz.timezone('Europe/London')

VERSION_MAP = {
    "AGS-3.2.0": "3.2.0",
    "AGS-3.1.2-SP1": "3.1.2-SP1",
    "AGS-3.1.2": "3.1.2",
    "AGS-3.1.1-Final": "3.1.1",
    "AGS-3.1.1": "3.1.1-pre",
    "AGS-3.1.0": "3.1.0",
    "AGS-3.0.2": "3.0.2",
    "AGS-3.0.0": "3.0.0",
    "demo2turn11": "2.4.0",
    "ags_23": "2.3.0",
    "ags_22": "2.2.0",
    "ags_214_sr5": "2.1.4-SR5",
    "ags_210": "2.1.0",
    "ags_207": "2.0.7",
    "ags_204": "2.0.4",
    "ags_203": "2.0.3",
    "ags_202": "2.0.2",
    "ags_201": "2.0.1",
    "ags_200x": "2.0.0",
    "ac_114": "1.1.4",
    "ac_113": "1.1.3",
    "ac_112": "1.1.2",
    "ac_11": "1.1.0",
    "ac_100": "1.0.0",
}


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def is_demo(path):
    path = path.lower()

    _,fname = os.path.split(path)
    if fname in ['acwin.exe', 'all3927.dll', 'seer.dll', 'demo.bat', 'agssave.999']:
        return False

    if 'demo game/' in path or 'demo/' in path:
        return True
    if 'demo' in path:
        return True

    ext = os.path.splitext(path)[1]
    return ext in ['.crm', '.prg', '.dat', '.dta', '.spr', '.wav', '.mid', '.pcx', '.ags']

# def is_doc(path):
#     exts = ".txt .url .chm .chw .htm .doc".split()
#     return os.path.splitext(path)[1].lower() in exts

# def is_engine(path):
#     exts = ".exe .dll .manifest .clb .hlp .ovl .dxe .xml".split()
#     return os.path.splitext(path)[1].lower() in exts

# def is_template(path):
#     if 'template' in path:
#         return True
#     exts = ".agt .gui".split()
#     return os.path.splitext(path)[1].lower() in exts

# def ftype(path):
#     if is_demo(path):
#         return "DEMO"
#     if is_template(path):
#         return "TMPL"
#     if is_doc(path):
#         return "DOC"
#     if is_engine(path):
#         return "ENG"
#     return ""

def startswith_any(s, vals):
    for val in vals:
        if s.startswith(val):
            return True
    return False

def clean_dest_path(filepath):
    dname,fname = os.path.split(filepath)

    dname_parts = [x.lower() for x in dname.split("/")]
    bad_parts = ['ags', '{app}', '{commonappdata}', 'demo', 'demo game']
    while True:
        if len(dname_parts) <= 0:
            break
        found = False
        for bad_part in bad_parts:
            if dname_parts[0].startswith(bad_part):
                found = True
        if found:
            dname_parts.pop(0)
        else:
            break

    dname_parts = [x.title() for x in dname_parts]
    dname = "/".join(dname_parts)


    if startswith_any(fname.lower(), ("room", "game", "globalscript", "minigame", "music", "sound")):
        root, ext = os.path.splitext(fname)
        fname = root.title() + ext.lower()
        fname = fname.replace("Globalscript", "GlobalScript")
        fname = fname.replace("Minigame", "MiniGame")
        fname = fname.replace("Game.Agf", "Game.agf")
    else:
        fname = fname.lower()

    destpath = os.path.join(dname, fname)
    return destpath


def copy_file(tmpdir, filepath, destdir):
    cpysrc = os.path.join(tmpdir, filepath)
    if not os.path.isfile(cpysrc):
        raise Exception("%s is not a file"%cpysrc)
    
    destpath = os.path.join(destdir, clean_dest_path(filepath))
    mkdir_p(os.path.dirname(destpath))

    print "copy ", filepath, "to", destpath
    shutil.copy2(cpysrc, destpath)

def clear_dir(path):
    with cd(path):
        subprocess.check_call('''rm -rf *''', shell=True)

def path_depth(path):
    path = os.path.normpath(path)
    return len(path.split(os.sep))

def add_all(path):
    with cd(path):
        subprocess.check_call('''git add -A .''', shell=True)

def dir_has_changed(path):
    with cd(path):
        output = subprocess.check_output("git status --porcelain", shell=True)
        return len(output.strip()) > 0

def start_of_time():
    dt = (1998,12,17,22,33,36)
    return convert_dt(dt)

def commit(path, msg, date=None):
    if date == None:
        date = start_of_time()
    with cd(path):
        last_ts = date.isoformat()
        subprocess.check_call('''GIT_COMMITTER_NAME='CJ' GIT_COMMITTER_EMAIL='<>' GIT_AUTHOR_DATE='%s' GIT_COMMITTER_DATE='%s' git commit --author="CJ <>" -m "%s"'''%(last_ts, last_ts, msg), shell=True)

def convert_dt(dt):
    d = datetime.datetime(*dt)
    return TZ.localize(d)

def process_zip(zippath):
    print
    print "Processing %s"%zippath

    game_out_dir = os.path.join(OUT_DIR, DEMO_GAME_DIR)
    if os.path.isdir(game_out_dir):
        clear_dir(game_out_dir)

    tmpdir = tempfile.mkdtemp(suffix="-ags")

    last = start_of_time()

    with zipfile.ZipFile(zippath, 'r') as myzip:
        myzip.extractall(tmpdir)
        # sort by depth so DEMO dir files overrides any files in base.
        for entry in sorted(myzip.infolist(), key=lambda x: path_depth(x.filename)):
            if os.path.isfile(os.path.join(tmpdir, entry.filename)) and is_demo(entry.filename):
                last = max(last, convert_dt(entry.date_time))
                copy_file(tmpdir, entry.filename, game_out_dir)

    shutil.rmtree(tmpdir)

    add_all(OUT_DIR)
    if dir_has_changed(OUT_DIR):
        root, _ = os.path.splitext(os.path.basename(zippath))
        msg = "Demo Quest for Adventure Game Studio v%s" % VERSION_MAP[root]
        commit(OUT_DIR, msg, last)

# must be zip AND have room data.
def is_viable_archive(path):
    _, ext = os.path.splitext(path)
    if ext.lower() != ".zip":
        return False
    with zipfile.ZipFile(path, 'r') as zf:
        for entry in zf.infolist():
            _, ext = os.path.splitext(entry.filename)
            if ext.lower() in (".crm", ".asc"):
                return True;
    return False;

def load_order_file(path):
    return [x.strip().lower() for x in file('order.txt').readlines() if x.strip()]

def find_files_in_dir(path):
    name_to_path = {}
    # errors = []
    for dirpath, dirnames, filenames in os.walk("data"):
        for f in filenames:
            value = os.path.join(dirpath, f)
            if is_viable_archive(value):
                key = f.lower()
                # if key in name_to_path:
                    # if not filecmp.cmp(name_to_path[key], value):
                        # errors.append("two files with same name but not match!: %s and %s"% (name_to_path[key], value))
                name_to_path[key] = value
    # if errors:
        # for error in errors:
            # print error
        # raise Exception("files with same name but different content!")
    return name_to_path

def initialise_out(path):
    if os.path.isdir(path):
        raise Exception("out dir already exists!")
    mkdir_p(path)
    subprocess.check_call('''git init "%s"'''%path, shell=True)
    shutil.copy2("GAME_README.md", os.path.join(path, "README.md"))
    add_all(path)
    commit(path, "Initial commit")

def main():
    order = load_order_file("./order.txt")
    name_to_path = find_files_in_dir("./data")

    initialise_out(OUT_DIR)

    for x in order:
        if x in name_to_path and is_viable_archive(name_to_path[x]):            
            process_zip(name_to_path[x])



if __name__ == "__main__":
    main()
