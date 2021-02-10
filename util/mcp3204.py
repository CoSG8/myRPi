import wiringpi as pi

class mcp3204:
    def __init__( self, ss, speed, vref ):
        self.ss = ss
        self.speed = speed
        self.vref = vref
        
        pi.wiringPiSPISetup( self.ss, self.speed )
        
    def get_value( self, ch ):
        cmd = 0xc0 | ( ch << 3 )
        buffer = cmd << 24
        buffer = buffer.to_bytes( 4, byteorder='big' )
        pi.wiringPiSPIDataRW( self.ss, buffer )
        value = (  buffer[0] << 24 | buffer[1] << 16 | buffer[2] << 8 | buffer[2] )  >> 13
        return value

    def get_volt( self, value ):
        return value * self.vref / float( 4095 )


