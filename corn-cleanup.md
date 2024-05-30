touch mycron

'''
0 * * * * /home/reform/venv/bin/python /home/reform/reformWeb/cleanup.py
'''

crontab mycron

crontab -l
