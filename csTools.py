import re
import pymem
import pymem.process
import struct
import ctypes
import psutil

class csApi:
    def __init__(self, pid=None):
        self.pm = None
        self.engine_base = None
        self.pid = pid

        # get players names
        self.names_base = 0x120304C  
        self.names_scan_size = 16048  
        self.names_scan_chunks = 5

        # team information constants
        self.team_base_offset = 0x12F4AC
        self.team_step = 0x74
        self.TEAM_MAP = {
            0: "Spectator",
            65536: "Terrorist",
            131072: "Counter-Terrorist"
        }
        
    def choose_process(self):

        if self.pid is not None:

            try:
                proc = psutil.Process(self.pid)
                if proc.name().lower() == 'hl.exe':
                    return self.pid
                else:
                    print(f"Proceso con PID {self.pid} no es hl.exe")
                    return None
            except psutil.NoSuchProcess:
                print(f"No existe proceso con PID {self.pid}")
                return None
        

        hl_processes = [proc for proc in psutil.process_iter(['pid', 'name']) 
                         if proc.info['name'] and proc.info['name'].lower() == 'hl.exe']
        
        if not hl_processes:
            print("No se encontraron procesos hl.exe")
            return None
            
        if len(hl_processes) == 1:
            return hl_processes[0].pid
            
        print("\nSe encontraron múltiples procesos de Half-Life | Counter Strike 1.6:")
        for i, proc in enumerate(hl_processes):
            print(f"{i+1}. hl.exe (PID: {proc.info['pid']})")
            
        while True:
            try:
                selection = input("\nSelecciona el número del proceso (o 'q' para cancelar): ")
                if selection.lower() == 'q':
                    return None
                    
                idx = int(selection) - 1
                if 0 <= idx < len(hl_processes):
                    return hl_processes[idx].pid
                else:
                    print("Selección inválida. Intenta de nuevo.")
            except ValueError:
                print("Por favor ingresa un número válido.")
    
    def attach_to_hl(self):
        try:
            pid = self.choose_process()
            if not pid:
                return False
                
            self.pm = pymem.Pymem()
            self.pm.open_process_from_id(pid)
            
            self.engine_base = self._get_engine_base()
            if not self.engine_base:
                print("No se pudo obtener la dirección base de engine.dll")
                return False
                
            
            return True
            
        except pymem.exception.ProcessNotFound:
            print("No se encontró hl.exe ejecutándose.")
            return False
        except Exception as e:
            print(f"Error al conectar con el proceso: {e}")
            return False
            
    def _get_engine_base(self):
        if not self.pm:
            return None
        try:
            engine_module = pymem.process.module_from_name(self.pm.process_handle, "engine.dll")
            if engine_module:
                return engine_module.lpBaseOfDll
            return None
        except:
            print("Error al obtener la dirección base de engine.dll")
            return None
            
    def _get_client_base(self):
 
     if not self.pm:
        return None
     try:
        client_module = pymem.process.module_from_name(self.pm.process_handle, "client.dll")
        if client_module:
            return client_module.lpBaseOfDll
        return None
     except Exception as e:
        print(f"Error al obtener la dirección base de client.dll: {e}")
        return None
    
    def _get_function_address(self):
        if not self.pm or not self.engine_base:
            return None, None
            
        try:
            ecx_address = self.engine_base + 0x166BC4
            ecx_value = self.pm.read_int(ecx_address) + 0x15C
            func_address = self.pm.read_int(ecx_value + 0x50)
            return ecx_value, func_address
        except:
            print("Error al obtener las direcciones de función")
            return None, None
            
    def send_command(self, command):
        if not self.pm:
            if not self.attach_to_hl():
                return "Error: No se pudo conectar a hl.exe"
                
        ecx_value, func_address = self._get_function_address()
        
        if not func_address:
            return "Error: No se pudo leer la dirección de la función"
            
        buffer_size = 64
        text_buffer = self.pm.allocate(buffer_size)
        encoded_command = command.encode("utf-8")
        data = encoded_command + b"\0"
        data_length = len(data)
        
        if data_length > buffer_size:
            self.pm.free(text_buffer)
            text_buffer = self.pm.allocate(data_length)
        
        self.pm.write_bytes(text_buffer, data, data_length)
        
        shellcode = (
            b"\x60" + 
            b"\xB9" + struct.pack("<I", ecx_value) +
            b"\x68" + struct.pack("<I", text_buffer) +
            b"\xB8" + struct.pack("<I", func_address) +
            b"\xFF\xD0" +
            b"\x83\xC4\x04" +
            b"\x61" +
            b"\xC3"
        )
        
        shellcode_addr = self.pm.allocate(len(shellcode))
        self.pm.write_bytes(shellcode_addr, shellcode, len(shellcode))
        
        kernel32 = ctypes.windll.kernel32
        thread_handle = kernel32.CreateRemoteThread(self.pm.process_handle, None, 0, shellcode_addr, None, 0, None)
        
        result = False
        if thread_handle:
            kernel32.WaitForSingleObject(thread_handle, 0xFFFFFFFF)
            kernel32.CloseHandle(thread_handle)
            result = True
        
        try:
            self.pm.free(text_buffer)
            self.pm.free(shellcode_addr)
        except Exception as e:
            print(f"Error al liberar memoria: {e}")
        
        return result
    
    def change_name(self, name):
        return self.send_command(f'name "{name}"')
    
    def say(self, text):
        return self.send_command(f'say "{text}"')
    
    def team_say(self, text):
        return self.send_command(f'say_team "{text}"')
    
    def voice_record(self):
        return self.send_command("+voicerecord")
    
    def stop_voice_record(self):
        return self.send_command("-voicerecord")
    
    def toggle_console(self):
        return self.send_command("toggleconsole")
    
    def connect_to_server(self, ip):
        if not ":" in ip:
            print("ERROR: Missing port")
            return False
        return self.send_command(f"connect {ip}")
    
    def disconnect_server(self):
        return self.send_command("disconnect")
    
    def show_hud(self, state):
        if state == True:
            return self.send_command("hud_draw 1")
        elif state == False:
            return self.send_command("hud_draw 0")
        else:
            print("Invalid state")
            return False
    
    def auto_buy(self):
        return self.send_command("autobuy")
    
    def kill(self):
        return self.send_command("kill")
    
    def record_demo(self, name, path=None):
        if path:
            full_path = f"{path.rstrip('/')}/{name}"
        else:
            full_path = name 
        return self.send_command(f"record {full_path}")
    
    def reconnect_to_server(self):
        return self.send_command("retry")
    
    # more movements

    def attack(self, activate=None):
     """
    Controla el ataque primario (disparar).
    
    Args:
        activate: 
            - True: Activa el ataque continuo (+attack)
            - False: Desactiva el ataque (-attack)
            - None: Simula un ataque rápido (envía +attack seguido de -attack)
    
    Returns:
        bool: True si se ejecutó correctamente
    """
     if activate is None:

        success1 = self.send_command("+attack")
        success2 = self.send_command("-attack")
        return success1 and success2
     else:
        command = "+attack" if activate else "-attack"
        return self.send_command(command)

    def attack2(self, activate=None):
     """
    Controla el ataque secundario (zoom/alternativo).
    
    Args:
        activate: 
            - True: Activa el ataque secundario continuo (+attack2)
            - False: Desactiva el ataque secundario (-attack2)
            - None: Simula un ataque secundario rápido (envía +attack2 seguido de -attack2)
    
    Returns:
        bool: True si se ejecutó correctamente
    """
     if activate is None:

        success1 = self.send_command("+attack2")
        success2 = self.send_command("-attack2")
        return success1 and success2
     else:
        command = "+attack2" if activate else "-attack2"
        return self.send_command(command)

    def jump(self, activate=None):
     """
    Controla el salto.
    
    Args:
        activate: 
            - True: Activa el salto continuo (+jump)
            - False: Desactiva el salto (-jump)
            - None: Simula un salto rápido (envía +jump seguido de -jump)
    
    Returns:
        bool: True si se ejecutó correctamente
    """
     if activate is None:

        success1 = self.send_command("+jump")
        success2 = self.send_command("-jump")
        return success1 and success2
     else:
        command = "+jump" if activate else "-jump"
        return self.send_command(command)

    def duck(self, activate=None):
     """
    Controla agacharse.
    
    Args:
        activate: 
            - True: Activa agacharse continuo (+duck)
            - False: Desactiva agacharse (-duck)
            - None: Simula agacharse rápido (envía +duck seguido de -duck)
    
    Returns:
        bool: True si se ejecutó correctamente
    """
     if activate is None:

        success1 = self.send_command("+duck")
        success2 = self.send_command("-duck")
        return success1 and success2
     else:
        command = "+duck" if activate else "-duck"
        return self.send_command(command)

    def forward(self, activate=None):
     """
    Controla el movimiento hacia adelante.
    
    Args:
        activate: 
            - True: Activa movimiento continuo (+forward)
            - False: Desactiva movimiento (-forward)
            - None: Simula un paso rápido (envía +forward seguido de -forward)
    
    Returns:
        bool: True si se ejecutó correctamente
    """
     if activate is None:

        success1 = self.send_command("+forward")
        success2 = self.send_command("-forward")
        return success1 and success2
     else:
        command = "+forward" if activate else "-forward"
        return self.send_command(command)

    def back(self, activate=None):
     """
    Controla el movimiento hacia atrás.
    
    Args:
        activate: 
            - True: Activa movimiento continuo (+back)
            - False: Desactiva movimiento (-back)
            - None: Simula un paso rápido (envía +back seguido de -back)
    
    Returns:
        bool: True si se ejecutó correctamente
    """
     if activate is None:

        success1 = self.send_command("+back")
        success2 = self.send_command("-back")
        return success1 and success2
     else:
        command = "+back" if activate else "-back"
        return self.send_command(command)

    def move_left(self, activate=None):
     """
    Controla el movimiento hacia la izquierda.
    
    Args:
        activate: 
            - True: Activa movimiento continuo (+moveleft)
            - False: Desactiva movimiento (-moveleft)
            - None: Simula un paso rápido (envía +moveleft seguido de -moveleft)
    
    Returns:
        bool: True si se ejecutó correctamente
    """
     if activate is None:

        success1 = self.send_command("+moveleft")
        success2 = self.send_command("-moveleft")
        return success1 and success2
     else:
        command = "+moveleft" if activate else "-moveleft"
        return self.send_command(command)

    def move_right(self, activate=None):
     """
    Controla el movimiento hacia la derecha.
    
    Args:
        activate: 
            - True: Activa movimiento continuo (+moveright)
            - False: Desactiva movimiento (-moveright)
            - None: Simula un paso rápido (envía +moveright seguido de -moveright)
    
    Returns:
        bool: True si se ejecutó correctamente
    """
     if activate is None:

        success1 = self.send_command("+moveright")
        success2 = self.send_command("-moveright")
        return success1 and success2
     else:
        command = "+moveright" if activate else "-moveright"
        return self.send_command(command)

    def use(self, activate=None):
     """
    Controla la acción de usar objetos.
    
    Args:
        activate: 
            - True: Activa el uso continuo (+use)
            - False: Desactiva el uso (-use)
            - None: Simula un uso rápido (envía +use seguido de -use)
    
    Returns:
        bool: True si se ejecutó correctamente
    """
     if activate is None:

        success1 = self.send_command("+use")
        success2 = self.send_command("-use")
        return success1 and success2
     else:
        command = "+use" if activate else "-use"
        return self.send_command(command)

    def walk(self, activate=None):
     """
    Controla el caminar lento (shift).
    
    Args:
        activate: 
            - True: Activa caminar lento continuo (+speed)
            - False: Desactiva caminar lento (-speed)
            - None: Simula un cambio rápido (envía +speed seguido de -speed)
    
    Returns:
        bool: True si se ejecutó correctamente
    """
     if activate is None:

        success1 = self.send_command("+speed")
        success2 = self.send_command("-speed")
        return success1 and success2
     else:
        command = "+speed" if activate else "-speed"
        return self.send_command(command)
    
    def get_player_names(self, with_player_prefix=False):
        """
        Obtiene los nombres de los jugadores en el servidor.
        
        Args:
            with_player_prefix (bool): Si es True, devuelve los nombres con formato "Player X: [nombre]"
        
        Returns:
            list: Lista de nombres de jugadores
        """
        
        if not self.pm:
            if not self.attach_to_hl():
                return []
        
        
        try:
            if not self.engine_base:
                print("Error: No se ha establecido la dirección base de engine.dll")
                return []
                
            base_player_address = self.engine_base + self.names_base
        except Exception as e:
            print(f"Error al obtener la dirección base para los jugadores: {e}")
            return []

        
        all_bytes = bytearray()
        current_address = base_player_address
        for _ in range(self.names_scan_chunks):
            try:
                chunk = self.pm.read_bytes(current_address, self.names_scan_size)
                all_bytes.extend(chunk)
                current_address += self.names_scan_size
            except Exception as e:
                print(f"Error al leer memoria en 0x{current_address:X}: {e}")
                break

        memory_bytes = bytes(all_bytes)
        if not memory_bytes:
            return []

        
        ascii_data = ''.join(
            '\x00' if b == 0 else chr(b) if 32 <= b <= 126 else '.'
            for b in memory_bytes
        )

        
        model_pattern = re.compile(r'\\model\\')
        match = model_pattern.search(ascii_data)
        if not match:
            return []

        start_pos = max(0, match.start() - 100)
        pre_slice = ascii_data[start_pos:match.start()]
        last_dot = pre_slice.rfind('.')
        start_index = start_pos + last_dot + 1 if last_dot != -1 else start_pos
        ascii_data = ascii_data[start_index:]

        
        name_pattern = re.compile(r'\\name\\([^\\]+)')
        model_pattern = re.compile(r'\\model\\([^\\]+)')
        sid_pattern = re.compile(r'\\[*]sid\\([^\\]+)')

        entries = []
        for typ, pat in [('name', name_pattern), ('model', model_pattern), ('sid', sid_pattern)]:
            for m in pat.finditer(ascii_data):
                entries.append({
                    'type': typ,
                    'value': m.group(1),
                    'pos': m.start()
                })

        entries.sort(key=lambda e: e['pos'])


        players = []
        current = {}
        player_id = 0

        def flush(cp):
            nonlocal player_id
            if all(k in cp for k in ('name', 'model', 'sid')):
                player_id += 1
                
                clean_name = cp['name']['value'].split('\x00')[0]  
                players.append({
                    'id': str(player_id),
                    'name': clean_name,
                    'model': cp['model']['value'][:6],
                    'sid': cp['sid']['value'][:17]
                })

        for e in entries:
            if e['type'] in current:
                flush(current)
                current = {}
            current[e['type']] = e
            if all(k in current for k in ('name', 'model', 'sid')):
                flush(current)
                current = {}

        
        flush(current)

        
        seen = set()
        result = []
        for idx, p in enumerate(players):
            if p['sid'] not in seen:
                seen.add(p['sid'])
                if with_player_prefix:
                    result.append(f"Player {idx+1}: {p['name']}")
                else:
                    result.append(p['name'])
        
        return result
    
    
    def get_player_teams(self):
     """
    Obtiene los equipos de los jugadores en el servidor.
    
    Returns:
        dict: Diccionario que mapea ID de jugador a nombre de equipo
    """
     if not self.pm:
        if not self.attach_to_hl():
            return {}
    
     try:
        client_module = pymem.process.module_from_name(self.pm.process_handle, "client.dll")
        if not client_module:
            print("Error: No se pudo obtener la dirección base de client.dll")
            return {}
            
        client_base = client_module.lpBaseOfDll
        player_teams = {}
        
        for i in range(32):  
            addr = client_base + self.team_base_offset + (i * self.team_step)
            try:
                value = self.pm.read_int(addr)
                if value in self.TEAM_MAP:
                    player_teams[i+1] = self.TEAM_MAP[value]
            except:
                continue  
                
        return player_teams
            
     except Exception as e:
        print(f"Error al obtener equipos de jugadores: {e}")
        return {}
    
   
    def get_players_with_teams(self):
     """
    Obtiene los nombres de los jugadores junto con sus equipos.
    
    Returns:
        list: Lista de diccionarios con información de jugadores
    """
     players = self.get_player_names(with_player_prefix=False)
     teams = self.get_player_teams()
    
     result = []
     for idx, name in enumerate(players):
        player_id = idx + 1
        team = teams.get(player_id, "Desconocido")
        result.append({
            "id": player_id,
            "name": name,
            "team": team
        })
    
     return result
     
    def get_local_player_id(self):
     """
    obtener la id del player local
    
    returns:
        int: ID del jugador local o 0 si no se puede obtener
    """
     if not self.pm or not self.engine_base:
        if not self.attach_to_hl():
            return 0
    
     local_player_id_offset = 0x119700C
     local_player_id_addr = self.engine_base + local_player_id_offset
    
     try:
        local_player_id = self.pm.read_int(local_player_id_addr)
        if local_player_id > 0 and local_player_id <= 32: 
            return local_player_id
     except Exception as e:
        print(f"Error al obtener ID del jugador local: {e}")
    
     return 0
    
    def get_local_player_coords(self):
     """
    obtiene las coordenadas del jugador local
    
    returns:
        tuple: Coordenadas (x, y, z) del jugador local o None si no se pueden obtener
    """
     if not self.pm or not self.engine_base:
        if not self.attach_to_hl():
            return None
    
     local_x_offset = 0x16CF30
     local_y_offset = 0x16CF34
     local_z_offset = 0x16CF38
    
     try:
        x = self.pm.read_float(self.engine_base + local_x_offset)
        y = self.pm.read_float(self.engine_base + local_y_offset)
        z = self.pm.read_float(self.engine_base + local_z_offset)
        
       
        if (abs(x) > 0.1 or abs(y) > 0.1 or abs(z) > 0.1):
            return (x, y, z)
     except Exception as e:
        print(f"Error al obtener coordenadas del jugador local: {e}")
    
     return None
    
    def get_player_coords(self, player_num=None):
     """
    Obtiene las coordenadas de un jugador específico o de todos los jugadores.
    
    Args:
        player_num: Número de jugador (1-32). Si es None, devuelve todos los jugadores.
    
    Returns:
        dict o tuple: Si player_num es None, devuelve un diccionario {player_num: (x, y, z)}.
                      Si player_num está especificado, devuelve una tupla (x, y, z) o None.
    """
     if not self.pm or not self.engine_base:
        if not self.attach_to_hl():
            return {} if player_num is None else None
    
   
     if player_num is not None:
        if player_num < 1 or player_num > 32:
            return None
        
       
        i = player_num - 1
        
       
        player_offsets = [0x16C160, 0x16C188, 0x16C1B0, 0x16C1D8]
        player_offset_step = 0x28
        
       
        if i < 4:
            z_offset = player_offsets[i]
        else:
            z_offset = player_offsets[3] + (i - 3) * player_offset_step
        
        
        x_offset_from_z = -0x8
        y_offset_from_z = -0x4
        
        x_offset = z_offset + x_offset_from_z
        y_offset = z_offset + y_offset_from_z
        
        try:
            x = self.pm.read_float(self.engine_base + x_offset)
            y = self.pm.read_float(self.engine_base + y_offset)
            z = self.pm.read_float(self.engine_base + z_offset)
            
           
            if (abs(x) > 0.1 or abs(y) > 0.1 or abs(z) > 0.1):
                return (x, y, z)
        except Exception as e:
            print(f"Error al obtener coordenadas del jugador {player_num}: {e}")
        
        return None
    

     else:
        player_coords = {}
        player_offsets = [0x16C160, 0x16C188, 0x16C1B0, 0x16C1D8]
        player_offset_step = 0x28
        x_offset_from_z = -0x8
        y_offset_from_z = -0x4
        
        for i in range(32): 
            player_num = i + 1
            
            
            if i < 4:
                z_offset = player_offsets[i]
            else:
                z_offset = player_offsets[3] + (i - 3) * player_offset_step
            
            x_offset = z_offset + x_offset_from_z
            y_offset = z_offset + y_offset_from_z
            
            try:
                x = self.pm.read_float(self.engine_base + x_offset)
                y = self.pm.read_float(self.engine_base + y_offset)
                z = self.pm.read_float(self.engine_base + z_offset)
                
               
                if (abs(x) > 0.1 or abs(y) > 0.1 or abs(z) > 0.1):
                    player_coords[player_num] = (x, y, z)
            except:
                continue  
        
        return player_coords
    
    def is_player_dead(self, player_num=None):
     """
     Determina si un jugador está muerto o el estado de todos los jugadores.
    
    Args:
        player_num: Número de jugador (1-32). Si es None, devuelve todos los jugadores.
    
    Returns:
        bool o dict: Si player_num es None, devuelve un diccionario {player_num: is_dead}.
                     Si player_num está especificado, devuelve True/False.
    """
     if not self.pm or not self.engine_base:
        if not self.attach_to_hl():
            return {} if player_num is None else False
    
    
     client_base = self._get_client_base()
     if not client_base:
        return {} if player_num is None else False
    
   
     if player_num is not None:
        if player_num < 1 or player_num > 32:
            return False
        
        
        i = player_num - 1
        
        
        player_state_offsets = [0x12F4C0, 0x12F534, 0x12F5A8]
        
       
        if i < 3:
            state_offset = player_state_offsets[i]
        else:
           
            state_offset = player_state_offsets[2] + ((i - 2) * 0x74)
        
        try:
            state_addr = client_base + state_offset
            player_state = self.pm.read_int(state_addr)
            
           
            return player_state == 1
        except Exception as e:
            print(f"Error al verificar si el jugador {player_num} está muerto: {e}")
        
        return False
    
    
     else:
        player_states = {}
        player_state_offsets = [0x12F4C0, 0x12F534, 0x12F5A8]
        
        for i in range(32): 
            player_num = i + 1
            
            
            if i < 3:
                state_offset = player_state_offsets[i]
            else:
               
                state_offset = player_state_offsets[2] + ((i - 2) * 0x74)
            
            try:
                state_addr = client_base + state_offset
                player_state = self.pm.read_int(state_addr)
                player_states[player_num] = (player_state == 1)  
            except:
                continue  
        
        return player_states
    
    def is_player_visible(self, player_num=None):
     """
    Determina si un jugador es visible o la visibilidad de todos los jugadores.
    
    Args:
        player_num: Número de jugador (1-32). Si es None, devuelve todos los jugadores.
    
    Returns:
        bool o dict: Si player_num es None, devuelve un diccionario {player_num: is_visible}.
                     Si player_num está especificado, devuelve True/False.
    """
     if not self.pm or not self.engine_base:
        if not self.attach_to_hl():
            return {} if player_num is None else False
    
    
     if player_num is not None:
        if player_num < 1 or player_num > 32:
            return False
        
        
        i = player_num - 1
        
        
        player_visibility_offsets = [0x16C154, 0x16C17C, 0x16C1A4]
        
        
        if i < 3:
            vis_addr = self.engine_base + player_visibility_offsets[i]
        else:
           
            vis_offset = player_visibility_offsets[2] + ((i - 2) * 0x28)
            vis_addr = self.engine_base + vis_offset
        
        try:
            vis_value = self.pm.read_int(vis_addr)
            return vis_value == 1
        except Exception as e:
            print(f"Error al verificar si el jugador {player_num} es visible: {e}")
        
        return False
    
   
     else:
        player_visibility = {}
        player_visibility_offsets = [0x16C154, 0x16C17C, 0x16C1A4]
        
        for i in range(32): 
            player_num = i + 1
            
            
            if i < 3:
                vis_addr = self.engine_base + player_visibility_offsets[i]
            else:

                vis_offset = player_visibility_offsets[2] + ((i - 2) * 0x28)
                vis_addr = self.engine_base + vis_offset
            
            try:
                vis_value = self.pm.read_int(vis_addr)
                player_visibility[player_num] = (vis_value == 1)
            except:
                continue  
        
        return player_visibility
     

    def get_all_players_info(self):
     """
    Obtiene información completa de todos los jugadores activos en el servidor.
    
    Returns:
        list: Lista de diccionarios con información de cada jugador activo.
              Cada diccionario contiene:
              - id: Número del jugador
              - name: Nombre del jugador
              - team: Equipo del jugador
              - coords: Coordenadas (x, y, z)
              - is_dead: Estado (vivo/muerto)
              - is_visible: Si es visible para el jugador local
              - distance: Distancia al jugador local (si se pueden obtener ambas coordenadas)
    """
     if not self.pm or not self.engine_base:
        if not self.attach_to_hl():
            return []
            

     local_player_id = self.get_local_player_id()
    

     local_coords = self.get_local_player_coords()
    

     all_names = self.get_player_names(with_player_prefix=False)
    

     all_teams = self.get_player_teams()
    

     all_coords = self.get_player_coords()
    

     all_states = self.is_player_dead()
    

     all_visibility = self.is_player_visible()
    

     def calculate_distance(coords1, coords2):
        if not coords1 or not coords2:
            return None
        x1, y1, z1 = coords1
        x2, y2, z2 = coords2
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5
    

     players_info = []
    
     for player_id in range(1, 33):

        has_name = player_id <= len(all_names) and all_names[player_id - 1]
        

        has_coords = player_id in all_coords
        

        if has_name or has_coords:
            name = all_names[player_id - 1] if has_name else f"Player {player_id}"
            coords = all_coords.get(player_id)
            team = all_teams.get(player_id, "Desconocido")
            is_dead = all_states.get(player_id, False)
            is_visible = all_visibility.get(player_id, False)
            

            distance = None
            if local_coords and coords:
                distance = calculate_distance(local_coords, coords)
            

            player_info = {
                "id": player_id,
                "name": name,
                "team": team,
                "coords": coords,
                "is_dead": is_dead,
                "is_visible": is_visible,
                "distance": distance,
                "is_local": player_id == local_player_id
            }
            
            players_info.append(player_info)
    

     players_info.sort(key=lambda p: p.get("distance", float('inf')) if p.get("distance") is not None else float('inf'))
    
     return players_info
    
    def get_closest_player(self):
     """
    Obtiene la información completa del jugador no local más cercano al jugador local.
    
    Returns:
        dict: Diccionario con información completa del jugador más cercano, o None si no hay jugadores.
              El diccionario contiene:
              - id: Número del jugador
              - name: Nombre del jugador
              - team: Equipo del jugador
              - coords: Coordenadas (x, y, z)
              - is_dead: Estado (vivo/muerto)
              - is_visible: Si es visible para el jugador local
              - distance: Distancia al jugador local
              - is_local: Siempre False para esta función
    """
   
     all_players = self.get_all_players_info()
    
     if not all_players:
        return None
    
   
     valid_players = [player for player in all_players
                     if not player.get("is_local", False) and 
                     player.get("distance") is not None]
    
     if not valid_players:
        return None
    
    
     valid_players.sort(key=lambda p: p.get("distance", float('inf')))
     closest_player = valid_players[0]
    
     return closest_player
    
    def get_view_angles(self):
     """
    Obtiene los ángulos de visión (cámara) del jugador local.
    
    Returns:
        tuple: (pitch, yaw, roll) o None si no se pudieron obtener.
               - pitch: ángulo vertical (mirar arriba/abajo)
               - yaw: ángulo horizontal (girar izquierda/derecha)
               - roll: inclinación de la cámara (generalmente no usado en CS)
    """
     if not self.pm or not self.engine_base:
        if not self.attach_to_hl():
            return None
    
  
     pitch_offset = 0x108AB44
     yaw_offset = 0x108AB48
     roll_offset = 0x108AB4C
    
     try:
       
        pitch = self.pm.read_float(self.engine_base + pitch_offset)
        yaw = self.pm.read_float(self.engine_base + yaw_offset)
        roll = self.pm.read_float(self.engine_base + roll_offset)
        
        return (pitch, yaw, roll)
     except Exception as e:
        print(f"Error al obtener ángulos de visión: {e}")
        return None
     
    def set_view_angles(self, pitch=None, yaw=None, roll=None):
     """
    Modifica los ángulos de visión (cámara) del jugador local.
    
    Args:
        pitch (float, opcional): Ángulo vertical (mirar arriba/abajo)
                                Valores: -90 (mirar arriba) a 90 (mirar abajo)
        yaw (float, opcional): Ángulo horizontal (girar izquierda/derecha)
                              Valores: 0-360 o -180 a 180
        roll (float, opcional): Inclinación de la cámara (generalmente no usado)
    
    Returns:
        bool: True si al menos un ángulo fue modificado exitosamente
    """
     if not self.pm or not self.engine_base:
        if not self.attach_to_hl():
            return False
    
   
     pitch_offset = 0x108AB44
     yaw_offset = 0x108AB48
     roll_offset = 0x108AB4C
    
     success = False
    
     try:
       
        if pitch is not None:
            
            pitch = max(-90, min(90, pitch))
            self.pm.write_float(self.engine_base + pitch_offset, pitch)
            success = True
            
       
        if yaw is not None:
            
            yaw = yaw % 360
            self.pm.write_float(self.engine_base + yaw_offset, yaw)
            success = True
            
        
        if roll is not None:
            self.pm.write_float(self.engine_base + roll_offset, roll)
            success = True
            
        return success
     except Exception as e:
        print(f"Error al modificar ángulos de visión: {e}")
        return False
     
    def aim_at_coords(self, target_x, target_y, target_z, smooth=0):
     """
    Apunta la cámara hacia las coordenadas especificadas.
    
    Args:
        target_x (float): Coordenada X del objetivo
        target_y (float): Coordenada Y del objetivo
        target_z (float): Coordenada Z del objetivo
        smooth (float): Factor de suavizado entre 0 y 1, donde:
                       0 = movimiento instantáneo
                       1 = sin movimiento
                       valores intermedios = movimiento gradual
    
    Returns:
        bool: True si se pudo apuntar correctamente
    """
     import math
    

     local_coords = self.get_local_player_coords()
     if not local_coords:
        return False
    
     local_x, local_y, local_z = local_coords
    

     current_angles = self.get_view_angles()
     if not current_angles:
        return False
    
     current_pitch, current_yaw, _ = current_angles
    

     delta_x = target_x - local_x
     delta_y = target_y - local_y
     delta_z = target_z - local_z
    

     distance_horizontal = math.sqrt(delta_x ** 2 + delta_y ** 2)
    

     new_pitch = -math.atan2(delta_z, distance_horizontal) * 180 / math.pi
     new_yaw = math.atan2(delta_y, delta_x) * 180 / math.pi
    

     if new_yaw < 0:
        new_yaw += 360
    

     if 0 < smooth < 1:

        pitch_diff = new_pitch - current_pitch

        if pitch_diff > 180:
            pitch_diff -= 360
        elif pitch_diff < -180:
            pitch_diff += 360
            

        yaw_diff = new_yaw - current_yaw

        if yaw_diff > 180:
            yaw_diff -= 360
        elif yaw_diff < -180:
            yaw_diff += 360
        

        new_pitch = current_pitch + pitch_diff * (1 - smooth)
        new_yaw = current_yaw + yaw_diff * (1 - smooth)
    
    
     return self.set_view_angles(pitch=new_pitch, yaw=new_yaw)
    
    def aim_at_player(self, player_id=None, target_head=True, smooth=0):
     """
    Apunta la cámara hacia un jugador específico o hacia el más cercano.
    
    Args:
        player_id (int, opcional): ID del jugador al que apuntar.
                                   Si es None, apunta al jugador más cercano.
        target_head (bool): Si es True, apunta a la cabeza; si es False, al cuerpo.
        smooth (float): Factor de suavizado entre 0 y 1.
    
    Returns:
        bool: True si se pudo apuntar correctamente
    """

     if player_id is None:
        closest_player = self.get_closest_player()
        if not closest_player:
            return False
        player_id = closest_player["id"]
    

     coords = self.get_player_coords(player_id)
     if not coords:
        return False
    
     target_x, target_y, target_z = coords
    

     if target_head:
        target_z += 1.0
     else:
        target_z += 0.0
    

     return self.aim_at_coords(target_x, target_y, target_z, smooth)
