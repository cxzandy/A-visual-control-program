# Tiaozhanbei2.0 - Intelligent Pipe Tracking System

## 📋 Project Overview

Tiaozhanbei2.0 is an intelligent pipe tracking system based on Intel RealSense depth camera, specifically designed for industrial pipe inspection robots. The system integrates computer vision, deep learning, and web control interface, providing real-time pipe tracking, obstacle detection, and intelligent steering control capabilities.

## � Quick Start

### 1. System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Ubuntu 18.04+ / Windows 10+ / macOS 10.15+
- **Hardware**: Intel RealSense D455 depth camera (required)
- **Memory**: 8GB+ recommended
- **GPU**: NVIDIA GPU with CUDA support (optional, for acceleration)

### 2. RealSense Driver Installation

#### Ubuntu/Linux System
```bash
# Install RealSense SDK
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE
sudo add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main" -u
sudo apt-get update
sudo apt-get install librealsense2-dkms librealsense2-utils librealsense2-dev
```

#### Windows System
1. Download RealSense SDK 2.0 from [Intel Official Website](https://www.intelrealsense.com/sdk-2/)
2. Run the installer and complete installation
3. Connect RealSense camera and verify device

#### macOS System
```bash
# Install using brew
brew install librealsense
```

### 3. Project Environment Setup
```bash
# Clone project
git clone https://github.com/cxzandy/A-visual-control-program.git
cd A-visual-control-program

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements_pip.txt
```

### 4. System Verification
```bash
# Verify RealSense camera connection
python -c "import pyrealsense2 as rs; print('RealSense SDK installed')"

# Run system demo
python -m src.main --mode demo --display
```

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

## 📖 Usage Guide

### Command Line Mode

#### Basic Commands
```bash
# Demo mode (quick functionality verification)
python -m src.main --mode demo --display

# Real-time tracking mode (continuous pipe detection)
python -m src.main --mode track --display

# Camera calibration mode (generate calibration parameters)
python -m src.main --mode calib --display --save

# System test mode (comprehensive functionality test)
python -m src.main --mode test --display --verbose
```

#### Parameter Description
- `--mode`: Running mode (demo/track/calib/test)
- `--display`: Show real-time image window
- `--save`: Save processing results to files
- `--verbose`: Show detailed debug information
- `--config-check`: Verify system configuration

### Web Interface Mode

#### Start Web Service
```bash
# Using startup script (recommended)
./start_web.sh

# Demo mode (automatically opens browser)
./demo_web.sh

# Direct Python execution
python web/web_simple.py

# Check environment only
./start_web.sh --check
```

#### Web Interface Features
- **Real-time Monitoring**: View camera feed and system status
- **Mode Switching**: Quick switching between Demo/Track/Calib/Test modes
- **Manual Control**: Manual robot movement control
- **Status Display**: Real-time display of processing FPS, connection status, etc.
- **Log Viewing**: View system operation logs and error information

Access Address: `http://localhost:5000`

---

## ⚙️ System Configuration

### Main Configuration Files
System configuration is located in `src/config.py`, including the following main settings:

#### Camera Configuration
```python
# Camera resolution and frame rate
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# Depth range settings
DEPTH_MIN = 0.1  # Minimum depth (meters)
DEPTH_MAX = 10.0  # Maximum depth (meters)
```

#### Detection Parameters
```python
# Pipe detection thresholds
PIPE_DEPTH_THRESHOLD = 2.0  # Pipe depth threshold (meters)
OBSTACLE_DEPTH_THRESHOLD = 1.0  # Obstacle depth threshold (meters)

# Image processing parameters
EDGE_THRESHOLD_LOW = 50   # Edge detection low threshold
EDGE_THRESHOLD_HIGH = 150 # Edge detection high threshold
```

#### Robot Communication Configuration
```python
# Serial port settings
SERIAL_PORT = "/dev/ttyUSB0"  # Linux
# SERIAL_PORT = "COM3"        # Windows
BAUD_RATE = 115200
TIMEOUT = 1.0

# Enable/disable robot control
ROBOT_ENABLED = False  # Set to True to enable robot control
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. RealSense Camera Issues
**Issue**: `pyrealsense2` import failed
```bash
# Solution: Reinstall RealSense SDK
sudo apt-get install --reinstall librealsense2-utils librealsense2-dev
pip install --upgrade pyrealsense2
```

**Issue**: Camera connection failed
```bash
# Check device connection
lsusb | grep Intel
realsense-viewer  # Official test tool
```

#### 2. Python Environment Issues
**Issue**: Module import error
```bash
# Ensure running from project root directory
cd A-visual-control-program
python -m src.main  # Use module method to run

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 3. Permission Issues
**Issue**: Serial port access denied
```bash
# Add user to serial port group
sudo usermod -a -G dialout $USER
# Logout and login again to take effect
```

#### 4. Web Interface Issues
**Issue**: Cannot access web interface
```bash
# Check port occupation
sudo netstat -tulpn | grep :5000

# Use different port
python web/web_simple.py --port 8080
```

### Debugging Tools

#### System Diagnostics
```bash
# Check system configuration
python -m src.main --config-check

# Hardware connection test
python tests/test_camera.py
python tests/test_robot.py
```

#### Log Viewing
```bash
# View real-time logs
tail -f output/logs/system.log

# View error logs
grep "ERROR" output/logs/system.log
```

---

## � Project Structure

```
A-visual-control-program/
├── 📦 Core Source Code
│   └── src/                    # Main source code directory
│       ├── main.py            # System main program entry
│       ├── config.py          # System configuration parameters
│       ├── camera/            # Camera module
│       │   ├── calibration.py      # Camera calibration
│       │   ├── stereo_capture.py   # RealSense data capture
│       │   ├── depth_estimation.py # Depth estimation
│       │   └── point_cloud_*.py    # Point cloud processing
│       ├── perception/        # Perception module
│       │   ├── pipe_tracking.py    # Main pipe tracking algorithm
│       │   ├── obstacle_detection.py # Obstacle detection
│       │   ├── partial_pipe_tracker.py # Partial pipe tracking
│       │   └── pipe_direction_predictor.py # Direction prediction
│       ├── control/          # Control module
│       │   └── turn_control.py    # Steering control management
│       ├── robot/            # Robot communication
│       │   └── communication.py   # Serial communication
│       └── utils/            # Utility module
│           ├── display.py         # Display management
│           ├── keyboard_control.py # Keyboard control
│           └── logger.py          # Logging system
│
├── 🌐 Web Control Interface
│   └── web/                   # Web interface
│       ├── web_simple.py      # Flask web server
│       ├── templates/         # HTML templates
│       │   └── index.html     # Main control interface
│       ├── static/            # Static resources (reserved)
│       └── README.md          # Web usage guide
│
├── 🧪 Testing & Scripts
│   ├── tests/                 # Unit tests
│   │   ├── test_camera.py     # Camera testing
│   │   ├── test_perception.py # Perception module testing
│   │   ├── test_robot.py      # Robot communication testing
│   │   └── *.py               # Other test files
│   └── scripts/               # Running scripts
│       ├── run_demo.sh        # Demo script
│       └── *.sh               # Other scripts
│
├── 📊 Data & Output
│   ├── data/                  # Data directory
│   │   └── calib/             # Camera calibration data
│   └── output/                # Output directory
│       ├── images/            # Saved processed images
│       ├── logs/              # System logs
│       ├── results/           # Detection results
│       └── videos/            # Recorded videos
│
├── 📚 Documentation & Configuration
│   ├── docs/                  # Detailed documentation
│   ├── requirements_pip.txt   # Python dependencies (simplified)
│   ├── requirements.txt       # Complete dependencies (conda export)
│   ├── start_web.sh          # Web startup script
│   ├── demo_web.sh           # Web demo script
│   ├── README.md             # Project description (Chinese)
│   └── README_EN.md          # Project description (this file)
```

---

## 💡 Usage Tips

### First-time Usage Recommendations
1. Run `python -m src.main --config-check` to check configuration first
2. Use `--mode demo` to quickly verify system functionality
3. Use web interface for more intuitive graphical operation
4. Save detection images for analysis: `--save` parameter

### Performance Optimization
- Lower camera resolution can improve processing speed
- Use `--verbose` parameter for performance analysis
- Adjust detection thresholds in configuration file to optimize accuracy

### Extension Development
- Add new perception algorithms to `src/perception/` directory
- Add control algorithms to `src/control/` directory
- Extend web interface by modifying `web/templates/index.html`

---

## 📞 Technical Support

### Issue Reporting
If you encounter problems, please provide the following information:
1. Operating system version
2. Python version
3. Error log content
4. Command parameters used

### Related Resources
- [Intel RealSense SDK Documentation](https://dev.intelrealsense.com/)
- [OpenCV Python Tutorial](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [Flask Web Development Documentation](https://flask.palletsprojects.com/)

---

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

**Tiaozhanbei2.0 - Intelligent Pipe Tracking System**  
*Empowering Robots with Visual Perception*
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
