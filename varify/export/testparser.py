import vcf
from cStringIO import StringIO

class Testparser(object):
    stream = None

    def __init__(buffer):
        
        stream = vcf.Reader()
        

