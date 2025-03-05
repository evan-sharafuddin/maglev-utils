import mcp3008
import RPi.GPIO as GPIO

adc=mcp3008.MCP3008(Vdd_hi=True)
while(True):
    out=adc.read(7)
    print("ADC reading")
    print(out)
        
