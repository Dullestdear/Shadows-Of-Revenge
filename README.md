# Shadows Of Revenge

A 2D platformer game built with Pygame.

## Directory Structure

```
Shadows Of Revenge/
├── assets/
│   ├── images/
│   │   ├── sky.png
│   │   ├── mountain.png
│   │   ├── pine1.png
│   │   ├── pine2.png
│   │   ├── end_screen.jpg
│   │   └── tiles/
│   ├── music/
│   │   ├── Bg_music.mp3
│   │   ├── evil_morty_song.mp3
│   │   └── 01 Counterstrike - Condition Zero.mp3
│   ├── fonts/
│   │   └── OldLondon.ttf
│   └── sprites/
│       ├── Runner.png
│       └── spearmen/
├── Latest.py
├── setup.py
└── README.md
```

## Development Setup

1. Install Python 3.8 or higher
2. Install required packages:
   ```
   pip install pygame
   pip install py2app
   ```

## Running the Game

### Development Mode
```
python Latest.py
```

### Building the Executable

#### Windows (using PyInstaller)
1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```
2. Build the executable:
   ```
   pyinstaller --onefile --windowed --add-data "assets;assets" Latest.py
   ```

#### macOS (using py2app)
1. Build the application:
   ```
   python setup.py py2app
   ```
2. The executable will be created in the `dist` folder

## Game Controls

- Arrow Keys: Move left/right
- Space: Jump
- Caps Lock: Trigger end screen
- ESC: Pause game

## Credits

- Game developed by [Your Name]
- Music: [Credits for music tracks]
- Fonts: OldLondon font 