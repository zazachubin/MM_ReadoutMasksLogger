# ------------------------------------------------- Install -----------------------------------------------------
#python -m pip install pyserial
#python -m pip install opencv-python
#python -m pip install pyfirmata
#---------------------------------------------------- Lib -------------------------------------------------------
import threading
import pyfirmata
import time
import cv2
import os
import shutil
#---------------------------------------------------- Var -------------------------------------------------------
#------------------------------------------------- top side -----------------------------------------------------
coord_code_T = ["100","104","104_m","108","300","304","304_m","308","500","504","504_m","102","106","106_m","110","302","306","306_m","310","502","506","506_m"]
#--------------------------------------------------------------------------------------
#------------------------------------------------- bot side -----------------------------------------------------
coord_code_B = ["506","506_m","502","310","306","306_m","302","110","106","106_m","102","504","504_m","500","308","304","304_m","300","108","104","104_m","100"]
#-------------------------------------------- Arduino port Config -----------------------------------------------
controller = True
while controller:
    try:
        #board = pyfirmata.Arduino('/dev/ttyUSB0')
        board = pyfirmata.Arduino('COM4')
        pyfirmata.util.Iterator(board).start()
#------------------------------------- configure arduin digital I/O ports ---------------------------------------
        sw = board.get_pin('d:6:i')                 # arduino digital input port 6 for CNC Triger signal reading
        led = board.get_pin('d:7:o')                # arduino digital output port 7 for CNC Transmit request signal
        controller = False
    except:
        print ('connect Contriller !!', end='\r')
        controller = True
        pass
#----------------------------------------------- Camera cnfig ---------------------------------------------------
cap = cv2.VideoCapture(1)                           # Create a VideoCapture object

#cap.set(cv2.CAP_PROP_SETTINGS,1)     # Camera LED on/off (environment variable OPENCV_VIDEOIO_PRIORITY_MSMF = 0)
if (cap.isOpened() == False):                       # Check if camera opened successfully
    print("Unable to read camera !!", end='\r')
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
#ret, frame = cap.read()
#--------------------------------------------- global variables -------------------------------------------------
iN = 0
tkp = 0
stop = False
value = 'False'
deltaTime = 1
#------------------------------------------------ input data ----------------------------------------------------
Pan_type = str(input ("Enter panel type (eta or stereo): "))
Pan_side = str(input ("Enter panel Side (top or bot): "))
Pan_Number = str(input ("Enter panel Number: "))
#----------------------------------------------------------------------------------------------------------------
if Pan_type == "eta" :
    pan_type = "e"
elif Pan_type == "stereo":
    pan_type = "s"
else :
    print("not corect panel type !! ")
#----------------------------------------------------------------------------------------------------------------
if Pan_side == "top" :
    Pan_side = "t"
elif Pan_side == "bot":
    Pan_side = "b"
else :
    print("not corect panel side !! ")
#----------------------------------------------------------------------------------------------------------------
if (pan_type == "e"):
    folderN = "eta"
if (pan_type == "s"):
    folderN = "stereo"
#---------------------------------------------- Directory path --------------------------------------------------
path = folderN + Pan_Number + Pan_side + "/"
try:
    os.mkdir(path)
except FileExistsError:
    shutil.rmtree(path)
    os.mkdir(path)
    pass
#----------------------------------------------- Bottom side ----------------------------------------------------
if Pan_side == "b" :
    coord_code = coord_code_B
    print("========================== BOT ==========================*")
    print("\    X                   Y 130                     X    / ")
    print(" \ * 2245                  295                    80 * /  ")
    print("  \ * 2235                 460                   90 * /   ") 
    print("   \-------------------------------------------------/    ")            
    print("    \ * 2225               590                100 * /     ")
    print("     \ * 2215              755               110 * /      ")
    print("      \ * 2205             920              120 * /       ")
    print("       \-----------------------------------------/        ")
    print("        \ * 2195           1050           130 * /         ")
    print("         \ * 2185          1215          145 * /          ")
    print("          \ * 2170         1380         155 * /           ")
    print("           ===================================            ")
#------------------------------------------------ Top side ------------------------------------------------------   
elif Pan_side == "t":
    coord_code = coord_code_T
    print("           =============== TOP ===============*           ")
    print("          / * 2170         130          155 * \           ")
    print("         / * 2185          295           145 * \          ")
    print("        / * 2195           460            130 * \         ") 
    print("       /-----------------------------------------\        ")            
    print("      / * 2205             590              120 * \       ")
    print("     / * 2215              755               110 * \      ")
    print("    / * 2225               920                100 * \     ")
    print("   /-------------------------------------------------\    ")
    print("  / * 2235                 1050                  90 * \   ")
    print(" / * 2245                  1215                   80 * \  ")
    print("/     X                     Y                      X    \ ")
    print("========================================================= ")
    
file_prefix = pan_type + Pan_Number + Pan_side + "_"
#----------------------------------------------------------------------------------------------------------------
#----------------------------------------- Recieve Signal from CNC ----------------------------------------------
def ardRead():
    global value
    while True:
        value = sw.read()
        #print(value, end='\r')
        if stop:
            break
    led.write(0)
    board.exit()
#------------------------------------------ Transfer Signal to CNC ----------------------------------------------
def ardWrite(req):
    led.write(req)
#------------------------------------------------- Controll -----------------------------------------------------     
def contr():
    global iN                                       # global variable for take picture emount controll
    global tkp
    global stop
    ardWrite(1)
    while True:
        if iN > 21:
            stop = True
            break
        if (str(value) == "False" or str(value) == "None"):
            tkp = 1
        if ((str(value) == "True") and (tkp == 1)):
            time.sleep(5)
            while(True):
                if (deltaTime < 0.5):
                    cv2.imwrite(os.path.join(path,file_prefix + coord_code[iN] + '.bmp', ),frame)
                if os.path.exists(path + '/'+ file_prefix + coord_code[iN] + '.bmp') and ret:
                    break
                if stop:
                    break
            print("N" + str(iN+1) + " ---- " + file_prefix + coord_code[iN] + '.bmp' + " -----------> OK")
            time.sleep(1)
            iN = iN + 1
            tkp = 0
            ardWrite(0)
            time.sleep(0.5)
            ardWrite(1)
#------------------------------------------------ Camera Show --------------------------------------------------
def cameraShow():
    global stop
    global frame
    global ret
    global deltaTime
    while True:
        try:
            start = time.time()
            ret, frame = cap.read()
            cv2.imshow('frame',frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop = True
                break
            if stop:
                break
            st = time.time()
            deltaTime = st - start
        except:
            pass
    cap.release()
    cv2.destroyAllWindows()
print ('------------------- start -----------------------')
#------------------------------------------------- threading ---------------------------------------------------
thread1 = threading.Thread(target = ardRead)
thread2 = threading.Thread(target = cameraShow)
thread3 = threading.Thread(target = contr)
#---------------------------------------------- Start threading ------------------------------------------------
thread1.start()
thread2.start()
thread3.start()
#---------------------------------------------------------------------------------------------------------------
thread1.join()
thread2.join()
thread3.join()
#------------------------------------------------- Work Done ---------------------------------------------------
print('program Done !!')
print ('------------------- end -----------------------')
#input ('Enter eny key to quit: ')
