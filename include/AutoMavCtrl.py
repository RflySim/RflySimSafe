import os, sys, re
import cv2
import time
import threading
import subprocess
import numpy as np
import tkinter
from tkinter.messagebox import *
import src.openSHA.ProfustSA.Ass as ProfustSA

try:
    import include.AutoREG as AutoREG
    import include.AutoMavDB as AutoMavDB
    import include.AutoMavCmd as AutoMavCmd
    import include.AutoVisConf as AutoVis
    import include.UE4CtrlAPI as UE4CtrlAPI
    import include.PX4MavCtrlV4 as PX4MavCtrl
except ImportError:
    import AutoREG 
    import AutoMavDB 
    import AutoMavCmd 
    import UE4CtrlAPI
    import AutoVisConf as AutoVis
    import PX4MavCtrlV4 as PX4MavCtrl


ue = UE4CtrlAPI.UE4CtrlAPI()

class InitMavAutoEnv:
    def __init__(self,mav,conf,map):
        self.mav = mav
        self.conf = conf
        ''' [['Quadcopter', 'SITL', 2]] '''
        self.map = map
        self.InitMAVEnv()
        
    def InitMAVEnv(self):
        self.BInfo()
        self.BReset()
        self.BatEnvConf()
        self.BMap()

    def BInfo(self):
        '''
        UAV information configuration:
            MAV_NUM
            MAV_FRAME
            MAV_FRAME_NUM
            MAV_FRAME_DICT
            TEST_MODE
        '''
        AutoREG.MAV_FRAME_NUM = len(self.conf)
        AutoREG.MAV_NUM = len(self.mav)
        AutoREG.MAV_FRAME = []

        '''['Quadcopter', 'SITL', 2]'''
        for conf in self.conf:
            MavDBobj = AutoMavDB.MAVDB(conf)
            CaseID = MavDBobj.GET_CASEID()
            if conf[0] == 'Quadcopter':
                AutoREG.MAV_QUADCOPTER_NUM = conf[2]
                AutoREG.MAV_FRAME_DICT[AutoREG.RFLYSIM_FRAME['Quadcopter']][1] = conf[2]
                AutoREG.MAV_FRAME.append(AutoREG.RFLYSIM_FRAME['Quadcopter'])

                '''Aircraft test case distribution, only used in multi-aircraft mode'''
                
                AutoREG.MAV_CASE_DISTRIBUTION_QUADCOPTER = CaseID
                AutoREG.MAV_TEST_CASE_REG[AutoREG.RFLYSIM_FRAME['Quadcopter']] = CaseID
                '''[[1,3], [2,4]]'''
                isSingle = False
                if conf[2] == 1:
                    isSingle = True

                Info = 'Single machine' if isSingle else 'Multiple machines'
                print(f'{conf[0]} Conf: \n \tFrame:{conf[0]} \n \tMode:{Info} \n \tMAV Num:{AutoREG.MAV_QUADCOPTER_NUM} \n \tTest Cases:{AutoREG.MAV_CASE_DISTRIBUTION_QUADCOPTER} \n')

                AutoREG.MAV_DATA_DISTRIBUTION_QUADCOPTER = [val+1 for val in range(AutoREG.MAV_QUADCOPTER_NUM)]
                AutoREG.MAV_DATA_FOLDER_REG[AutoREG.RFLYSIM_FRAME['Quadcopter']] = [val+1 for val in range(AutoREG.MAV_QUADCOPTER_NUM)]

            elif conf[0] == 'Fixedwing':
                AutoREG.MAV_FIXEXWING_NUM = conf[2]
                AutoREG.MAV_FRAME_DICT[AutoREG.RFLYSIM_FRAME['Fixedwing']][1] = conf[2]
                AutoREG.MAV_FRAME.append(AutoREG.RFLYSIM_FRAME['Fixedwing'])

                '''Aircraft test case distribution, only used in multi-aircraft mode'''
                AutoREG.MAV_CASE_DISTRIBUTION_FIXEXWING = CaseID
                AutoREG.MAV_TEST_CASE_REG[AutoREG.RFLYSIM_FRAME['Fixedwing']] = CaseID

                isSingle = False
                if conf[2] == 1:
                    isSingle = True

                Info = 'Single machine' if isSingle else 'Multiple machines'
                print(f'{conf[0]} Conf: \n \tFrame:{conf[0]} \n \tMode:{Info} \n \tMAV Num:{AutoREG.MAV_FIXEXWING_NUM} \n \tTest Cases:{AutoREG.MAV_CASE_DISTRIBUTION_FIXEXWING} \n')

                AutoREG.MAV_DATA_DISTRIBUTION_FIXEXWING = [val+1 for val in range(AutoREG.MAV_FIXEXWING_NUM)]
                AutoREG.MAV_DATA_FOLDER_REG[AutoREG.RFLYSIM_FRAME['Fixedwing']] = [val+1 for val in range(AutoREG.MAV_FIXEXWING_NUM)]

            elif conf[0] == 'Vtol':
                AutoREG.MAV_VTOL_NUM = conf[2]
                AutoREG.MAV_FRAME_DICT[AutoREG.RFLYSIM_FRAME['Vtol']][1] = conf[2]
                AutoREG.MAV_FRAME.append(AutoREG.RFLYSIM_FRAME['Vtol'])

                '''Aircraft test case distribution, only used in multi-aircraft mode'''
                AutoREG.MAV_CASE_DISTRIBUTION_VTOL = CaseID
                AutoREG.MAV_TEST_CASE_REG[AutoREG.RFLYSIM_FRAME['Vtol']] = CaseID

                isSingle = False
                if conf[2] == 1:
                    isSingle = True

                Info = 'Single machine' if isSingle else 'Multiple machines'
                print(f'{conf[0]} Conf: \n \tFrame:{conf[0]} \n \tMode:{Info} \n \tMAV Num:{AutoREG.MAV_VTOL_NUM} \n \tTest Cases:{AutoREG.MAV_CASE_DISTRIBUTION_VTOL} \n')

                AutoREG.MAV_DATA_DISTRIBUTION_VTOL = [val+1 for val in range(AutoREG.MAV_VTOL_NUM)]
                AutoREG.MAV_DATA_FOLDER_REG[AutoREG.RFLYSIM_FRAME['Vtol']] = [val+1 for val in range(AutoREG.MAV_VTOL_NUM)]
        
        if AutoREG.MAV_FRAME_NUM == 1 and AutoREG.MAV_NUM == 1:
            AutoREG.TEST_MODE = 1 
        elif AutoREG.MAV_FRAME_NUM == 1 and AutoREG.MAV_NUM > 1:
            AutoREG.TEST_MODE = 2
        elif AutoREG.MAV_FRAME_NUM > 1 and AutoREG.MAV_NUM == AutoREG.MAV_FRAME_NUM:
            AutoREG.TEST_MODE = 3
        else:
            AutoREG.TEST_MODE = 4

        AutoREG.MAV_FRAME = list(set(AutoREG.MAV_FRAME)) 
        '''[1,2,3]'''

    def BReset(self):
        '''
        Bat resets to its original state
        '''
        for frame in AutoREG.MAV_FRAME:
            BatPath = self.GetPath(frame)
            if BatPath[0]:
                p = BatPath[1]
                self.BSingle(p)
            else:
                warn = BatPath[1]
                '''AutoREG.MAV_FRAME_DICT[Frame][0] file does not exist, exit !'''
                print(warn)
                AutoREG.BREAK_DOWN = True

    def BatEnvConf(self):
        '''
        In the case of multiple aircraft, it is necessary to modify the start of the Bat environment, the index and the number of aircraft
        Keep the start of only one Bat software environment + START_INDEX + VehicleNum
        '''
        START_INDEX = 1
        '''
        Set the Frame type with the smallest serial number as the main Bat, which means opening all simulation software for this Bat.
        '''
        BatPath = self.GetPath(AutoREG.MAV_FRAME[0]) # Quadcopter
        if BatPath[0]:
            p = BatPath[1]
            VehicleNum = AutoREG.MAV_FRAME_DICT[AutoREG.MAV_FRAME[0]][1]
            self.BVNum(p,VehicleNum)
            START_INDEX += VehicleNum
        else:
            pass

        '''
        If there are multiple frame types, REM the simulation software of the Bat script with the larger serial number, and modify the "START_INDEX" and the "VehicleNum" at the same time.
        '''
        if AutoREG.MAV_FRAME_NUM > 1:
            for frame in AutoREG.MAV_FRAME[1:]:
                BatPath = self.GetPath(frame)
                if BatPath[0]:
                    p = BatPath[1]
                    VehicleNum = AutoREG.MAV_FRAME_DICT[frame][1]
                    self.BEnv(p,START_INDEX,VehicleNum)
                    START_INDEX += VehicleNum
                else:
                    pass

    def BSingle(self,Path):
        newdata = ''
        with open(Path,mode='r',encoding='UTF-8') as fline:
            for line in fline:
                if  line.find('SET /a START_INDEX=')!= -1:
                    line = line.replace(line,'SET /a START_INDEX=1 \n')
                if  line.find('SET /A VehicleNum=')!= -1:
                    line = line.replace(line,'SET /A VehicleNum=1 \n')
                if  line.find('REM tasklist|find /i "QGroundControl.exe" || start %PSP_PATH%\QGroundControl\QGroundControl.exe')!= -1:
                    line = line.replace(line,'tasklist|find /i "QGroundControl.exe" || start %PSP_PATH%\QGroundControl\QGroundControl.exe \n')
                if  line.find('REM tasklist|find /i "RflySim3D.exe" || start %PSP_PATH%\RflySim3D\RflySim3D.exe')!= -1:
                    line = line.replace(line,'tasklist|find /i "RflySim3D.exe" || start %PSP_PATH%\RflySim3D\RflySim3D.exe \n')
                if  line.find('REM tasklist|find /i "CopterSim.exe" && taskkill /im "CopterSim.exe"')!= -1:
                    line = line.replace(line,'tasklist|find /i "CopterSim.exe" && taskkill /im "CopterSim.exe" \n')
                if  line.find('REM tasklist|find /i "CopterSim.exe" && taskkill /im "CopterSim.exe"')!= -1:
                    line = line.replace(line,'tasklist|find /i "CopterSim.exe" && taskkill /im "CopterSim.exe" \n')
                if  line.find('REM tasklist|find /i "QGroundControl.exe" && taskkill /f /im "QGroundControl.exe"')!= -1:
                    line = line.replace(line,'tasklist|find /i "QGroundControl.exe" && taskkill /f /im "QGroundControl.exe" \n')
                if  line.find('REM tasklist|find /i "RflySim3D.exe" && taskkill /f /im "RflySim3D.exe"')!= -1:
                    line = line.replace(line,'tasklist|find /i "RflySim3D.exe" && taskkill /f /im "RflySim3D.exe" \n')
                newdata += line

        with open(Path,mode='w',encoding='UTF-8') as f:
            f.write(newdata)
    
    def GetPath(self,Frame):
        conf = self.conf[0][1] # SITL / HITL
        sf = conf + '.bat'    
        path = os.path.join(os.getcwd(), 'src', 'model', AutoREG.MAV_FRAME_DICT[Frame][0])
        if os.path.exists(path):
            mf = [filename for filename in os.listdir(path) if sf in filename]
            _path = os.path.join(path,mf[0])
            return [True, _path]
        else:
            return [False, f'{AutoREG.MAV_FRAME_DICT[Frame][0]} file does not exist, exit !']
    
    def BVNum(self,path,num):
        newdata = ''
        with open(path,mode='r',encoding='UTF-8') as fline:
            for line in fline:
                if  line.find('SET /A VehicleNum=')!= -1:
                    line = line.replace(line,'SET /A VehicleNum={} \n'.format(num))
                newdata += line

        with open(path,mode='w',encoding='UTF-8') as f:
            f.write(newdata)
    
    def BEnv(self,Path,Index,Num):
        newdata = ''
        with open(Path,mode='r',encoding='UTF-8') as fline:
            for line in fline:
                if  line.find('SET /a START_INDEX=')!= -1:
                    line = line.replace(line,'SET /a START_INDEX={} \n'.format(Index))
                if  line.find('SET /A VehicleNum=')!= -1:
                    line = line.replace(line,'SET /A VehicleNum={} \n'.format(Num))
                if  line.find('tasklist|find /i "QGroundControl.exe" || start %PSP_PATH%\QGroundControl\QGroundControl.exe')!= -1:
                    line = line.replace(line,'REM tasklist|find /i "QGroundControl.exe" || start %PSP_PATH%\QGroundControl\QGroundControl.exe \n')
                if  line.find('tasklist|find /i "RflySim3D.exe" || start %PSP_PATH%\RflySim3D\RflySim3D.exe')!= -1:
                    line = line.replace(line,'REM tasklist|find /i "RflySim3D.exe" || start %PSP_PATH%\RflySim3D\RflySim3D.exe \n')
                if  line.find('tasklist|find /i "CopterSim.exe" && taskkill /im "CopterSim.exe"')!= -1:
                    line = line.replace(line,'REM tasklist|find /i "CopterSim.exe" && taskkill /im "CopterSim.exe" \n')
                if  line.find('tasklist|find /i "CopterSim.exe" && taskkill /im "CopterSim.exe"')!= -1:
                    line = line.replace(line,'REM tasklist|find /i "CopterSim.exe" && taskkill /im "CopterSim.exe" \n')
                if  line.find('tasklist|find /i "QGroundControl.exe" && taskkill /f /im "QGroundControl.exe"')!= -1:
                    line = line.replace(line,'REM tasklist|find /i "QGroundControl.exe" && taskkill /f /im "QGroundControl.exe" \n')
                if  line.find('tasklist|find /i "RflySim3D.exe" && taskkill /f /im "RflySim3D.exe"')!= -1:
                    line = line.replace(line,'REM tasklist|find /i "RflySim3D.exe" && taskkill /f /im "RflySim3D.exe" \n')
                newdata += line
        
        with open(Path,mode='w',encoding='UTF-8') as f:
            f.write(newdata)
    
    def BEMap(self,path):
        '''
        Grasslands
        OldFactory
        RealForestBLake
        NeighborhoodPark
        '''
        newdata = ''
        with open(path,mode='r',encoding='UTF-8') as fline:
            for line in fline:
                if  line.find('SET UE4_MAP=')!= -1:
                    line = line.replace(line,'SET UE4_MAP={} \n'.format(self.map[0]))
                if  line.find('SET /a ORIGIN_POS_X=')!= -1:
                    line = line.replace(line,'SET /a ORIGIN_POS_X={} \n'.format(self.map[1]))
                if  line.find('SET /a ORIGIN_POS_Y=')!= -1:
                    line = line.replace(line,'SET /a ORIGIN_POS_Y={} \n'.format(self.map[2]))
                if  line.find('SET /a ORIGIN_YAW=')!= -1:
                    line = line.replace(line,'SET /a ORIGIN_YAW={} \n'.format(self.map[3]))
                if  line.find('SET /a VEHICLE_INTERVAL=')!= -1:
                    line = line.replace(line,'SET /a VEHICLE_INTERVAL={} \n'.format(self.map[4]))
                newdata += line

        with open(path,mode='w',encoding='UTF-8') as f:
            f.write(newdata)
    
    def BMap(self):
        for frame in AutoREG.MAV_FRAME:
                BatPath = self.GetPath(frame)
                if BatPath[0]:
                    p = BatPath[1]
                    self.BEMap(p)
                else:
                    pass

def MavMonitor():
    '''
    This thread monitors all drone instance threads "AutoMavCtrler.AutoMavThread". When all drones are initialized, all threads are started "AutoMavCtrler.AutoMavRun".
    '''
    monitor = threading.Thread(target=AutoMavMonitor().AutoMavThreadMonitor, args=())
    monitor.start()

def SimMonitor():
    '''
    Monitor all simulation software objects and only open the bat script with the smallest rack sequence
    '''
    smonitor = threading.Thread(target=AutoMavMonitor().SimProcessStartThreadMonitor, args=())
    smonitor.start()

    dmonitor = threading.Thread(target=AutoMavMonitor().DataRecordThreadMonitor, args=())
    dmonitor.start()

    emonitor = threading.Thread(target=AutoMavMonitor().SimProcessEndThreadMonitor, args=())
    emonitor.start()
    
    
    num = 1
    while not AutoREG.ALL_FINISHED:
        if AutoREG.SIM_END_PRO_ALL_DOWM_KEY:
            AutoREG.SIM_END_PRO_ALL_DOWM_KEY = False
            AutoREG.SIM_START_PRO_ALL_DOWM = False
            ReSetREG()
            num += 1

            smonitor = threading.Thread(target=AutoMavMonitor().SimProcessStartThreadMonitor, args=())
            smonitor.start()

            dmonitor = threading.Thread(target=AutoMavMonitor().DataRecordThreadMonitor, args=())
            dmonitor.start()

            emonitor = threading.Thread(target=AutoMavMonitor().SimProcessEndThreadMonitor, args=())
            emonitor.start()

        
        if num == AutoREG.MAV_CASE_LEN:
            AutoREG.ALL_FINISHED = True
       
def ReSetREG():
    MAV_COMMON_REG.SimProcessStartContainer = []
    MAV_COMMON_REG.SimProcessEndContainer = []
    MAV_COMMON_REG.DataRecordThreadsContainer = []

    AutoMavDB.DataREG.Mode2mavP = []
    AutoMavDB.DataREG.Mode2caseP = []
    AutoMavDB.DataREG.Mode3frameP = []
    AutoMavDB.DataREG.Mode3caseP = []
    AutoMavDB.DataREG.Mode4frameP = []
    AutoMavDB.DataREG.Mode4caseP = []
    AutoMavDB.DataREG.Mode4mavREG = {
        'Quadcopter' : [],
        'Fixedwing'  : [],
        'Vtol'       :[]
    }
    AutoMavDB.DataREG.MavNum = 0
    AutoMavDB.DataREG.isDeleted = False
    AutoMavDB.DataREG.dataPollNum = 0
    AutoMavDB.DataREG.Finally_Path_for_Multi = None

    AutoREG.ARMED_WARN = False
    AutoREG.DIND_REG = {
        'Quadcopter': 0,
        'Fixedwing':  0,
        'Vtol':       0
    }

    AutoREG.TEST_RESULT = {
    'Is_Fall'    : 'No',
    'Fall Time'  : 'No',
    'Failsafe Trigger' : 'No',
    'Fail Vel':'No',
    'Flight Status After Fault Injection' : 'None',
    'Deviation From Expected Speed After Fault Injection' : 'None',
    'Deviation From Expected Position After Fault Injection' : 'None',
    'Failure Casualty Level':'None'
    }


class MAV_COMMON_REG():
    AutoMavThreadsContainer = []
    '''Each aircraft maintains a thread for performing its respective tasks'''
    SimProcessStartContainer = []
    '''Manage processes started by simulation software'''
    SimProcessEndContainer = []
    '''Manage processes ended by simulation software'''
    Lock = threading.Lock()

    DataRecordThreadsContainer = []


    SimProcessObj = None
    '''Manage objects opened by simulation software'''


class AutoMavMonitor():
    def __init__(self) -> None:
        pass

    def AutoMavThreadMonitor(self):
        isbreak = False
        printed = False
        while not isbreak:
            if len(MAV_COMMON_REG.AutoMavThreadsContainer) == AutoREG.MAV_NUM:
                # print('Get all UAV theard instance! Start every UAV "AutoMavRun"!')
                for automavthread in MAV_COMMON_REG.AutoMavThreadsContainer:
                    '''[mavid,tAutoRun,conf] '''
                    automavthread[1].start()
                isbreak = True
            else:
                if not printed:
                    printed = True
    
    def SimProcessStartThreadMonitor(self):
        '''
        Set the Frame type with the smallest serial number as the main Bat, which means opening all simulation software for this Bat.
        So, need to open the smallest serial number’ bat ---> Quadcopter (AutoREG.MAV_FRAME [1,2,3])
        '''
        isbreak = False
        printed = False
        while not isbreak:
            if len(MAV_COMMON_REG.SimProcessStartContainer) == AutoREG.MAV_NUM:
                print('Get all SimProcessStart theard instance! Start open RflySim simulation tools!')

                # 1、Get the thread object with the smallest rack sequence
                My_SimProcessStartContainer = []
                for simthread in MAV_COMMON_REG.SimProcessStartContainer:
                    temp = simthread[:]
                    temp.append(AutoREG.RFLYSIM_FRAME[simthread[2][0]])
                    My_SimProcessStartContainer.append(temp)
                '''[mavid,tAutoRun,conf,FrameID]'''
                My_SimProcessStartContainer = sorted(My_SimProcessStartContainer,key=(lambda x:x[3]))
                '''[[1, <Thread(Thread-11, initial)>, ['Quadcopter', 'SITL', 2], 1], [2, <Thread(Thread-12, initial)>, ['Quadcopter', 'SITL', 2], 1]]'''

                # 2、Remove duplicates
                seen = set()
                SimProcessStartContainer = []

                for Container in My_SimProcessStartContainer:
                    if Container[3] not in seen:
                        seen.add(Container[3])
                        SimProcessStartContainer.append(Container)

                # 3、Open the frame sequence minimal bat，this process takes "AutoREG.SIM_WAIT_TIME" seconds
                SimProcessStartContainer[0][1].start()

                # 4、Open the remaining bat script(Multi Frame Mode)
                if len(SimProcessStartContainer) > 1:
                    for autosimthread in SimProcessStartContainer[1:]:
                        '''[mavid,tAutoRun,conf] conf:[['Quadrotor','SITL',3]]'''
                        autosimthread[1].start()
                
                printed = False
                isdowm = False
                while True:
                    if len(SimProcessStartContainer) > 1:
                        for autosimthread in SimProcessStartContainer[1:]:
                            if not autosimthread[1].is_alive():
                                isdowm = True
                            else:
                                isdowm = False
                    else:
                        isdowm = True

                    if  not SimProcessStartContainer[0][1].is_alive() and isdowm:
                        AutoREG.SIM_START_PRO_ALL_DOWM = True
                        break
                    else:
                        if not printed:
                            print('Waiting all UAV open!...')
                            printed = True
                print('All UAV have opened!...')

                isbreak = True
            else:
                if not printed:
                    print('Waiting all UAV arrive...')
                    printed = True
        
        '''Initialize the drone's end flag and data recording flag'''
        AutoREG.SIM_END_PRO_ALL_DOWM = False
        AutoREG.DATA_ALL_DOWN = False

    def SimProcessEndThreadMonitor(self):
        '''
        Set the Frame type with the smallest serial number as the main Bat, which means opening all simulation software for this Bat.
        So, need to open the smallest serial number’ bat ---> Quadcopter (AutoREG.MAV_FRAME [1,2,3])
        '''
        isbreak = False
        printed = False
        while not isbreak:
            if len(MAV_COMMON_REG.SimProcessEndContainer) == AutoREG.MAV_NUM and AutoREG.DATA_ALL_DOWN:
                print('Get all SimProcessEnd theard instance! Start close RflySim simulation tools!')

                # 1、Get the thread object with the smallest frame sequence
                My_SimProcessEndContainer = []
                for simthread in MAV_COMMON_REG.SimProcessEndContainer:
                    temp = simthread[:]
                    temp.append(AutoREG.RFLYSIM_FRAME[simthread[2][0]])
                    My_SimProcessEndContainer.append(temp)
                '''[mavid,tAutoRun,conf,FrameID]'''
                My_SimProcessEndContainer = sorted(My_SimProcessEndContainer,key=(lambda x:x[3]))
                '''[[1, <Thread(Thread-11, initial)>, ['Quadcopter', 'SITL', 2], 1], [2, <Thread(Thread-12, initial)>, ['Quadcopter', 'SITL', 2], 1]]'''

                # 2、Remove duplicates
                seen = set()
                SimProcessEndContainer = []

                for Container in My_SimProcessEndContainer:
                    if Container[3] not in seen:
                        seen.add(Container[3])
                        SimProcessEndContainer.append(Container)

                # close the frame sequence minimal bat
                SimProcessEndContainer[0][1].start()
                SimProcessEndContainer[0][1].join()

                # 4、
                # close the remaining bat script(Multi Frame Mode)
                if len(SimProcessEndContainer) > 1:
                    for autosimthread in SimProcessEndContainer[1:]:
                        autosimthread[1].start()

                '''
                All aircraft are blocked and waiting. When all simulation environments are closed, they will enter the next step simultaneously.
                '''
                printed = False
                isdowm = False
                while True:
                    if len(SimProcessEndContainer) > 1:
                        for autosimthread in SimProcessEndContainer[1:]:
                            if not autosimthread[1].is_alive():
                                isdowm = True
                            else:
                                isdowm = False
                    else:
                        isdowm = True

                    if  not SimProcessEndContainer[0][1].is_alive() and isdowm:
                        AutoREG.SIM_END_PRO_ALL_DOWM = True
                        AutoREG.SIM_END_PRO_ALL_DOWM_KEY = True
                        break
                    else:
                        if not printed:
                            print('Waiting all UAV closed!...')
                            printed = True
                print('All UAV have closed!...')

                isbreak = True
            else:
                if not printed:
                    printed = True
        
    def DataRecordThreadMonitor(self):
        isbreak = False
        printed = False
        while not isbreak:
            if len(MAV_COMMON_REG.DataRecordThreadsContainer) == AutoREG.MAV_NUM:
                for automavthread in MAV_COMMON_REG.DataRecordThreadsContainer:
                    '''[mavid,tAutoRun,conf] '''
                    automavthread[1].start()

                isdowm = False
                while True:
                    isdowm = True
                    for autosimthread in MAV_COMMON_REG.DataRecordThreadsContainer:
                        if  autosimthread[1].is_alive():
                            isdowm = False

                    if  isdowm:
                        AutoREG.DATA_ALL_DOWN = True
                        break
                    else:
                        if not printed:
                            print('Waiting all UAV data thread closed!...')
                            printed = True

                print('All UAV data record have closed!...')
                isbreak = True

            else:
                if not printed:
                    printed = True

        print('All data has been collected. Start closing the simulation software and starting the next round of testing!')



class AutoMavCtrler():
    def __init__(self,mav,conf):
        ''' conf_eg: ['Quadcopter', 'SITL', 3] '''
        self.mav = mav
        self.conf = conf
        self.port = self.mav.port
        self.mavid = int((self.port-20100)/2+1)
        self.alive = False
        self.caseIndex = AutoREG.MAV_CASE_INDEX[AutoREG.RFLYSIM_FRAME[self.conf[0]]]
        AutoREG.MAV_CASE_INDEX[AutoREG.RFLYSIM_FRAME[self.conf[0]]] += 1
        
        self.frame = AutoREG.RFLYSIM_FRAME[self.conf[0]]
        self.InitMavEnvCount = 0
        self.TEST_OVER_FLAG = False
        self.InitModelConf()
    
    def InitModelConf(self):
        '''
        Custom model frame and configuration path

        Frame:
        1:                 Quadrotor
        2:                 Fixedwing
        3:                 USV
        '''
        # Create Mav database objects, and synchronize the json file test data to the corresponding model's test case table
        self.MAVDBobj = AutoMavDB.MAVDB(self.conf)

        if self.conf[2] > 1:
            self.MavCaseList = AutoREG.MAV_TEST_CASE_REG[AutoREG.RFLYSIM_FRAME[self.conf[0]]][self.caseIndex]
        else:
            self.MavCaseList = AutoREG.MAV_TEST_CASE_REG[AutoREG.RFLYSIM_FRAME[self.conf[0]]]
        AutoREG.MAV_CASE_LEN = len(self.MavCaseList)
        print(f'mav{self.mavid} all case:',self.MavCaseList)
        '''
        Single Mode eg: [1, 2, 5]
        '''
        self.MavCaseInd = 0

    def InitMavEnv(self):
        self.InitMavEnvCount += 1

        if self.InitMavEnvCount >= 2:
            '''Start hardware in the loop simulation'''
            self.mav = PX4MavCtrl.PX4MavCtrler(self.port)

        # Start hardware in the loop simulation
        self.SimProcessLoopStart()

        '''
        All aircraft are blocked and waiting. When all simulation environments are opened, they will enter the next step simultaneously.
        '''

        while True:
            if AutoREG.SIM_START_PRO_ALL_DOWM:
                self.InitMavComm()
                break
        
        if self.MAVDBobj.VISIONFLAG == True:
            self.POD = AutoVis.MavVIS(self.conf)

        # Initialize control sequence class object
        self.CFID = AutoMavCmd.CmdCtrl(self.mav,self.frame) # ['Quadrotor','SITL',3]
        self.CID1OBJ = self.CFID.CID1
        self.CID2OBJ = self.CFID.CID2

        # Initialize flight truth data
        self.WCSVel = np.array([0,0,0]) 
        self.WCSAng = np.array([0,0,0]) 
        self.WCSAcc = np.array([0,0,0]) 
        self.WCSEular = np.array([0,0,0]) 
        self.WCSPos = np.array([0,0,0]) 
        self.MotorRPM = np.array([0,0,0,0,0,0,0,0]) 
        self.FallVEL = 0 
        self.FallEnergy = 0 
        self.m = 1.515 

        # Initialize Flight index variable
        self.FLYIND = 0 
        self.RECORDIND = 0 
        self.RECORDFLAG = False
        self.RECORDTIME = 0
        self.EXITUND = 0 
        self.EXITFLAG = False
        self.EXITTIME = 0
        self.INJECTIND = 0 
        self.INJECTFLAG = False
        self.INJECTTIME = 0
        self.FALLIND = 0 
        self.FALLFLAG = False
        self.FALLTIME = 0
        self.LANDIND = 0 
        self.LANDFLAG = False
        self.LANDTIME = 0

        # Fault test status parameters
        self.ARMEDERROR = False

        self.result_data = None

        # Start time and end time (unlock after startup to prevent the ground station from not starting timing)
        self.startTime = time.time()
        self.endTime = time.time()
        self.lastTime = time.time()
        self.mav.SendMavArm(1)
        ue.sendUE4Cmd('RflyShowTextTime "Sim Start" 10')
        print(f'mav{self.mavid} Sim start')

        # Initialize Control instruction sequence index
        self.MavCmdInd = 0
        self.CaseID = self.MavCaseList[self.MavCaseInd]
        self.MavCmd = self.MAVDBobj.GET_MAVCMD(self.CaseID)
        self.MavCmdNum = len(self.MavCmd)
        print(f'Start mav{self.mavid} caseID {self.CaseID}')
        print(f'mav{self.mavid} cmd',self.MavCmd)
        
    def SimProcessLoopStart(self):
        self.tSimStart = threading.Thread(target=self.StartSimProcess, args=())
        Info = [self.mavid,self.tSimStart,self.conf] # ['Quadrotor','SITL',3]
        MAV_COMMON_REG.SimProcessStartContainer.append(Info)

    def SimProcessLoopEnd(self):
        self.tSimEnd = threading.Thread(target=self.EndSimProcess, args=())
        Info = [self.mavid,self.tSimEnd,self.conf] # ['Quadrotor','SITL',3]
        MAV_COMMON_REG.SimProcessEndContainer.append(Info)

    def StartSimProcess(self):
        model_path = os.path.join(sys.path[0],'..','model',AutoREG.MAV_FRAME_DICT[AutoREG.RFLYSIM_FRAME[self.conf[0]]][0])
        conf = self.conf[1] + '.bat'  
        batp = [filename for filename in os.listdir(model_path) if conf in filename]  
        path = os.path.join(model_path, batp[0])

        self.child = subprocess.Popen(path,shell=True,stdout=subprocess.PIPE)
        MAV_COMMON_REG.SimProcessObj = self.child
        print(f'Starting {self.conf[1]} simulation software')
        time.sleep(AutoREG.SIM_WAIT_TIME_REG)

    def EndSimProcess(self):
        # Exit the simulation software
        print(f'Exit {self.conf[1]} simulation software')
        os.system('tasklist|find /i "CopterSim.exe" && taskkill /im "CopterSim.exe"')
        os.system('tasklist|find /i "QGroundControl.exe" && taskkill /f /im "QGroundControl.exe"')
        os.system('tasklist|find /i "RflySim3D.exe" && taskkill /f /im "RflySim3D.exe"')
        MAV_COMMON_REG.SimProcessObj.terminate()
        MAV_COMMON_REG.SimProcessObj.kill()
        print('All closed')
        time.sleep(5)

    def DataRecordLoop(self):
        self.tData = threading.Thread(target=self.DataRecord,args=())
        mavDataThreadInfo = [self.mavid,self.tData,self.conf] # ['Quadrotor','SITL',3]
        MAV_COMMON_REG.DataRecordThreadsContainer.append(mavDataThreadInfo)

    def DataRecord(self):
        TestNum = self.InitMavEnvCount
        Info = [self.MavCmd, self.result_data, self.mavid]
        Data = [self.WCSVel,self.WCSAng,self.WCSPos]
        print(f"mav{int((self.port-20100)/2+1)}:Start data processing")
        DataObj = AutoMavDB.DATAAPI(self.CaseID,self.conf,Data,Info) # ['Quadrotor','SITL',3]
        print(f"mav{int((self.port-20100)/2+1)}:Data processing Finished")

    def InitMavComm(self):
        self.mav.InitMavLoop()
        time.sleep(0.5)
        
        self.mav.InitTrueDataLoop()
        time.sleep(0.5)
        
        if self.conf[0] == 'Fixedwing':
            self.mav.enFixedWRWTO()
        else:
            self.mav.initOffboard()
            time.sleep(0.5)

    def EndMavComm(self):
        self.mav.EndTrueDataLoop()
        time.sleep(0.5)
        self.mav.endMavLoop() 
        time.sleep(0.5)

        time.sleep(5)

    def AutoMavLoopStart(self):
        self.tAutoRun = threading.Thread(target=self.AutoMavRun, args=())
        TMavInfo = [self.mavid,self.tAutoRun,self.conf]
        MAV_COMMON_REG.AutoMavThreadsContainer.append(TMavInfo) 
    
    def ShowWinLoop(self):
        self.tShow = threading.Thread(target=self.ShowWin, args=())
        self.tShow.start()
        self.tShow.join()
    
    def ShowWin(self):
        MAV_COMMON_REG.Lock.acquire()
        ProfustLevel=AutoREG.TEST_RESULT['Failure Safety Level']
        ID = self.CaseID
        window = tkinter.Tk()
        window.attributes("-topmost",1)
        window.withdraw()  
        ProfustSafty=AutoREG.TEST_RESULT['Failure Safety Score']
        Healthscore="%.1f" % 0.021
        myText="Test task:"+f"{self.FM}\n"+'Test case ID:'+str(ID)+"\nProfust Safty Level:"+ProfustLevel+"\nProfustSafty:"+ProfustSafty+"\nFault diagnosis is triggered correctly:"+f"{AutoREG.TEST_RESULT['Failsafe Trigger']}"
        myText=myText+'\n\nClick "OK" to archive the data and start the next test'
        window.after(3000, window.destroy)
        result = showinfo('提示',myText)
        window.mainloop() 
        MAV_COMMON_REG.Lock.release()

    def AutoMavRun(self):
        print(f'hello, mav{self.mavid}')

        while True: 
            if self.MavCaseInd >= len(self.MavCaseList):
                self.TEST_OVER_FLAG = True
                print(f'mav{self.mavid} all case test finish!')
                break

            AutoMavCtrler.InitMavEnv(self)

            self.alive = True
            while True:
                # 250HZ receiving data
                self.lastTime = self.lastTime + (1.0/250)
                sleepTime = self.lastTime - time.time()
                if sleepTime > 0:
                    time.sleep(sleepTime)
                else:
                    self.lastTime = time.time()

                
                # Need to restore !!!!
                if self.MAVDBobj.VISIONFLAG == True:
                    self.POD.visShow()
                    # if self.CID2OBJ.INJECTFLAG == True and (self.CID2OBJ.FAULTID == 123549 or self.CID2OBJ.FAULTID == 125340 or self.CID2OBJ.FAULTID == 125341):
                    #     self.POD.Podfault(self.CID2OBJ.FAULTID) # Trigger pod fault
                
                

                # Start recording data after the unlocking command is issued
                if self.CID2OBJ.ARMFLAG == True:
                    VEL = np.array(self.mav.trueVelNED)
                    ANGRATE = np.array(self.mav.trueAngRate) 
                    ACC = np.array(self.mav.trueAccB)
                    MOTORRPM = np.array(self.mav.trueMotorRPMS)
                    EULAR = np.array(self.mav.trueAngEular)
                    POS = np.array(self.mav.truePosNED)
                    self.FLYIND = self.FLYIND + 1
                    self.WCSVel = np.row_stack((self.WCSVel,VEL)) 
                    self.WCSAng = np.row_stack((self.WCSAng,ANGRATE)) 
                    self.WCSAcc = np.row_stack((self.WCSAcc,ACC)) 
                    self.WCSEular = np.row_stack((self.WCSEular,EULAR)) 
                    self.WCSPos =  np.row_stack((self.WCSPos,POS)) 
                    self.MotorRPM =  np.row_stack((self.MotorRPM,MOTORRPM)) 

                # Processing instruction sequence
                AutoMavCtrler.TRIGGERMAVCMD(self,self.MavCmd[self.MavCmdInd])
                # If one instruction sequence is completed, the next instruction is processed
                if re.findall(r'-?\d+\.?[0-9]*',self.MavCmd[self.MavCmdInd])[0] == '1' and self.CID1OBJ.isDone == 1 or re.findall(r'-?\d+\.?[0-9]*',self.MavCmd[self.MavCmdInd])[0] == '2' and self.CID2OBJ.isDone == 1:
                    self.MavCmdInd = self.MavCmdInd + 1

                if self.CID2OBJ.RECORDFLAG == True and self.RECORDFLAG == False:
                    self.RECORDIND = self.FLYIND 
                    self.RECORDTIME = round(time.time() - self.startTime)
                    self.RECORDFLAG = True
                
                if self.CID2OBJ.INJECTFLAG == True and self.INJECTFLAG == False:
                    self.INJECTIND = self.FLYIND 
                    self.INJECTTIME = round(time.time() - self.startTime)
                    self.INJECTFLAG = True
                
                if self.CID2OBJ.LANDFLAG == True and self.LANDFLAG == False:
                    self.LANDIND = self.FLYIND 
                    self.LANDTIME = round(time.time() - self.startTime)
                    self.LANDFLAG = True

                if self.MavCmdInd >= self.MavCmdNum and self.EXITFLAG == False:
                    self.EXITUND = self.FLYIND 
                    self.EXITTIME = round(time.time() - self.startTime)
                    self.EXITFLAG = True
                    print(f'mav{self.mavid}: CaseID {self.CaseID} test completed')
                    ue.sendUE4Cmd('RflyShowTextTime "CaseID %d test completed!" 10'%(self.CaseID))
                    self.endTime = time.time()
                    break

                # Judgment of crash, if the landing speed is greater than 3.5, the aircraft is considered to have crashed
                if  abs(np.array(self.mav.truePosNED[2])) < 1.2 and self.FALLFLAG == False  and abs(np.array(self.mav.trueVelNED[2])) > 3.5: 
                    self.FALLTIME =  round(time.time() - self.startTime)
                    self.FALLIND = self.FLYIND
                    self.FALLFLAG = True
                    self.FallVEL = round(np.max(self.WCSVel),2) 
                    self.FallEnergy = round(0.5*self.m*(self.FallVEL**2),2) 
                    self.EXITUND = self.FLYIND 
                    self.EXITTIME = round(time.time() - self.startTime)
                    self.EXITFLAG = True
                    self.endTime = time.time()

                    AutoREG.TEST_RESULT['Is_Fall'] = 'Yes'
                    AutoREG.TEST_RESULT['Fall Time'] = self.EXITTIME
                    AutoREG.TEST_RESULT['Fall Vel'] = self.FallVEL
                    AutoREG.TEST_RESULT['Fall Energy'] = self.FallEnergy

                    print("{}s,Crash! Exit the test".format(self.EXITTIME))
                    ue.sendUE4Cmd('RflyShowTextTime "Crash!" 10')
                    break

                # If the unlocking is abnormal, exit the test and start a new test again
                if self.mav.isArmerror == 1:
                    self.ARMEDERROR = True
                    AutoREG.ARMED_WARN = True
                    # break
                
                if self.mav.isFailsafeEn == True:
                    AutoREG.TEST_RESULT['Failsafe Trigger'] = 'Yes!' + self.mav.FailsafeInfo


            if self.ARMEDERROR == False:
                if self.CID2OBJ.RECORDFLAG == True:
                    
                    # SaftyAssessment API
                    '''
                    SaftyAssessment(Index,EvalName,EvalData,EvalDim,EvalParam,CtrlCmd)
                    Index is the list of index entries:start_index、end_index、fall_index
                    EvalName is the name of the data
                    EvalData is a data  item list:Ang、Vel、Pos、...
                    EvalDim is a dimension item list: Represents the specific dimension of Data
                    EvalParam is a parameter item list: Including: data frequency (number of data in 1s), ground kinetic energy, index weight
                    CtrlCmd is a Control command item list: Target command representing position and speed
                    '''

                    # Just a case
                    DataFreq = round(len(self.WCSVel)/(self.endTime - self.startTime))
                    FallEnergy = self.FallEnergy
                    PosCmd, VelCmd = self.GetDesiredPV()

                    StartIndex = self.INJECTIND
                    EndIndex = self.EXITUND
                    FallIndex = self.FALLIND
                    Index = [StartIndex,EndIndex,FallIndex]
                    EvalName = ['Ang']
                    EvalData = [self.WCSAng]
                    EvalDim = [0]
                    EvalWeight = [1]

                    EvalParam = [DataFreq,FallEnergy,EvalWeight]
                    CtrlCmd = [PosCmd,VelCmd]
                    ProfustSA.SaftyAssessment(Index,EvalName,EvalData,EvalDim,EvalParam,CtrlCmd)

                    AutoREG.TEST_RESULT['Failure Safety Score'] = ProfustSA.ProfustSaftyScoreUAV
                    AutoREG.TEST_RESULT['Failure Safety Level'] = ProfustSA.ProfustSaftyLevelUAV

                    AutoREG.TEST_RESULT['Flight Status After Fault Injection'] = self.calculate_flight_status(self.WCSAng[self.INJECTIND:])

                    if any(element != 0 for element in VelCmd):
                        AutoREG.TEST_RESULT['Deviation From Expected Speed After Fault Injection'] = self.Deviation(np.array(VelCmd), self.WCSVel[self.INJECTIND:])
                    
                    if any(element != 0 for element in PosCmd):
                        AutoREG.TEST_RESULT['Deviation From Expected Position After Fault Injection'] = self.Deviation(np.array(PosCmd), self.WCSPos[self.INJECTIND:])
                    
                    # ue.sendUE4Cmd('RflyShowTextTime "Profust Safty Score:%.3f" 10'%(AutoREG.TEST_RESULT['Failure Safety Score']))

                    # Data Base Pro
                    self.MAVDBobj.RESETR_DB(self.CaseID)
                    '''"DELETE FROM TEST_CASE WHERE CaseID = {}"'''

                    ID = self.CaseID
                    FaultID = self.CID2OBJ.FAULTID
                    fault_type = self.MAVDBobj.GET_CASEINFO(self.CaseID)['FaultType']
                    CaseDescription = f'Frame: {self.conf[0]} \n' + f'S/HITL: {self.conf[1]} \n' + 'Injection '+ f'{fault_type}' + ' During Normal Flight'
                    FaultMode = self.MAVDBobj.GET_CASEINFO(self.CaseID)['FaultMode']
                    ControlSequence = self.CMDANA(self.MavCmd)
                    TestResult = self.Get_TestResult(AutoREG.TEST_RESULT)
                    self.result_data = [ID, FaultID, CaseDescription, FaultMode, ControlSequence, TestResult]

                    self.MAVDBobj.RESULT_DBPro(self.result_data)
                    ''' insert into TEST_RESULT(CaseID, FaultID, CaseDescription, FaultMode, ControlSequence, TestResult) values(?, ?, ?, ?, ?, ?) '''
                    self.MAVDBobj.TEST_STATEPro(self.CaseID)
                    ''' update TEST_CASE set TestStatus = 'Finished' where CaseID = {} '''

                    # JSON Pro
                    MAV_COMMON_REG.Lock.acquire() 
                    self.MAVDBobj.MAV_JSONPro(self.CaseID)
                    MAV_COMMON_REG.Lock.release()

                    self.FM = FaultMode
                    # self.ShowWinLoop()
                
                print(f'mav{self.mavid} Sim end')
                ue.sendUE4Cmd('RflyShowTextTime "Sim end" 10')

                if self.MAVDBobj.VISIONFLAG == True:
                    cv2.destroyAllWindows() 

                AutoMavCtrler.EndMavComm(self)
                self.SimProcessLoopEnd()
                self.MavCaseInd += 1
            else:
                ID = self.CaseID
                FaultID = self.CID2OBJ.FAULTID
                fault_type = self.MAVDBobj.GET_CASEINFO(self.CaseID)['FaultType']
                CaseDescription = f'Frame: {self.conf[0]} \n' + f'S/HITL: {self.conf[1]} \n' + 'Injection '+ f'{fault_type}' + ' During Normal Flight'
                FaultMode = self.MAVDBobj.GET_CASEINFO(self.CaseID)['FaultMode']
                ControlSequence = self.CMDANA(self.MavCmd)
                TestResult = 'Armed exception, recommend retest!'
                self.result_data = [ID, FaultID, CaseDescription, FaultMode, ControlSequence, TestResult]

                self.MAVDBobj.RESULT_DBPro(self.result_data)
                ''' insert into TEST_RESULT(CaseID, FaultID, CaseDescription, FaultMode, ControlSequence, TestResult) values(?, ?, ?, ?, ?, ?) '''
                self.MAVDBobj.TEST_STATEPro(self.CaseID)
                ''' update TEST_CASE set TestStatus = 'Finished' where CaseID = {} '''

                print(f'mav{self.mavid} Armed exception, recommend retest!')
                print(f'mav{self.mavid} Sim end')
                AutoMavCtrler.EndMavComm(self)
                self.SimProcessLoopEnd()
                self.MavCaseInd += 1
            

            '''Start data processing thread'''
            AutoMavCtrler.DataRecordLoop(self)

            '''Block waiting for data processing threads of all drones'''
            printed = False
            while True:
                if AutoREG.DATA_ALL_DOWN:
                    break
                else:
                    if not printed:
                        # print(f'mav{self.mavid} data record havs ended! Wait for other UAV data record ending' )
                        printed = True

            '''Blocks waiting for SimEnd thread  of all drones'''
            printed = False
            while True:
                if AutoREG.SIM_END_PRO_ALL_DOWM:
                    break
                else:
                    if not printed:
                        # print(f'mav{self.mavid} simulation havs ended! Wait for other UAV sim ending' )
                        printed = True
            
            print(f'mav{self.mavid} next round')
        
    def TRIGGERMAVCMD(self,ctrlseq):
        cmdseq = ctrlseq # '2,3,0,0,-20'
        cmdseq = re.findall(r'-?\d+\.?[0-9]*',cmdseq) # ['2', '3', '0', '0', '-20']
        cmdCID = cmdseq[0]
        if  cmdCID in self.CFID.CID:
            FID = self.CFID.FIDPro(cmdCID)
            # if has param
            if len(cmdseq) > 2:
                # get param
                param = cmdseq[2:len(cmdseq)]
                param = [float(val) for val in param]
                FID[cmdseq[1]](param)

            else:
                FID[cmdseq[1]]()
        else:
            print(f'mav{self.MAVID} Command input error, please re-enter')      

    def is_alive(self):   
        while True:
            if AutoREG.SIM_START_PRO_ALL_DOWM:
                if self.alive:
                    return True
    
    def calculate_flight_status(self, angular_velocity_data):
        avg_angular_velocity = np.mean(angular_velocity_data, axis=0)

        if np.max(np.abs(avg_angular_velocity)) < 0.01:
            flight_status = "Smooth flight"
        elif np.max(np.abs(avg_angular_velocity)) < 0.1:
            flight_status = "Slight shaking"
        elif np.max(np.abs(avg_angular_velocity)) < 1.0:
            flight_status = "Violent shaking"
        else:
            if not self.FALLFLAG:
                flight_status = "Violent rolling"
            else:
                flight_status = "Violent rolling and crashing"

        return flight_status
                
    def GetDesiredPV(self):
        data = self.MavCmd
        result = {}

        if self.conf[0] == 'Quadcopter':
            target_indices = {
                '2,3': [0, 0, 0],
                '2,4': [0, 0, 0]
            }
            
            for i, d in enumerate(data):
                for target in target_indices:
                    if target in d:
                        params = d.split(',')[2:]
                        params_float = [float(param) for param in params]
                        if target == '2,3':
                            target_indices[target] = params_float[:3]
                        elif target == '2,4':
                            target_indices[target] = params_float[:3]
                        break
            result['Pos'] = target_indices['2,3']
            result['Vel'] = target_indices['2,4']
            return result['Pos'], result['Vel']

        elif self.conf[0] == 'Fixedwing':
            target_indices = {
                '2,4': [0, 0, 0],
                '2,7': [0, 0, 0]
            }
            result = {}

            for i, d in enumerate(data):
                for target in target_indices:
                    if target in d:
                        params = d.split(',')[2:]
                        params_float = [float(param) for param in params]
                        if target == '2,4':
                            target_indices[target] = params_float[:3]
                        elif target == '2,7':
                            target_indices[target] = params_float[:3]
                        break
            result['Pos'] = target_indices['2,4']
            result['Vel'] = target_indices['2,7']
            return result['Pos'], result['Vel']

    
    def Deviation(self, desired, true):
        deviation = np.abs(true - desired)
        mean_deviation = np.mean(deviation, axis=0)
        return mean_deviation

    def CMDANA(self,cmd):
        subcmd = ';'.join(cmd)
        subcmd = subcmd.split(';')

        mtime = 0
        info = ''

        if subcmd[0][0] == '2':
            for index, cmd in enumerate(subcmd):
                cmd = cmd.split(',')
                if cmd[0] == '2':
                    info += f'{mtime}s: '
                    if cmd[1] == '1' or cmd[1] == '2':
                        info += AutoREG.RFLYSIM_CMD[self.conf[0]][cmd[1]]
                    elif cmd[1] == '3' or cmd[1] == '4' or cmd[1] == '5':
                        info += AutoREG.RFLYSIM_CMD[self.conf[0]][cmd[1]].format(cmd[2],cmd[3],cmd[4])
                    elif cmd[1] == '6':
                        fp = [float(str) for str in cmd[3:] if str != cmd[2]]
                        info += AutoREG.RFLYSIM_CMD[self.conf[0]][cmd[1]].format(cmd[2],fp)
                    info += ' \n'

                if cmd[0] == '1':
                    mtime += int(float(cmd[2]))
                    if index == len(subcmd) - 1:
                        info += f'{mtime}s: Exit test!'
                
        elif subcmd[0][0] == '1':
            index = 0
            for i in range(len(subcmd)):
                if subcmd[i][0] != '1':
                    index = i
                    break
            
            for index, cmd in enumerate(subcmd[index:], start=index):
                cmd = cmd.split(',')
                if cmd[0] == '2':
                    info += f'{mtime}s: '
                    if cmd[1] == '1' or cmd[1] == '2':
                        info += AutoREG.RFLYSIM_CMD[self.conf[0]][cmd[1]]
                    elif cmd[1] == '3' or cmd[1] == '4' or cmd[1] == '5':
                        info += AutoREG.RFLYSIM_CMD[self.conf[0]][cmd[1]].format(cmd[2],cmd[3],cmd[4])
                    elif cmd[1] == '6':
                        fp = [float(str) for str in cmd[3:] if str != cmd[2]]
                        info += AutoREG.RFLYSIM_CMD[self.conf[0]][cmd[1]].format(cmd[2],fp)
                    info += ' \n'

                if cmd[0] == '1':
                    mtime += int(float(cmd[2]))
                    if index == len(subcmd) - 1:
                        info += f'{mtime}s: Exit test!'
        return info

    def Get_TestResult(self, test_result):
        result = ''
        for key, value in test_result.items():
            result += f"{key:5s}: {value} \n"
        
        return result
        
        

            
                
            