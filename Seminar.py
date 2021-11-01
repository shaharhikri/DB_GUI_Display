#Author: Shahar Hikri, Date: 29.10.2021 13:40
# The program displays all the tables in the chinook.db database.
# After selecting a table, the window will display the selected table and a return button.
# By clicking on a column header, the table will be sorted by this column in ascending order.
# Another click will sort the table by column in descending order.
# If the table is deleted during the selection - a notification (Error window) about it will be given.
# If the DB didn't - a notification (Error window) about it will be given.
# Errors will be printed to the file: "./Log/Log_'Date'_'Time'.txt".

import os
import datetime
import sqlite3
from tkinter import *
from tkinter import ttk


#Return time format string
def getFormatTime():
    return datetime.datetime.now().strftime('%d/%m/%Y %X')


#Return Opened Log file (and create 'Log' directory if doesn't exist)
def openLogFile():
    log_path = "./Log/"
    log_file_name = "Log_" + getFormatTime().replace('/', '-').replace(':', '-').replace(' ', '_') + ".txt"
    openFile = lambda: open(log_path + log_file_name, 'w', encoding="utf-8")
    try:
        return openFile()
    except FileNotFoundError: # dir "./Log/" doesn't exist
        os.mkdir(log_path)   # make dir "./Log/"
        return openFile()


#Output to log
def logOut(msg: str):
    print('['+ getFormatTime()+'] '+msg)


#Execute reading query and return the result as a list
def executeReadingQuery(cursor, query: str) -> list:
    cursor.execute(query)
    return cursor.fetchall()


#Remove all elements(componenets) from window
def cleanWindow(window):
    for ele in window.winfo_children():
        ele.destroy()


#Set window Icon
def setWindowIcon(window, icon_path: str):
    try:
        window.iconbitmap(icon_path)
    except TclError:
        logOut("Error: Icon \'"+icon_path+"\' didn't found, the program continue with the default icon.")


#Sort tkinter treeview by column
def treeviewSortColumn(treev, col: int, reverse: bool):
    l = [(treev.set(k, col), k) for k in treev.get_children('')]
    try:
        l.sort(key=lambda t: int(t[0]), reverse=reverse)
    except ValueError:
        l.sort(reverse=reverse)

    for index, (val, k) in enumerate(l):
        treev.move(k, '', index)

    treev.heading(col, command=lambda: treeviewSortColumn(treev, col, not reverse))


#Setup window as an Error screen
def setupErrorWindow(window, geometry, err_msg):
    #Config window
    cleanWindow(window)
    window.geometry(geometry)
    setWindowIcon(window, 'icons/error_icon.ico')
    window.title('ERROR')
    window.resizable(False, False)

    #Error label
    label = Label(window, text = err_msg)
    label.config(font=("Ariel", 12, "bold"), fg="red")
    label.pack(pady=20)


#Setup window as a table view window
# if the table dowsnt exist - it'll contain only a label "Table --- is no longer exists." and return button.
def setupTableWindow(window, cur, table_name: str):

    #Trying extract table information
    Q1 = "SELECT * FROM " + table_name;
    table_is_exist = True
    try:
        table = executeReadingQuery(cur, Q1)
    except sqlite3.OperationalError:
        # 'Table is no longer exist' Error window
        table_is_exist = False
        delet_table_msg = "Table ''" + table_name + "'' is no longer exists."
        logOut('Error: ' + delet_table_msg)
        setupErrorWindow(window, "270x130", delet_table_msg)

    if table_is_exist:
        #Config window
        cleanWindow(window)
        window.geometry("")
        setWindowIcon(window, 'icons/table_icon.ico')
        window.resizable(True, False)
        window.wm_attributes("-topmost", 1)
        window.title(table_name[0].upper()+table_name[1:] if len(table_name)>1 else table_name)

        #Create TreeView Frame
        treev_frame = Frame(window)
        treev_frame.grid(column=1, row=1, sticky="n")
        treev_frame.pack(padx=20, pady=20)

        #Create TreeView Scrollbars
        treev_right_scroll = Scrollbar(treev_frame, orient=VERTICAL)
        treev_right_scroll.pack(side=RIGHT, fill=Y)

        treev_down_scroll = Scrollbar(treev_frame, orient=HORIZONTAL)
        treev_down_scroll.pack(side=BOTTOM, fill=X)

        #Create TreeView
        table_headers = list(map(lambda x: x[0], cur.description))
        col = tuple((i for i in range(1, len(table_headers) + 1)))

        treev = ttk.Treeview(treev_frame, columns=col, height=20, show="headings", yscrollcommand=treev_right_scroll.set,xscrollcommand=treev_down_scroll.set)
        treev.pack(side='top')

        #Config Scrollbar
        treev_right_scroll.config(command=treev.yview)
        treev_down_scroll.config(command=treev.xview)

        #Data into the threeview
        for col in range(1, len(table_headers) + 1):
            treev.heading(col, text=table_headers[col - 1])
            treev.column(col, width=100, stretch=False)
            treeviewSortColumn(treev, col, True)

        for x in treev.get_children():
            treev.delete(x)
        cur.execute("SELECT *  FROM " + table_name)
        for row in cur:
            treev.insert('', 'end', values=row)

    #Return button
    def return_btn_command():
        setupMainWindow(window, cur)

    return_btn = Button(window, text="Choose another table", command = return_btn_command)
    return_btn.pack(pady=20, side='top')


#Setup window as a Selection screen
def setupMainWindow(window, cur):
    # Config window
    cleanWindow(window)
    window.geometry("240x100")
    window.resizable(False, False)
    setWindowIcon(window, 'icons/menu_icon.ico')
    window.title('Menu')

    #Instruction label
    labelTop = Label(window, text="Choose table:")
    labelTop.config(font=("Ariel", 12, "bold"))
    labelTop.grid(column=0, row=0, padx=5, pady=5)

    # Combobox for table names
    Q0 = "SELECT name FROM sqlite_master WHERE type='table';"
    table_names = executeReadingQuery(cur,Q0)
    table_names = [t[0] for t in table_names]
    combobox = ttk.Combobox(window, values=table_names)
    combobox.grid(column=0, row=1, padx=20, pady = 0)

    # Choosing button
    def show_me_btn_command():
        choice = combobox.current();
        if(choice>-1):
            setupTableWindow(window, cur, table_names[choice])

    show_me_btn = Button(window, text="Show", command = show_me_btn_command)
    show_me_btn.grid(column=1, row=1, padx=0, pady = 5)
    show_me_btn.config(state=DISABLED)

    # Grey Choosing button - if no table is selected
    def combobox_command():
        if(combobox.current()==-1):
            show_me_btn.config(state=DISABLED)
        else:
            show_me_btn.config(state=NORMAL)
    combobox.bind('<<ComboboxSelected>>', lambda event: combobox_command())

    # Instruction label
    labelCredit = Label(window, text="Created by Shahar Hikri")
    labelCredit.config(font=("Ariel", 8), fg="grey")
    labelCredit.grid(column=0, row=2)


#Run GUI program on db
def run(db_name):
    window = Tk()
    if os.path.isfile(db_name):
        conn = sqlite3.connect(db_name);
        cur = conn.cursor()
        setupMainWindow(window, cur)
        window.mainloop()
        conn.close()
    else:
        # 'DB doesn't exist' Error window
        err_msg = 'The DB \'' + db_name + '\' doesn\'t exist.'
        logOut('Error: '+err_msg)
        setupErrorWindow(window,"310x70",err_msg)
        window.mainloop()


def main():
    sys.stdout = openLogFile() # print into log file
    run('chinook.db')
    sys.stdout.close()


if __name__=='__main__':
    main()