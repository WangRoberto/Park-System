#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Eclipse SUMO, Simulation of Urban MObility; see https://eclipse.dev/sumo
# Copyright (C) 2008-2024 German Aerospace Center (DLR) and others.
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# https://www.eclipse.org/legal/epl-2.0/
# This Source Code may also be made available under the following Secondary
# Licenses when the conditions for such availability set forth in the Eclipse
# Public License 2.0 are satisfied: GNU General Public License, version 2
# or later which is available at
# https://www.gnu.org/licenses/old-licenses/gpl-2.0-standalone.html
# SPDX-License-Identifier: EPL-2.0 OR GPL-2.0-or-later

# @file    buildScenario.py
# @author  Roberto Wang
# @date    2024

"""
Create the XML input files for the generation of the SUMO network
of the CityMobil parking lot.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import math
import random
import subprocess
import os
import sys

from constants import PREFIX, DOUBLE_ROWS, ROW_DIST, SLOTS_PER_ROW, SLOT_WIDTH, PARKAREA_NAMES, RANDOM_POPULATION
from constants import MIN_DURATION, MAX_DURATION, SLOT_DURATION, NUMBER_BAD_VEHICLES, NUMBER_GOOD_VEHICLES

sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import sumolib  # noqa

random.seed(RANDOM_POPULATION)
# network building
nodes = open("%s.nod.xml" % PREFIX, "w")
sumolib.xml.writeHeader(nodes, root="nodes")
edges = open("%s.edg.xml" % PREFIX, "w")
sumolib.xml.writeHeader(edges, root="edges")

# Road construction
# This road leads to the "ParkArea" car park
nodeID = "main0"
print('<node id="in" x="-100" y="0"/>', file=nodes)
print('<edge id="mainin" from="in" to="%s" numLanes="3"/>' % nodeID, file=edges)
for row in range(DOUBLE_ROWS):
    nextNodeID = "main%s" % row
    x = row * ROW_DIST
    print('<node id="%s" x="%s" y="0"/>' % (nextNodeID, x), file=nodes)
    if row > 0:
        print('<edge id="main%sto%s" from="%s" to="%s" numLanes="3"/>' %
              (row - 1, row, nodeID, nextNodeID), file=edges)
    nodeID = nextNodeID

# This road leads to the "ParkAreaAlternative" car park
for row in range(DOUBLE_ROWS):
    nextNodeID = "mainAlternative%s" % row
    x = row * ROW_DIST + 100
    print('<node id="%s" x="%s" y="0"/>' % (nextNodeID, x), file=nodes)
    if row > 0:
        print('<edge id="mainAlternative%sto%s" from="%s" to="%s" numLanes="3"/>' %
              (row - 1, row, nodeID, nextNodeID), file=edges)
    nodeID = nextNodeID

howManyRows = math.ceil((NUMBER_GOOD_VEHICLES + NUMBER_BAD_VEHICLES) / 20)
offset = 21

if howManyRows < 4:
    howManyRows = 4
else:
    offset = offset - 14.5 * (howManyRows - 4)

# This road leads to the "ParkOutOfTown" car park
for row in range(howManyRows):
    nextNodeID = "mainOutOfTown%s" % row
    x = row * ROW_DIST + offset
    print('<node id="%s" x="%s" y="-150"/>' % (nextNodeID, x), file=nodes)
    if row > 0:
        print('<edge id="mainOutOfTown%sto%s" from="%s" to="%s" numLanes="3"/>' %
              (row, row - 1, nextNodeID, nodeID), file=edges)
    nodeID = nextNodeID

# Another roads that connect the various car parks
print('<edge id="mainmid" from="main1" to="mainAlternative0" numLanes="3"/>', file=edges)
print('<node id="out" x="225" y="0"/>', file=nodes)
print('<edge id="mainout" from="mainAlternative%s" to="out" numLanes="3"/>' % (DOUBLE_ROWS - 1), file=edges)

print('<node id="backin" x="-100" y="-150"/>', file=nodes)
print('<node id="backout" x="225" y="-150"/>', file=nodes)

print('<edge id="inOutOfTown" from="backout" to="mainOutOfTown%s" numLanes="3"/>' % (DOUBLE_ROWS * 2 - 1), file=edges)
print('<edge id="outOutOfTown" from="mainOutOfTown0" to="backin" numLanes="3"/>', file=edges)

print('<edge id="turnbackout" from="out" to="backout" numLanes="3"/>', file=edges)
print('<edge id="turnbackin" from="backin" to="in" numLanes="3"/>', file=edges)

# Roads in the parking area to change lane
y = (SLOTS_PER_ROW + 3) * SLOT_WIDTH
print('<node id="cyber" x="-100" y="%s"/>' % y, file=nodes)

# ParkArea
for row in range(DOUBLE_ROWS):
    nodeID = "cyber%s" % row
    x = row * ROW_DIST
    print('<node id="%s" x="%s" y="%s"/>' % (nodeID, x, y), file=nodes)
    if row > 0:
        edgeID = "cyber%sto%s" % (row - 1, row)
        print("""<edge id="%s" from="cyber%s" to="cyber%s" numLanes="2" spreadType="center">
            <lane index="0"/>
            <lane index="1"/>
        </edge>""" % (edgeID, row - 1, row), file=edges)
        print("""<edge id="-%s" from="cyber%s" to="cyber%s" numLanes="2" spreadType="center">
            <lane index="0"/>
            <lane index="1"/>
        </edge>""" % (edgeID, row, row - 1), file=edges)

y = (SLOTS_PER_ROW + 3) * SLOT_WIDTH
print('<node id="cyberAlternative" x="-500" y="%s"/>' % y, file=nodes)

# ParkAreaAlternative
for row in range(DOUBLE_ROWS):
    nodeID = "cyberAlternative%s" % row
    x = row * ROW_DIST + 100
    print('<node id="%s" x="%s" y="%s"/>' % (nodeID, x, y), file=nodes)
    if row > 0:
        edgeID = "cyberAlternative%sto%s" % (row - 1, row)
        print("""<edge id="%s" from="cyberAlternative%s" to="cyberAlternative%s" numLanes="2" spreadType="center">
            <lane index="0"/>
            <lane index="1"/>
        </edge>""" % (edgeID, row - 1, row), file=edges)
        print("""<edge id="-%s" from="cyberAlternative%s" to="cyberAlternative%s" numLanes="2" spreadType="center">
            <lane index="0"/>
            <lane index="1"/>
        </edge>""" % (edgeID, row, row - 1), file=edges)

y = (SLOTS_PER_ROW + 3) * SLOT_WIDTH - 150
print('<node id="cyberOutOfTown" x="-500" y="%s"/>' % y, file=nodes)

# ParkAreaOutOfTown
for row in range(howManyRows):
    nodeID = "cyberOutOfTown%s" % row
    x = row * ROW_DIST + offset
    print('<node id="%s" x="%s" y="%s"/>' % (nodeID, x, y), file=nodes)
    if row > 0:
        edgeID = "cyberOutOfTown%sto%s" % (row - 1, row)
        print("""<edge id="%s" from="cyberOutOfTown%s" to="cyberOutOfTown%s" numLanes="2" spreadType="center">
            <lane index="0"/>
            <lane index="1"/>
        </edge>""" % (edgeID, row - 1, row), file=edges)
        print("""<edge id="-%s" from="cyberOutOfTown%s" to="cyberOutOfTown%s" numLanes="2" spreadType="center">
            <lane index="0"/>
            <lane index="1"/>
        </edge>""" % (edgeID, row, row - 1), file=edges)

# Roads in the parking area
for row in range(DOUBLE_ROWS):

    # ParkArea
    print("""<edge id="road%s" from="main%s" to="cyber%s" numLanes="3">
        <lane index="0"/>
        <lane index="1"/>
        <lane index="2"/>
    </edge>""" % (row, row, row), file=edges)
    print("""<edge id="-road%s" from="cyber%s" to="main%s" numLanes="3">
        <lane index="0"/>
        <lane index="1"/>
        <lane index="2"/>
    </edge>""" % (row, row, row), file=edges)

    # ParkAreaAlternative
    print("""<edge id="roadAlternative%s" from="mainAlternative%s" to="cyberAlternative%s" numLanes="3">
        <lane index="0"/>
        <lane index="1"/>
        <lane index="2"/>
    </edge>""" % (row, row, row), file=edges)
    print("""<edge id="-roadAlternative%s" from="cyberAlternative%s" to="mainAlternative%s" numLanes="3">
        <lane index="0"/>
        <lane index="1"/>
        <lane index="2"/>
    </edge>""" % (row, row, row), file=edges)

# ParkAreaOutOfTown
for row in range(howManyRows):
    print("""<edge id="roadOutOfTown%s" from="mainOutOfTown%s" to="cyberOutOfTown%s" numLanes="3">
        <lane index="0"/>
        <lane index="1"/>
        <lane index="2"/>
    </edge>""" % (row, row, row), file=edges)
    print("""<edge id="-roadOutOfTown%s" from="cyberOutOfTown%s" to="mainOutOfTown%s" numLanes="3">
        <lane index="0"/>
        <lane index="1"/>
        <lane index="2"/>
    </edge>""" % (row, row, row), file=edges)

print("</nodes>", file=nodes)
nodes.close()
print("</edges>", file=edges)
edges.close()

subprocess.call([sumolib.checkBinary('netconvert'),
                 '-n', '%s.nod.xml' % PREFIX,
                 '-e', '%s.edg.xml' % PREFIX,
                 '-o', '%s.net.xml' % PREFIX])

# Parking areas
stops = open("%s.add.xml" % PREFIX, "w")
sumolib.xml.writeHeader(stops, root="additional")

# ParkArea construction
for row in range(DOUBLE_ROWS):
    print("""    <parkingArea id="ParkArea%s" lane="road%s_1" roadsideCapacity="%s" angle="270" length="8"> 
    </parkingArea>
    <parkingArea id="ParkArea-%s" lane="-road%s_1" roadsideCapacity="%s" angle="270" length="8"> 
    </parkingArea>""" %
          (row, row, SLOTS_PER_ROW, row, row, SLOTS_PER_ROW), file=stops)

# ParkAreaAlternative construction
for row in range(DOUBLE_ROWS):
    print("""    <parkingArea id="ParkAreaAlternative%s" lane="roadAlternative%s_1" roadsideCapacity="%s" angle="270" length="8"> 
    </parkingArea>
    <parkingArea id="ParkAreaAlternative-%s" lane="-roadAlternative%s_1" roadsideCapacity="%s" angle="270" length="8"> 
    </parkingArea>""" %
          (row, row, SLOTS_PER_ROW, row, row, SLOTS_PER_ROW), file=stops)

# ParkAreaOutOfTown construction
for row in range(howManyRows):
    print("""    <parkingArea id="ParkAreaOutOfTown%s" lane="roadOutOfTown%s_1" roadsideCapacity="%s" angle="270" length="8"> 
    </parkingArea>
    <parkingArea id="ParkAreaOutOfTown-%s" lane="-roadOutOfTown%s_1" roadsideCapacity="%s" angle="270" length="8"> 
    </parkingArea>""" %
          (row, row, SLOTS_PER_ROW, row, row, SLOTS_PER_ROW), file=stops)

# Vehicle types
#   1. carB is for vehicle with bad behaviour
print(("""    <vType id="car" color="0.7,0.7,0.7"/> <vType id="carB" color="red"/>
"""), file=stops)

print("</additional>", file=stops)
stops.close()

departTime = 5

# Routes for vehicles
routes = open("%s_demand%02i.rou.xml" % (PREFIX, RANDOM_POPULATION), "w")
print("<routes>", file=routes)

#Number of stops
stops = 10

howManyStopsInADay = 5

tempContVehicle = DOUBLE_ROWS

if NUMBER_BAD_VEHICLES > NUMBER_GOOD_VEHICLES:
    exit()

contGoodVehicles = 0
contBadVehicles = 0

vehiclesProportion = int(NUMBER_GOOD_VEHICLES / NUMBER_BAD_VEHICLES)
lastDepart = 0
begin = 0
last = vehiclesProportion

while contBadVehicles < NUMBER_BAD_VEHICLES or contGoodVehicles < NUMBER_GOOD_VEHICLES:

    for v in range(SLOTS_PER_ROW):
        # Generation of vehicles with normal behaviour
        if contGoodVehicles < NUMBER_GOOD_VEHICLES:
            for idx in range(begin, last):

                contGoodVehicles = contGoodVehicles + 1
                if contGoodVehicles > NUMBER_GOOD_VEHICLES:
                    break
                print("""    <trip id="v%s.%s" type="car" depart="%s" from="mainin" to="road%s">
                <param key="warning" value="0" /> 
                <param key="civil" value="0" /> 
                <param key="reviewStars" value="3" /> 
                <param key="wallet" value="100" /> 
                <param key="goodBehaviour" value="True" /> 
                <param key="delay" value="0" /> """ % (idx, v, lastDepart * departTime, idx % 2), end='', file=routes)
                for i in range(stops):
                    permanenceTime = random.randrange(MIN_DURATION, MAX_DURATION / 8) * SLOT_DURATION
                    randomPark = random.randrange(1, 100)
                    if randomPark % 2 == 0:
                        print("""
                <stop parkingArea="%s%s" duration="%i"/>""" % (PARKAREA_NAMES[0], idx % 2, permanenceTime), end='', file=routes)
                    else:
                        print("""
                <stop parkingArea="%s%s" duration="%i"/> """ % (PARKAREA_NAMES[1], idx % 2, permanenceTime), end='', file=routes)
                    permanenceTime = random.randrange(MAX_DURATION / 3, MAX_DURATION - MAX_DURATION / 3) * SLOT_DURATION
                    if (i + 1) % howManyStopsInADay == 0:
                        print("""
                <stop parkingArea="%s%s" duration="%i"/> """ % (PARKAREA_NAMES[2], idx % howManyRows, permanenceTime), end='', file=routes)
                print("""
            </trip>""", file=routes)

                contGoodVehicles = contGoodVehicles + 1
                if contGoodVehicles > NUMBER_GOOD_VEHICLES:
                    break
                print("""    <trip id="v-%s.%s" type="car" depart="%s" from="mainin" to="-road%s">  
                <param key="warning" value="0" /> 
                <param key="civil" value="0" /> 
                <param key="reviewStars" value="3" /> 
                <param key="wallet" value="100" />
                <param key="goodBehaviour" value="True" /> 
                <param key="delay" value="0" /> """ % (idx, v, lastDepart * departTime, idx % 2), end='', file=routes)
                for i in range(stops):
                    permanenceTime = random.randrange(MIN_DURATION, MAX_DURATION / 8) * SLOT_DURATION
                    randomPark = random.randrange(1, 100)
                    if randomPark % 2 == 0:
                        print("""
                <stop parkingArea="%s-%s" duration="%i"/>""" % (PARKAREA_NAMES[0],idx % 2, permanenceTime), end='', file=routes)
                    else:
                        print("""
                <stop parkingArea="%s-%s" duration="%i"/> """ % (PARKAREA_NAMES[1],idx % 2, permanenceTime), end='', file=routes)
                    permanenceTime = random.randrange(MAX_DURATION / 3, MAX_DURATION - MAX_DURATION / 3) * SLOT_DURATION
                    if (i + 1) % howManyStopsInADay == 0:
                        print("""
                <stop parkingArea="%s-%s" duration="%i"/> """ % (PARKAREA_NAMES[2], idx % howManyRows, permanenceTime), end='', file=routes)
                print("""
            </trip>""", file=routes)

        # Generation of vehicles with bad behaviour
        if contBadVehicles < NUMBER_BAD_VEHICLES:
            contBadVehicles = contBadVehicles + 1
            if contBadVehicles > NUMBER_BAD_VEHICLES:
                break
            print("""    <trip id="v%s.%s" type="carB" depart="%s" from="mainin" to="road%s">
            <param key="warning" value="0" /> 
            <param key="civil" value="0" /> 
            <param key="reviewStars" value="3" /> 
            <param key="wallet" value="100" />
            <param key="goodBehaviour" value="True" /> 
            <param key="delay" value="%i" /> """ % (last, v, lastDepart * departTime, contBadVehicles % 2, SLOT_DURATION), end='', file=routes)
            for i in range(stops):
                permanenceTime = random.randrange(MIN_DURATION, MAX_DURATION / 8) * SLOT_DURATION + SLOT_DURATION
                randomPark = random.randrange(1, 100)
                if randomPark % 2 == 0:
                    print("""
            <stop parkingArea="%s%s" duration="%i"/>""" % (PARKAREA_NAMES[0], contBadVehicles % 2, permanenceTime), end='',
                          file=routes)
                else:
                    print("""
            <stop parkingArea="%s%s" duration="%i"/> """ % (PARKAREA_NAMES[1], contBadVehicles % 2, permanenceTime), end='',
                          file=routes)
                permanenceTime = random.randrange(MAX_DURATION / 3, MAX_DURATION - MAX_DURATION / 3) * SLOT_DURATION
                if (i + 1) % howManyStopsInADay == 0:
                    print("""
            <stop parkingArea="%s%s" duration="%i"/> """ % (PARKAREA_NAMES[2], contBadVehicles % howManyRows, permanenceTime), end='',
                          file=routes)
            print("""
        </trip>""", file=routes)

            contBadVehicles = contBadVehicles + 1
            if contBadVehicles > NUMBER_BAD_VEHICLES:
                break
            print("""    <trip id="v-%s.%s" type="carB" depart="%s" from="mainin" to="-road%s">
            <param key="warning" value="0" /> 
            <param key="civil" value="0" /> 
            <param key="reviewStars" value="3" /> 
            <param key="wallet" value="100" />
            <param key="goodBehaviour" value="True" /> 
            <param key="delay" value="%i" /> """ % (last, v, lastDepart * departTime, contBadVehicles % 2, SLOT_DURATION), end='', file=routes)
            for i in range(stops):
                permanenceTime = random.randrange(MIN_DURATION, MAX_DURATION / 8) * SLOT_DURATION + SLOT_DURATION
                randomPark = random.randrange(1, 100)
                if randomPark % 2 == 0:
                    print("""
            <stop parkingArea="%s-%s" duration="%i"/>""" % (PARKAREA_NAMES[0], contBadVehicles % 2, permanenceTime), end='',
                          file=routes)
                else:
                    print("""
            <stop parkingArea="%s-%s" duration="%i"/> """ % (PARKAREA_NAMES[1], contBadVehicles % 2, permanenceTime), end='',
                          file=routes)
                permanenceTime = random.randrange(MAX_DURATION / 3, MAX_DURATION - MAX_DURATION / 3) * SLOT_DURATION
                if (i + 1) % howManyStopsInADay == 0:
                    print("""
            <stop parkingArea="%s-%s" duration="%i"/> """ % (PARKAREA_NAMES[2], contBadVehicles % howManyRows, permanenceTime), end='',
                          file=routes)
            print("""
        </trip>""", file=routes)

    lastDepart = lastDepart + 1
    begin = last + 1
    last = last + last + 1

print("</routes>", file=routes)
routes.close()


# Sumo config, the "traditional" bus does not work currently
config = open("%s%02i.sumocfg" % (PREFIX, RANDOM_POPULATION), "w")
print("""<configuration>
<input>
    <net-file value="%s.net.xml"/>
    <route-files value="%s_demand%02i.rou.xml"/>
    <additional-files value="%s.add.xml"/>
    <no-step-log value="True"/>
    <time-to-teleport value="0"/>
</input>
</configuration>""" % (PREFIX, PREFIX, RANDOM_POPULATION, PREFIX), file=config)
config.close()
