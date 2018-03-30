#!/usr/bin/env python

PKG = 'drone'
import roslib; roslib.load_manifest(PKG)
import rospy
import sys
import math
import numpy
import random
import time
import json
from drone.msg import NavSatFix
from drone.msg import GasSensorData
from drone.msg import DroneComm
from sensor_msgs.msg import NavSatFix

def Distance(triplet1, triplet2):
    (x1,y1,z1) = triplet1
    (x2,y2,z2) = triplet2
    #print "CommRangeDetector: drone 1 is (%f|%f|%f)" %(y1,x1,z1)
    #print "CommRangeDetector: drone 2 is (%f|%f|%f)" %(y2,x2,z2)
    xDist = (x1 - x2)*111111.11
    yDist = (y1 - y2)*111111.11
    zDist = (z1 - z2)
    #print "CommRangeDetector: axis dist is (%f|%f|%f) = (%f)" %(xDist,yDist,zDist, ((xDist ** 2) + (yDist ** 2) + (zDist ** 2)) ** (1./2))
    return ((xDist ** 2) + (yDist ** 2) + (zDist ** 2)) ** (1./2)

class DroneGPSSubscriber:
    def __init__(self, id):
        self.id = id
        self.GPSReceiverName = "uav%d/mavros/global_position/global" %id                                               #TODO MICHAEL: Change GPS topic to yours here
        self.longitude = -1000
        self.latitude = -1000
        self.altitude = -1000
        self.sub = None

    def setSubscribe(self):
        if self.sub == None:         #topic below
            self.sub = rospy.Subscriber(self.GPSReceiverName, NavSatFix, self.GPSReceive)               #TODO MICHAEL: Change GPS topic to yours AND/OR here

    def GPSReceive(self,msg):
        self.longitude = msg.longitude
        self.latitude = msg.latitude
        self.altitude = msg.altitude
        #print "CRD: Drone %d received GPS data: location is now (%f|%f|%f) on %s" %(self.id, msg.longitude, msg.latitude, msg.altitude, self.GPSReceiverName)

    def getGPS(self):
        #print "Get location issued: location is now (%f|%f|%f)" %(self.longitude, self.latitude, self.altitude)
        return (self.longitude,self.latitude,self.altitude)

class DroneCommPublisher:
    def __init__(self):
        self.pub = rospy.Publisher("CommDetection", DroneComm, queue_size=10)

    def publishDronePair(self, d1, d2):
        msg = DroneComm()
        msg.d1 = d1
        msg.d2 = d2
        #print "Drone Comm Range Detector publishing a drone pair: (%d|%d)" %(d1, d2)
        self.pub.publish(msg)

class CommRangeDetector:
    def __init__(self, numDrones, commRange):
        # Calculate explorable area grid bounds in terms of GPS locations based on input exploration area size
        self.num = numDrones
        self.commRange = commRange
        self.droneGPSTriples = {}
        self.droneROSTopics = {}
        for i in range(numDrones):
            self.droneROSTopics[i+1] = DroneGPSSubscriber(i+1)
            self.droneGPSTriples[i+1] = (-1000,-1000,-1000)
            self.droneROSTopics[i+1].setSubscribe()
        self.commPublisher = DroneCommPublisher()
        self.TxPairs = []
    
    def ProcessDroneSetGPS(self):
        for i in range(self.num):
            self.droneROSTopics[i+1].setSubscribe()
            self.droneGPSTriples[i+1] = self.droneROSTopics[i+1].getGPS()
        for i in range(self.num):
            for j in range(self.num - i - 1):
                t1 = self.droneGPSTriples[i+1]
                t2 = self.droneGPSTriples[j+i+1+1]
                dist = Distance(t1,t2)
                print "CommRangeDetector: dist between %d/%d is %f" %(i+1, j+i+1+1,dist)
                if (dist < self.commRange):
                    self.TxPairs.append((i+1,j+i+1+1))
                    self.commPublisher.publishDronePair(i+1,j+i+1+1)
                    print "CommRangeDetector: Publishing drone pair %d/%d" %(i+1, j+i+1+1)

    def CheckTxCorrect(self, drones):
        print "CommModule: Confirming data TX is correct"
        if len(self.TxPairs) == 0:
            print "CommModule: No Tx are expected, nothing to confirm"
            return
        i = 0
        n = len(self.TxPairs)
        while i < n:
            (ind1,ind2) = self.TxPairs[i]
            d1 = drones[ind1]
            d2 = drones[ind2]
            print "CommModule: Communication pair status: (id %d = %d) | (id %d = %d)" %(ind1, d1.GetTxStatus(), ind2, d2.GetTxStatus())
            if (not d1.GetTxStatus()) and (not d2.GetTxStatus()):
                print "CommModule: Expected comm pair %d/%d report no TX in progress, checking if maps correct:" %(d1.GetID(),d2.GetID())
                if(d1.CheckIfMapsSame(d2)):
                    print "CommModule: drones %d/%d maps are identical, TX success" %(d1.GetID(),d2.GetID())
                else:
                    print "CommModule: drones %d/%d maps are not identical, TX FAILURE************************" %(d1.GetID(),d2.GetID())
                del self.TxPairs[i]
                n = n - 1
                i = i - 1
            i = i + 1
        time.sleep(2)










