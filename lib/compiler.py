from log import Logger
from datetime import datetime
import os, errno, shutil, subprocess, urllib, tarfile, sys, re, tempfile

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
class Compiler:
    """
    
    """    
    def __init__(self, build_parameters):
        """
        
        """
        self._bp = build_parameters
        self.logger = Logger()
        self.deploy_date = datetime.today()

    def compile(self):
      # Create the BUILD and CACHE directories if they don't exists
      self.mkdir_p(self._bp.build_dir)
      self.mkdir_p(self._bp.cache_dir)

      self.logger.log("Symfony2 Heroku Buildpack: Slug compilation start")
      
      self.isolate_app_files()
      self.install_vendors()
      self.install_application()
      self.install_bootscripts()

    def isolate_app_files(self):
      self.logger.increase_indentation()

      os.chdir(self._bp.build_dir)
      self.logger.log("Move application files into 'www' folder")

      self.mkdir_p(self._bp.cache_dir + '/www')
      app_files = os.listdir('.')
      for app_file in app_files:
        shutil.move(app_file, self._bp.cache_dir + '/www')
      shutil.move(self._bp.cache_dir + '/www', '.')

      # keep conf folder
      if os.path.isdir('www/app/heroku'):
        if os.path.isdir('www/app/heroku/'+self._bp.sf_env+'/conf'):
            shutil.copytree('www/app/heroku/'+self._bp.sf_env+'/conf', './conf')
        else:
          self.logger.log('No Heroku conf folder found for Sf env '+self._bp.sf_env+'. Abording...')
          sys.exit(1)
        shutil.rmtree('www/app/heroku')

      # keep Node.js dependency file
      if os.path.isfile('www/package.json'):
        shutil.move('www/package.json', '.')

      # keep Procfile
      if os.path.isfile('www/Procfile'):
        shutil.move('www/Procfile', '.')

      self.logger.decrease_indentation()

    def install_vendors(self):
      self.logger.increase_indentation()
      self.logger.log("Install vendors")
      self.logger.increase_indentation()

      # unpack cache
      if not os.path.isdir('vendor'):
        self.mkdir_p('vendor')

      #TODO : Use cache to store previous version of vendor if it's the same version
      #for DIR in $NGINX_PATH $PHP_PATH ; do
      #  rm -rf $DIR
      #  if [ -d $CACHE_DIR/$DIR ]; then
      #    cp -r $CACHE_DIR/$DIR $DIR
      #  fi
      #done

      # Nginx
      self.logger.log("Install Nginx")
      self.logger.increase_indentation()
      os.chdir(self._bp.build_dir)

      if not os.path.isdir('vendor/nginx'):
        self.mkdir_p('vendor/nginx')
        os.chdir('vendor/nginx')
        
        self.logger.log("Download Nginx...")
        nginx_url = 'https://simpleit-heroku-builds.s3.amazonaws.com/nginx-1.0.11-heroku.tar.gz'
        urllib.urlretrieve(nginx_url, 'nginx.tar.gz', self.print_progression)
        print
        tar = tarfile.open('nginx.tar.gz')
        tar.extractall()
        tar.close()
        os.remove('nginx.tar.gz')
        os.chdir(self._bp.build_dir)
      
      self.logger.log("Install Nginx configuration file")
      conffile = open('conf/nginx.conf', 'w')
      subprocess.call(['erb', 'conf/nginx.conf.erb'], stdout=conffile)
      self.logger.decrease_indentation()

      # PHP
      self.logger.log("Install PHP")
      self.logger.increase_indentation()
      os.chdir(self._bp.build_dir)

      if not os.path.isdir('vendor/php'):
        self.mkdir_p('vendor/php')
        os.chdir('vendor/php')
        
        self.logger.log("Download PHP...")
        php_url = 'https://simpleit-heroku-builds.s3.amazonaws.com/php-5.3.10-with-fpm-sundown-heroku.tar.gz'
        urllib.urlretrieve(php_url, 'php.tar.gz', self.print_progression)
        print
        tar = tarfile.open('php.tar.gz')
        tar.extractall()
        tar.close()
        os.remove('php.tar.gz')
        os.chdir(self._bp.build_dir)
      
      self.logger.log("Install PHP configuration file")
      shutil.copyfile('conf/php-fpm.conf', 'vendor/php/etc/php-fpm.conf')
      shutil.copyfile('vendor/php/share/php/fpm/status.html', 'status.html')
      shutil.copyfile('conf/php.ini', 'vendor/php/php.ini')
      self.logger.decrease_indentation()

      # NewRelic
      self.logger.log("Install NewRelic")
      self.logger.increase_indentation()
      os.chdir(self._bp.build_dir)

      if not os.path.isdir('vendor/newrelic'):
        self.mkdir_p('vendor/newrelic')
        os.chdir('vendor/newrelic')
        
        self.logger.log("Download NewRelic...")
        newrelic_url = 'https://simpleit-heroku-builds.s3.amazonaws.com/newrelic-php5-2.7.5.64-linux.tar.gz'
        urllib.urlretrieve(newrelic_url, 'newrelic.tar.gz', self.print_progression)
        print
        tar = tarfile.open('newrelic.tar.gz')
        tar.extractall()
        tar.close()
        os.remove('newrelic.tar.gz')
        os.chdir(self._bp.build_dir)

      self.logger.log("Install NewRelic configuration file")
      conffile = open('vendor/newrelic/newrelic.cfg', 'w')
      subprocess.call(['erb', 'vendor/newrelic/scripts/newrelic.cfg.template.erb'], stdout=conffile)
      self.logger.decrease_indentation()
      
      # PHP Extensions
      self.logger.log("Install PHP extensions")
      self.logger.increase_indentation()

      if not os.path.isdir('vendor/php/ext'):
        self.mkdir_p('vendor/php/ext')
      self.logger.log("NewRelic")
      shutil.copyfile('vendor/newrelic/agent/newrelic-20090626.so', 'vendor/php/ext/newrelic-20090626.so')
      self.logger.log("Sundown")
      shutil.copyfile('vendor/php/lib/php/extensions/no-debug-non-zts-20090626/sundown.so', 'vendor/php/ext/sundown.so')
      self.logger.decrease_indentation()
      
      self.logger.log("Enabled PHP extensions")
      self.logger.increase_indentation()

      f = open('vendor/php/php.ini', 'a')
      f.write('extension_dir=/app/vendor/php/ext\n')
      self.logger.log("NewRelic")
      subprocess.call(['erb', 'vendor/newrelic/scripts/newrelic.ini.template.erb'], stdout=conffile)
      self.logger.log("Sundown")
      f.write('extension=sundown.so\n')
      self.logger.decrease_indentation()

      # NodeJS
      self.logger.log("Install Node")
      self.logger.increase_indentation()
      os.chdir(self._bp.build_dir)

      if not os.path.isdir('vendor/node'):
        self.mkdir_p('vendor/node')
        os.chdir('vendor/node')

        self.logger.log("Download Node...")
        node_version = '0.6.18'
        php_url = 'https://simpleit-heroku-builds.s3.amazonaws.com/node-'+node_version+'-heroku.tar.gz'
        urllib.urlretrieve(php_url, 'node.tar.gz', self.print_progression)
        print
        tar = tarfile.open('node.tar.gz')
        tar.extractall()
        tar.close()
        os.remove('node.tar.gz')

      os.chdir(self._bp.build_dir)
      myenv = dict(os.environ)
      myenv['PATH'] = self._bp.build_dir+'/vendor/node/bin:'+myenv['PATH']
      myenv['INCLUDE_PATH'] = self._bp.build_dir+'/vendor/node/include'
      myenv['CPATH'] = myenv['INCLUDE_PATH']
      myenv['CPPPATH'] = myenv['INCLUDE_PATH']

      cache_store_dir = self._bp.cache_dir+'/node_modules/'+node_version
      cache_target_dir = self._bp.build_dir+'node_modules'

      # unpack existing cache
      if os.path.isdir(cache_store_dir):
        # move existing node_modules out of the way
        if os.path.isdir(cache_target_dir):
          shutil.rmtree(cache_target_dir)
        # copy the cached node_modules in
        shutil.move(cache_store_dir, cache_target_dir)

      # install dependencies with npm
      self.logger.log("Installing Node dependencies")
      sys.stdout.flush()
      proc = subprocess.Popen(['npm', 'install'], env=myenv)
      proc.wait()
      proc = subprocess.Popen(['npm', 'rebuild'], env=myenv)
      proc.wait()

      # repack cache with new assets
      if os.path.isdir(cache_store_dir):
        shutil.rmtree(cache_store_dir)
        shutil.move(cache_target_dir, cache_store_dir)

      self.logger.decrease_indentation()
      self.logger.decrease_indentation()

    def install_application(self):
      self.logger.increase_indentation()
      self.logger.log("Install application")

      self.logger.increase_indentation()
      # This is clearly a hack but it allows PHP to find its php.ini
      self.logger.log('Adding a php.ini in /app/vendor/php (hacky but needed)')
      if os.path.isfile('/app/vendor/php/php.ini'):
        self.logger.log('A php.ini already exists in /app/vendor/php so cannot apply the hack for our conf')
        sys.exit(1)
      if not os.path.isdir('/app/vendor/php'):
        os.symlink(self._bp.build_dir+'/vendor/php', '/app/vendor/php')

      # This is clearly a hack but it allows Node to work during compilation time
      self.logger.log('Symlink /app/vendor/node (hacky but needed)')
      if not os.path.isdir('/app/vendor/node'):
        os.symlink(self._bp.build_dir+'/vendor/node', '/app/vendor/node')


      myenv = dict(os.environ)

      previous_ld_library_path = None
      if 'LD_LIBRARY_PATH' in myenv:
        previous_ld_library_path = myenv['LD_LIBRARY_PATH']
      myenv['LD_LIBRARY_PATH'] = self._bp.build_dir+'/vendor/php/icu/lib:'+self._bp.build_dir+'/vendor/php/ext'
      if previous_ld_library_path:
        myenv['LD_LIBRARY_PATH'] = myenv['LD_LIBRARY_PATH']+':'+previous_ld_library_path
      myenv['PATH'] = self._bp.build_dir+'/vendor/php/bin:'+myenv['PATH']

      if 'DATABASE_URL' in myenv:
        self.logger.log('Parsing Heroku database url')
        pg_url = myenv['DATABASE_URL']
        pattern = re.compile('postgres://([^:]+):([^@]+)@([\.\-_a-zA-Z0-9]+):?([0-9]{0,5})/(.+)')
        res = pattern.search(pg_url)
        myenv['HEROKU_DATABASE_USER'] = res.group(1)
        myenv['HEROKU_DATABASE_PASSWORD'] = res.group(2)
        myenv['HEROKU_DATABASE_HOST'] = res.group(3)
        myenv['HEROKU_DATABASE_PORT'] = res.group(4)
        myenv['HEROKU_DATABASE_DB'] = res.group(5)

        # The following steps are very linked to our application. This will be fixed as soon as possible
        if(myenv['HEROKU_DATABASE_PORT'] == ''):
            myenv['HEROKU_DATABASE_PORT'] = '5432'

        myenv['SDZ_DATABASE_HOST'] = myenv['SDZ_DATABASE_TEST_HOST'] = myenv['HEROKU_DATABASE_HOST']
        myenv['SDZ_DATABASE_PORT'] = myenv['SDZ_DATABASE_TEST_PORT'] = myenv['HEROKU_DATABASE_PORT']
        myenv['SDZ_DATABASE_DB'] = myenv['SDZ_DATABASE_TEST_DB'] = myenv['HEROKU_DATABASE_DB']
        myenv['SDZ_DATABASE_USER'] = myenv['SDZ_DATABASE_TEST_USER'] = myenv['SDZ_DATABASE_SESSION_USER'] = myenv['HEROKU_DATABASE_USER']
        myenv['SDZ_DATABASE_PASSWORD'] = myenv['SDZ_DATABASE_TEST_PASSWORD'] = myenv['SDZ_DATABASE_SESSION_PASSWORD'] = myenv['HEROKU_DATABASE_PASSWORD']

        myenv['SDZ_DATABASE_SESSION_DSN'] = "'pgsql:dbname="+myenv['HEROKU_DATABASE_DB']+";host="+myenv['HEROKU_DATABASE_HOST']+";port="+myenv['HEROKU_DATABASE_PORT']+"'"
        myenv['SDZ_ASSETS_VERSION'] = self.deploy_date.strftime("%Y%m%d%H%M%S")

      # Composer
      # check if we have Composer dependencies and vendors are not bundled
      if os.path.isfile('www/composer.json'):
        self.logger.log("Composer")

        # Use cache to restopre vendors
        if os.path.isdir(self._bp.cache_dir+'/www/vendor'):
          self.logger.log("Previous installed vendors founded in cache folder", 1)
          if os.path.isdir('www/vendor'):
            shutil.rmtree('www/vendor')
          shutil.copytree(self._bp.cache_dir+'/www/vendor', 'www/vendor')
          
        git_dir_origin = None      
        if 'GIT_DIR' in myenv:
          git_dir_origin = myenv['GIT_DIR']
          del myenv['GIT_DIR']
        
        self.logger.log("Download Composer PHAR script...", 1)
        composer_url = 'http://getcomposer.org/composer.phar'
        urllib.urlretrieve(composer_url, 'www/composer.phar', self.print_progression)
        print

        os.chdir(self._bp.build_dir+'/www')

        #Delete previous parameters.yml file if present
        if os.path.isfile('app/config/parameters.yml'):
          os.remove('app/config/parameters.yml')

        self.logger.log('Install Composer dependencies', 1)
        sys.stdout.flush()
        proc = subprocess.Popen(['php', 'composer.phar', 'install', '--prefer-source', '--optimize-autoloader', '--no-interaction'], env=myenv)
        proc.wait()

        os.chdir(self._bp.build_dir)

        self.logger.log('Delete Composer PHAR script', 1)
        os.remove('www/composer.phar') 

        #export GIT_DIR=$GIT_DIR_ORIG

        # Store installed vendors into cache
        self.logger.log("Store vendors in cache folder for next compilation", 1)
        if os.path.isdir(self._bp.cache_dir+'/www/vendor'):
          shutil.rmtree(self._bp.cache_dir+'/www/vendor')
          shutil.copytree('/www/vendor', self._bp.cache_dir+'/www/vendor')
      
      self.logger.log('Delete sub \'.git\' folder for each vendor')
      if os.path.isdir('www/vendor'):
        sys.stdout.flush()
        proc = subprocess.Popen(['find', 'www/vendor', '-name', '.git', '-type', 'd'], stdout=subprocess.PIPE)
        for line in proc.stdout:
          shutil.rmtree(line.rstrip())
        proc.wait()

      self.logger.log('Install assets')
      sys.stdout.flush()
      proc = subprocess.Popen(['php', 'www/app/console', 'assets:install', 'www/web', '--env='+self._bp.sf_env], env=myenv)
      proc.wait()
      self.logger.log('Process Assetic dump')
      sys.stdout.flush()
      proc = subprocess.Popen(['php', 'www/app/console', 'assetic:dump', '--no-debug', '--env='+self._bp.sf_env], env=myenv)
      proc.wait()

      self.logger.decrease_indentation()
      self.logger.decrease_indentation()

    def install_bootscripts(self):
      self.logger.increase_indentation()
      self.logger.log("Install boot & utilities scripts")

      shutil.copytree(self._bp.lp_dir+'/lib', self._bp.build_dir+'/lib')
      os.symlink('./lib/sf', './sf')

      self.logger.decrease_indentation()



    def print_progression(self, transferred_blocks, block_size, total_size):
      if(total_size != -1):
        percentage = round(transferred_blocks * block_size * 100 / total_size)
        #self.logger.log(percentage)
        #print '\r{0}'.format(percentage),
        sys.stdout.write('%s%d%%\r' % (self.logger.compute_prefix(1), percentage))
        sys.stdout.flush()


    def mkdir_p(self, path):
      try:
          os.makedirs(path)
      except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
          pass
        else: raise