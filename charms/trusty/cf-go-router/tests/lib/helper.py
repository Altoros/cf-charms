import requests

def finish_setup(unit, user='admin', password=None):
    h = {'User-Agent': 'Mozilla/5.0 Gecko/20100101 Firefox/12.0',
         'Content-Type': 'application/x-www-form-urlencoded',
         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*',
         'Accept-Encoding': 'gzip, deflate'}

#    r = requests.post('http://%s/wp-admin/install.php?step=2' % unit,
#                      headers=h, data={'weblog_title': 'Amulet Test %s' % unit,
#                     'user_name': user, 'admin_password': password,
#                     'admin_email': 'test@example.tld',
#                     'admin_password2': password,
#                     'Submit': 'Install WordPress'})
