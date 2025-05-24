# Counter-Strike 1.6 Python API (GSClient)

**EN**  
A powerful Python module for interacting with Counter-Strike 1.6 through memory manipulation. This tool was originally designed for cheat development and testing, allowing you to prototype features in Python before implementing them in C++ for production use.

**ES**  
Un módulo Python potente para interactuar con Counter-Strike 1.6 a través de manipulación de memoria. Esta herramienta fue originalmente diseñada para desarrollo y pruebas de cheats, permitiéndote crear prototipos en Python antes de implementarlos en C++ para uso en producción.

##  Features / Características

**EN**
- **Game Control**: Send console commands, chat messages, and control player actions
- **Player Information**: Get player names, teams, coordinates, and status
- **Movement Control**: Automate player movement (forward, back, strafe, jump, crouch)
- **Aiming System**: Automatic aiming with smooth transition support
- **Server Management**: Connect/disconnect from servers
- **Real-time Data**: Access live game data including player positions and visibility

**ES**
- **Control del Juego**: Enviar comandos de consola, mensajes de chat y controlar acciones del jugador
- **Información de Jugadores**: Obtener nombres, equipos, coordenadas y estado de los jugadores
- **Control de Movimiento**: Automatizar movimiento del jugador (adelante, atrás, lateral, salto, agacharse)
- **Sistema de Puntería**: Puntería automática con soporte de transición suave
- **Gestión de Servidor**: Conectar/desconectar de servidores
- **Datos en Tiempo Real**: Acceder a datos del juego en vivo incluyendo posiciones y visibilidad de jugadores


**EN**  
Required Python packages:

**ES**  
Paquetes Python requeridos:

```bash
pip install pymem psutil
```

##  Installation / Instalación

**EN**
1. Download the `csTools.py` file
2. Place it in your project directory
3. Install the required dependencies:

**ES**
1. Descarga el archivo `csTools.py`
2. Colócalo en el directorio de tu proyecto
3. Instala las dependencias requeridas:

```bash
pip install pymem psutil
```

##  Quick Start / Inicio Rápido

### Basic Setup / Configuración Básica

```python
from csTools import csApi

# Initialize the API / Inicializar la API
api = csApi()
```

### Multiple Processes / Múltiples Procesos

**EN**  
If you have multiple Counter-Strike instances running:

**ES**  
Si tienes múltiples instancias de Counter-Strike ejecutándose:

```python
# Option 1: Manual selection (interactive) / Opción 1: Selección manual (interactiva)
api = csApi()

# Option 2: Specify PID directly / Opción 2: Especificar PID directamente
api = csApi(pid=12345)  # Replace with actual process ID / Reemplaza con el ID del proceso real
```

##  Usage Examples / Ejemplos de Uso

### Basic Commands / Comandos Básicos

```python
from csTools import csApi
api = csApi()

# Send console command / Enviar comando de consola
api.send_command("fps_max 100")

# Send chat message / Enviar mensaje al chat
api.say("Hello world!")

# Send team message / Enviar mensaje al equipo
api.team_say("Hello team!")

# Connect to server / Conectar al servidor
api.connect_to_server("192.168.0.1:27015")

# Disconnect from server / Desconectar del servidor
api.disconnect_server()
```

### Player Actions / Acciones del Jugador

```python
# Single shot / Disparo único
api.attack()

# Hold fire (continuous shooting) / Mantener fuego (disparo continuo)
api.attack(True)   # Start shooting / Empezar a disparar
api.attack(False)  # Stop shooting / Dejar de disparar

# Secondary attack (zoom/knife) / Ataque secundario (zoom/cuchillo)
api.attack2()

# Movement / Movimiento
api.forward()      # Move forward once / Moverse hacia adelante una vez
api.forward(True)  # Start moving forward / Empezar a moverse hacia adelante
api.forward(False) # Stop moving forward / Dejar de moverse hacia adelante

# Jump / Saltar
api.jump()

# Crouch / Agacharse
api.duck()
```

### Player Information / Información de Jugadores

```python
# Get player coordinates / Obtener coordenadas del jugador
coords = api.get_player_coords(1)  # Player ID 1 / ID del jugador 1
print(f"Player 1 coordinates: {coords}")

# Get all player coordinates / Obtener coordenadas de todos los jugadores
all_coords = api.get_player_coords()
print(f"All players: {all_coords}")

# Get your coordinates / Obtener tus coordenadas
my_coords = api.get_local_player_coords()
print(f"My coordinates: {my_coords}")

# Get player names / Obtener nombres de jugadores
names = api.get_player_names()
print(f"Players in server: {names}")

# Get complete player information / Obtener información completa de jugadores
players_info = api.get_all_players_info()
for player in players_info:
    print(f"Player {player['id']}: {player['name']} - Team: {player['team']}")
```

### Aiming System / Sistema de Puntería

```python
# Aim at specific player / Apuntar a jugador específico
api.aim_at_player(1)  # Aim at player ID 1 / Apuntar al jugador ID 1

# Smooth aiming (less obvious) / Puntería suave (menos obvio)
api.aim_at_player(1, target_head=True, smooth=0.3)

# Aim at closest player / Apuntar al jugador más cercano
closest = api.get_closest_player()
if closest:
    api.aim_at_player(closest['id'])

# Aim at specific coordinates / Apuntar a coordenadas específicas
api.aim_at_coords(100.0, 200.0, 50.0)
```

### Advanced Examples / Ejemplos Avanzados

#### Simple Aimbot / Aimbot Simple
```python
def simple_aimbot():
    # Get closest player / Obtener jugador más cercano
    closest_player = api.get_closest_player()
    if closest_player and not closest_player['is_dead']:
        # Only aim if player is alive and visible / Solo apuntar si el jugador está vivo y visible
        if closest_player['is_visible']:
            api.aim_at_player(closest_player['id'], smooth=0.2)
            api.attack()  # Shoot / Disparar

# Run in a loop / Ejecutar en un bucle
while True:
    simple_aimbot()
    time.sleep(0.01)  # Small delay / Pequeña pausa
```

#### Knife Bot / Bot de Cuchillo
```python
def knife_bot():
    # Get closest player / Obtener jugador más cercano
    closest_player = api.get_closest_player()
    if closest_player and not closest_player['is_dead']:
        distance = closest_player.get('distance', float('inf'))
        
        # If player is close enough for knife attack / Si el jugador está lo suficientemente cerca para ataque con cuchillo
        if distance < 65:  # 65 units is knife range / 65 unidades es el rango del cuchillo
            api.aim_at_player(closest_player['id'])
            api.attack2()  # Knife attack / Ataque con cuchillo

while True:
    knife_bot()
    time.sleep(0.05)
```

## 📚 API Reference / Referencia de la API

### Core Methods / Métodos Principales

| Method / Método | Description / Descripción | Parameters / Parámetros |
|--------|-------------|------------|
| `send_command(command)` | Send console command / Enviar comando de consola | `command`: String command / Comando string |
| `say(text)` | Send public chat message / Enviar mensaje público al chat | `text`: Message text / Texto del mensaje |
| `team_say(text)` | Send team chat message / Enviar mensaje al chat del equipo | `text`: Message text / Texto del mensaje |
| `connect_to_server(ip)` | Connect to server / Conectar al servidor | `ip`: "IP:PORT" format / Formato "IP:PUERTO" |

### Player Actions / Acciones del Jugador

| Method / Método | Description / Descripción | Parameters / Parámetros |
|--------|-------------|------------|
| `attack(activate)` | Primary attack / Ataque primario | `activate`: True/False/None |
| `attack2(activate)` | Secondary attack / Ataque secundario | `activate`: True/False/None |
| `jump(activate)` | Jump / Saltar | `activate`: True/False/None |
| `duck(activate)` | Crouch / Agacharse | `activate`: True/False/None |
| `forward(activate)` | Move forward / Moverse hacia adelante | `activate`: True/False/None |
| `back(activate)` | Move backward / Moverse hacia atrás | `activate`: True/False/None |

### Information Gathering / Obtención de Información

| Method / Método | Description / Descripción | Returns / Retorna |
|--------|-------------|---------|
| `get_player_names()` | Get all player names / Obtener todos los nombres de jugadores | List of strings / Lista de strings |
| `get_player_coords(player_id)` | Get player coordinates / Obtener coordenadas del jugador | Tuple (x, y, z) / Tupla (x, y, z) |
| `get_local_player_coords()` | Get your coordinates / Obtener tus coordenadas | Tuple (x, y, z) / Tupla (x, y, z) |
| `get_closest_player()` | Get nearest player info / Obtener info del jugador más cercano | Player dictionary / Diccionario del jugador |
| `get_all_players_info()` | Get all players info / Obtener info de todos los jugadores | List of player dictionaries / Lista de diccionarios de jugadores |

### Aiming System / Sistema de Puntería

| Method / Método | Description / Descripción | Parameters / Parámetros |
|--------|-------------|------------|
| `aim_at_player(player_id, target_head, smooth)` | Aim at player / Apuntar al jugador | `player_id`: int, `target_head`: bool, `smooth`: float |
| `aim_at_coords(x, y, z, smooth)` | Aim at coordinates / Apuntar a coordenadas | `x, y, z`: float, `smooth`: float |
| `get_view_angles()` | Get camera angles / Obtener ángulos de cámara | Returns (pitch, yaw, roll) / Retorna (pitch, yaw, roll) |

## 🔧 Technical Details / Detalles Técnicos

**EN**
- **Memory Manipulation**: Uses `pymem` for reading/writing game memory
- **Process Detection**: Automatically finds hl.exe processes
- **Shellcode Injection**: Executes commands through remote thread injection
- **Real-time Data**: Accesses live game state information

**ES**
- **Manipulación de Memoria**: Usa `pymem` para leer/escribir memoria del juego
- **Detección de Procesos**: Encuentra automáticamente procesos hl.exe
- **Inyección de Shellcode**: Ejecuta comandos a través de inyección de hilos remotos
- **Datos en Tiempo Real**: Accede a información del estado del juego en vivo

##  Troubleshooting / Solución de Problemas

**EN**
1. **"No se encontró hl.exe"**: Make sure Counter-Strike 1.6 is running
2. **Memory access errors**: Run your script as Administrator
3. **Commands not working**: Verify the game is in focus and not paused
4. **Multiple processes**: Use the PID parameter to specify the correct instance

**ES**
1. **"No se encontró hl.exe"**: Asegúrate de que Counter-Strike 1.6 esté ejecutándose
2. **Errores de acceso a memoria**: Ejecuta tu script como Administrador
3. **Los comandos no funcionan**: Verifica que el juego esté enfocado y no pausado
4. **Múltiples procesos**: Usa el parámetro PID para especificar la instancia correcta

