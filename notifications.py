import pywhatkit as kit
import mysql.connector
from datetime import datetime, timedelta
import schedule
import time
import threading

# ===============================
# CONFIGURATION
# ===============================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'imane@1234',
    'database': 'securite_route'
}

#  Mettez votre numéro WhatsApp avec indicatif pays
VOTRE_NUMERO = "+212669686281"  # ← changez ici ex: +212612345678

# ===============================
# FONCTIONS
# ===============================

def get_jour_max_semaine():
    """Récupère le jour avec le plus d'alertes cette semaine"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT jour_semaine, COUNT(*) as total
            FROM alertes
            WHERE YEARWEEK(date_heure, 1) = YEARWEEK(NOW(), 1)
            GROUP BY jour_semaine
            ORDER BY total DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]  # ex: "Lundi"
        return None
    except Exception as e:
        print(f" Erreur DB: {e}")
        return None


def get_jour_demain():
    """Retourne le nom du jour de demain en français"""
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    demain = (datetime.now().weekday() + 1) % 7
    return jours[demain]


def get_jour_aujourd_hui():
    """Retourne le nom du jour d'aujourd'hui en français"""
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    return jours[datetime.now().weekday()]


def envoyer_whatsapp(message, heure, minute):
    """Envoie un message WhatsApp via pywhatkit"""
    try:
        print(f" Envoi WhatsApp prévu à {heure}h{minute:02d}...")
        kit.sendwhatmsg(VOTRE_NUMERO, message, heure, minute + 2, wait_time=15, tab_close=True) 
        print(f" Message envoyé : {message}")
    except Exception as e:
        print(f" Erreur envoi WhatsApp: {e}")


def verifier_et_notifier_veille():
    """Vérifie si demain est le jour max → envoie message la veille à 21h"""
    print("🔍 Vérification du soir...")
    
    jour_max = get_jour_max_semaine()
    jour_demain = get_jour_demain()
    
    if jour_max and jour_demain == jour_max:
        message = (
            f" Attention ! Demain ({jour_demain}) est ton jour "
            f"le plus somnolent de la semaine. "
            f" Dors bien ce soir pour être en forme !"
        )
        # Envoyer maintenant (heure actuelle + 1 minute)
        now = datetime.now()
        envoyer_whatsapp(message, now.hour, now.minute + 2)
    else:
        print(f"ℹ Demain ({jour_demain}) n'est pas le jour max ({jour_max})")


def verifier_et_notifier_matin():
    """Le matin du jour max → envoie message à 8h00"""
    print("🔍 Vérification du matin...")
    
    jour_max = get_jour_max_semaine()
    jour_aujourd_hui = get_jour_aujourd_hui()
    
    if jour_max and jour_aujourd_hui == jour_max:
        message = (
            f" Bonjour ! Aujourd'hui ({jour_aujourd_hui}) tu es "
            f"généralement plus somnolent. "
            f"Bois un café et sois prudent sur la route ! 🚗"
        )
        envoyer_whatsapp(message, 8, 1)
    else:
        print(f"ℹ Aujourd'hui ({jour_aujourd_hui}) n'est pas le jour max ({jour_max})")


# ===============================
# PLANIFICATION
# ===============================

def demarrer_planificateur():
    """Lance le planificateur en arrière-plan"""
    
    # Message veille → chaque soir à 21h00
    schedule.every().day.at("21:00").do(verifier_et_notifier_veille)
    
    # Message matin → chaque matin à 08:00
    schedule.every().day.at("08:00").do(verifier_et_notifier_matin)
    
    print("Planificateur démarré !")
    print("    Vérification veille : chaque soir à 21h00")
    print("     Vérification matin  : chaque matin à 08h00")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # vérifie chaque minute


def demarrer_en_background():
    """Lance le planificateur dans un thread séparé"""
    thread = threading.Thread(target=demarrer_planificateur, daemon=True)
    thread.start()
    print(" Notifications WhatsApp actives en arrière-plan !")


# ===============================
# TEST MANUEL
# ===============================

def tester_maintenant():
    """Pour tester sans attendre 21h ou 8h"""
    print("\n" + "="*50)
    print(" TEST MANUEL")
    print("="*50)
    
    jour_max = get_jour_max_semaine()
    print(f" Jour max cette semaine : {jour_max}")
    print(f" Aujourd'hui : {get_jour_aujourd_hui()}")
    print(f" Demain : {get_jour_demain()}")
    
    if jour_max:
        # Test message veille
        msg_veille = (
            f" Attention ! Demain ({get_jour_demain()}) est ton jour "
            f"le plus somnolent.  Dors bien ce soir !"
        )
        print(f"\n📱 Message veille :\n{msg_veille}")
        
        # Test message matin
        msg_matin = (
            f" Bonjour ! Aujourd'hui tu es généralement plus somnolent. "
            f"Bois un café et sois prudent ! 🚗"
        )
        print(f"\n📱 Message matin :\n{msg_matin}")
        
        # Envoyer le message test maintenant
        now = datetime.now()
        print(f"\n Envoi du message test dans 1 minute...")
        envoyer_whatsapp(msg_veille, now.hour, now.minute + 1)
    else:
        print(" Pas assez de données cette semaine")
    
    print("="*50 + "\n")


# ===============================
# MAIN
# ===============================

if __name__ == "__main__":
    print("="*50)
    print("📱 SYSTÈME DE NOTIFICATIONS WHATSAPP")
    print("="*50)
    print("1  Démarrer en arrière-plan (automatique)")
    print("2  Tester maintenant")
    print("="*50)
    
    choix = input("Votre choix (1 ou 2) : ")
    
    if choix == "1":
        demarrer_en_background()
        # Garder le programme actif
        while True:
            time.sleep(1)
    elif choix == "2":
        tester_maintenant()