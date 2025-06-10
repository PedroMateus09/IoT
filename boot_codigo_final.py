# boot.py -- run on boot-up
from machine import I2C
from AXP2101 import AXP2101

SDA = 'G21'
SCL = 'G22'
IRQ = 'G35'

I2CBUS = I2C(0, pins = (SDA,SCL)) # sda, scl
PMU = AXP2101(I2CBUS)
PMU.setALDO3Voltage(3300)        # Definir tensão de alimentação saída 4 (3.3V)
PMU.enableALDO3()                # GPS Enabled

PMU.setALDO2Voltage(2800)   # T-Beam LORA VCC 3v3
PMU.enableALDO2()           # Turn on LORA VCC
PMU.disableTSPinMeasure()
PMU.enableTemperatureMeasure()
PMU.enableBattDetection()
PMU.enableVbusVoltageMeasure()
PMU.enableBattVoltageMeasure()
PMU.enableSystemVoltageMeasure()

#PMU.setALDO2Voltage(3300)        # Definir tensão de alimentação saída 4 (3.3V)
#PMU.enableALDO2()
