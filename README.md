# TimeTracker - Windows Application Usage Monitor

![Screenshot Placeholder](./screenshot.png)

A Windows application that tracks time spent in different applications, categorizes them, and provides detailed reports with visualizations.

## Features

- **Real-time Tracking**: Monitors active applications and tracks time spent
- **Category Management**: 
  - Assign applications to custom categories
  - Create/edit/delete categories
  - Right-click context menu for quick categorization
- **Visual Reports**:
  - Real-time pie chart of daily usage by category
  - Daily and weekly time breakdowns
  - Export reports to CSV
- **System Tray Integration**:
  - Minimize to tray
  - Continue tracking in background
- **Icon Support**:
  - Automatic application icon caching
  - Custom icon handling for UWP and Win32 apps
- **Data Persistence**:
  - Automatic saving to JSON files
  - Hourly, daily, and weekly data tracking

## Installation

### Requirements
- Python 3.8+
- Windows 10/11

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/TimeTracker.git
   cd TimeTracker
