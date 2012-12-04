from log import Logger
import os, errno, shutil, subprocess, urllib, tarfile, sys, re

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

    def compile(self):
      # Create the BUILD and CACHE directories if they don't exists
      self.mkdir_p(self._bp.build_dir)
      self.mkdir_p(self._bp.cache_dir)

      self.logger.log("Symfony2 Heroku Buildpack: Slug compilation start")
      
      self.isolate_app_files()
      self.install_vendors()
      self.install_application()

    def isolate_app_files(self):
      env = 'prod'
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
        if os.path.isdir('www/app/heroku/'+env+'/conf'):
            shutil.copytree('www/app/heroku/'+env+'/conf', './conf')
        else:
          self.logger.log('No Heroku conf folder found for Sf env '+env+'. Abording...')
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

      f= open('vendor/php/php.ini', 'a')
      f.write('extension_dir=/app/vendor/php/ext\n')
      #self.logger.log("NewRelic")
      self.logger.log("Sundown")
      f.write('extension=sundown.so\n')
      self.logger.decrease_indentation()
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
        self.mkdir_p('/app/vendor/php')
      os.symlink(self._bp.build_dir+'/vendor/php/php.ini', '/app/vendor/php/php.ini')

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

      # Composer
      # check if we have Composer dependencies and vendors are not bundled
      if os.path.isfile('www/composer.json'):
        self.logger.log("Composer")
          
        git_dir_origin = None      
        if 'GIT_DIR' in myenv:
          git_dir_origin = myenv['GIT_DIR']
          del myenv['GIT_DIR']
        
        self.logger.log("Download Composer PHAR script...")
        composer_url = 'http://getcomposer.org/composer.phar'
        urllib.urlretrieve(composer_url, 'www/composer.phar', self.print_progression)
        print

        os.chdir('www')
        self.logger.log('Install Composer dependencies')
        subprocess.Popen(['php', 'composer.phar', 'install', '--prefer-source', '--optimize-autoloader', '--no-interaction'], env=myenv)

        os.chdir(self._bp.build_dir)

        self.logger.log('Delete Composer PHAR script')
        os.remove('www/composer.phar') 

        #export GIT_DIR=$GIT_DIR_ORIG
      
      # Delete sub '.git' folders for each vendor
      if os.path.isdir('www/vendor'):
        proc = subprocess.Popen(['find', 'www/vendor', '-name', '.git', '-type', 'd'], stdout=subprocess.PIPE)
        for line in proc.stdout:
          #the real code does filtering here
          print "test:", line.rstrip()
        #find www/vendor -name .git -type d | xargs rm -rf
      


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