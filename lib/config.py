import os

class BuildParameters:
    """Build parameters storage class
    This class store the build parameters and other info used for the building process
    """    
    def __init__(self, folders):
        """Initialize the storage object
        
        Argument:
        - folders : a dictionary with these required elements:
            - build_dir: the root folder used to bundle the slug
            - cache_dir: the folder used to store/get files to be available between each slug compilation
            - bin_dir: the folder of the cloned buildpack
            - lp_dir: the parent of the cloned buildpack
        """
        self._build_dir = folders['build_dir']
        self._cache_dir = folders['cache_dir']
        self._bin_dir = folders['bin_dir']
        self._lp_dir = folders['lp_dir']

        my_env = dict(os.environ)
        if 'SF_ENV' in my_env:
            self._sf_env = my_env['SF_ENV']
        else
            self._sf_env = 'prod'

    @property
    def build_dir(self):
        return self._build_dir

    @property
    def cache_dir(self):
        return self._cache_dir

    @property
    def bin_dir(self):
        return self._bin_dir

    @property
    def lp_dir(self):
        return self._lp_dir

    @property
    def sf_env(self):
        return self._sf_env

    def str(self):
        return 'build_dir: {}\ncache_dir: {}\nbin_dir: {}\nlp_dir: {}'.format(
            self._build_dir, self._cache_dir, self._bin_dir, self._lp_dir)