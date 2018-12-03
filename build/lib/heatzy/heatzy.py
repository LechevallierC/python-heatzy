import requests
import time

# Handler Heatzy : 'pont', s'authentifie auprès du serveur Gizwits et récupère le token
class HeatzyHandler:
    # Constantes
    API_BASE_URL = "https://euapi.gizwits.com/app"  # URL de base pour l'API Gizwits employée 
    APPID = "c70a66ff039d41b4a220e198b0fcc8b3"      # APPID Heatzy dans Gizwits

    # Constructeur
    def __init__(self,login,password):
        self.login = login          # Identificant
        self.password = password    # Mot de passe
        self.token = None           # Initialisation du token
        self.token_expires = None   # TODO : expiration du token
        self.get_token()            # Récupération du token

    # Récupération du token
    def get_token(self):
        # Todo : return token si l'expiration est dans + de 24h : vérifier time.now?
        #if self.token and self.token_expires < time.time:
        #    return self.token:

        login_headers = {'Accept': 'application/json', 'X-Gizwits-Application-Id': HeatzyHandler.APPID}     # Préparation des headers
        login_payload = {'username': self.login, 'password': self.password, 'lang': 'en'}                   # Payload du login
        loginRequest = requests.post(HeatzyHandler.API_BASE_URL+'/login', json=login_payload, headers=login_headers)

        loginJSON = loginRequest.json()
        # Si on récupère un token : OK
        if 'token' in loginJSON:
            # TODO : ajouter champ d'expiration du token
            self.token = loginJSON['token']
            self.token_expires = loginJSON['expire_at']
            return self.token

        else:
            raise Exception('Erreur de login : '+loginRequest.json())

    # Récupère les devices
    def getHeatzyDevices(self):
        login_headers = {'Accept': 'application/json', 'X-Gizwits-Application-Id': HeatzyHandler.APPID, 'X-Gizwits-User-token' : self.get_token()}
        loginRequest = requests.get(HeatzyHandler.API_BASE_URL+'/bindings', headers=login_headers)

        # TODO : Check for errors 

        request_devices_list = loginRequest.json()['devices']
        devices_dict = dict()

        # Infos à extraire : device alias, did, product_name
        for device in request_devices_list:
            dev = HeatzyDevice(self,name=device['dev_alias'], did=device['did'], version=device['product_name'])
            devices_dict[dev.name] = dev

        return devices_dict

# Classe HeatzyDevice
class HeatzyDevice:
    def __init__(self,handler,name,did,version):
        self.handler = handler                  # Object HeatzyHandler (pour gérer les connexions à l'API Gizwits)
        self.name = name                        # Nom du device, tel que reporté dans l'application
        self.did = did                          # Device ID (UID Gizwits)
        self.version = version                  # Version du heatzy ('Heatzy' : Gen 1, 'Pilote2': Gen 2)
        self.mode = None                        # Mode (Aucun pour l'instant)
        self.status()                           # Récupération de l'état

    # Améliorer tostring...
    # ToString
    def __str__(self):
        str = 'HeatzyDevice : name:'+self.name+',did:'+self.did+',version:'+self.version+',mode:'+self.status()
        return str

    # Rafraichit l'etat
    def status(self):
        # Matrice de décodage des modes
        modes_decode = {
            'Pilote2' : {'stop' : 'OFF', 'eco' : 'ECO', 'fro' : 'HGEL', 'cft' : 'CONFORT'}, # Modes pour Pilote2
            'Heatzy' : {'停止' : 'OFF', '经济' : 'ECO', '解冻' : 'HGEL', '舒适' : 'CONFORT'} # Modes pour Pilote Gen 1
        }
        request_headers = {'Accept': 'application/json', 'X-Gizwits-Application-Id': HeatzyHandler.APPID}
        statusRequest = requests.get(HeatzyHandler.API_BASE_URL+'/devdata/'+self.did+'/latest', headers=request_headers)

        mode = statusRequest.json()['attr']['mode']

        # TODO : Check for errors here

        self.mode = modes_decode[self.version][mode]
        return self.mode

    # Définit le mode à partir du texte
    def setMode(self, mode):
        # Matrice d'encodage des modes
        modes_encode = {
            # Matrice d'encodage des modes pour Heatzy Pilote (Gen 1)
            'Heatzy' : {'OFF':{'raw':(1,1,3)},'ECO':{'raw':(1,1,1)},'HGEL':{'raw':(1,1,2)},'CONFORT':{'raw':(1,1,0)}},
            # Matrice d'encodage des modes pour Heatzy Pilote Gen 2
            'Pilote2' : {
                'OFF':{'attrs': {'mode':'stop'}},
                'ECO':{'attrs': {'mode':'eco'}},
                'HGEL':{'attrs': {'mode':'fro'}},
                'CONFORT':{'attrs': {'mode':'cft'}}
                }}

        request_headers = {'Accept': 'application/json', 'X-Gizwits-Application-Id': HeatzyHandler.APPID,'X-Gizwits-User-token': self.handler.get_token()}
        request_payload = modes_encode[self.version][mode]
        requests.post(HeatzyHandler.API_BASE_URL+'/control/'+self.did, json=request_payload, headers=request_headers)
        # TODO : check for errors

    # Méthodes de définition de modes plus lisilbes
    def confort(self):
        self.setMode('CONFORT')

    def eco(self):
        self.setMode('ECO')

    def off(self):
        self.setMode('OFF')

    def horsgel(self):
        self.setMode('HGEL')

    def on(self):
        self.setMode('CONFORT')