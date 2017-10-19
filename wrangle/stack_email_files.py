#-------------------------------------------------------------------#
#Read each csv file, extract from, to, date, subject, body
#write out with folder name
#-------------------------------------------------------------------#


#-------------------------------------------------------------------#
# Libs
#-------------------------------------------------------------------#
import pandas as pd
import sys, os
import re
#https://stackoverflow.com/questions/17245415/read-and-write-csv-files-including-unicode-with-python-2-7
import csv

#-------------------------------------------------------------------#
# Globals and settings
#-------------------------------------------------------------------#
#Put path to data directory here
myDataDir = "c:\\Users\\pviechnicki\\Desktop\\pviechnicki_home\\sandbox\\state\\data\\pv_email"


#Put the names of your own email export files here
files = ['email_mission_analytics.csv', 'email_future_of_work.csv',
         'email_fraud_waste_abuse.csv', 'email_workforce_analytics.csv']


try:
    os.chdir(myDataDir)
except Exception as e:
    sys.stderr.write("Couldn't change to directory {}:{}\n".format(myDataDir, str(e)))


with open('combined_emails.csv', 'w+', encoding='utf-8') as fout:
    writer=csv.writer(fout, quoting=csv.QUOTE_MINIMAL,
                      delimiter="|")
    writer.writerow(['subject', 'sender', 'recipient', 'body', 'cat'])
    for file in files:
        lineNo = 0
        myCat = re.search('email_(.*)\.csv', file).group(1)
        with open(file, 'r', encoding='ISO-8859-1') as fin:

            reader = csv.reader(fin)
            for line in reader:
                if (lineNo > 0):
                    #Don't write out headers again
                    subject = line[0]
                    body = line[1].replace('\n', '')
                    sender = line[2]
                    recipient = line[5]
                    cat = myCat
                    writer.writerow([subject, sender, recipient, body, cat])
                lineNo += 1
        
