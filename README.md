### BMS - Building Management System

#### Hardware
1 - Raspberry Pi
1 - DHT11
1 - 16x2 LCD
4 - Push buttons
3 - LEDS
1 - PIR Sensor

#### Lab Report
[https://github.com/andyyang2003/BMS/blob/main/Final%20Project%20EECS%20113.pdf
](https://github.com/andyyang2003/BMS/blob/main/Final%20Project%20EECS%20113.pdf)

Ambient light control: Your BMS should be able to detect human presence in the room and sub-
sequently turn on the lights (represented by GREEN LED). Use the PIR sensor to implement this
function. To save energy, turn off the lights if no motion is detected for 10 seconds. Ambient lighting
status should always be displayed on the LCD (on/off).\
Room temperature (HVAC): There are two input data for the HVAC system: the temperature and \
the humidity. Your BMS should retrieve ambient temperature from the DHT-11 sensor once every 1 \
second and average the last three measurements to eliminate possible mistakes in measurements. \
Round the measurements to the nearest number. Although DHT-11 can provide the humidity as well, \
we do not trust the measurements (!) and will get the local humidity from the CIMIS system. \
Based on the nearest station to you (Irvine station \
if you live in Irvine), humidity value needs to be extracted from CIMIS API\
Calculate a weather index \
using the following equation: \
weatherindex = temperature + 0.05 ∗ humidity \
example: weatherindex = 71 + 0.05 ∗ 80 = 75 \ 
Round the measurements to the nearest number. This weather index is also referred to as the ”feels \
like temperature”. It is more useful since the more humidity in the air, the hotter it feels. We try to \
compensate the humidity feeling by adjusting the input temperature. Compare the weather index with \ 
the user input temperature and enable the HVAC accordingly. User should be able to seamlessly set the \
desired temperature in range of [65 - 95] degrees using two push buttons. The input buttons should be \
implemented using external interrupts. To avoid constant switching between the heater (RED LED) \
and the AC (BLUE LED), you must implement a hysteresis-like function that will set the AC on only \
if the weather index is 3 degrees above the desired temperature. Same goes for the heater (3 degrees \
below the set temperature). To conserve energy, the HVAC should be turned off temporarily while \ 
the doors or windows are open. Display concise information, including the weather index, the desired \
temperature and the HVAC status (off/AC/heat) on the LCD. Any action regarding the HVAC system \
should be announced on the entire LCD. For instance, when the AC is turning on, the entire LCD should \
be erased and a single notification should appear as ”AC is on” for 3 seconds. The display goes back \
to normal after 3 seconds. \
Fire Alarm system: If the weather index rises above 95 degrees, the BMS assumes that there is a \
fire going on and will automatically opens the door/window, turns off the HVAC, and flashes the lights\
(1 second period). The LCD should show an emergency message (along with door status) and notify\
people to evacuate the building. Things will get back to normal when the temperature goes below 95\
degrees. \
Security system: The room has one entrance (door) and one window, both of which are equipped \
with security sensors, and represented by one push button (one button for both). When the button \
status changes, display a warning message such as “door/window open!” or ”door/window closed!” on \
the entire LCD for 3 seconds. Do not forget to turn off the HVAC while the door/window is open. \
Also, always display the door/window status as open/closed or open/safe on the LCD. \ 
