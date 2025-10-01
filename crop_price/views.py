#for gemini connectivity , llm configuration & model details
import google.generativeai as genai

#returning data for front-end
from django.shortcuts import render
from django.http import JsonResponse

#for web scraping
from .utils import fetch_agri_data
from .models import crop_price # for storing it in db

#for ml model ( pest/disease detection )
import os # for path
from ultralytics import YOLO
from django.core.files.storage import default_storage # for storing the image
from django.core.files.base import ContentFile # for reading the image
from django.conf import settings

#for translation and chatbot
from deep_translator import GoogleTranslator
from langdetect import detect


# from django.utils import timezone
# from datetime import datetime, timedelta
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import Select
# from selenium.webdriver.support.ui import WebDriverWait
# import time

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from PIL import Image
# import speech_recognition as sr
# from gtts import gTTS
# from googletrans import Translator
# from django.views.decorators.csrf import csrf_exempt
# import tempfile

# --- API Keys ---
# I have used Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyARai_a6FZvR-rbZ6SZgdk3DUYBPKoUnEE")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


#model configuration
generation_config = genai.GenerationConfig(
    temperature=0.3,
    top_p=0.9,
    top_k=40,
    max_output_tokens=300,
)

#model details
gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)


# system prompt is to help chatbot understand , what kind of questions user can ask
SYSTEM_PROMPT = (
    "You are Crop Crystalline, a helpful agriculture assistant. "
    "Respond in 2-4 concise sentences with practical, actionable advice. "
    "If the question is broad, give a short bullet list of options. "
    "Avoid introductions/disclaimers. If key info is missing (crop, location, problem), ask all targeted follow-up"
)


def pest(request):
    if request.method == "POST" and request.FILES.get("image"):

        MODEL_PATH = os.path.join(settings.BASE_DIR, "best.pt")
        model = YOLO(MODEL_PATH)

        # 1. Save uploaded file
        uploaded_file = request.FILES["image"]
        temp_path = default_storage.save(
            "uploads/" + uploaded_file.name,
            ContentFile(uploaded_file.read())
        )
        input_path = os.path.join(settings.MEDIA_ROOT, temp_path)

        # 2. Run YOLOv8 inference
        results = model.predict(
            source=input_path,
            save=True,  # save annotated image(s)
            project=os.path.join(settings.MEDIA_ROOT, "results"),
            name="exp",   # folder name under project
            exist_ok=True # reuse "exp" instead of exp2, exp3...
        )

        # 3. YOLOv8 saves image in: media/results/exp/<filename>
        output_filename = os.path.basename(input_path)
        output_url = settings.MEDIA_URL + f"results/exp/{output_filename}"

        return render(request, "pest_disease_detection.html", {"output_url": output_url})    
    return render(request,'pest_disease_detection.html')

    
def marketPrice(req):

    commodity = req.GET.get("commodity", "")
    state = req.GET.get("state", "")

    if( commodity and state ):

        data = crop_price.objects.filter(commodity=commodity,state=state).order_by('-date').values()
        return render(req,'market_price.html',{"data":data})

    return render(req,'market_price.html')


def ask(request):
    user_message = request.GET.get("message")
    if not user_message:
        return JsonResponse({"error": "No message provided"}, status=400)


    try:
        msg = (user_message or "").strip()

        LANG_MAP = {
        "ta": "ta", "hi": "hi", "en": "en", "te": "te", "ml": "ml", "kn": "kn", "ur": "ur"
        }

        detected = detect(msg)
        user_lang = LANG_MAP.get(detected, "en")

        # Translate to English if needed
        if user_lang != "en":
            msg_en = GoogleTranslator(source=user_lang, target="en").translate(msg)
        else:
            msg_en = msg

        # Bot logic
        short = msg_en.lower()
        if short in {"hi", "hai", "hello", "hey"}:
            bot_reply_en = "Hello! What crop and location? (e.g., paddy in Thanjavur)"
        elif len(msg_en.split()) <= 3 and "crop" in short:
            bot_reply_en = (
                "Do you want common crop categories (cereals, pulses, oilseeds, vegetables, fruits), "
                "or recommendations for your climate? Share location and season."
            )
        else:
            resp = gemini_model.generate_content([SYSTEM_PROMPT, msg_en])
            bot_reply_en = resp.text or ""

        # Translate back to user language
        if user_lang != "en":
            bot_reply = GoogleTranslator(source="en", target=user_lang).translate(bot_reply_en)
        else:
            bot_reply = bot_reply_en

        return JsonResponse({"reply": bot_reply})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=200)


def weather(req):
    return render(req,'weather.html')

def chatbot(req):
    return render(req,'chatbot.html')

def voiceChat(req):
    return render(req,'voice_chat.html')

def dashboard(req):
    return render(req,'dashboard.html')


'''def home_page(request):
    return JsonResponse({
        "Page": "Home Page - navigate to /scraper/request",
        "Time Stamp": timezone.now().timestamp()
    })'''

    
'''def data(req):
    data = list(crop_price.objects.filter(commodity='Rice').values())
    return JsonResponse({"data":data},status=200,safe=False)'''


'''def request_page(request):

    commodity = request.GET.get("commodity")
    state = request.GET.get("state")


    if not commodity or not state:
        return JsonResponse({"error": "Missing query parameters"}, status=400)

    try:
        data = fetch_agri_data(state, commodity)
        print(" data fetched and going to return")
        #return JsonResponse(data, safe=False, json_dumps_params={"indent": 5})
        return render(request,'data.html',{"data":data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)'''

# Create your views here.
'''def home(req):

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    count=41485

    commodities = ['Bamboo','Banana flower','Beetroot','Cabbage'] # list of commodities
    #state=['Andaman and Nicobar','Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chandigarh','Chattisgarh','Dadra and Nagar Haveli','Daman and Diu','Goa','Gujarat','Haryana','Himachal Pradesh','Jammu and Kashmir','Jharkhand','Karnataka','Kerala','Lakshadweep','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram','Nagaland','NCT of Delhi','Odisha','Pondicherry','Punjab','Rajasthan','Sikkim','Tamil Nadu','Telangana','Tripura','Uttar Pradesh','Uttrakhand','West Bengal']
    market_to_state={
        "Nicobar": "Andaman and Nicobar",
        "North and Middle Andaman": "Andaman and Nicobar",
        "South Andaman": "Andaman and Nicobar",
        "Anantapur": "Andhra Pradesh",
        "Chittor": "Andhra Pradesh",
        "Cuddapah": "Andhra Pradesh",
        "East Godavari": "Andhra Pradesh",
        "Guntur": "Andhra Pradesh",
        "Krishna": "Andhra Pradesh",
        "Kurnool": "Andhra Pradesh",
        "Nellore": "Andhra Pradesh",
        "Prakasam": "Andhra Pradesh",
        "Srikakulam": "Andhra Pradesh",
        "Vijayanagaram": "Andhra Pradesh",
        "Visakhapatnam": "Andhra Pradesh",
        "West Godavari": "Andhra Pradesh",
        "Changlang": "Arunachal Pradesh",
        "East Kameng": "Arunachal Pradesh",
        "East Siang": "Arunachal Pradesh",
        "Kurung Kummey": "Arunachal Pradesh",
        "Lohit": "Arunachal Pradesh",
        "Lower Dibang Valley": "Arunachal Pradesh",
        "Lower Subansiri": "Arunachal Pradesh",
        "Papum Pore": "Arunachal Pradesh",
        "Tawang": "Arunachal Pradesh",
        "Tirap": "Arunachal Pradesh",
        "Upper Siang": "Arunachal Pradesh",
        "Upper Subansiri": "Arunachal Pradesh",
        "West Kameng": "Arunachal Pradesh",
        "West Siang": "Arunachal Pradesh",
        "Barpeta": "Assam",
        "BONGAIGAON": "Assam",
        "Cachar": "Assam",
        "Darrang": "Assam",
        "Dhemaji": "Assam",
        "Dhubri": "Assam",
        "Dibrugarh": "Assam",
        "Goalpara": "Assam",
        "Golaghat": "Assam",
        "Hailakandi": "Assam",
        "Jorhat": "Assam",
        "Kamrup": "Assam",
        "Karbi Anglong": "Assam",
        "Karimganj": "Assam",
        "Kokrajhar": "Assam",
        "Lakhimpur": "Uttar Pradesh",
        "Mangaldoi": "Assam",
        "MORIGAON": "Assam",
        "Nagaon": "Assam",
        "Nalbari": "Assam",
        "North Cachar Hills": "Assam",
        "Sibsagar": "Assam",
        "Sonitpur": "Assam",
        "Tinsukia": "Assam",
        "Araria": "Bihar",
        "Arwal": "Bihar",
        "Aurangabad": "Bihar",
        "Banka": "Bihar",
        "Begusarai": "Bihar",
        "Bhagalpur": "Bihar",
        "Bhojpur": "Bihar",
        "Buxar": "Bihar",
        "Chhapra": "Bihar",
        "Darbhanga": "Bihar",
        "East Champaran/ Motihari": "Bihar",
        "Gaya": "Bihar",
        "Gopalgang": "Bihar",
        "Jamui": "Bihar",
        "Jehanabad": "Bihar",
        "Kaimur/Bhabhua": "Bihar",
        "Kaithar": "Bihar",
        "Khagaria": "Bihar",
        "Kishanganj": "Bihar",
        "Luckeesarai": "Bihar",
        "Madhepura": "Bihar",
        "Madhubani": "Bihar",
        "Munghair": "Bihar",
        "Muzaffarpur": "Bihar",
        "Nalanda": "Bihar",
        "Nawada": "Bihar",
        "Patna": "Bihar",
        "Purnea": "Bihar",
        "Rohtas": "Bihar",
        "Saharsa": "Bihar",
        "Samastipur": "Bihar",
        "Saran": "Bihar",
        "Sheikhpura": "Bihar",
        "Sheohar": "Bihar",
        "Sitamarhi": "Bihar",
        "Siwan": "Bihar",
        "Supaul": "Bihar",
        "Vaishali": "Bihar",
        "West Chambaran": "Bihar",
        "Chandigarh": "Chandigarh",
        "Balod": "Chattisgarh",
        "Balodabazar": "Chattisgarh",
        "Balrampur": "Uttar Pradesh",
        "Bastar": "Chattisgarh",
        "Bemetara": "Chattisgarh",
        "Bijapur": "Karnataka",
        "Bilaspur": "Himachal Pradesh",
        "Dantewada": "Chattisgarh",
        "Dhamtari": "Chattisgarh",
        "Durg": "Chattisgarh",
        "Gariyaband": "Chattisgarh",
        "Jagdalpur": "Chattisgarh",
        "Janjgir": "Chattisgarh",
        "Jashpur": "Chattisgarh",
        "Kabirdham": "Chattisgarh",
        "Kanker": "Chattisgarh",
        "Kawardha": "Chattisgarh",
        "Kondagaon": "Chattisgarh",
        "Korba": "Chattisgarh",
        "Koria": "Chattisgarh",
        "Mahasamund": "Chattisgarh",
        "Mungeli": "Chattisgarh",
        "Narayanpur": "Chattisgarh",
        "North Bastar": "Chattisgarh",
        "Raigarh": "Chattisgarh",
        "Raipur": "Chattisgarh",
        "Rajnandgaon": "Chattisgarh",
        "Sukma": "Chattisgarh",
        "Surajpur": "Chattisgarh",
        "Surguja": "Chattisgarh",
        "Dadra & Nagar Haveli": "Dadra and Nagar Haveli",
        "Silvassa": "Dadra and Nagar Haveli",
        "Daman": "Daman and Diu",
        "Diu": "Daman and Diu",
        "North Goa": "Goa",
        "South Goa": "Goa",
        "Ahmedabad": "Gujarat",
        "Amreli": "Gujarat",
        "Anand": "Gujarat",
        "Aravalli": "Gujarat",
        "Banaskanth": "Gujarat",
        "Bharuch": "Gujarat",
        "Bhavnagar": "Gujarat",
        "Botad": "Gujarat",
        "Chhota Udaipur": "Gujarat",
        "Dahod": "Gujarat",
        "Dang": "Gujarat",
        "Devbhumi Dwarka": "Gujarat",
        "Gandhinagar": "Gujarat",
        "Gir Somnath": "Gujarat",
        "Jamnagar": "Gujarat",
        "Junagarh": "Gujarat",
        "Kachchh": "Gujarat",
        "Kheda": "Gujarat",
        "Mahisagar": "Gujarat",
        "Mehsana": "Gujarat",
        "Morbi": "Gujarat",
        "Narmada": "Gujarat",
        "Navsari": "Gujarat",
        "Panchmahals": "Gujarat",
        "Patan": "Gujarat",
        "Porbandar": "Gujarat",
        "Rajkot": "Gujarat",
        "Sabarkantha": "Gujarat",
        "Surat": "Gujarat",
        "Surendranagar": "Gujarat",
        "Tapi": "Gujarat",
        "The Dangs": "Gujarat",
        "Vadodara(Baroda)": "Gujarat",
        "Valsad": "Gujarat",
        "Ambala": "Haryana",
        "Bhiwani": "Haryana",
        "Faridabad": "Haryana",
        "Fatehabad": "Haryana",
        "Gurgaon": "Haryana",
        "Hissar": "Haryana",
        "Jhajar": "Haryana",
        "Jind": "Haryana",
        "Kaithal": "Haryana",
        "Karnal": "Haryana",
        "Kurukshetra": "Haryana",
        "Mahendragarh-Narnaul": "Haryana",
        "Mewat": "Haryana",
        "Palwal": "Haryana",
        "Panchkula": "Haryana",
        "Panipat": "Haryana",
        "Rewari": "Haryana",
        "Rohtak": "Haryana",
        "Sirsa": "Haryana",
        "Sonipat": "Haryana",
        "Yamuna Nagar": "Haryana",
        "Chamba": "Himachal Pradesh",
        "Hamirpur": "Uttar Pradesh",
        "Kangra": "Himachal Pradesh",
        "Kangra (at Dharmashala)": "Himachal Pradesh",
        "Kinnaur (at Kalpa)": "Himachal Pradesh",
        "Kullu": "Himachal Pradesh",
        "Lahul & Spiti": "Himachal Pradesh",
        "Mandi": "Himachal Pradesh",
        "Shimla": "Himachal Pradesh",
        "Sirmore": "Himachal Pradesh",
        "Solan": "Himachal Pradesh",
        "Una": "Himachal Pradesh",
        "Anantnag": "Jammu and Kashmir",
        "Badgam": "Jammu and Kashmir",
        "Bandipora": "Jammu and Kashmir",
        "Baramulla": "Jammu and Kashmir",
        "Doda": "Jammu and Kashmir",
        "Ganderbal": "Jammu and Kashmir",
        "Jammu": "Jammu and Kashmir",
        "Kargil": "Jammu and Kashmir",
        "Kathua": "Jammu and Kashmir",
        "Kishtwar": "Jammu and Kashmir",
        "Kulgam": "Jammu and Kashmir",
        "Kupwara": "Jammu and Kashmir",
        "Leh": "Jammu and Kashmir",
        "Poonch": "Jammu and Kashmir",
        "Pulwama": "Jammu and Kashmir",
        "Rajouri": "Jammu and Kashmir",
        "Ramban": "Jammu and Kashmir",
        "Samba": "Jammu and Kashmir",
        "Shopian": "Jammu and Kashmir",
        "Srinagar": "Jammu and Kashmir",
        "Udhampur": "Jammu and Kashmir",
        "Bokaro": "Jharkhand",
        "Chatra": "Jharkhand",
        "Deogarh": "Odisha",
        "Dhanbad": "Jharkhand",
        "Dumka": "Jharkhand",
        "East Singhbhum": "Jharkhand",
        "Garhwa": "Jharkhand",
        "Giridih": "Jharkhand",
        "Godda": "Jharkhand",
        "Gumla": "Jharkhand",
        "Hazaribagh": "Jharkhand",
        "Jamtara": "Jharkhand",
        "Koderma": "Jharkhand",
        "Latehar": "Jharkhand",
        "Lohardaga": "Jharkhand",
        "Pakur": "Jharkhand",
        "Palamu": "Jharkhand",
        "Ranchi": "Jharkhand",
        "Sahebgang": "Jharkhand",
        "Saraikela(Kharsanwa)": "Jharkhand",
        "Simdega": "Jharkhand",
        "West Singbhum": "Jharkhand",
        "Bagalkot": "Karnataka",
        "Bangalore": "Karnataka",
        "Belgaum": "Karnataka",
        "Bellary": "Karnataka",
        "Bidar": "Karnataka",
        "Chamrajnagar": "Karnataka",
        "Chikmagalur": "Karnataka",
        "Chitradurga": "Karnataka",
        "Davangere": "Karnataka",
        "Dharwad": "Karnataka",
        "Gadag": "Karnataka",
        "Hassan": "Karnataka",
        "Haveri": "Karnataka",
        "Kalburgi": "Karnataka",
        "Karwar(Uttar Kannad)": "Karnataka",
        "Kolar": "Karnataka",
        "Koppal": "Karnataka",
        "Madikeri(Kodagu)": "Karnataka",
        "Mandya": "Karnataka",
        "Mangalore(Dakshin Kannad)": "Karnataka",
        "Mysore": "Karnataka",
        "Raichur": "Karnataka",
        "Ramanagar": "Karnataka",
        "Shimoga": "Karnataka",
        "Tumkur": "Karnataka",
        "Udupi": "Karnataka",
        "Yadgiri": "Karnataka",
        "Alappuzha": "Kerala",
        "Alleppey": "Kerala",
        "Calicut": "Kerala",
        "Ernakulam": "Kerala",
        "Idukki": "Kerala",
        "Kannur": "Kerala",
        "Kasargod": "Kerala",
        "Kollam": "Kerala",
        "Kottayam": "Kerala",
        "Kozhikode(Calicut)": "Kerala",
        "Malappuram": "Kerala",
        "Palakad": "Kerala",
        "Pathanamthitta": "Kerala",
        "Thirssur": "Kerala",
        "Thiruvananthapuram": "Kerala",
        "Wayanad": "Kerala",
        "Kavaratti": "Lakshadweep",
        "Agar Malwa": "Madhya Pradesh",
        "Alirajpur": "Madhya Pradesh",
        "Anupur": "Madhya Pradesh",
        "Ashoknagar": "Madhya Pradesh",
        "Badwani": "Madhya Pradesh",
        "Balaghat": "Madhya Pradesh",
        "Betul": "Madhya Pradesh",
        "Bhind": "Madhya Pradesh",
        "Bhopal": "Madhya Pradesh",
        "Burhanpur": "Madhya Pradesh",
        "Chhatarpur": "Madhya Pradesh",
        "Chhindwara": "Madhya Pradesh",
        "Damoh": "Madhya Pradesh",
        "Datia": "Madhya Pradesh",
        "Dewas": "Madhya Pradesh",
        "Dhar": "Madhya Pradesh",
        "Dindori": "Madhya Pradesh",
        "Guna": "Madhya Pradesh",
        "Gwalior": "Madhya Pradesh",
        "Harda": "Madhya Pradesh",
        "Hoshangabad": "Madhya Pradesh",
        "Indore": "Madhya Pradesh",
        "Jabalpur": "Madhya Pradesh",
        "Jhabua": "Madhya Pradesh",
        "Katni": "Madhya Pradesh",
        "Khandwa": "Madhya Pradesh",
        "Khargone": "Madhya Pradesh",
        "Mandla": "Madhya Pradesh",
        "Mandsaur": "Madhya Pradesh",
        "Morena": "Madhya Pradesh",
        "Narsinghpur": "Madhya Pradesh",
        "Neemuch": "Madhya Pradesh",
        "Panna": "Madhya Pradesh",
        "Raisen": "Madhya Pradesh",
        "Rajgarh": "Madhya Pradesh",
        "Ratlam": "Madhya Pradesh",
        "Rewa": "Madhya Pradesh",
        "Sagar": "Madhya Pradesh",
        "Satna": "Madhya Pradesh",
        "Sehore": "Madhya Pradesh",
        "Seoni": "Madhya Pradesh",
        "Shajapur": "Madhya Pradesh",
        "Shehdol": "Madhya Pradesh",
        "Sheopur": "Madhya Pradesh",
        "Shivpuri": "Madhya Pradesh",
        "Sidhi": "Madhya Pradesh",
        "Singroli": "Madhya Pradesh",
        "Tikamgarh": "Madhya Pradesh",
        "Ujjain": "Madhya Pradesh",
        "Umariya": "Madhya Pradesh",
        "Vidisha": "Madhya Pradesh",
        "Ahmednagar": "Maharashtra",
        "Akola": "Maharashtra",
        "Amarawati": "Maharashtra",
        "Bandra(E)": "Maharashtra",
        "Beed": "Maharashtra",
        "Bhandara": "Maharashtra",
        "Buldhana": "Maharashtra",
        "Chandrapur": "Maharashtra",
        "Chattrapati Sambhajinagar": "Maharashtra",
        "Dharashiv(Usmanabad)": "Maharashtra",
        "Dhule": "Maharashtra",
        "Gadchiroli": "Maharashtra",
        "Gondiya": "Maharashtra",
        "Hingoli": "Maharashtra",
        "Jalana": "Maharashtra",
        "Jalgaon": "Maharashtra",
        "Kolhapur": "Maharashtra",
        "Latur": "Maharashtra",
        "Mumbai": "Maharashtra",
        "Murum": "Maharashtra",
        "Nagpur": "Maharashtra",
        "Nanded": "Maharashtra",
        "Nandurbar": "Maharashtra",
        "Nashik": "Maharashtra",
        "Osmanabad": "Maharashtra",
        "Parbhani": "Maharashtra",
        "Pune": "Maharashtra",
        "Raigad": "Maharashtra",
        "Ratnagiri": "Maharashtra",
        "Sangli": "Maharashtra",
        "Satara": "Maharashtra",
        "Sholapur": "Maharashtra",
        "Sindhudurg": "Maharashtra",
        "Thane": "Maharashtra",
        "Vashim": "Maharashtra",
        "Wardha": "Maharashtra",
        "Yavatmal": "Maharashtra",
        "Bishnupur": "Manipur",
        "Chandel": "Manipur",
        "Churachandpur": "Manipur",
        "Imphal East": "Manipur",
        "Imphal West": "Manipur",
        "Kakching": "Manipur",
        "Senapati": "Manipur",
        "Tamenglong": "Manipur",
        "Tengnoupal": "Manipur",
        "Thoubal": "Manipur",
        "Ukhrul": "Manipur",
        "East Garo Hills": "Meghalaya",
        "East Jaintia Hills": "Meghalaya",
        "East Khasi Hills": "Meghalaya",
        "Nongpoh (R-Bhoi)": "Meghalaya",
        "North Garo Hills": "Meghalaya",
        "South Garo Hills": "Meghalaya",
        "South West Garo Hills": "Meghalaya",
        "South West Khasi Hills": "Meghalaya",
        "West Garo Hills": "Meghalaya",
        "West Jaintia Hills": "Meghalaya",
        "West Khasi Hills": "Meghalaya",
        "Aizawl": "Mizoram",
        "Kolasib": "Mizoram",
        "Lungli": "Mizoram",
        "Mamit": "Mizoram",
        "Saiha": "Mizoram",
        "Dimapur": "Nagaland",
        "Kiphire": "Nagaland",
        "Kohima": "Nagaland",
        "Longleng": "Nagaland",
        "Mokokchung": "Nagaland",
        "Mon": "Nagaland",
        "Peren": "Nagaland",
        "Phek": "Nagaland",
        "Tsemenyu": "Nagaland",
        "Tuensang": "Nagaland",
        "Wokha": "Nagaland",
        "Zunheboto": "Nagaland",
        "Delhi": "NCT of Delhi",
        "Angul": "Odisha",
        "Balasore": "Odisha",
        "Bargarh": "Odisha",
        "Berhampur": "Odisha",
        "Bhadrak": "Odisha",
        "Bhubaneswar": "Odisha",
        "Bolangir": "Odisha",
        "Boudh": "Odisha",
        "Cuttack": "Odisha",
        "Dhenkanal": "Odisha",
        "Gajapati": "Odisha",
        "Ganjam": "Odisha",
        "Jagatsinghpur": "Odisha",
        "Jajpur": "Odisha",
        "Jharsuguda": "Odisha",
        "Kalahandi": "Odisha",
        "Kandhamal": "Odisha",
        "Kendrapara": "Odisha",
        "Keonjhar": "Odisha",
        "Khurda": "Odisha",
        "Koraput": "Odisha",
        "Malkangiri": "Odisha",
        "Mayurbhanja": "Odisha",
        "Nayagarh": "Odisha",
        "Nowarangpur": "Odisha",
        "Nuapada": "Odisha",
        "Puri": "Odisha",
        "Rayagada": "Odisha",
        "Rourkela": "Odisha",
        "Sambalpur": "Odisha",
        "Sonepur": "Odisha",
        "Sundergarh": "Odisha",
        "Karaikal": "Pondicherry",
        "Mahe": "Pondicherry",
        "Pondicherry": "Pondicherry",
        "Yanam": "Pondicherry",
        "Amritsar": "Punjab",
        "Barnala": "Punjab",
        "Bhatinda": "Punjab",
        "Faridkot": "Punjab",
        "Fatehgarh": "Punjab",
        "Fazilka": "Punjab",
        "Ferozpur": "Punjab",
        "Gurdaspur": "Punjab",
        "Hoshiarpur": "Punjab",
        "Jalandhar": "Punjab",
        "kapurthala": "Punjab",
        "Ludhiana": "Punjab",
        "Mansa": "Punjab",
        "Moga": "Punjab",
        "Mohali": "Punjab",
        "Muktsar": "Punjab",
        "Nawanshahr": "Punjab",
        "Pathankot": "Punjab",
        "Patiala": "Punjab",
        "Ropar (Rupnagar)": "Punjab",
        "Sangrur": "Punjab",
        "Tarntaran": "Punjab",
        "Jhunjhunu": "Rajasthan",
        "Ajmer": "Rajasthan",
        "Alwar": "Rajasthan",
        "Anupgarh": "Rajasthan",
        "Balotra": "Rajasthan",
        "Banswara": "Rajasthan",
        "Baran": "Rajasthan",
        "Barmer": "Rajasthan",
        "Beawar": "Rajasthan",
        "Bharatpur": "Rajasthan",
        "Bhilwara": "Rajasthan",
        "Bikaner": "Rajasthan",
        "Bundi": "Rajasthan",
        "Chittorgarh": "Rajasthan",
        "Churu": "Rajasthan",
        "Dausa": "Rajasthan",
        "Deedwana Kuchaman": "Rajasthan",
        "Deeg": "Rajasthan",
        "Dholpur": "Rajasthan",
        "Dudu": "Rajasthan",
        "Dungarpur": "Rajasthan",
        "Ganganagar": "Rajasthan",
        "Gangapur City": "Rajasthan",
        "Hanumangarh": "Rajasthan",
        "Jaipur": "Rajasthan",
        "Jaipur Rural": "Rajasthan",
        "Jaisalmer": "Rajasthan",
        "Jalore": "Rajasthan",
        "Jhalawar": "Rajasthan",
        "Jodhpur": "Rajasthan",
        "Jodhpur Rural": "Rajasthan",
        "Karauli": "Rajasthan",
        "Kekri": "Rajasthan",
        "Khairthal Tijara": "Rajasthan",
        "Kota": "Rajasthan",
        "Kotputli- Behror": "Rajasthan",
        "Nagaur": "Rajasthan",
        "Neem Ka Thana": "Rajasthan",
        "Pali": "Rajasthan",
        "Phalodi": "Rajasthan",
        "Pratapgarh": "Uttar Pradesh",
        "Rajsamand": "Rajasthan",
        "Sanchore": "Rajasthan",
        "Shahpura": "Rajasthan",
        "Sikar": "Rajasthan",
        "Sirohi": "Rajasthan",
        "Swai Madhopur": "Rajasthan",
        "Tonk": "Rajasthan",
        "Udaipur": "Rajasthan",
        "East": "Sikkim",
        "North Sikkim (Mangan)": "Sikkim",
        "South Sikkim (Namchi)": "Sikkim",
        "West Sikkim (Gyalsing)": "Sikkim",
        "Ariyalur": "Tamil Nadu",
        "Chengalpattu": "Tamil Nadu",
        "Chennai": "Tamil Nadu",
        "Coimbatore": "Tamil Nadu",
        "Cuddalore": "Tamil Nadu",
        "Dharmapuri": "Tamil Nadu",
        "Dindigul": "Tamil Nadu",
        "Erode": "Tamil Nadu",
        "Kallakuruchi": "Tamil Nadu",
        "Kancheepuram": "Tamil Nadu",
        "Karur": "Tamil Nadu",
        "Krishnagiri": "Tamil Nadu",
        "Madurai": "Tamil Nadu",
        "Mayiladuthurai": "Tamil Nadu",
        "Nagapattinam": "Tamil Nadu",
        "Nagercoil (Kannyiakumari)": "Tamil Nadu",
        "Namakkal": "Tamil Nadu",
        "Perambalur": "Tamil Nadu",
        "Pudukkottai": "Tamil Nadu",
        "Ramanathapuram": "Tamil Nadu",
        "Ranipet": "Tamil Nadu",
        "Salem": "Tamil Nadu",
        "Sivaganga": "Tamil Nadu",
        "Tenkasi": "Tamil Nadu",
        "Thanjavur": "Tamil Nadu",
        "The Nilgiris": "Tamil Nadu",
        "Theni": "Tamil Nadu",
        "Thiruchirappalli": "Tamil Nadu",
        "Thirunelveli": "Tamil Nadu",
        "Thirupathur": "Tamil Nadu",
        "Thirupur": "Tamil Nadu",
        "Thiruvannamalai": "Tamil Nadu",
        "Thiruvarur": "Tamil Nadu",
        "Thiruvellore": "Tamil Nadu",
        "Tuticorin": "Tamil Nadu",
        "Vellore": "Tamil Nadu",
        "Villupuram": "Tamil Nadu",
        "Virudhunagar": "Tamil Nadu",
        "Adilabad": "Telangana",
        "Hyderabad": "Telangana",
        "Jagityal": "Telangana",
        "Kamareddy": "Telangana",
        "Karimnagar": "Telangana",
        "Khammam": "Telangana",
        "Mahbubnagar": "Telangana",
        "Medak": "Telangana",
        "Nalgonda": "Telangana",
        "Nizamabad": "Telangana",
        "Ranga Reddy": "Telangana",
        "Siddipet": "Telangana",
        "Warangal": "Telangana",
        "Dhalai": "Tripura",
        "Gomati": "Tripura",
        "Khowai": "Tripura",
        "North Tripura": "Tripura",
        "Sepahijala": "Tripura",
        "South District": "Tripura",
        "Unokoti": "Tripura",
        "West District": "Tripura",
        "Agra": "Uttar Pradesh",
        "Aligarh": "Uttar Pradesh",
        "Ambedkarnagar": "Uttar Pradesh",
        "Amethi": "Uttar Pradesh",
        "Amroha": "Uttar Pradesh",
        "Auraiya": "Uttar Pradesh",
        "Ayodhya": "Uttar Pradesh",
        "Azamgarh": "Uttar Pradesh",
        "Badaun": "Uttar Pradesh",
        "Baghpat": "Uttar Pradesh",
        "Bahraich": "Uttar Pradesh",
        "Ballia": "Uttar Pradesh",
        "Banda": "Uttar Pradesh",
        "Barabanki": "Uttar Pradesh",
        "Bareilly": "Uttar Pradesh",
        "Basti": "Uttar Pradesh",
        "Bhadohi(Sant Ravi Nagar)": "Uttar Pradesh",
        "Bijnor": "Uttar Pradesh",
        "Bulandshahar": "Uttar Pradesh",
        "Chandauli": "Uttar Pradesh",
        "Chitrakut": "Uttar Pradesh",
        "Deoria": "Uttar Pradesh",
        "Etah": "Uttar Pradesh",
        "Etawah": "Uttar Pradesh",
        "Farukhabad": "Uttar Pradesh",
        "Fatehpur": "Uttar Pradesh",
        "Firozabad": "Uttar Pradesh",
        "Gautam Budh Nagar": "Uttar Pradesh",
        "Ghaziabad": "Uttar Pradesh",
        "Ghazipur": "Uttar Pradesh",
        "Gonda": "Uttar Pradesh",
        "Gorakhpur": "Uttar Pradesh",
        "Hardoi": "Uttar Pradesh",
        "Hathras": "Uttar Pradesh",
        "Jalaun (Orai)": "Uttar Pradesh",
        "Jaunpur": "Uttar Pradesh",
        "Jhansi": "Uttar Pradesh",
        "Kannuj": "Uttar Pradesh",
        "Kanpur": "Uttar Pradesh",
        "Kanpur Dehat": "Uttar Pradesh",
        "Kasganj": "Uttar Pradesh",
        "Kaushambi": "Uttar Pradesh",
        "Khiri (Lakhimpur)": "Uttar Pradesh",
        "Kushinagar": "Uttar Pradesh",
        "Lalitpur": "Uttar Pradesh",
        "Lucknow": "Uttar Pradesh",
        "Maharajganj": "Uttar Pradesh",
        "Mahoba": "Uttar Pradesh",
        "Mainpuri": "Uttar Pradesh",
        "Mathura": "Uttar Pradesh",
        "Mau(Maunathbhanjan)": "Uttar Pradesh",
        "Meerut": "Uttar Pradesh",
        "Mirzapur": "Uttar Pradesh",
        "Muzaffarnagar": "Uttar Pradesh",
        "Oraya": "Uttar Pradesh",
        "Pillibhit": "Uttar Pradesh",
        "Prayagraj": "Uttar Pradesh",
        "Raebarelli": "Uttar Pradesh",
        "Rampur": "Uttar Pradesh",
        "Saharanpur": "Uttar Pradesh",
        "Sambhal": "Uttar Pradesh",
        "Sant Kabir Nagar": "Uttar Pradesh",
        "Shahjahanpur": "Uttar Pradesh",
        "Shamli": "Uttar Pradesh",
        "Shravasti": "Uttar Pradesh",
        "Siddharth Nagar": "Uttar Pradesh",
        "Sitapur": "Uttar Pradesh",
        "Sonbhadra": "Uttar Pradesh",
        "Unnao": "Uttar Pradesh",
        "Varanasi": "Uttar Pradesh",
        "Almora": "Uttrakhand",
        "Bageshwar": "Uttrakhand",
        "Chamoli (Gopeshwar)": "Uttrakhand",
        "Champawat": "Uttrakhand",
        "Dehradoon": "Uttrakhand",
        "Garhwal (Pauri)": "Uttrakhand",
        "Haldwani": "Uttrakhand",
        "Haridwar": "Uttrakhand",
        "Nanital": "Uttrakhand",
        "Pithoragarh": "Uttrakhand",
        "Rudraprayag": "Uttrakhand",
        "Tehri Garhwal": "Uttrakhand",
        "UdhamSinghNagar": "Uttrakhand",
        "Uttarkashi": "Uttrakhand",
        "Alipurduar": "West Bengal",
        "Bankura": "West Bengal",
        "Birbhum": "West Bengal",
        "Burdwan": "West Bengal",
        "Coochbehar": "West Bengal",
        "Dakshin Dinajpur": "West Bengal",
        "Darjeeling": "West Bengal",
        "Hooghly": "West Bengal",
        "Howrah": "West Bengal",
        "Jalpaiguri": "West Bengal",
        "Jhargram": "West Bengal",
        "Kalimpong": "West Bengal",
        "Kolkata": "West Bengal",
        "Malda": "West Bengal",
        "Medinipur(E)": "West Bengal",
        "Medinipur(W)": "West Bengal",
        "Murshidabad": "West Bengal",
        "Nadia": "West Bengal",
        "North 24 Parganas": "West Bengal",
        "Paschim Bardhaman": "West Bengal",
        "Purba Bardhaman": "West Bengal",
        "Puruliya": "West Bengal",
        "Sounth 24 Parganas": "West Bengal",
        "Uttar Dinajpur": "West Bengal"
        }
    
    for i in commodities:  # commodity
        data_list = fetch_agri_data(driver,i)

        if not data_list:
            continue

        objs = []    
        for d in data_list:
            district=d["city"]
            stateName=market_to_state[district]
            result = crop_price(
                s_no=count,
                state=stateName,
                city=district,
                market_name=d["market_name"],
                commodity=d["commodity"],
                variety=d["variety"],
                Grade=d["grade"],
                min_Price=d["min_Price"],
                max_Price=d["max_Price"],
                modal_Price=d["modal_Price"],
                date=datetime.strptime(d["date"], "%d %b %Y").date()  

            )

            print(stateName,"done")
            objs.append(result)
            count += 1
        crop_price.objects.bulk_create(objs, ignore_conflicts=True)
        print(count)
    driver.quit()

    data = crop_price.objects.filter(commodity='Rice').values()
    return render(req,'index.html',{"data":data})'''




