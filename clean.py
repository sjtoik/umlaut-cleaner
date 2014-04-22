#!/bin/python
import os
import unicodedata
from stat import * 
import subprocess
import platform

"""
UTF8 symbol table used in character mapping. The integers are
same, what char() and ord() uses.
"""
repl = {
        65:196, #A Ä
        79:214, #O Ö
        97:228, #a ä
        111:246,#o ö
        }

def traverse(cwd):
    ret_files = []
    ret_dirs = []
    for root, dirs, files in os.walk(cwd):
        for d in dirs:
            (found, positions) = checkName(root, d)
            if found == True:
                ret_dirs.append((root, d, positions))

        for f in files:
            (found, positions) = checkName(root, f)
            if found == True:
                ret_files.append((root, f, positions))

    return (ret_dirs, ret_files) 

def checkName(root, name):
    found = False
    positions = []
    for i, c in enumerate(name):
        if (ord(c) == 776):
            found = True
            positions.append(i)

    return (found, positions)

def debug(root, name):
    """
    Usefull helpper, if you wan't to closely examine the string.
    Not used currently. Check the unicodedata package for more
    verbalism.
    """
    print(os.path.join(root, name))
    for i, c in enumerate(name):
        if (ord(c) == 776):
            print(" ", ord(c), unicodedata.category(c))
        else:
            print(c, ord(c), unicodedata.category(c))
    
    print("inode: " + str(getInode(root, name)))
    
def fixName(name, positions):
    i = 0

    if positions[0] == 0:
        del positions[0]
        c = chr(repl[ord(name[0])])
        name = name[2:]
        name = c + name
        i += 1

    for pos in positions:
        pos = pos - i # i characters already removed, adjust position
        c = chr(repl[ord(name[pos-1])])
        name = name[:pos-1] + name[pos+1:]
        name = name[:pos-1] + c + name[pos-1:]
        i += 1

    return name

def getInode(root, name):
    fstat = os.stat(os.path.join(root, name))
    return fstat[ST_INO]

def isBoth(root, name, fname):
    try:
        ni = getInode(root, name)
        fi = getInode(root, fname)
    except FileNotFoundError:
        return False 

    return True


if (__name__ == "__main__"):
    """
    Detects Finnish umlauts and fixes them if told so. Detection is done
    by searching for the special character u776. Found character and
    predessing vovel is replaced with correct UTF8 symbol based on dictionary
    defined above.

    Directories and files are handled separately, and I strongly suggest
    checking the directories by hand, because this script doesn't compare 
    the contents. OsX converts for example all u226 to u97u776 when writing
    the file to disk, so some of the edits between commits could have ended
    up in wrong file or directory. stat and diff are your friends.

    Don't forget to update your settings in OsX! 

    git config --global core.precomposeunicode true

    http://stackoverflow.com/questions/5581857/git-and-the-umlaut-problem-on-mac-os-x
    """

    if platform.system() == 'Darwin':
        print("OsX is the orginal reason for this corruption. It changes all the filenames")
        print("to this corrupt format. You need some other combo of OS and filesystem to")
        print("clean this messed up git (linux). This script needs the physical files in")
        print("disk, inorder to identify the corrupted ones.")
        exit("So done.")
    
    (dirs, files) = traverse(os.getcwd())

    for (root, name, positions) in dirs:
        fname = fixName(name, positions)
        if isBoth(root, name, fname):
            print("Duplicate! : " + os.path.join(root, fname))
        else:
            print("Just broken: " + os.path.join(root, fname))
   
    for (root, name, positions) in files:
        fname = fixName(name, positions)
        if isBoth(root, name, fname):
            print("Duplicate! : " + os.path.join(root, fname))
        else:
            print("Just broken: " + os.path.join(root, fname))
        """
        if isBoth(root, name, fname):
            subprocess.call(["git", "rm", os.path.join(root,name)])
        else:
            subprocess.call(["git", "mv", os.path.join(root,name), os.path.join(root,fname)])
            print("Renamed: " + os.path.join(root,fname))
        """
