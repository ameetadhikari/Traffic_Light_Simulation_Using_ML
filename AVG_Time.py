import random
import time
import threading
import pygame
import sys
import matplotlib.pyplot as plt
import numpy as np

# Default values of signal timers
defaultGreen = {0: 10, 1: 10, 2: 10, 3: 10}
defaultRed = 150
defaultYellow = 5

signals = []
noOfSignals = 4
currentGreen = 0  # Indicates which signal is green currently
nextGreen = (currentGreen + 1) % noOfSignals  # Indicates which signal will turn green next
currentYellow = 0  # Indicates whether yellow signal is on or off

speeds = {'car': 2.0, 'bus': 1.8, 'truck': 2, 'bike': 2.0, 'emergency': 3.0}  # Average speeds of vehicles including emergency vehicle

# Coordinates of vehicles' start
x = {'right': [0, 0, 0], 'down': [755, 727, 697], 'left': [1400, 1400, 1400], 'up': [602, 627, 657]}
y = {'right': [348, 370, 398], 'down': [0, 0, 0], 'left': [498, 466, 436], 'up': [800, 800, 800]}

vehicles = {'right': {0: [], 1: [], 2: [], 'crossed': 0}, 'down': {0: [], 1: [], 2: [], 'crossed': 0}, 'left': {0: [], 1: [], 2: [], 'crossed': 0}, 'up': {0: [], 1: [], 2: [], 'crossed': 0}}
vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike', 4: 'emergency'}
directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

# Coordinates of signal image, timer, and vehicle count
signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]

# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

# Gap between vehicles
stoppingGap = 25  # Stopping gap
movingGap = 25  # Moving gap

# Set allowed vehicle types here
allowedVehicleTypes = {'car': True, 'bus': True, 'truck': True, 'bike': True, 'emergency': False}  # Emergency vehicle set to False initially
allowedVehicleTypesList = []
vehiclesTurned = {'right': {1: [], 2: []}, 'down': {1: [], 2: []}, 'left': {1: [], 2: []}, 'up': {1: [], 2: []}}
vehiclesNotTurned = {'right': {1: [], 2: []}, 'down': {1: [], 2: []}, 'left': {1: [], 2: []}, 'up': {1: [], 2: []}}
rotationAngle = 3
mid = {'right': {'x': 705, 'y': 445}, 'down': {'x': 695, 'y': 450}, 'left': {'x': 695, 'y': 425}, 'up': {'x': 695, 'y': 400}}
# Set random or default green signal time here
randomGreenSignalTimer = True
# Set random green signal time range here
randomGreenSignalTimerRange = [10, 20]

pygame.init()
simulation = pygame.sprite.Group()
emergency_active = False  # Flag to indicate if an emergency vehicle is active
emergency_vehicle_detected = False
emergency_vehicle_passed = False
time_emergency_vehicle_passed = None
emergency_vehicle = None
pygame.mixer.init()
emergency_sound = pygame.mixer.Sound('images/sound.mp3')  

# Initialize the plot
plt.ion()  # Turn on interactive mode
fig, ax = plt.subplots()  # Create a figure and an axes
line, = ax.plot([], [])  # Create a line object for the plot (initially empty)

# Set labels for the axes
ax.set_xlabel('Frames (in hundreds)')
ax.set_ylabel('Average Waiting Time (ms)')
# Set the figure title
plt.title('Average Waiting Time of Normal Simulation')


# Rest of your code...

class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""

class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        self.crossedIndex = 0
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.image = pygame.image.load(path)
        self.exit_triggered = False  # Add this line
        self.stop_time = None  # Time when the vehicle stops at a signal
        self.start_time = None  # Time when the vehicle starts moving
        self.waiting_time = 0  # Total waiting time
        self.has_stopped = False  # Flag to indicate if the vehicle has stopped at the current signal



        destination = None  # Define the variable "destination"
        self.destination = destination  # Assign "destination" to "self.destination"

        if(len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index-1].crossed == 0):   
            if(direction == 'right'):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].image.get_rect().width - stoppingGap         
            elif(direction == 'left'):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].image.get_rect().width + stoppingGap
            elif(direction == 'down'):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].image.get_rect().height - stoppingGap
            elif(direction == 'up'):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].image.get_rect().height + stoppingGap
        else:
            self.stop = defaultStop[direction]
            
        # Set new starting and stopping coordinate
        if(direction=='right'):
            temp = self.image.get_rect().width + stoppingGap    
            x[direction][lane] -= temp
        elif(direction=='left'):
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] += temp
        elif(direction=='down'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= temp
        elif(direction=='up'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    # Add methods to set stop and start times
    def set_stop_time(self, time):
        self.stop_time = time

    def set_start_time(self, time):
        if self.stop_time is not None:
            self.start_time = time
            self.waiting_time += self.start_time - self.stop_time
            self.stop_time = None  # Reset stop time for the next stop

    def move(self):
        global currentGreen, currentYellow, vehicles, vehiclesNotTurned, vehiclesTurned, movingGap

        if self.vehicleClass == 'emergency':
            # Move emergency vehicles with moving gap
            if self.direction == 'right':
                if self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[self.direction]:
                    self.crossed = 1
                    vehicles[self.direction]['crossed'] += 1
                    if self.willTurn == 0:
                        vehiclesNotTurned[self.direction][self.lane].append(self)
                        self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
                    
                if self.willTurn == 1:
                    if self.lane == 1:
                        if self.crossed == 0 or self.x + self.image.get_rect().width < stopLines[self.direction] + 40:
                            if (self.x + self.image.get_rect().width <= self.stop or (currentGreen == 0 and currentYellow == 0) or self.crossed == 1) and (self.index == 0 or self.x + self.image.get_rect().width < (vehicles[self.direction][self.lane][self.index - 1].x - movingGap) or vehicles[self.direction][self.lane][self.index - 1].turned == 1):
                                self.x += self.speed
                        else:
                            if self.turned == 0:
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x += 2.4
                                self.y -= 2.8
                                if self.rotateAngle == 90:
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if self.crossedIndex == 0 or (self.y > (vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].y + vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].image.get_rect().height + movingGap)):
                                    self.y -= self.speed
                    elif self.lane == 2:
                        if self.crossed == 0 or self.x + self.image.get_rect().width < mid[self.direction]['x']:
                            if (self.x + self.image.get_rect().width <= self.stop or (currentGreen == 0 and currentYellow == 0) or self.crossed == 1) and (self.index == 0 or self.x + self.image.get_rect().width < (vehicles[self.direction][self.lane][self.index - 1].x - movingGap) or vehicles[self.direction][self.lane][self.index - 1].turned == 1):
                                self.x += self.speed
                        else:
                            if self.turned == 0:
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                                self.x -= 2
                                self.y += 1.8
                                if self.rotateAngle == 90:
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if self.crossedIndex == 0 or ((self.y + self.image.get_rect().height) < (vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].y - movingGap)):
                                    self.y += self.speed
                else:
                    if self.crossed == 0:
                        if (self.x + self.image.get_rect().width <= self.stop or (currentGreen == 0 and currentYellow == 0)) and (self.index == 0 or self.x + self.image.get_rect().width < (vehicles[self.direction][self.lane][self.index - 1].x - movingGap)):
                            self.x += self.speed
                    else:
                        if (self.crossedIndex == 0) or (self.x + self.image.get_rect().width < (vehiclesNotTurned[self.direction][self.lane][self.crossedIndex - 1].x - movingGap)):
                            self.x += self.speed

            elif self.direction == 'down':
                if self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[self.direction]:
                    self.crossed = 1
                    vehicles[self.direction]['crossed'] += 1
                    if self.willTurn == 0:
                        vehiclesNotTurned[self.direction][self.lane].append(self)
                        self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
                if self.willTurn == 1:
                    if self.lane == 1:
                        if self.crossed == 0 or self.y + self.image.get_rect().height < stopLines[self.direction] + 50:
                            if (self.y + self.image.get_rect().height <= self.stop or (currentGreen == 1 and currentYellow == 0) or self.crossed == 1) and (self.index == 0 or self.y + self.image.get_rect().height < (vehicles[self.direction][self.lane][self.index - 1].y - movingGap) or vehicles[self.direction][self.lane][self.index - 1].turned == 1):
                                self.y += self.speed
                        else:
                            if self.turned == 0:
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x += 1.2
                                self.y += 1.8
                                if self.rotateAngle == 90:
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if self.crossedIndex == 0 or ((self.x + self.image.get_rect().width) < (vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].x - movingGap)):
                                    self.x += self.speed
                    elif self.lane == 2:
                        if self.crossed == 0 or self.y + self.image.get_rect().height < mid[self.direction]['y']:
                            if (self.y + self.image.get_rect().height <= self.stop or (currentGreen == 1 and currentYellow == 0) or self.crossed == 1) and (self.index == 0 or self.y + self.image.get_rect().height < (vehicles[self.direction][self.lane][self.index - 1].y - movingGap) or vehicles[self.direction][self.lane][self.index - 1].turned == 1):
                                self.y += self.speed
                        else:
                            if self.turned == 0:
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                                self.x -= 2.5
                                self.y += 2
                                if self.rotateAngle == 90:
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if self.crossedIndex == 0 or (self.x > (vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].x + vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].image.get_rect().width + movingGap)):
                                    self.x -= self.speed
                else:
                    if self.crossed == 0:
                        if (self.y + self.image.get_rect().height <= self.stop or (currentGreen == 1 and currentYellow == 0)) and (self.index == 0 or self.y + self.image.get_rect().height < (vehicles[self.direction][self.lane][self.index - 1].y - movingGap)):
                            self.y += self.speed
                    else:
                        if (self.crossedIndex == 0) or (self.y + self.image.get_rect().height < (vehiclesNotTurned[self.direction][self.lane][self.crossedIndex - 1].y - movingGap)):
                            self.y += self.speed
            
            elif self.direction == 'left':
                if self.crossed == 0 and self.x < stopLines[self.direction]:
                    self.crossed = 1
                    vehicles[self.direction]['crossed'] += 1
                    if self.willTurn == 0:
                        vehiclesNotTurned[self.direction][self.lane].append(self)
                        self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
                if self.willTurn == 1:
                    if self.lane == 1:
                        if self.crossed == 0 or self.x > stopLines[self.direction] - 70:
                            if (self.x >= self.stop or (currentGreen == 2 and currentYellow == 0) or self.crossed == 1) and (self.index == 0 or self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().width + movingGap) or vehicles[self.direction][self.lane][self.index - 1].turned == 1):
                                self.x -= self.speed
                        else:
                            if self.turned == 0:
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x -= 1
                                self.y += 1.2
                                if self.rotateAngle == 90:
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if self.crossedIndex == 0 or ((self.y + self.image.get_rect().height) < (vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].y - movingGap)):
                                    self.y += self.speed
                    elif self.lane == 2:
                        if self.crossed == 0 or self.x > mid[self.direction]['x']:
                            if (self.x >= self.stop or (currentGreen == 2 and currentYellow == 0) or self.crossed == 1) and (self.index == 0 or self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().width + movingGap) or vehicles[self.direction][self.lane][self.index - 1].turned == 1):
                                self.x -= self.speed
                        else:
                            if self.turned == 0:
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                                self.x -= 1.8
                                self.y -= 2.5
                                if self.rotateAngle == 90:
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if self.crossedIndex == 0 or (self.y > (vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].y + vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].image.get_rect().height + movingGap)):
                                    self.y -= self.speed
                else:
                    if self.crossed == 0:
                        if (self.x >= self.stop or (currentGreen == 2 and currentYellow == 0)) and (self.index == 0 or self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().width + movingGap)):
                            self.x -= self.speed
                    else:
                        if (self.crossedIndex == 0) or (self.x > (vehiclesNotTurned[self.direction][self.lane][self.crossedIndex - 1].x + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex - 1].image.get_rect().width + movingGap)):
                            self.x -= self.speed

            elif self.direction == 'up':
                if self.crossed == 0 and self.y < stopLines[self.direction]:
                    self.crossed = 1
                    vehicles[self.direction]['crossed'] += 1
                    if self.willTurn == 0:
                        vehiclesNotTurned[self.direction][self.lane].append(self)
                        self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
                if self.willTurn == 1:
                    if self.lane == 1:
                        if self.crossed == 0 or self.y > stopLines[self.direction] - 60:
                            if (self.y >= self.stop or (currentGreen == 3 and currentYellow == 0) or self.crossed == 1) and (self.index == 0 or self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().height + movingGap) or vehicles[self.direction][self.lane][self.index - 1].turned == 1):
                                self.y -= self.speed
                        else:
                            if self.turned == 0:
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x -= 2
                                self.y -= 1.2
                                if self.rotateAngle == 90:
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if self.crossedIndex == 0 or (self.x > (vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].x + vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].image.get_rect().width + movingGap)):
                                    self.x -= self.speed
                    elif self.lane == 2:
                        if self.crossed == 0 or self.y > mid[self.direction]['y']:
                            if (self.y >= self.stop or (currentGreen == 3 and currentYellow == 0) or self.crossed == 1) and (self.index == 0 or self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().height + movingGap) or vehicles[self.direction][self.lane][self.index - 1].turned == 1):
                                self.y -= self.speed
                        else:
                            if self.turned == 0:
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                                self.x += 1
                                self.y -= 1
                                if self.rotateAngle == 90:
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if self.crossedIndex == 0 or (self.x < (vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].x - vehiclesTurned[self.direction][self.lane][self.crossedIndex - 1].image.get_rect().width - movingGap)):
                                    self.x += self.speed
                else:
                    if self.crossed == 0:
                        if (self.y >= self.stop or (currentGreen == 3 and currentYellow == 0)) and (self.index == 0 or self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().height + movingGap)):
                            self.y -= self.speed
                    else:
                        if (self.crossedIndex == 0) or (self.y > (vehiclesNotTurned[self.direction][self.lane][self.crossedIndex - 1].y + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex - 1].image.get_rect().height + movingGap)):
                            self.y -= self.speed

        else:
    
            if(self.direction=='right'):
                if(self.crossed==0 and self.x+self.image.get_rect().width>stopLines[self.direction]):
                    self.crossed = 1
                    vehicles[self.direction]['crossed'] += 1
                    if(self.willTurn==0):
                        vehiclesNotTurned[self.direction][self.lane].append(self)
                        self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1

                    if not self.has_stopped and (currentGreen != 0 or currentYellow == 1):
                        self.set_stop_time(pygame.time.get_ticks())
                        self.has_stopped = True
                        self.waiting_time = 0 

                if(self.willTurn==1):
                    if(self.lane == 1):
                        if(self.crossed==0 or self.x+self.image.get_rect().width<stopLines[self.direction]+40):
                            if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):               
                                self.x += self.speed
                        else:
                            if(self.turned==0):
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x += 2.4
                                self.y -= 2.8
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if(self.crossedIndex==0 or (self.y>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + movingGap))):
                                    self.y -= self.speed
                    elif(self.lane == 2):
                        if(self.crossed==0 or self.x+self.image.get_rect().width<mid[self.direction]['x']):
                            if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                 
                                self.x += self.speed
                        else:
                            if(self.turned==0):
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                                self.x += 2
                                self.y += 1.8
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if(self.crossedIndex==0 or ((self.y+self.image.get_rect().height)<(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y - movingGap))):
                                    self.y += self.speed
                else: 
                    if(self.crossed == 0):
                        if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap))):                
                            self.x += self.speed
                    else:
                        if((self.crossedIndex==0) or (self.x+self.image.get_rect().width<(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].x - movingGap))):                 
                            self.x += self.speed

                if self.crossed == 0 and currentGreen == 0 and currentYellow == 0 and self.has_stopped:
                    self.waiting_time += pygame.time.get_ticks() - self.stop_time  # Update waiting time
                    self.set_start_time(pygame.time.get_ticks())
                    self.has_stopped = False

            elif(self.direction=='down'):
                if(self.crossed==0 and self.y+self.image.get_rect().height>stopLines[self.direction]):
                    self.crossed = 1
                    vehicles[self.direction]['crossed'] += 1
                    if(self.willTurn==0):
                        vehiclesNotTurned[self.direction][self.lane].append(self)
                        self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1

                    if not self.has_stopped and (currentGreen != 0 or currentYellow == 1):
                        self.set_stop_time(pygame.time.get_ticks())
                        self.has_stopped = True
                        self.waiting_time = 0 

                if(self.willTurn==1):
                    if(self.lane == 1):
                        if(self.crossed==0 or self.y+self.image.get_rect().height<stopLines[self.direction]+50):
                            if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                                self.y += self.speed
                        else:   
                            if(self.turned==0):
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x += 1.2
                                self.y += 1.8
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if(self.crossedIndex==0 or ((self.x + self.image.get_rect().width) < (vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x - movingGap))):
                                    self.x += self.speed
                    elif(self.lane == 2):
                        if(self.crossed==0 or self.y+self.image.get_rect().height<mid[self.direction]['y']):
                            if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                                self.y += self.speed
                        else:   
                            if(self.turned==0):
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                                self.x -= 2.5
                                self.y += 2
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if(self.crossedIndex==0 or (self.x>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))): 
                                    self.x -= self.speed
                else: 
                    if(self.crossed == 0):
                        if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap))):                
                            self.y += self.speed
                    else:
                        if((self.crossedIndex==0) or (self.y+self.image.get_rect().height<(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].y - movingGap))):                
                            self.y += self.speed

                if self.crossed == 0 and currentGreen == 0 and currentYellow == 0 and self.has_stopped:
                    self.waiting_time += pygame.time.get_ticks() - self.stop_time  # Update waiting time
                    self.set_start_time(pygame.time.get_ticks())
                    self.has_stopped = False

            elif(self.direction=='left'):
                if(self.crossed==0 and self.x<stopLines[self.direction]):
                    self.crossed = 1
                    vehicles[self.direction]['crossed'] += 1
                    if(self.willTurn==0):
                        vehiclesNotTurned[self.direction][self.lane].append(self)
                        self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1

                    if not self.has_stopped and (currentGreen != 0 or currentYellow == 1):
                        self.set_stop_time(pygame.time.get_ticks())
                        self.has_stopped = True
                        self.waiting_time = 0 
                        
                if(self.willTurn==1):
                    if(self.lane == 1):
                        if(self.crossed==0 or self.x>stopLines[self.direction]-70):
                            if((self.x>=self.stop or (currentGreen==2 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                                self.x -= self.speed
                        else: 
                            if(self.turned==0):
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x -= 1
                                self.y += 1.2
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if(self.crossedIndex==0 or ((self.y + self.image.get_rect().height) <(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y  -  movingGap))):
                                    self.y += self.speed
                    elif(self.lane == 2):
                        if(self.crossed==0 or self.x>mid[self.direction]['x']):
                            if((self.x>=self.stop or (currentGreen==2 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                                self.x -= self.speed
                        else:
                            if(self.turned==0):
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                                self.x -= 1.8
                                self.y -= 2.5
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if(self.crossedIndex==0 or (self.y>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height +  movingGap))):
                                    self.y -= self.speed
                else: 
                    if(self.crossed == 0):
                        if((self.x>=self.stop or (currentGreen==2 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap))):                
                            self.x -= self.speed
                    else:
                        if((self.crossedIndex==0) or (self.x>(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))):                
                            self.x -= self.speed


                if self.crossed == 0 and currentGreen == 0 and currentYellow == 0 and self.has_stopped:
                    self.waiting_time += pygame.time.get_ticks() - self.stop_time  # Update waiting time
                    self.set_start_time(pygame.time.get_ticks())
                    self.has_stopped = False


            elif(self.direction=='up'):
                if(self.crossed==0 and self.y<stopLines[self.direction]):
                    self.crossed = 1
                    vehicles[self.direction]['crossed'] += 1
                    if(self.willTurn==0):
                        vehiclesNotTurned[self.direction][self.lane].append(self)
                        self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1

                    if not self.has_stopped and (currentGreen != 0 or currentYellow == 1):
                        self.set_stop_time(pygame.time.get_ticks())
                        self.has_stopped = True
                        self.waiting_time = 0 

                if(self.willTurn==1):
                    if(self.lane == 1):
                        if(self.crossed==0 or self.y>stopLines[self.direction]-60):
                            if((self.y>=self.stop or (currentGreen==3 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height +  movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                                self.y -= self.speed
                        else:   
                            if(self.turned==0):
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                                self.x -= 2
                                self.y -= 1.2
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if(self.crossedIndex==0 or (self.x>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))):
                                    self.x -= self.speed
                    elif(self.lane == 2):
                        if(self.crossed==0 or self.y>mid[self.direction]['y']):
                            if((self.y>=self.stop or (currentGreen==3 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height +  movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):
                                self.y -= self.speed
                        else:   
                            if(self.turned==0):
                                self.rotateAngle += rotationAngle
                                self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                                self.x += 1
                                self.y -= 1
                                if(self.rotateAngle==90):
                                    self.turned = 1
                                    vehiclesTurned[self.direction][self.lane].append(self)
                                    self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                            else:
                                if(self.crossedIndex==0 or (self.x<(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x - vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width - movingGap))):
                                    self.x += self.speed
                else: 
                    if(self.crossed == 0):
                        if((self.y>=self.stop or (currentGreen==3 and currentYellow==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height + movingGap))):                
                            self.y -= self.speed
                    else:
                        if((self.crossedIndex==0) or (self.y>(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + movingGap))):                
                            self.y -= self.speed 

                if self.crossed == 0 and currentGreen == 0 and currentYellow == 0 and self.has_stopped:
                    self.waiting_time += pygame.time.get_ticks() - self.stop_time  # Update waiting time
                    self.set_start_time(pygame.time.get_ticks())
                    self.has_stopped = False
                        

# Initialization of signals with default values
def initialize():
    minTime = randomGreenSignalTimerRange[0]
    maxTime = randomGreenSignalTimerRange[1]
    if(randomGreenSignalTimer):
        ts1 = TrafficSignal(0, defaultYellow, random.randint(minTime,maxTime))
        signals.append(ts1)
        ts2 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow, random.randint(minTime,maxTime))
        signals.append(ts2)
        ts3 = TrafficSignal(defaultRed, defaultYellow, random.randint(minTime,maxTime))
        signals.append(ts3)
        ts4 = TrafficSignal(defaultRed, defaultYellow, random.randint(minTime,maxTime))
        signals.append(ts4)
    else:
        ts1 = TrafficSignal(0, defaultYellow, defaultGreen[0])
        signals.append(ts1)
        ts2 = TrafficSignal(ts1.yellow+ts1.green, defaultYellow, defaultGreen[1])
        signals.append(ts2)
        ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[2])
        signals.append(ts3)
        ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[3])
        signals.append(ts4)
    repeat()

def repeat():
    global currentGreen, currentYellow, nextGreen
    while(signals[currentGreen].green>0):   # while the timer of current green signal is not zero
        updateValues()
        time.sleep(1)
    currentYellow = 1   # set yellow signal on
    # reset stop coordinates of lanes and vehicles 
    for i in range(0,3):
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[currentGreen]]
    while(signals[currentGreen].yellow>0):  # while the timer of current yellow signal is not zero
        updateValues()
        time.sleep(1)
    currentYellow = 0   # set yellow signal off
    
    # reset all signal times of current signal to default/random times
    if(randomGreenSignalTimer):
        signals[currentGreen].green = random.randint(randomGreenSignalTimerRange[0],randomGreenSignalTimerRange[1])
    else:
        signals[currentGreen].green = defaultGreen[currentGreen]
    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed
       
    currentGreen = nextGreen # set next signal as green signal
    nextGreen = (currentGreen+1)%noOfSignals    # set next green signal
    signals[nextGreen].red = signals[currentGreen].yellow+signals[currentGreen].green    # set the red time of next to next signal as (yellow time + green time) of next signal
    repeat()  


previousGreen = 0  # Add this line at the top of your file to store the active lane before the emergency
previousSignals = []  # Add this line at the top of your file to store the state of the signals before the emergency

previousState = None  # Add this line at the top of your file to store the state before the emergency

def adjust_signals_for_emergency(emergency_direction):
    global currentGreen
    global currentYellow
    global previousState

    # Store the current state before the emergency
    previousState = (currentGreen, currentYellow, [(signal.green, signal.red, signal.yellow) for signal in signals])

    # Set the current signal to yellow for 3 seconds
    signals[currentGreen].yellow = 3
    currentYellow = 1

    # Start a new thread that will wait for 3 seconds and then adjust the signals
    threading.Thread(target=delayed_adjust_signals, args=(emergency_direction,)).start()


def delayed_adjust_signals(emergency_direction):
    global currentGreen
    global currentYellow

    # Wait for 3 seconds for the yellow light
    time.sleep(3)

    for i in range(len(signals)):
        if i == emergency_direction:
            signals[i].green = float('inf')  # Set green light indefinitely
            signals[i].red = 0
            signals[i].yellow = 0
        else:
            signals[i].green = 0
            signals[i].red = float('inf')  # Set red light indefinitely
            signals[i].yellow = 0

    currentGreen = emergency_direction
    currentYellow = 0

def revert_signals_post_emergency():
    global currentGreen
    global currentYellow

    # Set the current signal to yellow for 3 seconds
    signals[currentGreen].yellow = 3
    currentYellow = 1

    # Start a new thread that will wait for 3 seconds and then revert the signals
    threading.Thread(target=delayed_revert_signals).start()


def delayed_revert_signals():
    global currentGreen
    global currentYellow
    global previousState

    # Wait for 3 seconds for the yellow light
    time.sleep(3)

    # Revert back to the state before the emergency
    currentGreen, currentYellow, previousSignals = previousState
    for i in range(len(signals)):
        signals[i].green, signals[i].red, signals[i].yellow = previousSignals[i]

    # Set the green signal time to a random value within the randomGreenSignalTimerRange
    if randomGreenSignalTimer:
        signals[currentGreen].green = random.randint(*randomGreenSignalTimerRange)
def handle_emergency_vehicle_exit(vehicle):
    print(f"Emergency vehicle {vehicle} has exited the intersection.")
    revert_signals_post_emergency()

# Update values of the signal timers after every second
def updateValues():
    for i in range(0, noOfSignals):
        if(i==currentGreen):
            if(currentYellow==0):
                signals[i].green-=1
            else:
                signals[i].yellow-=1
        else:
            signals[i].red-=1

# Generating vehicles in the simulation
def generateVehicles():
    while(True):
        vehicle_type = random.choice(allowedVehicleTypesList)
        lane_number = random.randint(1,2)
        will_turn = 0
        if(lane_number == 1):
            temp = random.randint(0,99)
            if(temp<40):
                will_turn = 1
        elif(lane_number == 2):
            temp = random.randint(0,99)
            if(temp<40):
                will_turn = 1
        temp = random.randint(0,99)
        direction_number = 0
        dist = [25,50,75,100]
        if(temp<dist[0]):
            direction_number = 0
        elif(temp<dist[1]):
            direction_number = 1
        elif(temp<dist[2]):
            direction_number = 2
        elif(temp<dist[3]):
            direction_number = 3
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number], will_turn)
        time.sleep(1)

class Main:
    global allowedVehicleTypesList
    i = 0
    for vehicleType in allowedVehicleTypes:
        if(allowedVehicleTypes[vehicleType]):
            allowedVehicleTypesList.append(i)
        i += 1
    thread1 = threading.Thread(name="initialization",target=initialize, args=())    # initialization
    thread1.daemon = True
    thread1.start()

    # Colours 
    black = (0, 0, 0)
    white = (255, 255, 255)

    # Screensize 
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load('images/intersection.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("SIMULATION")

    frame_counter = 0


    # Loading signal images and font
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)
    thread2 = threading.Thread(name="generateVehicles",target=generateVehicles, args=())    # Generating vehicles
    thread2.daemon = True
    thread2.start()

    EMERGENCY_EVENT = pygame.USEREVENT + 1

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:  # Check if the 'e' key is pressed
                    global emergency_active  # Ensure this is declared at the top if not already
                    emergency_active = True
                    # Play the sound
                    emergency_sound.play()
                    emergency_direction = random.randint(0, 3)
                    pygame.event.clear(pygame.KEYDOWN)  # Clear the key down event to prevent it from being processed again
                    # Randomly choose a direction for the emergency vehicle
                    adjust_signals_for_emergency(emergency_direction)
                    # Introduce the emergency vehicle into the simulation
                    Vehicle(1, 'emergency', emergency_direction, directionNumbers[emergency_direction], random.randint(0, 1))
                    pygame.display.update()  # Force an update of the display
                    pygame.time.set_timer(EMERGENCY_EVENT, 0)  # Cancel the timer

                    break

        screen.blit(background,(0,0))   # display background in simulation
        for i in range(0,noOfSignals):  # display signal and set timer according to current status: green, yello, or red
            if(i==currentGreen):
                if(currentYellow==1):
                    signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                if(signals[i].red<=10):
                    signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])
        signalTexts = ["","","",""]

        # display signal timer
        for i in range(0,noOfSignals):  
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i],signalTimerCoods[i])

        # display the vehicles
        for vehicle in simulation:  
            old_position = (vehicle.x, vehicle.y)
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()
            new_position = (vehicle.x, vehicle.y)
            if old_position == new_position:
                vehicle.waiting_time += 1  # Increment waiting_time if vehicle didn't move

            # Check if emergency vehicle has crossed midpoint
            # Check if emergency vehicle has crossed midpoint
            if vehicle.vehicleClass == 'emergency' and not vehicle.exit_triggered:
                
                if vehicle.turned:
                    # Adjust condition for vehicles that have turned
                    if (vehicle.direction == 'right' and vehicle.y < mid['up']['y']) or \
                        (vehicle.direction == 'down' and vehicle.x > mid['right']['x']) or \
                        (vehicle.direction == 'left' and vehicle.y > mid['down']['y']) or \
                        (vehicle.direction == 'up' and vehicle.x < mid['left']['x']):
                        vehicle.exit_triggered = True
                        handle_emergency_vehicle_exit(vehicle)
                else:
                    if (vehicle.direction == 'right' and vehicle.x > mid['right']['x']) or \
                        (vehicle.direction == 'down' and vehicle.y > mid['down']['y']) or \
                        (vehicle.direction == 'left' and vehicle.x < mid['left']['x']) or \
                        (vehicle.direction == 'up' and vehicle.y < mid['up']['y']):
                        vehicle.exit_triggered = True
                        handle_emergency_vehicle_exit(vehicle)


        frame_counter += 1
        if frame_counter % 100 == 0:
            total_waiting_time = sum(vehicle.waiting_time for vehicle in simulation)
            total_vehicles_waited = sum(1 for vehicle in simulation if vehicle.waiting_time > 0)
            if total_vehicles_waited > 0:
                average_waiting_time = total_waiting_time / total_vehicles_waited
                # print(f"{average_waiting_time} ")
                print(f"Average waiting time: {average_waiting_time} ms")


                # Update the plot
                x_data = np.append(line.get_xdata(), frame_counter)
                y_data = np.append(line.get_ydata(), average_waiting_time)
                line.set_data(x_data, y_data)  # Update the line data
                ax.relim()  # Recalculate the limits
                ax.autoscale_view()  # Rescale the view
                plt.draw()  # Redraw the plot
                plt.pause(0.01)  # Pause to allow the plot to update
            else:
                print("0")
                print("No vehicles waited.")


        
        pygame.display.update()


Main()
(quit(1))