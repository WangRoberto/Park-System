#!/usr/bin/env python
# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.dev/sumo
# Copyright (C) 2011-2024 German Aerospace Center (DLR) and others.
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0/
# This Source Code may also be made available under the following Secondary
# Licenses when the conditions for such availability set forth in the Eclipse
# Public License 2.0 are satisfied: GNU General Public License, version 2
# or later which is available at
# https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html
# SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later

# @file    runner.py
# @author  Roberto Wang
# @date    2024

from __future__ import absolute_import
from __future__ import print_function
from data.constants import DOUBLE_ROWS, SLOTS_PER_ROW, STANDARD_AUCTION_PRICE, PARKAREA_NAMES, RANDOM_POPULATION, CONSTANT_FREE_PARKS, INITIAL_CONSTANT_FREE_PARKS
from data.constants import STARTING_STOP, MAX_DURATION, SLOT_DURATION, TIME_INITIAL_CONSTANT_FREE_PARKS, REFRESH_FREE_PARKS, INITIAL_FREE_PARKS, NUMBER_GOOD_VEHICLES, NUMBER_BAD_VEHICLES
import os
import sys
import math
import optparse
# import xml.etree.ElementTree as ET
from lxml import etree

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please set environment variable 'SUMO_HOME'")

from sumolib import checkBinary
import traci

# Function to check if the vehicle's user has enough money to pay
def checkWallet(duration, idVehicle):
    extraCost = 0
    reviewStars = int(traci.vehicle.getParameter(idVehicle, "reviewStars"))
    cost = int(duration / SLOT_DURATION * STANDARD_AUCTION_PRICE)

    if reviewStars < 3:
        extraCost = int(cost * 25 / 100)

    currentCredit = int(traci.vehicle.getParameter(idVehicle, "wallet"))
    print("Credit:", str(currentCredit))
    newWallet = currentCredit - int(cost + extraCost)

    if newWallet < 0:
        print("Insufficient credit!")
        return 0

    return newWallet

# Function to change the vehicle's reputation
def systemCharge(idVehicle):
    reviewStars = int(traci.vehicle.getParameter(idVehicle, "reviewStars"))
    delay = int(traci.vehicle.getParameter(idVehicle, "delay"))

    if delay > 0:
        traci.vehicle.setParameter(idVehicle, "goodBehaviour", False)
        if reviewStars == 0:
            return
        warning = int(traci.vehicle.getParameter(idVehicle, "warning"))
        warning = warning + 1
        if warning == 5:
            reviewStars = reviewStars - 1
            traci.vehicle.setParameter(idVehicle, "reviewStars", reviewStars)
            traci.vehicle.setParameter(idVehicle, "warning", 0)
        else:
            traci.vehicle.setParameter(idVehicle, "warning", warning)
            traci.vehicle.setParameter(idVehicle, "civil", 0)
    else:
        traci.vehicle.setParameter(idVehicle, "goodBehaviour", True)
        if reviewStars == 5:
            return
        civil = int(traci.vehicle.getParameter(idVehicle, "civil"))
        civil = civil + 1
        if civil == 5:
            reviewStars = reviewStars + 1
            traci.vehicle.setParameter(idVehicle, "reviewStars", reviewStars)
            traci.vehicle.setParameter(idVehicle, "civil", 0)
        else:
            traci.vehicle.setParameter(idVehicle, "civil", civil)

# Function to tell the vehicle's that his next destination is "OutOfTown"
def goToNoSystemPark(idVehicle, duration, stopPos, numberCarsAboutToPark):
    # Opposite Direction (left)
    for row in range((math.ceil((NUMBER_GOOD_VEHICLES + NUMBER_BAD_VEHICLES) / 20) - 1), -1, -1):
        contPark1 = 0
        park1 = str("%s%s" % (PARKAREA_NAMES[2], row))
        if park1 in numberCarsAboutToPark:
            contPark1 = numberCarsAboutToPark[park1]

        # print("contPark1:", contPark1)
        if traci.parkingarea.getVehicleCount(park1) < SLOTS_PER_ROW and contPark1 < SLOTS_PER_ROW:
            print("Changing park...")
            traci.vehicle.replaceStop(idVehicle, stopPos, park1, flags=65, duration=duration,
                                      startPos=0.0)
            return str(park1)

        contPark2 = 0
        park2 = str("%s-%s" % (PARKAREA_NAMES[2], row))
        if park2 in numberCarsAboutToPark:
            contPark2 = numberCarsAboutToPark[park2]

        # print("contPark2:", contPark2)
        if traci.parkingarea.getVehicleCount(park2) < SLOTS_PER_ROW and contPark2 < SLOTS_PER_ROW:
            print("Changing park...")
            traci.vehicle.replaceStop(idVehicle, stopPos, park2, flags=65, duration=duration,
                                      startPos=0.0)
            return str(park2)

    return "End"

# Function that try to get a new reservation for the vehicle
def changeReservation(idVehicle, parkArea, duration, stopPos, reservations, freeParks):
    contStops = len(list(traci.vehicle.getStops(idVehicle, 0)))
    print("Stops:", traci.vehicle.getStops(idVehicle, 0))
    simulationTime = traci.simulation.getTime()
    # In case the vehicle does not have stops
    if contStops < 1:
        return "End"

    # Right Direction
    if PARKAREA_NAMES[0] in parkArea:
        parkAreaSuffix = PARKAREA_NAMES[0]
        parkAreaSuffix2 = PARKAREA_NAMES[1]
    if PARKAREA_NAMES[1] in parkArea:
        parkAreaSuffix = PARKAREA_NAMES[1]
        parkAreaSuffix2 = PARKAREA_NAMES[0]

    for row in range(DOUBLE_ROWS):
        contPark1 = 0
        park1 = str("%s%s" % (parkAreaSuffix, row))
        if park1 in reservations:
            contPark1 = reservations[park1]

        contFreeParks = INITIAL_FREE_PARKS
        if park1 in freeParks:
            contFreeParks = freeParks[park1]

        if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
            print("simulationTime:", simulationTime)
            contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS

        # contPark1 = int(traci.simulation.getParameter(("%s%s" % (parkAreaSuffix, row)), "parkingArea.occupancy"))
        print("contPark1:", contPark1)
        if contPark1 < (SLOTS_PER_ROW - contFreeParks):
            traci.vehicle.replaceStop(idVehicle, stopPos, park1, flags=65,
                                      duration=duration,
                                      startPos=0.0)

            return str(park1)

        contPark2 = 0
        park2 = str("%s-%s" % (parkAreaSuffix, row))
        if park2 in reservations:
            contPark2 = reservations[park2]

        contFreeParks = INITIAL_FREE_PARKS
        if park2 in freeParks:
            contFreeParks = freeParks[park2]

        if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
            print("simulationTime:", simulationTime)
            contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS


        # contPark2 = int(traci.simulation.getParameter(("%s-%s" % (parkAreaSuffix, row)), "parkingArea.occupancy"))
        print("contPark2:", contPark2)
        if contPark2 < (SLOTS_PER_ROW - contFreeParks):
            traci.vehicle.replaceStop(idVehicle, stopPos, park2, flags=65,
                                      duration=duration,
                                      startPos=0.0)
            return str(park2)

    parkAreaSuffix = parkAreaSuffix2

    for row in range(DOUBLE_ROWS):
        contPark1 = 0
        park1 = str("%s%s" % (parkAreaSuffix, row))
        if park1 in reservations:
            contPark1 = reservations[park1]

        contFreeParks = INITIAL_FREE_PARKS
        if park1 in freeParks:
            contFreeParks = freeParks[park1]

        if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
            print("simulationTime:", simulationTime)
            contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS

        # contPark1 = int(traci.simulation.getParameter(("%s%s" % (parkAreaSuffix, row)), "parkingArea.occupancy"))
        print("contPark1:", contPark1)
        if contPark1 < (SLOTS_PER_ROW - contFreeParks):
            traci.vehicle.replaceStop(idVehicle, stopPos, park1, flags=65,
                                      duration=duration,
                                      startPos=0.0)
            return str(park1)

        contPark2 = 0
        park2 = str("%s-%s" % (parkAreaSuffix, row))
        if park2 in reservations:
            contPark2 = reservations[park2]

        contFreeParks = INITIAL_FREE_PARKS
        if park2 in freeParks:
            contFreeParks = freeParks[park2]

        if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
            print("simulationTime:", simulationTime)
            contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS

        # contPark2 = int(traci.simulation.getParameter(("%s-%s" % (parkAreaSuffix, row)), "parkingArea.occupancy"))
        print("contPark2:", contPark2)
        if contPark2 < (SLOTS_PER_ROW - contFreeParks):
            traci.vehicle.replaceStop(idVehicle, stopPos, park2, flags=65,
                                      duration=duration,
                                      startPos=0.0)
            return str(park2)

    return "End"

    #parkingareaIdList = list(traci.parkingarea.getIDList())

def goToFreePark(idVehicle, parkArea, duration, stopPos, reservations, freeParks):
    contStops = len(list(traci.vehicle.getStops(idVehicle, 0)))
    print("Stops:", traci.vehicle.getStops(idVehicle, 0))
    simulationTime = traci.simulation.getTime()
    # In case the vehicle does not have stops
    if contStops < 1:
        return "End"

    # Right Direction
    if PARKAREA_NAMES[0] in parkArea:
        parkAreaSuffix = PARKAREA_NAMES[0]
        parkAreaSuffix2 = PARKAREA_NAMES[1]
    if PARKAREA_NAMES[1] in parkArea:
        parkAreaSuffix = PARKAREA_NAMES[1]
        parkAreaSuffix2 = PARKAREA_NAMES[0]

    for row in range(DOUBLE_ROWS):
        contPark1 = 0
        park1 = str("%s%s" % (parkAreaSuffix, row))
        if park1 in reservations:
            contPark1 = reservations[park1]

        contFreeParks = INITIAL_FREE_PARKS
        if park1 in freeParks:
            contFreeParks = freeParks[park1]

        if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
            print("simulationTime:", simulationTime)
            contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS

        # contPark1 = int(traci.simulation.getParameter(("%s%s" % (parkAreaSuffix, row)), "parkingArea.occupancy"))
        print("contPark1:", contPark1)
        if contFreeParks and (contPark1 + contFreeParks < SLOTS_PER_ROW) and  int(traci.parkingarea.getVehicleCount(park1)) < (SLOTS_PER_ROW):
            traci.vehicle.replaceStop(idVehicle, stopPos, park1, flags=65,
                                      duration=duration,
                                      startPos=0.0)

            return str(park1)

        contPark2 = 0
        park2 = str("%s-%s" % (parkAreaSuffix, row))
        if park2 in reservations:
            contPark2 = reservations[park2]

        contFreeParks = INITIAL_FREE_PARKS
        if park2 in freeParks:
            contFreeParks = freeParks[park2]

        if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
            print("simulationTime:", simulationTime)
            contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS


        # contPark2 = int(traci.simulation.getParameter(("%s-%s" % (parkAreaSuffix, row)), "parkingArea.occupancy"))
        print("contPark2:", contPark2)
        if contFreeParks and (contPark2 + contFreeParks < SLOTS_PER_ROW)  and  int(traci.parkingarea.getVehicleCount(park2)) < (SLOTS_PER_ROW):
            traci.vehicle.replaceStop(idVehicle, stopPos, park2, flags=65,
                                      duration=duration,
                                      startPos=0.0)
            return str(park2)

    parkAreaSuffix = parkAreaSuffix2

    for row in range(DOUBLE_ROWS):
        contPark1 = 0
        park1 = str("%s%s" % (parkAreaSuffix, row))
        if park1 in reservations:
            contPark1 = reservations[park1]

        contFreeParks = INITIAL_FREE_PARKS
        if park1 in freeParks:
            contFreeParks = freeParks[park1]

        if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
            print("simulationTime:", simulationTime)
            contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS

        # contPark1 = int(traci.simulation.getParameter(("%s%s" % (parkAreaSuffix, row)), "parkingArea.occupancy"))
        print("contPark1:", contPark1)
        if contFreeParks and (contPark1 + contFreeParks < SLOTS_PER_ROW) and  int(traci.parkingarea.getVehicleCount(park1)) < (SLOTS_PER_ROW):
            traci.vehicle.replaceStop(idVehicle, stopPos, park1, flags=65,
                                      duration=duration,
                                      startPos=0.0)
            return str(park1)

        contPark2 = 0
        park2 = str("%s-%s" % (parkAreaSuffix, row))
        if park2 in reservations:
            contPark2 = reservations[park2]

        contFreeParks = INITIAL_FREE_PARKS
        if park2 in freeParks:
            contFreeParks = freeParks[park2]

        if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
            print("simulationTime:", simulationTime)
            contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS

        # contPark2 = int(traci.simulation.getParameter(("%s-%s" % (parkAreaSuffix, row)), "parkingArea.occupancy"))
        print("contPark2:", contPark2)
        if contFreeParks and (contPark2 + contFreeParks < SLOTS_PER_ROW)  and  int(traci.parkingarea.getVehicleCount(park2)) < (SLOTS_PER_ROW):
            traci.vehicle.replaceStop(idVehicle, stopPos, park2, flags=65,
                                      duration=duration,
                                      startPos=0.0)
            return str(park2)

    return "End"

    #parkingareaIdList = list(traci.parkingarea.getIDList())

def changePark(idVehicle, parkArea, duration, stopPos, reservations, freeParks):
    contStops = len(list(traci.vehicle.getStops(idVehicle, 0)))
    print("Stops:", traci.vehicle.getStops(idVehicle, 0))
    simulationTime = traci.simulation.getTime()
    # In case the vehicle does not have stops
    if contStops < 1:
        return "End"

    # Right Direction
    if PARKAREA_NAMES[0] in parkArea:
        parkAreaSuffix = PARKAREA_NAMES[0]
        parkAreaSuffix2 = PARKAREA_NAMES[1]
    if PARKAREA_NAMES[1] in parkArea:
        parkAreaSuffix = PARKAREA_NAMES[1]
        parkAreaSuffix2 = PARKAREA_NAMES[0]

    for row in range(DOUBLE_ROWS):
        park1 = str("%s%s" % (parkAreaSuffix, row))

        contFreeParks = INITIAL_FREE_PARKS
        if park1 in freeParks:
            contFreeParks = freeParks[park1]

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS
        else:
            if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
                print("simulationTime:", simulationTime)
                contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if contFreeParks > 0 and int(traci.parkingarea.getVehicleCount(park1)) < (SLOTS_PER_ROW - contFreeParks):
            traci.vehicle.replaceStop(idVehicle, stopPos, park1, flags=65,
                                      duration=duration,
                                      startPos=0.0)

            return str(park1)

        park2 = str("%s-%s" % (parkAreaSuffix, row))

        contFreeParks = INITIAL_FREE_PARKS
        if park2 in freeParks:
            contFreeParks = freeParks[park2]

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS
        else:
            if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
                print("simulationTime:", simulationTime)
                contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if contFreeParks > 0 and int(traci.parkingarea.getVehicleCount(park2)) < (SLOTS_PER_ROW - contFreeParks):
            traci.vehicle.replaceStop(idVehicle, stopPos, park2, flags=65,
                                      duration=duration,
                                      startPos=0.0)
            return str(park2)

    parkAreaSuffix = parkAreaSuffix2

    for row in range(DOUBLE_ROWS):

        park1 = str("%s%s" % (parkAreaSuffix, row))

        contFreeParks = INITIAL_FREE_PARKS
        if park1 in freeParks:
            contFreeParks = freeParks[park1]

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS
        else:
            if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
                print("simulationTime:", simulationTime)
                contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if contFreeParks > 0 and int(traci.parkingarea.getVehicleCount(park1)) < (SLOTS_PER_ROW - contFreeParks):
            traci.vehicle.replaceStop(idVehicle, stopPos, park1, flags=65,
                                      duration=duration,
                                      startPos=0.0)
            return str(park1)

        park2 = str("%s-%s" % (parkAreaSuffix, row))

        contFreeParks = INITIAL_FREE_PARKS
        if park2 in freeParks:
            contFreeParks = freeParks[park2]

        if CONSTANT_FREE_PARKS != -1:
            contFreeParks = CONSTANT_FREE_PARKS
        else:
            if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
                print("simulationTime:", simulationTime)
                contFreeParks = INITIAL_CONSTANT_FREE_PARKS

        if contFreeParks > 0 and int(traci.parkingarea.getVehicleCount(park2)) < (SLOTS_PER_ROW - contFreeParks):
            traci.vehicle.replaceStop(idVehicle, stopPos, park2, flags=65,
                                      duration=duration,
                                      startPos=0.0)
            return str(park2)

    return "End"

def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandLine version of sumo")
    options, args = optParser.parse_args()
    return options


def run():
    xmlDocument = etree.parse(("data/park_demand%02i.rou.xml") % RANDOM_POPULATION)
    root = xmlDocument.getroot()
    maxTrips = len(root.xpath("trip")) # Maximum number of vehicles

    stopPosVehicle = {} # Keeps track of which stop you reached
    problem = False # Check if the number the reservations is equal to the number of vehicles in the scenario

    # Load all ID vehicle in a list
    vehicleIdListXML = []
    for posTrip in range(maxTrips):
        vehicleIdListXML.append(root[posTrip].attrib.get("id"))

    print("Number of vehicle:", str(maxTrips))
    print("List of vehicles in XML file:", vehicleIdListXML)

    contNoPark = 0 # Number of times the vehicles don't park
    contSamePark = 0 # Number of times a vehicles that his current stop is equal to his next stop
    contEndPark = 0 # Number of times the vehicles end a park
    contBadBehaviourVehicles = 0 # Number of times the vehicles don't respect the reservations
    newWallet = 0  # Variable that change value if the user has enough money to pay to system
    simulationTime = 0
    unsatisfiedReservationsCont = 0
    noFoundReservationCont = 0

    contTemp = 0
    vehiclesDoNotPark = []

    reservationVehicles = []  # Vehicles that have a reservation
    paidVehicle = []  # Vehicles that paid the park
    waitingVehicles = []  # Vehicles that don't park
    vehiclesChangeRoute = []  # All vehicles that changed at least one time the route

    freeParks = {} # Number of free park that parkarea must have
    badBehaviour = {} # Number of times someone had a bad behaviour for each park
    reservations = {} # keeps track of the number of reservations for each park
    vehicleLastPark = {} # Keeps track of the last park of vehicles
    vehicleParkDuration = {}  # Keeps track of the last park of vehicles
    leavingAreaParkVehicle = {}

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        # 1 loading vehicles
        runningVehicleIdList = list(traci.vehicle.getIDList())
        print("------------------------ Still active vehicle:", str(len(runningVehicleIdList)),
              "------------------------")

        # 2 Reset free parks after 8 hours (800 time steps)
        simulationTime = traci.simulation.getTime()
        print("Time:", simulationTime)
        if simulationTime % (MAX_DURATION * SLOT_DURATION / REFRESH_FREE_PARKS) == 0:
            badBehaviour.clear()
            freeParks.clear()

        # 3 Remove all ending park vehicles' reservations
        leavingAreaParkVehicle.clear()
        endStopVehicles = list(traci.simulation.getParkingEndingVehiclesIDList())
        print("List of vehicles that are leaving their park:", endStopVehicles)
        for endStopVehicle in endStopVehicles:

            if endStopVehicle in reservationVehicles:
                reservations.update(
                    {vehicleLastPark[endStopVehicle]: reservations[vehicleLastPark[endStopVehicle]] - 1})
                contEndPark = contEndPark + 1
                if reservations[vehicleLastPark[endStopVehicle]] < 0:
                    exit()
                reservationVehicles.remove(endStopVehicle)

            posVehicle = vehicleIdListXML.index(endStopVehicle)
            stopPosOffset = stopPosVehicle[endStopVehicle]
            parkArea = root[posVehicle][STARTING_STOP + stopPosOffset].attrib.get("parkingArea")
            vehicleLastPark.update({endStopVehicle: parkArea})
            oldParkArea = root[posVehicle][STARTING_STOP + stopPosOffset - 1].attrib.get("parkingArea")

            # 4 Counting number of vehicles that are leaving a park
            if oldParkArea not in leavingAreaParkVehicle:
                leavingAreaParkVehicle.update({oldParkArea: 1})
            else:
                leavingAreaParkVehicle.update({oldParkArea: leavingAreaParkVehicle[oldParkArea] + 1})

        # Iterate only vehicle that are running in this scenario
        for idVehicle in runningVehicleIdList:

            problem = False

            print("Number of reservations for each park reservation:", reservations)
            print("List of vehicles with reservation:", reservationVehicles)
            print("Number of vehicles with reservation:", len(reservationVehicles))

            posVehicle = vehicleIdListXML.index(idVehicle) # Vehicle's position in XML file

            if idVehicle not in stopPosVehicle:
                stopPosVehicle.update({idVehicle: 0})

            stopPosOffset = int(stopPosVehicle[idVehicle])

            print("Vehicle position in XML:", str(posVehicle))

            parkArea = root[posVehicle][STARTING_STOP + stopPosOffset].attrib.get("parkingArea")

            if idVehicle not in vehicleLastPark:
                vehicleLastPark.update({idVehicle: parkArea})

            print("Id vehicle:", str(idVehicle))
            print("Current Parkingarea:", str(vehicleLastPark[idVehicle]))
            print("Next Parkingarea:", str(parkArea))
            print("StopPosOffeset:", str(stopPosOffset))

            contStops = len(list(traci.vehicle.getStops(idVehicle, 0)))
            print("Number of stops:", contStops)

            isStoppedParking = traci.vehicle.isStoppedParking(idVehicle)
            print("Is the vehicle stopped?:", str(isStoppedParking))

            duration = int(root[posVehicle][STARTING_STOP + stopPosOffset].attrib.get("duration"))
            print("Park's duration:", str(duration))

            print("FreeParks:", freeParks)

            # Vehicle is not stopped
            if (not isStoppedParking and contStops > 0):

                # After parking
                if idVehicle in paidVehicle:
                    paidVehicle.remove(idVehicle)

                if idVehicle not in reservationVehicles:
                    if PARKAREA_NAMES[2] not in parkArea:
                        # Check if the vehicle has the requirements to park in "Town (ParkArea and ParkAreaAlternative)"
                        # In case the vehicle does not have the requirements, it must go to "ParkAreaOutOfTown"
                        reviewStars = int(traci.vehicle.getParameter(idVehicle, "reviewStars"))
                        print("Review Stars:", reviewStars)
                        goodBehaviour = traci.vehicle.getParameter(idVehicle, "goodBehaviour")
                        print("goodBehaviour:", goodBehaviour)
                        if reviewStars < 3 and goodBehaviour == "False":
                            #contBadBehaviourVehicles = contBadBehaviourVehicles + 1
                            #newParkArea = changeRoute(idVehicle, parkArea, duration, 0, reservations, freeParks)
                            newParkArea = goToNoSystemPark(idVehicle, duration, 0, reservations)
                            if newParkArea == "End":
                                print("------------------------")
                                continue
                            print("Stops:", traci.vehicle.getStops(idVehicle, 0))
                            print("New Park Area:", newParkArea)
                            traci.vehicle.setParameter(idVehicle, "goodBehaviour", True)
                            root[posVehicle][STARTING_STOP + stopPosOffset].set("parkingArea", newParkArea)
                            vehicleLastPark.update({idVehicle: newParkArea})
                            parkArea = newParkArea

                        # Check if the user has enough money to pay to the system
                        # If the money are insufficient, the vehicles must go to "ParkAreaOutOfTown"
                        if PARKAREA_NAMES[2] not in parkArea:
                            newWallet = checkWallet(duration, idVehicle)
                            if not newWallet:
                                newParkArea = goToNoSystemPark(idVehicle, duration, 0, reservations)
                                print("Stops:", traci.vehicle.getStops(idVehicle, 0))
                                print("New Park Area:", newParkArea)
                                if newParkArea == "End":
                                    print("------------------------")
                                    continue
                                root[posVehicle][STARTING_STOP + stopPosOffset].set("parkingArea", newParkArea)
                                vehicleLastPark.update({idVehicle: newParkArea})
                                parkArea = newParkArea

                # Set if is dynamic o static free park system
                # There are no free parks in "ParkAreaOutOfTown"
                contFreeParks = INITIAL_FREE_PARKS
                if PARKAREA_NAMES[2] not in parkArea:
                    if parkArea in freeParks:
                        contFreeParks = freeParks[parkArea]

                    if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
                        contFreeParks = INITIAL_CONSTANT_FREE_PARKS

                    if CONSTANT_FREE_PARKS != -1:
                        contFreeParks = CONSTANT_FREE_PARKS

                else:
                    contFreeParks = 0

                if idVehicle not in reservationVehicles:
                    reservationVehicles.append(idVehicle)
                    if parkArea not in reservations:
                        reservations.update({parkArea: 1})
                    else:
                        reservations.update({parkArea: reservations[parkArea] + 1})

                # Optional
                if (sum(reservations.values()) != len(runningVehicleIdList)):
                    problem = True

                contEndingPark = 0
                if parkArea in leavingAreaParkVehicle:
                    contEndingPark = leavingAreaParkVehicle[parkArea]

                print("contFreeParks:", contFreeParks)
                print("Soglia:", (SLOTS_PER_ROW - contFreeParks))

                # These are not applied to "ParkAreaOutOfTown"
                # Check if its parking area is full
                if (reservations[parkArea] > (SLOTS_PER_ROW - contFreeParks)):

                    if contEndingPark > 0:
                        leavingAreaParkVehicle.update({parkArea: leavingAreaParkVehicle[parkArea] - 1})
                        continue

                    if (PARKAREA_NAMES[2] not in parkArea):
                        unsatisfiedReservationsCont = unsatisfiedReservationsCont + 1

                        print("Number of reservations in that ParkArea:", str(reservations[parkArea]))
                        print("Waiting...")
                        # avoid loop if you are looking for a new park with available reservations
                        # newParkArea = goToNoSystemPark(idVehicle, duration, 0, reservations)
                        #newParkArea = str("%s%s" % (PARKAREA_NAMES[2], DOUBLE_ROWS * 2 - 1))
                        #newParkArea = changeRoute(idVehicle, newParkArea, duration, 0, reservations, freeParks)
                        newParkArea = changeReservation(idVehicle, parkArea, duration, 0, reservations, freeParks)
                        if newParkArea == "End":
                            noFoundReservationCont = noFoundReservationCont + 1
                            newParkArea = goToNoSystemPark(idVehicle, duration, 0, reservations)
                    else:
                        newParkArea = goToNoSystemPark(idVehicle, duration, 0, reservations)

                    print("Stops:", traci.vehicle.getStops(idVehicle, 0))
                    print("New Park Area:", newParkArea)

                    if newParkArea == "End":
                        print("------------------------")
                        continue
                    root[posVehicle][STARTING_STOP + stopPosOffset].set("parkingArea", newParkArea)
                    vehicleLastPark.update({idVehicle: newParkArea})

                    reservations.update({parkArea: reservations[parkArea] - 1})
                    if newParkArea not in reservations:
                        reservations.update({newParkArea: 1})
                    else:
                        reservations.update({newParkArea: reservations[newParkArea] + 1})

                    print("------------------------")
                    parkArea = newParkArea

                    contFreeParks = INITIAL_FREE_PARKS
                    if PARKAREA_NAMES[2] not in parkArea:
                        if parkArea in freeParks:
                            contFreeParks = freeParks[parkArea]

                        if simulationTime < TIME_INITIAL_CONSTANT_FREE_PARKS:
                            contFreeParks = INITIAL_CONSTANT_FREE_PARKS

                        if CONSTANT_FREE_PARKS != -1:
                            contFreeParks = CONSTANT_FREE_PARKS

                    else:
                        contFreeParks = 0

                contEndingPark = 0
                if parkArea in leavingAreaParkVehicle:
                    contEndingPark = leavingAreaParkVehicle[parkArea]

                if (reservations[parkArea] <= (SLOTS_PER_ROW - contFreeParks)) and traci.parkingarea.getVehicleCount(parkArea) == (SLOTS_PER_ROW):

                    if contEndingPark > 0:
                        leavingAreaParkVehicle.update({parkArea: leavingAreaParkVehicle[parkArea] - 1})
                        continue

                    if (PARKAREA_NAMES[2] not in parkArea):
                        # It doesn't keep track of number of times of a vehicles does not park/vehicles change its route if that parkarea is "ParkAreaOutOfTown"
                        if idVehicle not in waitingVehicles:
                            contNoPark = contNoPark + 1
                            waitingVehicles.append(idVehicle)

                        if idVehicle not in vehiclesChangeRoute:
                            vehiclesChangeRoute.append(idVehicle)

                        print("Number of vehicles in that ParkArea:",
                              str(traci.parkingarea.getVehicleCount(parkArea)))
                        print("Waiting...")

                        newParkArea = goToFreePark(idVehicle, parkArea, duration, 0, reservations, freeParks)
                        if newParkArea == "End":
                            noFoundReservationCont = noFoundReservationCont + 1
                            newParkArea = goToNoSystemPark(idVehicle, duration, 0, reservations)
                    else:
                        newParkArea = goToNoSystemPark(idVehicle, duration, 0, reservations)

                    # avoid loop if you are looking for a new park with available reservations
                    # newParkArea = str("%s%s" % (PARKAREA_NAMES[2], DOUBLE_ROWS * 2 - 1))
                    # newParkArea = changeRoute(idVehicle, newParkArea, duration, 0, reservations, freeParks)

                    #newParkArea = changePark(idVehicle, parkArea, duration, 0, reservations, freeParks)

                    print("Stops:", traci.vehicle.getStops(idVehicle, 0))
                    print("New Park Area:", newParkArea)
                    if newParkArea == "End":
                        print("------------------------")
                        continue
                    root[posVehicle][STARTING_STOP + stopPosOffset].set("parkingArea", newParkArea)
                    vehicleLastPark.update({idVehicle: newParkArea})

                    reservations.update({parkArea: reservations[parkArea] - 1})
                    if newParkArea not in reservations:
                        reservations.update({newParkArea: 1})
                    else:
                        reservations.update({newParkArea: reservations[newParkArea] + 1})


            # Update the last list of vehicles that are ending their park
            #endStopVehiclesBefore = endStopVehicles

            # If the vechicle is stopped
            if (isStoppedParking):
                stops = list(traci.vehicle.getStops(idVehicle, 0))
                delay = int(traci.vehicle.getParameter(idVehicle, "delay"))

                #In case if the park is "ParkAreaOutOfTown", we don't need to track the ending time of reservation
                if PARKAREA_NAMES[2] not in vehicleLastPark[idVehicle]:
                    currentStop = stops[0]
                    # Check only bad behaviour car
                    if delay > 0:
                        simulationTime = int(traci.simulation.getTime())
                        print("Simulation time:", simulationTime)
                        # If the current duration is negative that means someone is blocking the park
                        if currentStop.duration > 0:
                            if idVehicle in vehicleParkDuration:
                                if simulationTime == int(vehicleParkDuration[idVehicle]):
                                    if idVehicle in reservationVehicles:
                                        reservationVehicles.remove(idVehicle)
                                        reservations.update({vehicleLastPark[idVehicle]: reservations[vehicleLastPark[idVehicle]] - 1})
                                        contBadBehaviourVehicles = contBadBehaviourVehicles + 1

                                        if vehicleLastPark[idVehicle] not in freeParks:
                                            freeParks.update({vehicleLastPark[idVehicle]: 1})
                                        elif freeParks[vehicleLastPark[idVehicle]] < INITIAL_CONSTANT_FREE_PARKS:
                                                freeParks.update({vehicleLastPark[idVehicle]: freeParks[vehicleLastPark[
                                                    idVehicle]] + 1})

                                        vehicleLastPark.update({idVehicle: parkArea})
                                        vehicleParkDuration.pop(idVehicle)

                if idVehicle in waitingVehicles:
                    waitingVehicles.remove(idVehicle)

                if idVehicle not in paidVehicle:
                    paidVehicle.append(idVehicle)
                    contStops = len(stops)
                    print("Stops:", traci.vehicle.getStops(idVehicle, 0))

                    # Vehicle doesn't pay if it doesn't park in "Town (ParkArea and ParkAreaAlternative)"
                    if PARKAREA_NAMES[2] not in parkArea:

                        leavingTime = simulationTime + (duration - delay)
                        print("When it must end the park at:", leavingTime)
                        vehicleParkDuration.update({idVehicle: leavingTime})
                        print("List of vehicles' ending time park:", vehicleParkDuration)

                        traci.vehicle.setParameter(idVehicle, "wallet", newWallet)
                        systemCharge(idVehicle)

                    if contStops > 1:
                        # Update which stop the vehicle is at
                        stopPosVehicle.update({idVehicle: stopPosVehicle[idVehicle] + 1})
                        print("Where:", stopPosVehicle[idVehicle])

                print("------------------------")
                continue

            print("------------------------")

        print("------------------------ Still active vehicle:", str(len(runningVehicleIdList)),
              "------------------------")

        print("Reservation Total:", sum(reservations.values()))

    if problem == True:
        print("Reservation:", reservations)
        print("PROBLEM!")

    print("Which population:", RANDOM_POPULATION)
    if CONSTANT_FREE_PARKS == -1:
        print("Free park: ", INITIAL_FREE_PARKS, " - ", INITIAL_CONSTANT_FREE_PARKS)
        print("Refresh for each", (MAX_DURATION * SLOT_DURATION / REFRESH_FREE_PARKS), "time step")
    else:
        print("Free park:", CONSTANT_FREE_PARKS)
    print("How many times a vehicle change its route?", str(len(vehiclesChangeRoute)))
    print("How many times a vehicle does not park? (when there are no more car park)", str(contNoPark))
    print("How many times a vehicle change its route? (when there are no more reservations)", str(unsatisfiedReservationsCont))
    print("How many times a vehicle could not book a reservation?",
          str(noFoundReservationCont))
    print("End park(good behaviour):", contEndPark)
    # print("Reservation:", reservations)
    # print("contSamePark:", contSamePark)
    print("End park(bad behaviour):", contBadBehaviourVehicles)
    print("Total end park:", contEndPark + contBadBehaviourVehicles)
    print("Finish time step:", simulationTime)
    print("Reservation:", reservations)

    print("contTemp:", contTemp)

    print("Vehicles that not park during sleep time:", len(vehiclesDoNotPark))

    with open("output.txt", "a") as f:

        print("Which population:", RANDOM_POPULATION, file=f)
        if CONSTANT_FREE_PARKS == -1:
            print("Free park: ", INITIAL_FREE_PARKS, " - ", INITIAL_CONSTANT_FREE_PARKS, file=f)
            print("Refresh for each", (MAX_DURATION * SLOT_DURATION / REFRESH_FREE_PARKS), "time step", file=f)
        else:
            print("Free park:", CONSTANT_FREE_PARKS, file=f)
        print("How many times a vehicle change its route? ", str(len(vehiclesChangeRoute)), file=f)
        print("How many times a vehicle does not park? (when there are no more car park)", str(contNoPark), file=f)
        print("How many times a vehicle change its route? (when there are no more reservations)",
              str(unsatisfiedReservationsCont), file=f)
        print("How many times a vehicle could not book a reservation?",
              str(noFoundReservationCont), file=f)
        print("End park(good behaviour):", contEndPark, file=f)
        # print("Reservation:", reservations, file=f)
        # print("contSamePark:", contSamePark, file=f)
        print("End park(bad behaviour):", contBadBehaviourVehicles, file=f)
        print("Total end park:", contEndPark + contBadBehaviourVehicles, file=f)
        print("Finish time step:", simulationTime, file=f)
        print("Reservation:", reservations, file=f)
        print("------------------------------------------------------------------------", file=f)

    sys.stdout.flush()


# Start sumo and TraCI with the same port
if __name__ == "__main__":
    options = get_options()

    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')
    print(sumoBinary)
    traci.start([sumoBinary, "-c", ("data/park%02i.sumocfg") % RANDOM_POPULATION])
    run()