import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import json
import time
import threading
import paho.mqtt.client as mqtt
from telepot.namedtuple import ReplyKeyboardMarkup


# CONFIG
import json

# === Load config from catalog ===
with open("catalog.json") as f:
    config = json.load(f)["botConfig"]

TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = config["TELEGRAM_CHAT_ID"]
CATALOG_URL = config["CATALOG_URL"]
VALVE_API_URL = config["VALVE_API_URL"]
THINGSPEAK_READ_URL = config["THINGSPEAK_READ_URL"]
MQTT_BROKER = config["MQTT_BROKER"]
MQTT_PORT = config["MQTT_PORT"]
MQTT_ALERT_TOPIC = config["MQTT_ALERT_TOPIC"]

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        ['/start', '/device'],
        ['/admin']
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)


bot = telepot.Bot(TELEGRAM_BOT_TOKEN)
user_state = {}
admin_sessions = {}

def log_command(chat_id, text):
    print(f"[BOT COMMAND] From {chat_id}: {text}")

def send_start_menu(chat_id, message="Choose an option:"):
    user_state[chat_id] = {}

    # Inline keyboard (for button navigation)
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔍 SEE_DEVICES', callback_data='see_devices')],
        [InlineKeyboardButton(text='🔐 ADMIN', callback_data='admin_login')]
    ])

    # First message with inline buttons
    bot.sendMessage(chat_id, message, reply_markup=inline_keyboard)

    # Second message with custom keyboard
    bot.sendMessage(chat_id, "Main Menu:", reply_markup=main_keyboard)

    

def return_button():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="↩ Restart", callback_data="restart")]])

def on_chat(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    text = msg.get("text", "").strip()
    log_command(chat_id, text)

    state = user_state.get(chat_id, {})

    if text.lower() == "/start" or text == "↩ Restart":
        send_start_menu(chat_id)

    elif state.get("awaiting_device_id"):
        user_state[chat_id]["awaiting_device_id"] = False
        show_device_status(chat_id, text)

    elif state.get("awaiting_admin_user"):
        user_state[chat_id]["admin_user"] = text
        user_state[chat_id]["awaiting_admin_user"] = False
        user_state[chat_id]["awaiting_admin_pass"] = True
        sent = bot.sendMessage(chat_id, "Enter admin password:")
        user_state[chat_id]["delete_last"] = sent["message_id"]

    elif state.get("awaiting_admin_pass"):
        username = user_state[chat_id].get("admin_user")
        password = text
        user_state[chat_id]["awaiting_admin_pass"] = False

        # Delete the user’s password message
        try:
            bot.deleteMessage((chat_id, msg['message_id']))
        except:
            print("[Bot] Couldn't delete password message.")

        try:
            res = requests.post(f"{CATALOG_URL}/admin-login", json={"username": username, "password": password})
            if res.json().get("success"):
                admin_sessions[chat_id] = True
                user_state[chat_id] = {}
                show_admin_menu(chat_id)
            else:
                bot.sendMessage(chat_id, "❌ Incorrect credentials. Try again.")
                send_start_menu(chat_id)
        except:
            bot.sendMessage(chat_id, "❌ Error contacting server.")
            send_start_menu(chat_id)
            
    elif state.get("awaiting_house_details"):
        user_state[chat_id]["awaiting_house_details"] = False
        try:
            lines = text.splitlines()
            if len(lines) != 20:
                bot.sendMessage(chat_id, "❌ Please enter exactly 20 lines: houseID, Address, Number, CAP")
                return
            house_id, address, number, cap = lines
            new_house = {
                "houseID": house_id.strip(),
                "location": {
                    "Address": address.strip(),
                    "Number": number.strip(),
                    "CAP": cap.strip()
                },
                "devices": []
            }
            requests.post(f"{CATALOG_URL}/building", json=new_house)
            bot.sendMessage(chat_id, f"✅ New house '{house_id}' added.", reply_markup=return_button())
        except Exception as e:
            bot.sendMessage(chat_id, f"❌ Failed to add house: {e}", reply_markup=return_button())

    elif text.lower() == "/device":
        user_state[chat_id] = {"awaiting_device_id": True}
        bot.sendMessage(chat_id, "Please enter the device ID:", reply_markup=return_button())
    
    elif state.get("awaiting_new_sensor"):
        house_id = user_state[chat_id]["house_id"]
        user_state[chat_id] = {}

        try:
            text = msg["text"].strip()
            
            # Try parsing JSON first
            try:
                sensor_data = json.loads(text)
            except json.JSONDecodeError:
                # If not JSON, try 3-line format: deviceID, deviceName, measureType
                lines = text.splitlines()
                if len(lines) != 3:
                    raise ValueError("Please enter 3 lines: deviceID, deviceName, measureType")
                
                sensor_data = {
                    "deviceID": int(lines[0].strip()),
                    "deviceName": lines[1].strip(),
                    "measureType": [lines[2].strip()],
                    "deviceStatus": "On",
                    "min_threshold": 10,
                    "max_threshold": 80,
                    "services": {
                        "MQTT": {
                            "topic": f"gasDetector/sensor/gas/{lines[0].strip()}"
                        }
                    }
                }

            res = requests.post(f"{CATALOG_URL}/device/{house_id}", json=sensor_data)
            if res.status_code == 200:
                bot.sendMessage(chat_id, "✅ Sensor added successfully!", reply_markup=return_button())
            else:
                bot.sendMessage(chat_id, f"⚠ Failed to add sensor: {res.json()}", reply_markup=return_button())

        except Exception as e:
            bot.sendMessage(chat_id, f"❌ Error parsing or sending sensor data:\n{e}", reply_markup=return_button())

    
    elif state.get("awaiting_update_sensor"):
        try:
            house_id = user_state[chat_id]["house_id"]
            sensor_data = json.loads(msg["text"])
            res = requests.put(f"{CATALOG_URL}/device/{house_id}", json=sensor_data)
            if res.status_code == 200:
                bot.sendMessage(chat_id, "✅ Sensor updated.", reply_markup=return_button())
            else:
                bot.sendMessage(chat_id, f"⚠ Failed to update: {res.json()}", reply_markup=return_button())
        except Exception as e:
            bot.sendMessage(chat_id, f"❌ Error updating sensor: {e}", reply_markup=return_button())
        user_state[chat_id] = {}



def show_device_status(chat_id, device_id):
    try:
        r = requests.get(f"{CATALOG_URL}/buildings")
        for b in r.json():
            for d in b["devices"]:
                if str(d["deviceID"]) == device_id:
                    msg = f"📟 Device: {d['deviceName']}\\nStatus: {d['deviceStatus']}"
                    if "Gas" in d.get("measureType", []):
                        level = requests.get(THINGSPEAK_READ_URL).json().get("field1", "N/A")
                        msg += f"\\n🌫️ Gas Level: {level} ppm"
                    bot.sendMessage(chat_id, msg, reply_markup=return_button())
                    return
        bot.sendMessage(chat_id, "⚠️ Device not found.", reply_markup=return_button())
    except Exception as e:
        bot.sendMessage(chat_id, f"❌ Error: {e}", reply_markup=return_button())

def show_admin_menu(chat_id):
    try:
        buildings = requests.get(f"{CATALOG_URL}/buildings").json()
        inline_buttons = [[InlineKeyboardButton(text=b["houseID"], callback_data=f"select_house:{b['houseID']}")] for b in buildings]
        inline_buttons.append([InlineKeyboardButton(text="➕ ADD_NEW_HOUSE", callback_data="add_house")])
        inline_buttons.append([InlineKeyboardButton(text="↩ Restart", callback_data="restart")])
        bot.sendMessage(chat_id, "🏠 Select a house to manage:", reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_buttons))
    except Exception as e:
        bot.sendMessage(chat_id, f"❌ Error loading houses: {e}", reply_markup=return_button())

def show_house_admin_options(chat_id, house_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Show Sensors', callback_data=f"show_sensors:{house_id}")],
        [InlineKeyboardButton(text='🌫 Get Gas Level', callback_data=f"gas_level:{house_id}")],
        [InlineKeyboardButton(text='🆕 Add Sensor', callback_data=f"add_sensor:{house_id}")],
        [InlineKeyboardButton(text='🔄 Update Sensor', callback_data=f"update_sensor:{house_id}")],
        [InlineKeyboardButton(text='❌ Remove Sensor', callback_data=f"remove_sensor:{house_id}")],
        [InlineKeyboardButton(text="↩ Restart", callback_data="restart")]
    ])
    bot.sendMessage(chat_id, f"🏠 Managing {house_id}:", reply_markup=keyboard)

def on_callback(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    chat_id = msg['message']['chat']['id']
    log_command(chat_id, f"[Button] {query_data}")

    if query_data == "restart":
        send_start_menu(chat_id)

    elif query_data == "see_devices":
        user_state[chat_id] = {"awaiting_device_id": True}
        bot.sendMessage(chat_id, "Please enter the device ID:", reply_markup=return_button())

    elif query_data == "admin_login":
        user_state[chat_id] = {"awaiting_admin_user": True}
        bot.sendMessage(chat_id, "Enter admin username:", reply_markup=return_button())

    elif query_data.startswith("select_house:"):
        house_id = query_data.split(":")[1]
        user_state[chat_id] = {"house_id": house_id}
        bot.sendMessage(chat_id, f"✅ You selected: {house_id}", reply_markup=return_button())
        show_house_admin_options(chat_id, house_id)

    elif query_data == "add_house":
        user_state[chat_id] = {"awaiting_house_details": True}
        bot.sendMessage(chat_id, "🆕 Enter houseID, Address, Number, CAP (one per line):", reply_markup=return_button())
    
    elif query_data.startswith("show_sensors:"):
        house_id = query_data.split(":")[1]
        try:
            r = requests.get(f"{CATALOG_URL}/building/{house_id}")
            devices = r.json().get("devices", [])
            if not devices:
                bot.sendMessage(chat_id, f"📭 No devices found in {house_id}.", reply_markup=return_button())
                return
            msg = f"📋 Devices in {house_id}:\n"
            for d in devices:
                msg += f"- {d['deviceName']} (ID: {d['deviceID']}, Type: {', '.join(d.get('measureType', []))})\n"
            bot.sendMessage(chat_id, msg, reply_markup=return_button())
        except Exception as e:
            bot.sendMessage(chat_id, f"❌ Error fetching sensors: {e}", reply_markup=return_button())


    elif query_data.startswith("gas_level:"):
        house_id = query_data.split(":")[1]
        try:
            r = requests.get(f"{CATALOG_URL}/buildings")
            for b in r.json():
                if b["houseID"] == house_id:
                    for d in b["devices"]:
                        if "Gas" in d.get("measureType", []):
                            level = requests.get(THINGSPEAK_READ_URL).json().get("field1", "N/A")
                            bot.sendMessage(chat_id, f"🌫 Gas Level for {d['deviceName']} (ID {d['deviceID']}): {level} ppm", reply_markup=return_button())
                            return
            bot.sendMessage(chat_id, "⚠ No gas sensors found.", reply_markup=return_button())
        except Exception as e:
            bot.sendMessage(chat_id, f"❌ Error getting gas level: {e}", reply_markup=return_button())

    elif query_data.startswith("add_sensor:"):
        house_id = query_data.split(":")[1]
        user_state[chat_id] = {
            "awaiting_new_sensor": True,
            "house_id": house_id
        }
        bot.sendMessage(chat_id, "🆕 Send new sensor as JSON (e.g. deviceID, deviceName, measureType, etc.):", reply_markup=return_button())

    elif query_data.startswith("remove_sensor:"):
        house_id = query_data.split(":")[1]
        bot.sendMessage(chat_id, f"❌ Enter sensor ID to remove from {house_id}", reply_markup=return_button())
    
    elif query_data.startswith("update_sensor:"):
        house_id = query_data.split(":")[1]
        user_state[chat_id] = {
            "awaiting_update_sensor": True,
            "house_id": house_id
        }
        bot.sendMessage(chat_id, "🔁 Send updated sensor JSON (must include deviceID):", reply_markup=return_button())
    
    elif query_data == "restart":
        user_state[chat_id] = {}
        send_start_menu(chat_id, "🔄 Restarted.")

def on_mqtt_message(client, userdata, msg):
    alert = msg.payload.decode()
    print("🚨 GAS ALERT:", alert)
    # bot.sendMessage(TELEGRAM_CHAT_ID, f"🚨 GAS ALERT: {alert}")

def mqtt_listen():
    client = mqtt.Client(clean_session=True)
    client.on_message = on_mqtt_message
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.subscribe(MQTT_ALERT_TOPIC)
    client.loop_forever()

MessageLoop(bot, {'chat': on_chat, 'callback_query': on_callback}).run_as_thread()
print("🤖 Telegram bot with admin, restart, alerts, and SEE_DEVICES running...")
threading.Thread(target=mqtt_listen).start()

while True:
    time.sleep(10)