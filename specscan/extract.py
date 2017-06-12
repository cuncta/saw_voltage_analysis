import sys
import specscan_V0_03 as specscan

spec=specscan.SpecFile('d:/Profile/jny/Desktop/Work/Measurements/2017-04-14-Roschupkin/2017-04-22-LMB01_01.spec')

for i in range(80,100):
    a=spec.get_scan(i)
    print "\nscan No:",i
    print "RF_ON", a.data["rf_ON"]
    print "Voltage", a.data["rf_V"]
    print "Theta", a.data["Theta"]
    print "Detector", type(a.data["Detector"])
    