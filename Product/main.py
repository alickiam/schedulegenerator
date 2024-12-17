"""
title: schedule generator
author: alicia
date: 2023-06-25
"""
from flask import Flask, render_template, request, redirect
from pathlib import Path
import sqlite3
import random

### --- VARIABLES --- ###
DB_NAME = "schedule2.db"
FIRST_RUN = True
if (Path.cwd() / DB_NAME).exists():
    FIRST_RUN = False

### --- FLASK --- ###
app = Flask(__name__)
@app.route("/", methods=["GET", "POST"])
def index():
    QUERY_SCHEDULES = getAllSchedules()
    SCHEDULE_LIST = []
    for x in QUERY_SCHEDULES:
        if x not in SCHEDULE_LIST:
            SCHEDULE_LIST.append(x)
    return render_template("index.html", schedules=SCHEDULE_LIST)

@app.route("/createSchedule/", methods=["GET", "POST"])
def create():
    global SCHEDULE_NAME
    ALERT = ""
    if request.form:
        SCHEDULE_NAME = request.form.get("schedule_name")
        START_TIME = request.form.get("start_time")
        if SCHEDULE_NAME != "" and START_TIME != "" and checkTime(START_TIME) == True:
            insertInfo(SCHEDULE_NAME, START_TIME)
            ALERT = f"Successfully created schedule {SCHEDULE_NAME}!"
        else:
            ALERT = "Please fill in all fields and make sure you enter a valid time. "
    return render_template("createSchedule.html", alert=ALERT)

@app.route("/addTasks/", methods=["GET", "POST"])
def add():
    global SCHEDULE_NAME
    ALERT = ""
    if request.form:
        TASK = request.form.get("task")
        TIME = request.form.get("time")
        if TASK != "" and TIME != "":
            addActivity(SCHEDULE_NAME, TASK, TIME)
            ALERT = f"Successfully added new activity to {SCHEDULE_NAME}!"
        else:
            ALERT = "Please fill in all fields."
    return render_template("addTasks.html", alert=ALERT, schedule=SCHEDULE_NAME)

@app.route("/viewSchedule/<SCHEDULE_NAME>", methods=["GET", "POST"])
def view(SCHEDULE_NAME):
    SCHEDULE = getSchedule(SCHEDULE_NAME)
    TIME_BREAKS = getInfo(SCHEDULE_NAME)
    SCHEDULE = createSchedule(TIME_BREAKS[0][1], SCHEDULE, SCHEDULE_NAME)
    return render_template("viewSchedule.html", schedule=SCHEDULE, name=SCHEDULE_NAME)

@app.route("/delete/<SCHEDULE_NAME>")
def deleteContactPage(SCHEDULE_NAME):
    deleteSchedule(SCHEDULE_NAME)
    return redirect("/")


### --- SQLITE --- ###
def deleteSchedule(SCHEDULE_NAME):
    global DB_NAME
    CONNECTION = sqlite3.connect(DB_NAME)
    CURSOR = CONNECTION.cursor()
    CURSOR.execute("""
        DELETE FROM
            schedules
        WHERE
            schedule_name = ?
    ;""", [SCHEDULE_NAME])
    CONNECTION.commit()
    CONNECTION.close()


def createTable():
    global DB_NAME
    CONNECTION = sqlite3.connect(DB_NAME)
    CURSOR = CONNECTION.cursor()

    CURSOR.execute("""
        CREATE TABLE 
            schedules (
                schedule_name NOT NULL,
                activity_name NOT NULL,
                time NOT NULL,
                clock_time NOT NULL,
                id INTEGER PRIMARY KEY,
                orders TEXT
            )
    ;""")
    CONNECTION.commit()


    CURSOR.execute("""
        CREATE TABLE
            info (
                schedule_name,
                start_time
            )

    ;""")
    CONNECTION.commit()
    CONNECTION.close()


def insertInfo(SCHEDULE_NAME, START):
    global DB_NAME
    CONNECTION = sqlite3.connect(DB_NAME)
    CURSOR = CONNECTION.cursor()
    CURSOR.execute("""
        INSERT INTO
            info (
                schedule_name,
                start_time
                )
        VALUES (
            ?, ?
        )
    ;""", [SCHEDULE_NAME, START])
    CONNECTION.commit()
    CONNECTION.close()

def getInfo(SCHEDULE_NAME):
    global DB_NAME
    CONNECTION = sqlite3.connect(DB_NAME)
    CURSOR = CONNECTION.cursor()
    INFO = CURSOR.execute("""
        SELECT
            *
        FROM
            info
        WHERE
            schedule_name = ?
    ;""", [SCHEDULE_NAME]).fetchall()
    CONNECTION.commit()
    CONNECTION.close()
    return INFO

def addActivity(SCHEDULE_NAME, TASK, TIME):
    global DB_NAME
    CONNECTION = sqlite3.connect(DB_NAME)
    CURSOR = CONNECTION.cursor()
    CURSOR.execute("""
        INSERT INTO
             schedules (
                schedule_name,
                activity_name,
                time,
                clock_time
             )
        VALUES (
            ?, ?, ?, ?
        )
    ;""", [SCHEDULE_NAME, TASK, TIME, 0])
    CONNECTION.commit()
    CONNECTION.close()


def getSchedule(SCHEDULE_NAME):
    global DB_NAME
    CONNECTION = sqlite3.connect(DB_NAME)
    CURSOR = CONNECTION.cursor()
    SCHEDULE = CURSOR.execute("""
        SELECT
            *
        FROM
            schedules
        WHERE
            schedule_name = ?

    ;""", [SCHEDULE_NAME]).fetchall()
    print(SCHEDULE)
    CONNECTION.close()
    return SCHEDULE


def getAllSchedules():
    global DB_NAME
    CONNECTION = sqlite3.connect(DB_NAME)
    CURSOR = CONNECTION.cursor()
    ALL_SCHEDULES = CURSOR.execute("""
        SELECT
            schedule_name
        FROM
            schedules
        ORDER BY
            schedule_name
    ;""").fetchall()
    CONNECTION.close()
    return ALL_SCHEDULES


### --- PYTHON --- ###
def createSchedule(START_TIME, SCHEDULE, SCHEDULE_NAME):
    global DB_NAME
    CONNECTION = sqlite3.connect(DB_NAME)
    CURSOR = CONNECTION.cursor()

    random.shuffle(SCHEDULE)
    for i in range(len(SCHEDULE)):
        CURSOR.execute("""
            UPDATE
                schedules
            SET
                orders = ?
            WHERE
                id = ?
        ;""", [i, SCHEDULE[i][4]])
        CONNECTION.commit()


    CURSOR.execute("""
        UPDATE
            schedules
        SET
            clock_time = ?
        WHERE
            id = ?
            
    ;""", [START_TIME, SCHEDULE[0][4]])
    CONNECTION.commit()

    CLOCK_TIME = START_TIME  # get time taken and add to clock time order by

    for i in range(len(SCHEDULE)):  # traverse skipping first, if first, clocktime = start time when appending
        if i == 0:
            CLOCK_TIME = START_TIME

        elif i > 0:
            CLOCK_TIME = CLOCK_TIME.split(":")
            HOURS = int(CLOCK_TIME[0])
            MINUTES = int(CLOCK_TIME[1])

            TIME_TAKEN = int(SCHEDULE[i-1][2])
            MINUTES = TIME_TAKEN + MINUTES
            ## change to 05 rather than 5
            if MINUTES > 59:
                ADD_HOURS = MINUTES // 60
                HOURS = ADD_HOURS + HOURS
                MINUTES = MINUTES - 60
            if MINUTES < 10:
                MINUTES = f"0{MINUTES}"
            if HOURS > 12:
                HOURS = HOURS - 12
            HOURS = str(HOURS)
            MINUTES = str(MINUTES)
            CLOCK_TIME[0] = HOURS
            CLOCK_TIME[1] = MINUTES
            CLOCK_TIME = ":".join(CLOCK_TIME)
            CURSOR.execute("""
                UPDATE
                    schedules
                SET
                    clock_time = ?
                WHERE
                    id = ?
                
            ;""", [CLOCK_TIME, SCHEDULE[i][4]])
            CONNECTION.commit()

    SCHEDULE = CURSOR.execute("""
        SELECT
            *
        FROM
            schedules
        WHERE
            schedule_name = ?
    ;""", [SCHEDULE_NAME]).fetchall()

    for i in range(len(SCHEDULE)-1, 0, -1):  # range(start, stop, step) range(last index, 0, adding -1) traverse backwards until the 2nd position
        for j in range(i):  # traverse forward until the sorted value index
            if SCHEDULE[j][5] > SCHEDULE[j+1][5]:  # switch spots
                TEMP = SCHEDULE[j]
                SCHEDULE[j] = SCHEDULE[j+1]
                SCHEDULE[j+1] = TEMP

    return SCHEDULE

def checkTime(TIME):
    print(len(TIME), TIME[1])
    if len(TIME) == 4 and TIME[1] != ":":
        return False
    elif len(TIME) == 5 and TIME[2] != ":":
        return False
    else:
        return True


### --- MAIN PROGRAM CODE --- ###
if __name__ == "__main__":
    if FIRST_RUN:
        createTable()
    app.run(debug=True)