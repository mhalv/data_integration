"""ST_Math_Progress
This script
(i)    logs into a ST Math SFTP server,
(ii)   downloads available 'ST Math Progress' csv,
(iii)  strips date information from the file names,
(iv)   loads each file into a pandas data frame,
(v)    adds and populates a date column to each data frame,
(vi)   concatenates the data frames together,
(viii) saves the resulting data frame as a csv,
(vii)  connects to Silo instance,
(viii) call a SQL Server Agent job that runs a stored procedure to upsert/merge the csv,
(ix)   close the sql server and sftp connections.
"""
# Import modules

__author__ = 'chaid'

print('Importing Python Modules')
import pandas as pd
import pysftp
import ConfigParser as cp
import os
import dateutil.parser as dparser
import pyodbc

if __name__ == "__main__":
    print("Loading ST Math configuration file")
    config = cp.ConfigParser()

    config.read('ST_Math.config')

    # Connect to ST MAth
    print('Connecting to ST Math via sFTP')
    host = config.get('STMathSFTP', 'host')
    password = config.get('STMathSFTP', 'password')
    username = config.get('STMathSFTP', 'username')

    local_path = os.getcwd()

    local_path = local_path + "\\raw_data\\"

    remote_path = "Progress Completion Reports 2014-2015"

    print("Downloading ST Math Progress Files")
    with pysftp.Connection(host, username=username, password=password) as sftp:
         sftp.get_d(remotedir=remote_path, localdir=local_path, preserve_mtime=True)
         sftp.close()

    progress_files = [f for f in os.listdir(local_path) if os.path.isfile(os.path.join(local_path,f))]

    print("Extracting date from file names")

    progress_dates = {}
    for f in progress_files:
        progress_dates[f] = dparser.parse(f, fuzzy=True)

    print("Reading csv into data frames and appending week ending date column")
    def csv_to_df_MAP_Progress(file_dir, file_name, file_date):
        st_df = pd.read_csv(file_dir + "\\" + file_name )
        st_df['week_ending_date']=file_date
        return st_df

    out_df=pd.DataFrame() #instantiate empty data frame
    for i, f in enumerate(progress_dates):
        out_part = csv_to_df_MAP_Progress(local_path, str(f), progress_dates[str(f)])
        out_df = pd.concat([out_df, out_part], ignore_index=True)
    print("Data Frames concatenated!")

    out_path = os.getcwd() + '\\for_nardo\\progress.csv'

    print("Writing data frame to " + out_path)
    out_df.to_csv(out_path, index=False)

    print "Loading to DB"
    #get credential
    f = open("C:/data_robot/logistical/nardo_secret.txt", "r")
    secret = f.read()

    #upload
    conn = pyodbc.connect(driver='{SQL Server}', server='WINSQL01\NARDO',
        database='STMath', uid='sa', pwd=secret)
    conn.execute("exec msdb.dbo.sp_start_job N'STMath | Load Data'")
    conn.commit()
    conn.close()
