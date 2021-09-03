# ##### BEGIN GPL LICENSE BLOCK #####
#
# <Keep track of your Blender-Behavior>
#  Copyright (C) <2020>  <Blender Defender>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.app.handlers import persistent

import time

import os
from os import path as p

from .jsonFunctions import (
    decode_json,
    encode_json
)


# Check, if the default cube has been deleted.
def check_for_cube(data, path):
    if data is 0:
        print("Default Cube deleted!")

        j = decode_json(path)
        j["default_cube"] += 1
        encode_json(j, path)


# Save the date and time on Blender Startup.
def date_register(path):
    j = decode_json(path)
    date = [time.localtime()[2], time.localtime()[1], time.localtime()[0]]
    current_time = [time.localtime()[3], time.localtime()[
        4], time.localtime()[5]]

    if j["date"] != date:
        j_date = time.strftime(
            "%Y-%m-%d", time.strptime(str(j["date"]), "[%d, %m, %Y]"))

        j["dates_hours_alignment"][j_date] = j["time_today"]
        j["date"] = date
        j["time_yesterday"] = j["time_today"]
        j["time_today"] = 0.00

    j["start_time"] = current_time
    encode_json(j, path)


# Save the difference between the start date/time and the end date/time as Blender usage time.
# Save the current date/time as new start date/time.
def date_unregister(path):
    j = decode_json(path)

    current_time = [time.localtime()[3], time.localtime()[
        4], time.localtime()[5]]

    hours = current_time[0] - j["start_time"][0]
    minutes = current_time[1] - j["start_time"][1]
    seconds = current_time[2] - j["start_time"][2]

    total_minutes = (hours * 60) + minutes + round((seconds / 60))
    if total_minutes < 0:
        total_minutes += 24 * 60
    j["time_today"] += round(total_minutes, 2)
    j["start_time"] = current_time

    encode_json(j, path)


# Get the usage time from yesterday.
def get_yesterday(path):
    return decode_json(path)["time_yesterday"]


# Get the usage time from today.
def get_today(path):
    return decode_json(path)["time_today"]


# Get the usage time from the last week
def get_last_week(path):
    data = decode_json(path)
    current_time = time.time()
    time_last_week = data["time_today"]

    DAY_IN_SECONDS = 60 * 60 * 24
    FORMAT = "%Y-%m-%d"

    for i in range(1, 8):
        day = time.strftime(FORMAT, time.localtime(
            current_time - i * DAY_IN_SECONDS))
        if day in data["dates_hours_alignment"].keys():
            time_last_week += data["dates_hours_alignment"][day]

    return time_last_week


# Get the count of deleted default cubes.
def get_default_cubes(path):
    return int(decode_json(path)["default_cube"])


def get_undos(path):
    data = decode_json(path)

    if "undo_count" in data.keys():
        return data["undo_count"]

    return 0


# Count the number of undos
@persistent
def count_undo(*args):
    path = p.join(p.expanduser(
        "~"), "Blender Addons Data", "blender-analytics", "data.json")
    data = decode_json(path)

    if not "undo_count" in data.keys():
        data["undo_count"] = 0

    data["undo_count"] += 1

    encode_json(data, path)


@persistent
def startup_setup(*args):
    path = p.join(p.expanduser(
        "~"), "Blender Addons Data", "blender-analytics", "data.json")

    bpy.context.preferences.addons[__package__.split(
        ".")[0]].preferences.display_reminder = True

    # threading.Timer(5, lambda: test()).start()

    # Start the default cube counter.
    # global t
    # t = threading.Timer(40, lambda: check_for_cube(bpy.data.meshes['Cube'].users,
    #                                                p.join(path, "data.json")))
    # t.start()

    # Save the date/time at startup.
    date_register(path)


# Update the data to version 1.0.1!
def update_json101(path):
    j = decode_json(path)

    j["check_update"] = 101

    for i in j["dates_hours_alignment"]:
        j["dates_hours_alignment"][i] = round(
            j["dates_hours_alignment"][i] * 60, 2)

    j["time_yesterday"] = round(j["time_yesterday"] * 60, 2)
    j["time_today"] = round(j["time_today"] * 60, 2)

    encode_json(j, path)


# Update the data to version 1.1.0!
def update_json_and_data110(path):
    j = decode_json(path)

    j["check_update"] = 110

    encode_json(j, path)

    db_filenames = ["Blender Analytics c704d36c50269763b8bce4479f.db",
                    "Blender Analytics e6017460ea3479e67886f3430845.db"]

    for file in db_filenames:
        file = p.join(p.dirname(path), file)
        if p.exists(file):
            os.remove(file)


def update_json_and_data120(path):
    FORMAT = "[%d, %m, %Y]"

    j = decode_json(path)

    elements = list(j["dates_hours_alignment"].keys())

    for i in elements:
        try:
            new_label = time.strftime("%Y-%m-%d", time.strptime(i, FORMAT))
        except Exception:
            continue
        j["dates_hours_alignment"][new_label] = j["dates_hours_alignment"].pop(
            i)

    j["check_update"] = 120

    encode_json(j, path)


# Checks the version of the JSON Data file and updates, if necessary.
def update_json(path):
    j = decode_json(path)

    if not "check_update" in j.keys():
        update_json101(path)

    if j["check_update"] == 101:
        update_json_and_data110(path)

    if j["check_update"] == 110:
        update_json_and_data120(path)
