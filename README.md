🔋 Low-Power Motion Activated Alert System

🏆 Hackathon Project

Team Name
-TECH FUSION

Team Members

- Vivek S
- Thejas BC
- Hemanth H
- Shivkumar A
- Sachit N Mandre

---

📌 Project Overview

The Low-Power Motion Activated Alert System is an energy-efficient security solution designed for long-term deployment. The system remains in ultra-low-power sleep mode and wakes only when motion is detected by a PIR sensor.

Upon detecting motion, the Raspberry Pi Pico 2W activates a buzzer and LED alert to notify nearby users. After the alert period, the system automatically returns to low-power mode, maximizing battery life and reducing energy consumption.

---

🎯 Problem Statement

Design an ultra-low-power motion-activated alert system that:

- Stays in deep sleep mode most of the time
- Wakes only on motion detection
- Triggers a visual or audio alert
- Consumes minimal standby power for long-term deployment

---

💡 Proposed Solution

Our solution uses a Raspberry Pi Pico 2W and a PIR Motion Sensor to continuously monitor movement while consuming minimal power.

The microcontroller remains in sleep mode during idle periods and wakes only when the PIR sensor detects human motion. The system then activates visual and audio indicators before returning to sleep mode.

This approach significantly reduces power consumption compared to continuously running monitoring systems.

---

✨ Key Features

✅ Ultra-low-power operation

✅ Motion-triggered wake-up

✅ Deep sleep functionality

✅ Real-time intrusion detection

✅ Audio alert using buzzer

✅ Visual alert using LED

✅ Battery-powered deployment

✅ Long operational life

✅ Low-cost implementation

---

🛠 Hardware Components

Component| Quantity
Raspberry Pi Pico 2W| 1
PIR Motion Sensor| 1
Active Buzzer| 1
LED| 1
220Ω Resistor| 1
Battery Supply| 1
Connecting Wires| As Required

---

🏗 System Architecture

Motion Detection Flow:

PIR Motion Sensor

↓

Raspberry Pi Pico 2W

↓

Alert Processing

↓

LED Alert + Buzzer Alert

↓

Return to Sleep Mode

---

⚙ Working Principle

Step 1: Sleep Mode

The Raspberry Pi Pico 2W remains in low-power sleep mode to conserve energy.

Step 2: Motion Detection

The PIR sensor continuously monitors infrared radiation changes caused by moving objects or humans.

Step 3: Wake-Up Event

When motion is detected, the PIR sensor sends a trigger signal to the Raspberry Pi Pico 2W.

Step 4: Alert Generation

The controller wakes up and activates:

- LED Indicator
- Buzzer Alarm

Step 5: Return to Sleep

After a predefined alert duration, the system returns to sleep mode to reduce power consumption.

---

🔌 Circuit Diagram
## Circuit Diagram

![Circuit Diagram](circuit_diagram.jpeg)

---

📷 Hardware Setup

Upload images of your project setup.

Example:

"Hardware Setup" (images/hardware_setup.jpg)

---

💻 Software Used

- MicroPython
- Thonny IDE
- GitHub
- Raspberry Pi Pico SDK

---

📁 Source Code Structure

code/
│
├── main.py
├── sensor.py
├── buzzer.py
└── led.py

---

🚀 Applications

- Home Security Systems
- Smart Buildings
- Office Security
- Warehouse Monitoring
- Wildlife Monitoring
- Restricted Area Surveillance
- Energy-Efficient Monitoring Systems

---

📊 Expected Outcome

The developed system successfully:

- Detects motion in real time
- Wakes only when required
- Generates instant alerts
- Minimizes standby power consumption
- Extends battery life
- Supports long-term deployment

---

🔮 Future Scope

- Mobile App Notifications
- IoT Cloud Integration
- Solar-Powered Operation
- GSM-Based SMS Alerts
- Camera Integration
- AI-Based Motion Recognition
- Smart Home Integration

---

📹 Demonstration Video

Add your YouTube video link here.

Example:

https://youtube.com/your-demo-video

---

📸 Project Gallery

Add images of:

- Circuit Diagram
- Hardware Setup
- Final Prototype
- Testing Process
- Working Demonstration

---

🏅 Innovation Highlights

- Low-cost solution
- Energy-efficient design
- Easy deployment
- Scalable architecture
- Suitable for remote locations
- Long battery life

---

📜 License

This project is licensed under the MIT License.

---

🙏 Acknowledgements

Special thanks to the hackathon organizers, mentors, and team members for their support and guidance throughout the project development process.
