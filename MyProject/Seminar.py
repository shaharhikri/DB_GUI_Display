# Author: Shahar Hikri, Date: 1.12.2021 18:30
# The program displays all the tables in the chinook.db database.
# After selecting a table and datatype, the window will display the selected table.
# By clicking on a column header, the table will be sorted by this column in ascending order.
# Another click will sort the table by column in descending order.
# If the table is deleted during the selection - an error message about it will be given.
# If the DB didn't -  an error message about it will be given and comboboxes won't be displayed.
# Errors will be printed to the file: "./Log/Log_'Date'_'Time'.txt".

import sys
import os
import datetime
import sqlite3
from tkinter import *
from tkinter import ttk


def getFormatTime():
    """
    :return: time format string.
    """
    return datetime.datetime.now().strftime('%d/%m/%Y %X')


def openLogFile():
    """
    openLogFile() creates the log file "./Log/Log_'Date'_'Time'.txt" and create 'Log' directory if doesn't exist.
    :return: Opened Log file
    """
    log_path = "./Log/"
    log_file_name = "Log_" + getFormatTime().replace('/', '-').replace(':', '-').replace(' ', '_') + ".txt"
    openFile = lambda: open(log_path + log_file_name, 'w', encoding="utf-8")
    try:
        return openFile()
    except FileNotFoundError:  # dir "./Log/" doesn't exist
        os.mkdir(log_path)  # make dir "./Log/"
        return openFile()


def logOut(msg: str):
    """
    logOut(...) output texts to the log.
    :param msg: message (string) to log out
    """
    print('[' + getFormatTime() + '] ' + msg)


def executeReadingQuery(cursor, query: str) -> list:
    """
    executeReadingQuery(...) Execute reading query and return the result as a list
    :param cursor: cursor (sqlite3 object) of a connection to DB.
    :param query: query string.
    :return: query results list.
    """
    cursor.execute(query)
    return cursor.fetchall()


def getTableNamesList(cur):
    """
    getTableNamesList(...) gives list of table names.
    :param cur: cursor (sqlite3 object) of a connection to DB.
    :return:  list of table names.
    """
    Q0 = "SELECT name FROM sqlite_master WHERE type='table';"
    q_result = executeReadingQuery(cur, Q0)
    table_names_list = [t[0] for t in q_result]
    return table_names_list


def checkTableExists(cur, table_name: str):
    """
    checkTableExists(...) check if a table exists in the DB.
    :param cur: cursor (sqlite3 object) of a connection to DB.
    :param table_name: name of table
    :return: True - if the table exists in the DB, else - False.
    """
    # Trying extract table information
    table_names = getTableNamesList(cur)
    return table_names.__contains__(table_name)


def setWindowIcon(window, icon_path: str):
    """
    setWindowIcon(...) Sets window Icon.
    if cant find the icon - the icon won't change and Error will be logged out.
    :param window: the window (some tkinter.TK).
    :param icon_path: icon (img) path (and name).
    """
    try:
        window.iconbitmap(icon_path)
    except TclError:
        logOut("Error: Icon \'" + icon_path + "\' didn't found, the program continue with the default icon.")


def removeValFromCombobox(combobox, val: str):
    """
    removeValFromCombobox(...) remove value(option) from combobox.
    :param combobox: the combobox that you want to remove the selection from.
    :param val: the selection you want to remove.
    """
    options = list(combobox['values'])
    options.remove(val)
    combobox['values'] = options


def showError(window, err_msg):
    """
    showError(...) add to window an error message.
    :param window: the window (some tkinter.TK).
    :param err_msg: The error message you want to add to the error screen.
    :return: the elements that added to the window.
    """

    # Config window
    setWindowIcon(window, 'icons/error_icon.ico')
    window.title('ERROR')

    # Error label
    label = Label(window, text=err_msg, font=("Ariel", 12, "bold"), fg="red")
    label.pack(padx=30, pady=50)  # label.grid(column=0, row=4)
    return [label]


def treeviewSortColumn(treev, col: int, reverse: bool, numOfLastRowsToIgnore: bool):
    """
    treeviewSortColumn(...) Sorts tkinter treeview by column.
    :param treev: treeview you want to sort bu column.
    :param col: the col (index) you want to sort by.
    :param reverse: True - for descending, False - for ascending, will be switched every call.
    :param numOfLastRowsToIgnore: in sorting ignore(exclude) the numOfLastRowsToIgnore # of last rows(this last rows stay in the bottom of the table).
    """
    l = [(treev.set(k, col), k) for k in treev.get_children('')]
    if len(l) > 0 and numOfLastRowsToIgnore>0:
        for i in range(numOfLastRowsToIgnore):
            l.remove(l[-1])
    try:
        l.sort(key=lambda t: int(t[0]), reverse=reverse)
    except ValueError:
        l.sort(reverse=reverse)

    for index, (val, k) in enumerate(l):
        treev.move(k, '', index)

    treev.heading(col, command=lambda: treeviewSortColumn(treev, col, not reverse, numOfLastRowsToIgnore))


def showTableInfo(window, cur, table_name: str, show_metadata):
    """
    showTableInfo(...) adds to window a table info.
    :param window: the window (some tkinter.TK).
    :param cur: cursor (sqlite3 object) of a connection to DB.
    :param table_name: The name of the table you want to show it's info.
    :param show_metadata: True - show metadata of the table, False - show the actual table.
    :return: the elements that added to the window.
    """

    # Config window
    setWindowIcon(window, 'icons/table_icon.ico')
    window.title((table_name[0].upper() + table_name[1:] if len(table_name) > 1 else table_name) + ' ' + (
        'Metadata' if show_metadata else 'Data'))

    # Extract table information
    Q_data = "SELECT * FROM " + table_name
    Q_metadata = "PRAGMA table_info(" + table_name + ")"
    if show_metadata:
        Q1 = Q_metadata
    else:
        Q1 = Q_data
    table = executeReadingQuery(cur, Q1)

    # Create TreeView Frame
    treev_frame = Frame(window)
    treev_frame.pack(padx=5, pady=8, side='top', fill="both", expand=1)

    # Create TreeView Scrollbars
    treev_right_scroll = Scrollbar(treev_frame, orient=VERTICAL)
    treev_right_scroll.pack(side=RIGHT, fill=Y)
    treev_down_scroll = Scrollbar(treev_frame, orient=HORIZONTAL)
    treev_down_scroll.pack(side=BOTTOM, fill=X)

    # Create TreeView
    table_headers = list(map(lambda x: x[0], cur.description))
    cols = tuple((i for i in range(1, len(table_headers) + 1)))
    treev = ttk.Treeview(treev_frame, columns=cols, show="headings", yscrollcommand=treev_right_scroll.set,
                         xscrollcommand=treev_down_scroll.set)
    treev.pack(side='top', fill="both", expand=1)

    # Config Scrollbar
    treev_right_scroll.config(command=treev.yview)
    treev_down_scroll.config(command=treev.xview)

    # Data into the threeview
    for col in range(1, len(table_headers) + 1):
        treev.heading(col, text=table_headers[col - 1], anchor='nw')
        treev.column(col, stretch=NO)
        treeviewSortColumn(treev, col, True,4 if show_metadata else 0)

    for x in treev.get_children():
        treev.delete(x)

    cur.execute(Q1)
    for row in cur:
        fixed_row = list(row)
        if show_metadata:
            for i in [3,5]:
                if fixed_row[i]==1:
                    fixed_row[i] = 'Yes'
                elif fixed_row[i]==0:
                    fixed_row[i] = 'No'
        treev.insert('', 'end', values=fixed_row)

    # Statistics rows config
    if show_metadata:
        num_of_cols = len(table)
        num_of_rows = executeReadingQuery(cur, "SELECT COUNT(*) FROM " + table_name)[0][0]
        empty_start = ['' for i in range(len(table_headers) - 1)]
        treev.insert('', 'end', values=empty_start + [''])
        treev.insert('', 'end', values=empty_start + ['Statistics:'])
        treev.insert('', 'end', values=empty_start + ['* num of cols - '+ str(num_of_cols)])
        treev.insert('', 'end', values=empty_start + ['* num of rows - '+ str(num_of_rows)])

    return [treev, treev_frame, treev_right_scroll, treev_down_scroll]


def setupMainWindow(window, cur):
    """
    setupMainWindow(...) Setups window as a Selection screen
    :param window: the window (some tkinter.TK).
    :param cur: the window (some tkinter.TK).
    """

    # Selection Wrapper (frame) - wraps the comboboxes and their titles.
    wrapper = LabelFrame(window, text='Select a Table & DataType:', font=("Ariel", 10, "bold"))
    wrapper.pack(pady=2, padx=30, side='top')

    # Comoboxes tiltes
    Label(wrapper, text="Table:", anchor='w', font=("Ariel", 8), fg="grey").grid(column=0, row=0, padx=0, pady=5)
    Label(wrapper, text="DataType:", anchor='w', font=("Ariel", 8), fg="grey").grid(column=0, row=1, padx=0, pady=5)

    # Combobox for Table Names
    table_names = getTableNamesList(cur)
    # table_names.append('FakeTable') #for checking handling table that had been removed (in real time).
    tablenames_combobox = ttk.Combobox(wrapper, values=table_names, state="readonly")
    tablenames_combobox.current(0)
    tablenames_combobox.grid(column=1, row=0, padx=20, pady=5)  # tablenames_combobox.pack(pady=5, padx=10, side='top')

    # Combobox for datatype
    datatype_combobox = ttk.Combobox(wrapper, values=["Data", "Metadata"], state="readonly")
    datatype_combobox.current(0)
    datatype_combobox.grid(column=1, row=1, padx=20, pady=5)  # datatype_combobox.pack(pady=5, padx=10, side='top')

    # Tables Combobox command
    def combobox_command(last_selection=[None, None], last_selection_views=[]):
        # if the current selection is the same as the last - do nothing!
        if last_selection[0] == tablenames_combobox.current() and last_selection[1] == datatype_combobox.current():
            return

        table_name = table_names[tablenames_combobox.current()]
        if checkTableExists(cur, table_name):
            views = showTableInfo(window, cur, table_name, (datatype_combobox.current() == 1))
        else:
            deleted_table_msg = "Table ''" + table_name + "'' is no longer exists."
            views = showError(window, deleted_table_msg)
            logOut('Error: ' + deleted_table_msg)
            removeValFromCombobox(tablenames_combobox,
                                  table_name)  # Remove this option (the name of the table which doesn't exist) from tablenames_combobox

        # Destroy views from the last selection
        for view in last_selection_views:
            view.destroy()
        last_selection_views.clear()
        # Add to last_selection_views the views of the current selection
        last_selection_views.extend(views)
        # Save the current selection for the next selection
        last_selection[0] = tablenames_combobox.current()
        last_selection[1] = datatype_combobox.current()

    combobox_command()  # The first screen - by comboboxes default selections
    tablenames_combobox.bind('<<ComboboxSelected>>', lambda event: combobox_command())
    datatype_combobox.bind('<<ComboboxSelected>>', lambda event: combobox_command())


def run(db_name, win_w, win_h, win_min_w, win_min_h):
    """
    run(...) runs the GUI program on db.
    :param db_name: the DB path (and name).
    :param win_w: width of the window.
    :param win_h: height of the window.
    :param win_min_w: minimum width of the window.
    :param win_min_h: minimum height of the window.
    """

    # Config window
    window = Tk()
    window.geometry(str(win_w) + 'x' + str(win_h))
    window.minsize(win_min_w, win_min_h)
    window.resizable(True, True)
    window.wm_attributes("-topmost", 1)

    if os.path.isfile(db_name):  # change to "if False:" for checking
        conn = sqlite3.connect(db_name);
        cur = conn.cursor()
        setupMainWindow(window, cur)
        window.mainloop()
        conn.close()
    else:
        # 'DB doesn't exist' Error window
        err_msg = 'The DB \'' + db_name + '\' doesn\'t exist.'
        logOut('Error: ' + err_msg)
        showError(window, err_msg)
        window.mainloop()


def main():
    """
    main() starts the program and adjusts the output to a log file.
    """
    sys.stdout = openLogFile()  # print into log file
    run('chinook.db', 500, 500, 350, 300)
    sys.stdout.close()


if __name__ == '__main__':
    main()
