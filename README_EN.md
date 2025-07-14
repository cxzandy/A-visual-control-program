# Tiaozhanbei2.0 - Pipe Tracking and Flange Recognition System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.5+-green.svg)
![RealSense](https://img.shields.io/badge/Intel-RealSense-lightblue.svg)
![DJI](https://img.shields.io/badge/DJI-RoboMaster-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Real-time Pipe Tracking and Flange Recognition System based on Intel RealSense D455**  
**Visual Navigation Solution with DJI RoboMaster C-board Communication**

[Features](#-features) •
[Hardware](#-hardware-requirements) •
[Quick Start](#-quick-start) •
[Usage](#-detailed-usage) •
[API](#-api-documentation) •
[Troubleshooting](#-troubleshooting)

</div>

---

## 📋 Overview

Tiaozhanbei2.0 is a computer vision system designed for industrial robots that can real-time identify and track pipes, detect flange positions, and provide precise navigation information. The system integrates Intel RealSense depth camera and DJI RoboMaster C-board communication, providing a complete visual perception solution for autonomous navigation robots.

### 🎯 Main Applications
- 🏭 **Industrial Pipe Detection**: Automatically identify and track various pipe structures
- 🔧 **Flange Positioning**: Precisely detect pipe connection points and flange positions  
- 🤖 **Robot Navigation**: Provide visual navigation commands for mobile robots
- 📊 **Real-time Monitoring**: Provide real-time visual feedback of pipe status
- 🚧 **Obstacle Detection**: Identify obstacles in path and perform avoidance

---

## ✨ Features

### 🎥 Vision Perception
- **Real-time Pipe Tracking**: 3D pipe detection and tracking based on depth information
- **Flange Recognition**: Automatically identify circular flanges and provide precise position information
- **Obstacle Detection**: Real-time obstacle detection using depth data
- **Point Cloud Processing**: RANSAC cylinder fitting algorithm for pipe modeling

### 🤖 Robot Communication
- **DJI C-board Integration**: Complete serial communication protocol support
- **Real-time Command Transmission**: Low-latency navigation command sending
- **Bidirectional Data Exchange**: Support robot status feedback and command confirmation

### 📊 System Functions
- **Multi-mode Operation**: Demo, calibration, tracking, test four working modes
- **Configuration Management**: Flexible parameter configuration and environment adaptation
- **Logging System**: Complete operation logs and error tracking
- **Visualization Output**: Real-time image display and result saving

---

## 🔧 Hardware Requirements

### 🎥 Required Hardware

#### Intel RealSense D455 Depth Camera
- **Purpose**: Primary visual sensor providing RGB images and depth data
- **Specifications**:
  - Depth Technology: Stereo Vision
  - Depth Resolution: Up to 1280×720 @ 30fps
  - RGB Resolution: Up to 1920×1080 @ 30fps
  - Measurement Range: 0.2m - 10m
  - Field of View: 87° × 58° (depth)

#### DJI RoboMaster C-board
- **Purpose**: Robot main control board receiving visual system navigation commands
- **Interface Requirements**:
  - UART serial communication
  - Baud rate: 115200
  - Data bits: 8, Stop bits: 1, No parity
- **Connection**:
  - USB to TTL serial module connected to PC
  - Or directly use development board USB virtual serial port

### 💻 Computing Platform Requirements

#### Minimum Configuration
- **CPU**: Intel i5-8th gen or AMD Ryzen 5 3600+
- **RAM**: 8GB (16GB recommended)
- **Storage**: 50GB available space
- **OS**: Windows 10/11, Ubuntu 18.04+, macOS 10.15+

#### Recommended Configuration
- **CPU**: Intel i7-10th gen or AMD Ryzen 7 4000 series
- **GPU**: NVIDIA GTX 1660 or higher (optional, for acceleration)
- **RAM**: 16GB
- **USB**: USB 3.0 interface (for RealSense connection)

---

## 🚀 Quick Start

### 1️⃣ Environment Setup

#### Install Python Environment (Python 3.8+ recommended)
```bash
# Windows users recommend using Anaconda
conda create -n tiaozhanbei python=3.8
conda activate tiaozhanbei

# Or use system Python
python -m venv tiaozhanbei_env
# Windows
tiaozhanbei_env\Scripts\activate
# Linux/Mac
source tiaozhanbei_env/bin/activate
```

#### Install Dependencies
```bash
# Core dependencies
pip install pyrealsense2 opencv-python numpy pyserial

# Complete dependencies (recommended)
pip install -r requirements.txt
```

### 2️⃣ Hardware Connection

#### RealSense Camera Connection
1. Connect RealSense D455 to computer via USB 3.0
2. Run Intel RealSense Viewer to verify connection:
   ```bash
   realsense-viewer
   ```
3. Confirm you can see depth and color image streams

#### Robot Communication Connection (Optional)
1. Connect USB to TTL module to computer
2. Connect TTL module TX, RX, GND to DJI C-board corresponding pins
3. Confirm serial port number in Device Manager (e.g., COM3)

### 3️⃣ Project Setup

#### Clone Project
```bash
git clone https://github.com/cxzandy/A-vision-project-for-pipe-tracking-and-flange-recognition-available-for-DJI-c-board-communication.git
cd A-vision-project-for-pipe-tracking-and-flange-recognition-available-for-DJI-c-board-communication
```

#### Verify Installation
```bash
# Run environment check
python src/main.py --config-check

# Run complete demo script (Windows PowerShell)
.\scripts\run_demo.ps1

# Run complete demo script (Windows CMD)
scripts\run_demo.bat

# Run complete demo script (Linux/Mac/WSL)
bash scripts/run_demo.sh
```

### 4️⃣ First Run

#### Quick Demo Mode
```bash
# Basic demo (no hardware required)
python src/main.py --mode demo

# Demo with image display
python src/main.py --mode demo --display

# Verbose output mode
python src/main.py --mode demo --display --verbose
```

---

## 📖 Detailed Usage

### 🎮 Operation Modes

#### 1. Demo Mode
**Purpose**: System function demonstration, no real hardware required
```bash
# Basic demo
python src/main.py --mode demo

# Display image processing
python src/main.py --mode demo --display

# Save demo results
python src/main.py --mode demo --display --save
```

#### 2. Calibration Mode
**Purpose**: Calibrate RealSense camera parameters
```bash
# Run camera calibration
python src/main.py --mode calib

# Specify calibration image directory
python src/main.py --mode calib --calib-dir data/calib
```

#### 3. Real-time Tracking Mode
**Purpose**: Real-time pipe tracking and flange recognition
```bash
# Start real-time tracking
python src/main.py --mode track

# Display real-time images
python src/main.py --mode track --display

# Save tracking results
python src/main.py --mode track --display --save

# Robot communication mode
python src/main.py --mode track --robot --port COM3
```

#### 4. System Test Mode
**Purpose**: System function verification and performance testing
```bash
# Run system tests
python src/main.py --mode test

# Detailed test report
python src/main.py --mode test --verbose
```

---

## 🔌 API Documentation

### Camera Module API

#### RealSenseCapture Class
```python
from src.camera.stereo_capture import RealSenseCapture

# Initialize camera
camera = RealSenseCapture()
camera.start()

# Get frame data
color_frame, depth_frame = camera.get_frames()

# Get point cloud
points = camera.get_point_cloud(depth_frame)

# Release resources
camera.stop()
```

### Perception Module API

#### Pipe Tracking
```python
from src.perception.pipe_tracking import PipeTracker

# Initialize tracker
tracker = PipeTracker()

# Detect pipes
pipes = tracker.detect_pipes(color_image, depth_image)

# Estimate pipe pose
pose = tracker.estimate_pipe_pose(pipes[0])
```

### Robot Communication API

#### Serial Communication
```python
from src.robot.communication import RoboMasterCSerial

# Initialize communication
robot = RoboMasterCSerial(port='COM3', baudrate=115200)

# Send move command
robot.send_move_command(linear_x=0.5, angular_z=0.1)

# Send stop command
robot.send_stop_command()

# Receive status data
status = robot.receive_status()
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 🚫 Camera Connection Issues

**Issue**: `pyrealsense2.error: No device connected`
```bash
# Solution steps:
1. Check USB 3.0 connection
2. Reinstall Intel RealSense SDK
3. Update camera firmware
4. Check USB port power capability

# Verify connection
realsense-viewer

# List devices
python -c "import pyrealsense2 as rs; print(rs.context().devices)"
```

#### 🔌 Serial Communication Issues

**Issue**: `serial.SerialException: Could not open port`
```bash
# Windows solution:
1. Check serial port number in Device Manager
2. Confirm port is not occupied by other programs
3. Run program with administrator privileges

# Linux solution:
sudo usermod -a -G dialout $USER  # Add user to serial group
sudo chmod 666 /dev/ttyUSB0        # Modify permissions

# List available ports
python -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"
```

---

## 👥 Development Guide

### 🏗️ Project Structure
```
Tiaozhanbei2.0/
├── src/                     # Source code directory
│   ├── main.py             # Main program entry
│   ├── config.py           # Configuration management
│   ├── camera/             # Camera module
│   ├── perception/         # Perception algorithms
│   ├── robot/              # Robot communication
│   └── utils/              # Utility functions
├── tests/                  # Test files
├── data/                   # Data directory
├── output/                 # Output results
├── scripts/               # Script files
└── docs/                  # Documentation
```

### 🧪 Testing Guide

#### Run Unit Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific module tests
python -m pytest tests/test_camera.py -v
```

---

## 📚 References

### 📖 Technical Documentation
- [Intel RealSense SDK Documentation](https://intelrealsense.github.io/librealsense/python_docs/_generated/pyrealsense2.html)
- [OpenCV Python Tutorials](https://opencv-python-tutroals.readthedocs.io/)
- [DJI RoboMaster Development Guide](https://robomaster-dev.readthedocs.io/)

---

## 🤝 Contributing

### 🔄 Contribution Process
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push branch: `git push origin feature/new-feature`
5. Create Pull Request

### 🐛 Issue Reporting
Please report issues through GitHub Issues, including:
- Detailed problem description
- Reproduction steps
- System environment information
- Error logs

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details

---

## 👨‍💻 Author

- **Author**: cxzandy
- **Email**: [your-email@example.com]
- **GitHub**: [cxzandy](https://github.com/cxzandy)

---

<div align="center">

**⭐ If this project helps you, please give it a Star! ⭐**

**🔗 [Project Home](https://github.com/cxzandy/A-vision-project-for-pipe-tracking-and-flange-recognition-available-for-DJI-c-board-communication) | 📧 [Contact Us](mailto:your-email@example.com) | 📖 [Documentation](docs/)**

</div>
