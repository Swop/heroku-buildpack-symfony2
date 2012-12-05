from log import Logger
import subprocess, os, shutil, sys, time

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
        myenv = dict(os.environ);
        if 'SF_ENV' in myenv:
            sf_env = myenv['SF_ENV']
        else:
            sf_env = 'prod'

        self.logger.log("Launch application")
        self.logger.increase_indentation()

        self.logger.log("Create write-able cache directory")
        if os.path.isdir(self._app_dir+'/cache'):
            shutil.rmtree(self._app_dir+'/cache')

        if os.path.isdir('/tmp/sf-cache'):
            shutil.rmtree('/tmp/sf-cache')
        
        os.mkdir('/tmp/sf-cache')
        os.symlink('/tmp/sf-cache', self._app_dir+'/cache')

        self.logger.log("Enabled Sf2 logging system")
        open(self._app_dir+'/logs/prod.log', "a")
        open(self._app_dir+'/logs/dev.log', "a")
        sys.stdout.flush()
        proc_tail_sf2logs_prod = subprocess.Popen(['tail', '-F', '-n', '0', self._app_dir+'/logs/prod.log'], env=myenv)
        proc_tail_sf2logs_dev = subprocess.Popen(['tail', '-F', '-n', '0', self._app_dir+'/logs/dev.log'], env=myenv)

        self.logger.log("Enabled Nginx logging system")
        open('/app/vendor/nginx/logs/access.log', "a")
        open('/app/vendor/nginx/logs/error.log', "a")
        os.mkdir('client_body_temp')
        os.mkdir('fastcgi_temp')
        os.mkdir('proxy_temp')
        os.mkdir('scgi_temp')
        os.mkdir('uwsgi_temp')
        sys.stdout.flush()
        proc_tail_nginx_access = subprocess.Popen(['tail', '-F', '-n', '0', '/app/vendor/nginx/logs/access.log'], env=myenv)
        proc_tail_nginx_error = subprocess.Popen(['tail', '-F', '-n', '0', '/app/vendor/nginx/logs/error.log'], env=myenv)

        self.logger.log("Enabled PHP logging system")
        os.mkdir('/app/vendor/php/log')
        open('/app/vendor/php/log/php-fpm.log', "a")
        sys.stdout.flush()
        proc_tail_php = subprocess.Popen(['tail', '-F', '-n', '0', '/app/vendor/php/log/php-fpm.log'], env=myenv)

        self.logger.log("Enabled NewRelic logging system")
        open('/app/vendor/php/log/newrelic-agent.log', "a")
        open('/app/vendor/php/log/newrelic-daemon.log', "a")
        sys.stdout.flush()
        proc_tail_newrelic_agent = subprocess.Popen(['tail', '-F', '-n', '0', '/app/vendor/php/log/newrelic-agent.log'], env=myenv)
        proc_tail_newrelic_daemon = subprocess.Popen(['tail', '-F', '-n', '0', '/app/vendor/php/log/newrelic-daemon.log'], env=myenv)

        self.logger.log("Booting NewRelic")
        sys.stdout.flush()
        proc_newrelic = subprocess.Popen(['/app/vendor/newrelic/newrelic-daemon.x64', '-c', '/app/vendor/newrelic/newrelic.cfg'], env=myenv)

        self.logger.log("Booting PHP-FPM")
        sys.stdout.flush()
        proc_php = subprocess.Popen(['/app/vendor/php/sbin/php-fpm'], env=myenv)

        self.logger.log("Booting Nginx")
        sys.stdout.flush()
        proc_nginx = subprocess.Popen(['/app/vendor/nginx/sbin/nginx'], env=myenv)

        #self.logger.log('Clear application caches')
        #sys.stdout.flush()
        #proc = subprocess.Popen(['/app/vendor/php/bin/php', '-d', 'memory_limit=256M', '/app/www/app/console', 'cache:clear', '--no-debug', '--env='+sf_env], env=myenv)
        #proc.wait()

        self.logger.log('Warming up the cache')
        sys.stdout.flush()
        proc = subprocess.Popen(['/app/vendor/php/bin/php', '-d', 'memory_limit=256M', '/app/www/app/console', 'cache:warmup', '--no-interaction',  '--env='+sf_env], env=myenv)
        proc.wait()

        self.logger.decrease_indentation()
        self.logger.log("Application started!")

    def wait_forever(self)!
        while True:
            time.sleep(10)

    def run_sf2_command(self, command):
        subprocess.call('/app/vendor/php/bin/php /app/www/app/console '+command, shell=True)