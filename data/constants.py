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

# @file    constants.py
# @author  Roberto Wang
# @date    2024

from __future__ import absolute_import
import os
import sys

INFINITY = 1e400
PREFIX = "park"
PARKAREA_NAMES = ["ParkArea", "ParkAreaAlternative", "ParkAreaOutOfTown"]
STARTING_STOP = 6
RANDOM_POPULATION = 100 # 1 5 10 50 100
STANDARD_AUCTION_PRICE = 1
MIN_DURATION = 1
MAX_DURATION = 24
SLOT_DURATION = 100
CONSTANT_FREE_PARKS = -1
INITIAL_CONSTANT_FREE_PARKS = 3
INITIAL_FREE_PARKS = 3
TIME_INITIAL_CONSTANT_FREE_PARKS = 100
NUMBER_GOOD_VEHICLES = 40
NUMBER_BAD_VEHICLES = 40
REFRESH_FREE_PARKS = 3

DOUBLE_ROWS = 2
ROW_DIST = 29
STOP_POS = ROW_DIST - 9
SLOTS_PER_ROW = 10
SLOT_WIDTH = 5
SLOT_LENGTH = 9
SLOT_FOOT_LENGTH = 5
CAR_CAPACITY = 3
OCCUPATION_PROBABILITY = 0.5
BREAK_DELAY = 1200

SUMO_HOME = os.path.realpath(os.environ.get(
    "SUMO_HOME", os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
sys.path.append(os.path.join(SUMO_HOME, "tools"))
try:
    from sumolib import checkBinary  # noqa
except ImportError:
    def checkBinary(name):
        return name
NETCONVERT = checkBinary("netconvert")
SUMO = checkBinary("sumo")
SUMOGUI = checkBinary("sumo-gui")
