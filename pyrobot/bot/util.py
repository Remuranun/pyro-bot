import util
import time
import struct

def pad(n):
    return struct.pack('%dx'%n)

def packByte(n):
    return struct.pack('B', n)

def packWord(n):
    return struct.pack('H', n)

def packInt(n):
    return struct.pack('I', n)

def setByte(buffer, offset, byte):
    s = packByte(byte)
    
    buffer[offset] = byte
        
def setWord(buffer, offset, word):
    s = packInt(word)
    print repr(buffer), repr(s)
    buffer[offset] = s[0]
    buffer[offset+1] = s[1]

def setInt(buffer, offset, int):
    s = packInt(int)
    for i in range(0, 4):
        buffer[offset + i] = s[i] 
        
def toHex(string):
    result=''
    for char in string:
        result += '%x '%ord(char)
    return result

def getTickCount(n):
    a=int(time.time()*1000);
    return struct.pack("Q", a)[0:n];

def getPos(b0, b1, b2):
        x = (b0 << 2) + (b1 >> 6)
        y = ((b1&0x3f)<<4) + (b2 >> 4)
        return (x, y)
    
def getPos2(b0, b1, b2, b3, b4, b5):
        x0 = (b0 << 2) + (b1 >> 6) 
        y0 = ((b1 & 0x3f) << 4) + (b2 >> 4)
        x1 = ((b2 & 0xf) << 6) + (b3 >> 2)
        y1 = ((b3 & 0x03) << 8) + b4
        
        return x0, y0, x1, y1
    
def getConfig(config, key):
    values = filter(lambda (k, _): key == k, config)
    if len(values) > 0:
        return values[0][1]
    return None