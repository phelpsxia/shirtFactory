import RPi.GPIO as GPIO
import time
import sys
import numpy as np
import requests
from flask import Flask, request
from hx711 import HX711

app = Flask(__name__)
hx = ['' for i in range(4) ]
unit_weight = [0 for i in range(4)]
recent_data = [[0]*10 for i in range(4) ]
count = [0 for i in range(4) ]
total = [0 for i in range(4) ]
flag = [0 for i in range(4) ]
val = [0 for i in range(4) ]
real_weight = [0 for i in range(4) ]
unitRefer = [0 for i in range(4) ]
unitInBasket = [0 for i in range(4) ]
weight_refer = [0 for i in range(4) ]
effeciency = [0 for i in range(4) ]
global id


def cleanAndExit():
    print "Cleaning..."
    GPIO.cleanup()
    print "Bye!"
    sys.exit()
    

def init(pin1,pin2,id):
    hx[id] = HX711(pin1, pin2)
    unit_weight[id] = 0
    recent_data[id] = [0]*10
    count[id] = 0
    total[id] = 0
    flag[id] = 0
     
# I've found out that, for some reason, the order of the bytes is not always the same between versions of python, numpy and the hx711 itself.
# Still need to figure out why does it change.
# If you're experiencing super random values, change these values to MSB or LSB until to get more stable values.
# There is some code below to debug and log the order of the bits and the bytes.
# The first parameter is the order in which the bytes are used to build the "long" value.
# The second paramter is the order of the bits inside each byte.
# According to the HX711 Datasheet, the second parameter is MSB so you shouldn't need to modify it.
    hx[id].set_reading_format("LSB", "MSB")

# HOW TO CALCULATE THE REFFERENCE UNIT
# To set the reference unit to 1. Put 1kg on your sensor or anything you have and know exactly how much it weights.
# In this case, 92 is 1 gram because, with 1 as a reference unit I got numbers near 0 without any weight
# and I got numbers around 184000 when I added 2kg. So, according to the rule of thirds:
# If 2000 grams is 184000 then 1000 grams is 184000 / 2000 = 92.
#hx.set_reference_unit(113)
    hx[id].set_reference_unit(100)

    hx[id].reset()
    hx[id].tare()

def most_common(lst):
    return max(set(lst), key=lst.count)

def weight(id):
    val[id] = round(hx[id].get_weight(5))
    if id == 3:
        print "current sample:" , val[id]
    recent_data[id][1:10] = recent_data[id][0:9]
    
    if val[id] >= 0:
        recent_data[id][0] =  val[id]
    else:
        recent_data[id][0] = 0
    
    if most_common(recent_data[id]) == 0:
        empty = 1
    else:
        empty = 0
        
    if id == 3:
        print "recent 10 data:", recent_data[id]
        
    if empty:
        unit_weight[id] = most_common(recent_data[id][0:3])
    
    real_weight[id] = most_common(recent_data[id])
    if real_weight[id] <= 1:
        real_weight[id] = 0
            
    weight_refer[id] = most_common(recent_data[id][5:10])
    if weight_refer[id] <= 1:
        weight_refer[id] = 0
    if id == 3:        
        print "real weight:",real_weight[id], "refer weight:", weight_refer[id], "unit weight:", unit_weight[id]
        
    if unit_weight[id] > 1:
        unitInBasket[id] = round(real_weight[id] / unit_weight[id])
        unitRefer[id] = round(weight_refer[id] / unit_weight[id])
    else:
        unitInBasket[id] = 0
        unitRefer[id] = 0
    if id == 3:
        print "unit in the basket:", unitInBasket[id], "refer unit:", unitRefer[id]
        
    if real_weight[id] > weight_refer[id] and count[id] == 0:
        total[id] += unitInBasket[id] - unitRefer[id]
        flag[id] = 1
    if id == 3:        
        print "subtotal:",total[id]
        print "==============="
        
    hx[id].power_down()
    hx[id].power_up()
    time.sleep(0.05)
    
#@app.route("/main/<int:id>", methods=['GET', 'POST'])    
def main(id):
    init(16,12,0)
    init(24,23,1)
    init(6,5,2)
    init(13,26,3)
    start_time = time.time()
    while True:
    
        # These three lines are usefull to debug wether to use MSB or LSB in the reading formats
        # for the first parameter of "hx.set_reading_format("LSB", "MSB")".
        # Comment the two lines "val = hx.get_weight(5)" and "print val" and uncomment the three lines to see what it prints.
        #np_arr8_string = hx.get_np_arr8_string()
        #binary_string = hx.get_binary_string()
        #print binary_string + " " + np_arr8_string
        try:
            
            if flag[id] == 1:
                count[id] += 1
        
            if count[id] == 4:
                count[id] = 0
                flag[id] = 0
            
            weight(id)
            elapsed_time = time.time() - start_time
            if elapsed_time >= 300:
                effeciency = list(map(operator.sub, total, effeciency))
                start_time = time.time()
                
            id += 1
            if id == 4:
                id = 0
                r = requests.post('',json=({'effeciency': {
                    'worker1':{'total': total[0], 'unitInBasket': unitInBasket[0], 'effeciency': effeciency[0]},
                    'worker2':{'total': total[1], 'unitInBasket': unitInBasket[1], 'effeciency': effeciency[1]},
                    'worker3':{'total': total[2], 'unitInBasket': unitInBasket[2], 'effeciency': effeciency[2]},
                    'worker4':{'total': total[3], 'unitInBasket': unitInBasket[3], 'effeciency': effeciency[3]}}})
                print r
            print "id:" , id
        except (KeyboardInterrupt, SystemExit):
            cleanAndExit()
        # Prints the weight. Comment if you're debbuging the MSB and LSB issue.

#app.run(host='0.0.0.0',port=5000)

    
    
    
