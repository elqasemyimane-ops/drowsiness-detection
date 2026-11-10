import cv2
import numpy as np
# Remarque : Dlib n'est plus nécessaire car nous utilisons Mediapipe.
# import dlib 
import mediapipe as mp
from playsound import playsound
import time
from math import hypot

# -------------------------------
# Paramètres
# Seuils ajustés pour Mediapipe (plus permissifs que dlib)
EAR_THRESHOLD = 0.24 # seuil yeux fermés (typiquement 0.28-0.30 pour MP)
MAR_THRESHOLD = 0.7 # seuil bâillement (typiquement 0.80-0.85 pour MP)
ALERT_DELAY = 2 # secondes entre alertes répétées
ALERT_SOUND = "alert.wav"
# -------------------------------

# Méthodes pour calculer EAR et MAR
def euclidean_dist(p1, p2):
    # Calcule la distance euclidienne entre deux points (x, y)
    return np.linalg.norm(np.array(p1) - np.array(p2))

def compute_EAR(eye):
    # eye: liste de 6 points (x,y)
    # A et B sont les distances verticales, C est la distance horizontale
    A = euclidean_dist(eye[1], eye[5])
    B = euclidean_dist(eye[2], eye[4])
    C = euclidean_dist(eye[0], eye[3])
    
    # Évite la division par zéro
    if C == 0:
        return 0
        
    ear = (A + B) / (2.0 * C)
    return ear

def compute_MAR(mouth_points):
    # mouth_points: doit contenir les points [13, 14, 61, 291]
    # Indices spécifiques de Mediapipe (topologie du visage)
    
    # Distance Verticale (Centre Supérieur - Centre Inférieur)
    # 13: Centre lèvre supérieure, 14: Centre lèvre inférieure
    A = euclidean_dist(mouth_points[0], mouth_points[1])
    
    # Distance Horizontale (Coin Gauche - Coin Droit)
    # 61: Coin gauche, 291: Coin droit
    B = euclidean_dist(mouth_points[2], mouth_points[3])
    
    if B == 0:
        return 0
        
    mar = A / B
    return mar

# Initialisation Mediapipe
mp_face_mesh = mp.solutions.face_mesh
# Utilisation de min_detection_confidence pour une meilleure performance
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False, 
    max_num_faces=1, 
    min_detection_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# Ouvrir la webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Erreur : caméra non détectée")
    exit()

last_alert_time = 0

print("🚀 Système de détection de somnolence lancé...")
print("➡️ Fermez les yeux pour tester l’alerte")
print("➡️ Bâillez pour tester le MAR")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Erreur capture image")
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Optimisation : Mediapipe doit travailler sur l'image RGB
    results = face_mesh.process(rgb_frame)

    alert = False
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            
            ih, iw, _ = frame.shape
            # Extraction de tous les landmarks du visage
            landmarks = [(int(p.x*iw), int(p.y*ih)) for p in face_landmarks.landmark]

            # Indices Mediapipe standard pour les yeux (laissés intacts)
            left_eye_indices = [33, 160, 158, 133, 153, 144]
            right_eye_indices = [362, 385, 387, 263, 373, 380]
            
            # **IMPORTANT** : Indices de la bouche pour le MAR simplifié : 
            # 13 (centre lèvre sup), 14 (centre lèvre inf), 61 (coin gauche), 291 (coin droit)
            mouth_indices = [13, 14, 61, 291] 
            
            # Récupération des points
            left_eye = [landmarks[i] for i in left_eye_indices]
            right_eye = [landmarks[i] for i in right_eye_indices]
            # Création de la liste dans l'ordre attendu par compute_MAR : [13, 14, 61, 291]
            mouth_points = [landmarks[i] for i in mouth_indices]

            ear = (compute_EAR(left_eye) + compute_EAR(right_eye)) / 2.0
            mar = compute_MAR(mouth_points) 

            # Détection somnolence
            if ear < EAR_THRESHOLD or mar > MAR_THRESHOLD:
                alert = True
                
                # Gestion de l'alerte sonore temporisée
                current_time = time.time()
                if current_time - last_alert_time > ALERT_DELAY:
                    print(f"⚠️ Somnolence détectée ! EAR: {ear:.2f}, MAR: {mar:.2f}")
                    # Assurez-vous que 'alert.wav' est dans le même dossier
                    playsound(ALERT_SOUND) 
                    last_alert_time = current_time
                
                # Afficher l'alerte à l'écran
                cv2.putText(frame, "!!! ALERTE SOMNOLENCE !!!", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Afficher les valeurs pour le débogage
            cv2.putText(frame, f"EAR: {ear:.2f}", (450, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"MAR: {mar:.2f}", (450, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Dessiner les landmarks (pour visualisation)
            mp_drawing.draw_landmarks(frame, face_landmarks, mp_face_mesh.FACEMESH_TESSELATION)

    cv2.imshow("Détection Somnolence", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()