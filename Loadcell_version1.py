import RPi.GPIO as GPIO
import time
import sys
import numpy as np
from hx711 import HX711

def cleanAndExit():
    print "Cleaning..."
    GPIO.cleanup()
    print "Bye!"
    sys.exit()

hx = HX711(6, 5)
unit_weight = 0
recent_data = [0]*10
count = 0
total = 0
flag = 0
# I've found out that, for some reason, the order of the bytes is not always the same between versions of python, numpy and the hx711 itself.
# Still need to figure out why does it change.
# If you're experiencing super random values, change these values to MSB or LSB until to get more stable values.
# There is some code below to debug and log the order of the bits and the bytes.
# The first parameter is the order in which the bytes are used to build the "long" value.
# The second paramter is the order of the bits inside each byte.
# According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
hx.set_reading_format("LSB", "MSB")

# HOW TO CALCULATE THE REFFERENCE UNIT
# To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
# In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
# and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
# If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
#hx.set_reference_unit(113)
hx.set_reference_unit(410)

hx.reset()
hx.tare()

def most_common(lst):
    return max(set(lst), key=lst.count)

while True:
    try:
        # These three lines are usefull to debug wether to use MSB or LSB in the reading formats
        # for the first parameter of "hx.set_reading_format("LSB", "MSB")".
        # Comment the two lines "val = hx.get_weight(5)" and "print val" and uncomment the three lines to see what it prints.
        #np_arr8_string = hx.get_np_arr8_string()
        #binary_string = hx.get_binary_string()
        #print binary_string + " " + np_arr8_string
        
        if flag == 1:
            count += 1
        
        if count == 4:
            count = 0
            flag = 0
        # Prints the weight. Comment if you're debbuging the MSB and LSB issue.
        val = round(hx.get_weight(5))
        print "current sample:" ,val
        recent_data[1:10] = recent_data[0:9]
        recent_data[0] =  val
        print "recent 10 data:", recent_data
        
        if recent_data[5] <= 0 and recent_data[4] > 0:
            unit_weight = most_common(recent_data[0:3])
            
        real_weight = most_common(recent_data)
        if real_weight <= 1:
            real_weight = 0
            
        weight_refer = most_common(recent_data[5:10])
        if weight_refer <= 1:
            weight_refer = 0
            
        print "real weight:",real_weight, "refer weight:", weight_refer, "unit weight:", unit_weight
        
        if unit_weight > 1:
            unitInBasket = round(real_weight / unit_weight)
            unitRefer = round(weight_refer / unit_weight)
        else:
            unitInBasket = 0
            unitRefer = 0
        print"unit in the basket:", unitInBasket, "refer unit:", unitRefer
        
        if real_weight > weight_refer and count == 0:
            total += unitInBasket - unitRefer
            flag = 1
            
        print "subtotal:", total
        print "==============="
        
        hx.power_down()
        hx.power_up()
        time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
