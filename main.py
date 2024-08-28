import os
import math
import time
from datetime import datetime
import sqlite3

def print_screen(lines):
    lengths = [len(line) for line in lines]
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

def go_working():
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

    lines = [
        f'Working "{selected_title}"',
        'Press enter to quit'
    ]
    print_screen(lines)

    input()

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

def monitor():
    return None

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
    while(True):
        if selected == '1':
            result = go_working()
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
            while(True):
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
            break
        else:
            selected = home(message='Invalid input')