import os
import yaml


class ConfigReader:
    def __init__(self, cpath=None):
        files = [
            os.path.join(cdir, 'config.yml')
            for cdir in (os.getcwd(), os.path.dirname(__file__))
        ]
        if cpath:
            files.insert(0, cpath)
        for fname in files:
            try:
                fobj = open(fname, 'r')
            except IOError:
                pass
            else:
                self.data = yaml.full_load(fobj)
                fobj.close()
                return
        raise Exception("None of config files (%s) found" % files)

    def __getitem__(self, key):
        return self.data.get(key, '')
