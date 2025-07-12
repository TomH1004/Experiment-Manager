# VR Experiment Supervisor Web Application

A modern, dynamic web-based interface for controlling Unity VR experiments via UDP broadcast messages. This application replaces the original tkinter-based GUI with a responsive, user-friendly web interface built using Flask backend and Tailwind CSS frontend.

## ✨ Features

- **🌐 Dynamic Network Configuration**: Configure UDP IP address and port in real-time
- **📊 Session Management**: Track experiment sessions with Group IDs and supervisor notes
- **⚙️ Experiment Configuration**: Set up three experimental conditions with different condition types and objects
- **🎮 Real-time Control**: Start conditions, move between conditions, and force overrides
- **⏰ Live Countdown Timer**: 5-minute timer for each condition with visual feedback
- **📡 UDP Communication**: Broadcasts control messages to Unity VR applications
- **📝 Data Logging**: Automatic logging of all experiment events with timestamps
- **💾 Session Data Export**: Save session data to text files for record keeping
- **🎨 Modern UI/UX**: Glass-morphism design with animations and visual feedback
- **⌨️ Keyboard Shortcuts**: Ctrl+S to save, Ctrl+Enter to configure experiment
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices

## 🚀 Quick Start

### Option 1: Using the run script (Recommended)
```bash
python run.py
```

### Option 2: Manual setup
1. Install dependencies: `pip install -r requirements.txt`
2. Start the application: `python app.py`
3. Open your browser and go to `http://localhost:5000`

## 📋 Requirements

- Python 3.7+
- Modern web browser with JavaScript enabled
- Network access to Unity VR application (same network recommended)

## 🛠️ Installation

1. **Download the project files**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify the project structure**:
   ```
   project/
   ├── app.py                 # Flask backend
   ├── run.py                 # Run script
   ├── requirements.txt       # Python dependencies
   ├── README.md             # This file
   ├── templates/
   │   └── index.html        # HTML template
   └── static/
       └── script.js         # Frontend JavaScript
   ```

## 📖 Usage Guide

### 1. **Start the Application**
```bash
python run.py
```
The application will automatically install dependencies and start the server.

### 2. **Access the Web Interface**
Open your browser and navigate to `http://localhost:5000`

### 3. **Configure Network Settings**
- **UDP IP Address**: Enter the broadcast IP address (e.g., `192.168.1.255`)
- **UDP Port**: Enter the port number (default: `1221`)
- Click "Update Network Settings" to save

### 4. **Set Up Session Information**
- Enter a **Group ID** for identification
- Add **Session Notes** for observations and comments
- Click "Save Session Data" to export session information

### 5. **Configure Experiment**
- Set up three conditions by selecting:
  - **Condition Type**: Helpful, Demotivating, or Control
  - **Object Type**: Brick, Paperclip, or Rope
- Each type must be used exactly once
- Click "Set Experiment Parameters" to confirm

### 6. **Run the Experiment**
- Click "Start Current Condition" to begin
- The system automatically starts a 5-minute countdown timer
- Use "Next Condition" after the timer expires
- Use "Force Next" to override the timer if needed
- Click "Reset Experiment" to start over

### 7. **Monitor Progress**
- Watch the real-time countdown timer
- Monitor experiment status and current condition
- View system logs for detailed information

## 🌐 Network Configuration

The application supports dynamic network configuration:

- **Default IP**: `10.195.83.255` (broadcast address)
- **Default Port**: `1221` (shared with avatar sync system)
- **IP Validation**: Ensures valid IP address format
- **Port Validation**: Ensures port is in valid range (1-65535)

### Setting Up Network

1. **Find your network's broadcast address**:
   - Windows: `ipconfig` → look for subnet mask
   - Mac/Linux: `ifconfig` → calculate broadcast address
   - Common examples: `192.168.1.255`, `10.0.0.255`

2. **Choose an available port**:
   - Default `1221` works with Unity avatar sync
   - Use ports above 1024 for better compatibility
   - Avoid common ports (80, 443, 8080, etc.)

3. **Configure Unity Application**:
   - Set Unity to listen on the same IP and port
   - Ensure firewall allows UDP traffic
   - Test connection before starting experiment

## 📨 UDP Message Format

The application sends JSON-formatted messages:

### Start Condition
```json
{
    "command": "start_condition",
    "condition_type": "Helpful",
    "object_type": "Brick",
    "condition_index": 0
}
```

### Next Condition
```json
{
    "command": "next_condition",
    "condition_type": "Demotivating",
    "object_type": "Paperclip",
    "condition_index": 1
}
```

### Disable All (Timer Expired)
```json
{
    "command": "disable_all",
    "reason": "timer_expired"
}
```

## 🎨 User Interface Features

### Visual Feedback
- **Glass-morphism design** with backdrop blur effects
- **Gradient buttons** with hover animations
- **Color-coded status indicators**:
  - 🟢 Green: Ready/Active states
  - 🔵 Blue: Information/Configuration
  - 🟠 Orange: Warnings/Overrides
  - 🔴 Red: Errors/Timer expiration

### Animations
- **Fade-in animations** for smooth page loading
- **Scale animations** for button interactions
- **Pulse animations** for active states
- **Shimmer effects** for status indicators

### Interactive Elements
- **Loading overlays** during operations
- **Success/Error modals** with appropriate icons
- **Confirmation dialogs** for destructive actions
- **Real-time countdown** with visual emphasis

## 🔧 File Structure

- **`app.py`**: Main Flask application with UDP messaging and session management
- **`run.py`**: Convenient run script with automatic dependency installation
- **`templates/index.html`**: HTML template with modern Tailwind CSS styling
- **`static/script.js`**: Frontend JavaScript for UI interactions and WebSocket communication
- **`requirements.txt`**: Python dependencies
- **`data/`**: Directory for exported session data files (created automatically)

## 🆚 Features Comparison

| Feature | Original tkinter | Web Application |
|---------|------------------|-----------------|
| **Platform** | Desktop only | Any device with browser |
| **Network Config** | Hardcoded | Dynamic configuration |
| **Real-time Updates** | Local only | WebSocket-based |
| **Multiple Users** | Single user | Multi-session support |
| **Styling** | Basic GUI | Modern glass-morphism |
| **Animations** | None | Smooth transitions |
| **Data Export** | Local files | Server-side management |
| **Session Management** | Single session | UUID-based sessions |
| **Responsive Design** | Fixed size | Adaptive layout |
| **Keyboard Shortcuts** | None | Ctrl+S, Ctrl+Enter |

## 🌍 Browser Compatibility

**Supported browsers:**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Required features:**
- ES6 JavaScript
- WebSocket connections
- CSS Grid and Flexbox
- Fetch API
- CSS backdrop-filter (for glass effect)

## 🔧 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Change port in app.py or run.py
   socketio.run(app, debug=True, host='0.0.0.0', port=5001)
   ```

2. **UDP messages not received**
   - Verify IP address is correct for your network
   - Check firewall allows UDP traffic on specified port
   - Ensure Unity application is listening on same port
   - Test with network tools (netcat, wireshark)

3. **WebSocket connection issues**
   - Enable JavaScript in browser
   - Check for proxy/firewall blocking WebSocket
   - Verify server is running and accessible
   - Try different browser or incognito mode

4. **Glass effect not working**
   - Update to modern browser with backdrop-filter support
   - Effects will gracefully degrade on older browsers

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export FLASK_ENV=development
python app.py
```

### Network Testing

Test UDP connectivity:
```bash
# Send test message (Linux/Mac)
echo "test" | nc -u 192.168.1.255 1221

# Listen for messages (Linux/Mac)
nc -u -l 1221
```

## 🔒 Security Considerations

**For local network use:**
- Application designed for trusted local networks
- No authentication required for local use
- Session data stored locally on server

**For production deployment:**
- Add authentication and authorization
- Use HTTPS for secure communication
- Implement rate limiting
- Validate all user inputs
- Set up proper logging and monitoring
- Use environment variables for configuration

## 🎯 Development

### Customization

1. **Backend changes**: Edit `app.py` for API endpoints and UDP messaging
2. **Frontend styling**: Modify `templates/index.html` for layout and design
3. **Frontend logic**: Update `static/script.js` for UI interactions
4. **Configuration**: Adjust default values in `VRExperimentManager` class

### Adding Features

The modular design makes it easy to add new features:
- New experiment types in `condition_types` array
- Additional object types in `object_types` array
- Custom UDP message formats
- Extended session data fields
- Additional UI components

### Hot Reload

Development mode includes hot-reload for rapid iteration:
```bash
export FLASK_ENV=development
python app.py
```

## 📄 License

This project is designed for research and educational purposes. Please ensure compliance with your institution's policies when using for academic research.

## 🤝 Contributing

Contributions are welcome! Please consider:
- Following the existing code style
- Adding tests for new features
- Updating documentation
- Submitting pull requests with clear descriptions

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review browser console for JavaScript errors
3. Check server logs for Python errors
4. Verify network configuration
5. Test with minimal setup first 