class Logger:
    def __init__(self, header, objects):
        self.header = header
        self.objects = objects
        
    def info(self, str):
        w = self.header + ': ' + str
        if not w.endswith('\n'):
            w+='\n'
        for object in self.objects:
            object.write(w)
            object.flush()
            