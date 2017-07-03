#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess


def compileUI():
    fld = os.path.dirname(__file__)
    for fl in os.listdir(fld):
        if fl.endswith('.ui'):
            prog = 'pyuic4 --from-imports'
            o = '%s\%s.py' % (fld, fl.split('.')[0])
            # print fl
            # print o
            out = open(o, 'w')
        elif fl.endswith('.qrc'):
            prog = 'pyrcc4 -py2'
            out = open('%s\%s_rc.py' % (fld, fl.split('.')[0]), 'w')
        else:
            prog = ''
            out = None
        if prog and out:
            out.write('# -*- coding: utf-8 -*-\n')
            run = '%s "%s\%s"' % (prog, fld, fl)
            # print run 
            for line in subprocess.check_output(run, shell=True).split('\n'):
                if not line.startswith('#'):
                    out.write('%s' % line)


if __name__ == '__main__':
    compileUI()