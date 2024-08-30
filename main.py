import os
import math
import time
from datetime import datetime, timedelta
import sqlite3
import asyncio
import aioconsole
import random

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

FULL_BLOCK = '\u2588'
EMPTY_BLOCK = '\u2591'

COLORS = [
    '\033[91m',
    '\033[92m',
    '\033[93m',
    '\033[94m',
    '\033[95m',
    '\033[96m',
    '\033[97m',
]
RESET_COLOR = '\033[0m'

def get_visible_length(text):
    return len(text.replace('\033[91m', '').replace('\033[92m', '').replace('\033[93m', '').replace('\033[94m', '').replace('\033[95m', '').replace('\033[96m', '').replace('\033[97m', '').replace(RESET_COLOR, ''))

def print_screen(lines):
    lengths = [get_visible_length(line) for line in lines]
    max_length = max(lengths) + 4
    top_border = '┌' + '─' * max_length + '┐'
    bottom_border = '└' + '─' * max_length + '┘'
    empty_line = '│' + ' ' * max_length + '│'

    os.system('cls' if os.name == 'nt' else 'clear')
    print(top_border)
    print(empty_line)
    for idx, line in enumerate(lines):
        left_padding = math.floor((max_length - lengths[idx])/2)
        right_padding = math.ceil((max_length - lengths[idx])/2)
        if idx == 0:
            print('│' + ' '*left_padding + '\033[4m' + line + '\033[0m' + ' '*right_padding + '│')
            print(empty_line)
        else:
            print('│' + ' '*left_padding + line + ' '*right_padding + '│')
    print(empty_line)
    print(bottom_border)

def home(message=None):
    lines = [
        'TIME MANAGER',
        '1. go working',
        '2. monitor',
        '3. work manager',
        '0. exit',
    ]
    print_screen(lines)

    if message is not None:
        print(message)

    selected = input("CHOOSE OPTION:")

    return selected

def show_work_list():
    lines = [
        'WORK LIST',
    ]

    conn = sqlite3.connect('work.db')
    cursor = conn.cursor()

    cursor.execute('SELECT title FROM work')
    rows = cursor.fetchall()

    for idx, row in enumerate(rows):
        lines.append(f'{idx+1}. {row[0]}')
    lines.append('0. back')

    cursor.close()
    conn.close()

    print_screen(lines)

    return

async def go_working():
    show_work_list()

    try:
        selected = int(input('CHOOSE WORK:'))-1
    except ValueError:
        return 'Invalid input(not number). No changes were made.'
    
    conn = sqlite3.connect('work.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, description FROM work')
    rows = cursor.fetchall()

    if selected == -1:
        return 'back'

    if 0 <= selected < len(rows):
        selected_title = rows[selected][1]
    else:
        return 'Invalid input. Not on working.'
    
    start_time = datetime.now()

    async def update_time():
        while True:
            current_time = datetime.now()
            elapsed_time = current_time - start_time
            elapsed_str = str(elapsed_time).split('.')[0]

            lines = [
                f'Working "{selected_title}"',
                elapsed_str,
                'Press enter to quit'
            ]
            print_screen(lines)

            await asyncio.sleep(1)

    async def wait_for_input():
        await aioconsole.ainput()
    
    task_update_time = asyncio.create_task(update_time())
    task_input = asyncio.create_task(wait_for_input())

    await task_input

    task_update_time.cancel()

    end_time = datetime.now()
    elapsed_time = (end_time - start_time).total_seconds() / 60
    current_date = datetime.now().strftime('%Y-%m-%d')

    conn_monitor = sqlite3.connect('monitor.db')
    cursor_monitor = conn_monitor.cursor()

    cursor_monitor.execute('''
    CREATE TABLE IF NOT EXISTS work_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_title TEXT NOT NULL,
        date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        elapsed_time REAL NOT NULL
    )
    ''')

    cursor_monitor.execute('''
    INSERT INTO work_log (work_title, date, start_time, end_time, elapsed_time)
    VALUES (?, ?, ?, ?, ?)
    ''', (selected_title, current_date, start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'), elapsed_time))

    conn_monitor.commit()
    cursor_monitor.close()
    conn_monitor.close()
    cursor.close()
    conn.close()

    return 'Work completed and logged successfully!'

def get_random_color():
    return random.choice(COLORS)

def monitor():
    conn = sqlite3.connect('monitor.db')
    cursor = conn.cursor()

    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=6)

    cursor.execute('''
    SELECT work_title, start_time, elapsed_time 
    FROM work_log 
    WHERE date >= ?
    ORDER BY start_time DESC
    ''', (seven_days_ago,))

    rows = cursor.fetchall()

    lines = []
    work_colors = {}
    for row in rows:
        work_title = row[0]
        if work_title not in work_colors:
            work_colors[work_title] = get_random_color()

    grid = [["" for _ in range(48)] for _ in range(7)]

    for row in rows:
        work_title = row[0]
        start_time = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
        elapsed_time = row[2]

        date_index = 6 - (start_time.date() - seven_days_ago).days
        if date_index < 0 or date_index >= 7:
            continue

        start_half_hour = (start_time.hour * 2) + (start_time.minute // 30)
        blocks = int(elapsed_time // 15)

        for i in range(blocks):
            if start_half_hour + i < 48:
                grid[date_index][start_half_hour + i] = work_colors[work_title] + FULL_BLOCK + RESET_COLOR

    lines.append("WORK TIME DISTRIBUTION")

    for work_title, color in work_colors.items():
        lines.append(f"{color}{FULL_BLOCK}{RESET_COLOR}: {work_title}")

    #lines.append('\n   ' + ' '.join([f"{i//2:02d}:{(i%2)*30:02d}" for i in range(48)]))

    for i in range(7):
        date_str = (seven_days_ago + timedelta(days=6 - i)).strftime('%Y-%m-%d')
        row = f"{date_str} "
        for j in range(48):
            block = grid[i][j] if grid[i][j] else EMPTY_BLOCK
            row += block
        lines.append(row)

    print_screen(lines)
    input()
    
    cursor.close()
    conn.close()

    return

def work_manager(message=None):
    lines = [
        'WORK MANAGER',
        '1. add work',
        '2. modify work',
        '3. delete work',
        '0. back',
    ]
    print_screen(lines)

    if message is not None:
        print(message)

    selected = input("CHOOSE OPTION:")

    return selected

def add_work():
    title = input('ENTER TITLE OF WORK:')
    description = input('ENTER DESCRIPTON OF WORK:')
    is_sure = input("ARE YOU SURE TO ADD WORK? (Y/N):")

    if is_sure == 'Y':
        conn = sqlite3.connect('work.db')
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS work (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL
        )
        ''')

        cursor.execute('''
        INSERT INTO work (title, description)
        VALUES (?, ?)
        ''', (title, description))

        conn.commit()
        cursor.close()
        conn.close()
        return 'Work added successfully!'
    
    elif is_sure == 'N':
        return 'Work not added.'
    else:
        return 'Invalid input. Work not added.'
    
def modify_work():
    show_work_list()

    try:
        selected = int(input('CHOOSE WORK:'))-1
    except ValueError:
        return 'Invalid input(not number). No changes were made.'
    
    conn = sqlite3.connect('work.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, description FROM work')
    rows = cursor.fetchall()

    if selected == -1:
        return 'back'

    if 0 <= selected < len(rows):
        selected_id = rows[selected][0]
        selected_title = rows[selected][1]
        selected_description = rows[selected][2]

        lines = [
            selected_title,
            selected_description
        ]

        print_screen(lines)

        new_title = input("ENTER NEW TITLE OF WORK (IF YOU DON'T WANT TO CHANGE, JUST PRESS ENTER):")
        new_description = input("ENTER NEW DESCRIPTION OF WORK (IF YOU DON'T WANT TO CHANGE, JUST PRESS ENTER):")
        is_sure = input("ARE YOU SURE TO MODIFY? (Y/N):")
    else:
        return f'Invalid input("{selected+1}"). No changes were made.'

    if is_sure == 'Y':
        if not new_title == '':
            cursor.execute('UPDATE work SET title = ? WHERE id = ?', (new_title, selected_id))
        if not new_description == '':
            cursor.execute('UPDATE work SET description = ? WHERE id = ?', (new_description, selected_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return 'Work modified successfully!'
    
    elif is_sure == 'N':
        return 'No changes were made.'
    else:
        return 'Invalid input. No changes were made.'

def delete_work():
    show_work_list()

    try:
        selected = int(input('CHOOSE WORK:'))-1
    except ValueError:
        return 'Invalid input(not number). No changes were made.'
    
    conn = sqlite3.connect('work.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, description FROM work')
    rows = cursor.fetchall()

    if selected == -1:
        return 'back'
    
    if 0 <= selected < len(rows):
        selected_id = rows[selected][0]
        selected_title = rows[selected][1]

        is_sure = input(f"ARE YOU SURE TO DELETE '{selected_title}'? (Y/N):")
    else:
        return f'Invalid input("{selected+1}"). No changes were made.'
    
    if is_sure == 'Y':
        cursor.execute('DELETE FROM work WHERE id = ?', (selected_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return 'Work deleted successfully!'
    elif is_sure == 'N':
        return 'No changes were made.'
    else:
        return 'Invalid input. No changes were made.'

if __name__ == '__main__':
    selected = home()
    while True:
        if selected == '1':
            result = asyncio.run(go_working())
            if result == 'back':
                selected = home()
            else:
                selected = home(message=result)
        elif selected == '2':
            monitor()
            break
        elif selected == '3':
            selected = work_manager()
            result = None
            while True:
                if selected == '1':
                    result = add_work()
                    break
                elif selected == '2':
                    result = modify_work()
                    if result == 'back':
                        selected = work_manager()
                    else:
                        break
                elif selected == '3':
                    result = delete_work()
                    if result == 'back':
                        selected = work_manager()
                    else:
                        break
                elif selected == '0':
                    break
                else:
                    selected = work_manager(message='Invalid input.')
            selected = home(message=result)
        elif selected == '0':
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Time manager quit successfully! Goodbye.")
            break
        else:
            selected = home(message='Invalid input')