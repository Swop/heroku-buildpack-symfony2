from log import Logger
import subprocess, os

def singleton(cls):
    """Return a singleton of the class
    """
    instances = {}
    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getinstance

@singleton
class App:
    def __init__(self):
        self._root_dir = '/app/www'
        self._app_dir = self._root_dir+'/app'
        self._web_dir = self._root_dir+'/web'
        self.logger = Logger()

    def hello(self):
        self.logger.log('Hello!')

    def launch(self):
        self.logger.log("Launch application")
        self.logger.increase_indentation()

        self.logger.log("Create write-able cache directory")
        if os.path.isdir(self._app_dir+'/cache'):
            os.rmdir(self._app_dir+'/cache')

        if os.path.isdir('/tmp/sf-cache'):
            os.rmdir('/tmp/sf-cache')
        
        os.mkdir('/tmp/sf-cache')
        os.symlink('/tmp/sf-cache', self._app_dir+'/cache')

        self.logger.log("Enabled Sf2 logging system")
        open(self._app_dir+'logs/prod.log', "a")
        open(self._app_dir+'logs/dev.log', "a")
        proc_tail_sf2logs_prod = subprocess.Popen(['tail', '-F', '-n', '0', self._app_dir+'logs/prod.log'])
        proc_tail_sf2logs_dev = subprocess.Popen(['tail', '-F', '-n', '0', self._app_dir+'logs/dev.log'])

        self.logger.log("Enabled Nginx logging system")
        open('/app/vendor/nginx/logs/access.log', "a")
        open('/app/vendor/nginx/logs/error.log', "a")
        os.mkdir('client_body_temp')
        os.mkdir('fastcgi_temp')
        os.mkdir('proxy_temp')
        os.mkdir('scgi_temp')
        os.mkdir('uwsgi_temp')
        proc_tail_nginx_access = subprocess.Popen(['tail', '-F', '-n', '0', '/app/vendor/nginx/logs/access.log'])
        proc_tail_nginx_error = subprocess.Popen(['tail', '-F', '-n', '0', '/app/vendor/nginx/logs/error.log'])

        self.logger.log("Enabled PHP logging system")
        os.mkdir('/app/vendor/php/log')
        open('/app/vendor/php/log/php-fpm.log', "a")
        proc_tail_php = subprocess.Popen(['tail', '-F', '-n', '0', '/app/vendor/php/log/php-fpm.log'])

        self.logger.log("Enabled NewRelic logging system")
        open('/app/vendor/php/log/newrelic-agent.log', "a")
        open('/app/vendor/php/log/newrelic-daemon.log', "a")
        proc_tail_newrelic_agent = subprocess.Popen(['tail', '-F', '-n', '0', '/app/vendor/php/log/newrelic-agent.log'])
        proc_tail_newrelic_daemon = subprocess.Popen(['tail', '-F', '-n', '0', '/app/vendor/php/log/newrelic-daemon.log'])

        self.logger.log("Booting NewRelic")
        proc_newrelic = subprocess.Popen(['newrelic-daemon.x64', '-c', '/app/vendor/newrelic/newrelic.cfg'])

        self.logger.log("Booting PHP-FPM")
        proc_newrelic = subprocess.Popen(['newrelic-daemon.x64', '-c', '/app/vendor/newrelic/newrelic.cfg'])

        self.logger.log("Booting Nginx")
        proc_newrelic = subprocess.Popen(['newrelic-daemon.x64', '-c', '/app/vendor/newrelic/newrelic.cfg'])

        self.logger.increase_indentation()
        self.logger.log("Application started!")

    def run_sf2_command(self, command):
        subprocess.call('php /app/www/app/console '+command, shell=True)