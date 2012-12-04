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
class Logger:
    """
    
    """    
    def __init__(self):
        """
        
        """
        self._indent = 1
        self._indent_symbol = "----"
        self._indent_end_symbol = "-> "

    def increase_indentation(self):
        """

        """
        self._indent += 1

    def decrease_indentation(self):
        """

        """
        self._indent -= 1
        if self._indent < 0:
            self._indent = 0

    def log(self, msg, sub_indentation_level = 0):
        """

        """
        print '{}{}'.format(self.compute_prefix(sub_indentation_level), msg)

    def compute_prefix(self, sub_indentation_level = 0):
        return self._indent_symbol * self._indent \
            + self._indent_symbol * sub_indentation_level \
            + self._indent_end_symbol
