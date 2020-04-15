from os import walk
import datetime

import pywintypes, win32file, win32con

def changeFileCreationTime(fname, newtime):
    wintime = pywintypes.Time(newtime)
    winfile = win32file.CreateFile(
        fname, win32con.GENERIC_WRITE,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None, win32con.OPEN_EXISTING,
        win32con.FILE_ATTRIBUTE_NORMAL, None)

    win32file.SetFileTime(winfile, wintime, None, None)

    winfile.close()

mypath =r"C:\DIRECTORY\WITH\PICTURES"

files = []
for (dirpath, dirnames, filenames) in walk(mypath):
    files.extend(filenames)
    break

for file in files:
    fullpath = mypath+"\\"+file

    if file.find("IMG_")==0 or file.find("VID_")==0 :
        firstunderscore=3
    else:
        firstunderscore=-1
        

    
    #firstunderscore = file.index("_")
    year = file[firstunderscore+1: firstunderscore+5]
    month = file[firstunderscore+5: firstunderscore+7]
    day = file[firstunderscore+7: firstunderscore+9]
    hour =file[firstunderscore+10: firstunderscore+12]
    minute =file[firstunderscore+12: firstunderscore+14]
    second = file[firstunderscore+14: firstunderscore+16]
    timestamp = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute),int(second),tzinfo=datetime.timezone.utc).timestamp()
    utcdatetime = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
    


    print(file+" "+fullpath+" "+month+"/"+day+"/"+year+" "+hour+":"+minute+":"+second+" "+str(timestamp))
    changeFileCreationTime(fullpath,utcdatetime)
    
