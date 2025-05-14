
from flask import Flask, request, jsonify,send_from_directory
import whisper
import os
import sqlite3
import tempfile
import requests
import random
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_cors import CORS
from flask import Flask, request, jsonify
import spacy
from spacy.matcher import Matcher

app = Flask(__name__)

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")



app = Flask(__name__)
CORS(app)


# Initialize Whisper (small model for balance of speed/accuracy)
model = whisper.load_model("tiny")
def init_db():
    conn = sqlite3.connect('translation_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS translations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  audio_path TEXT,
                  original_text TEXT,
                  translated_text TEXT,
                  language_code TEXT,
                  language_name TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Initialize the matcher
matcher = Matcher(nlp.vocab)

# Define rule-based action item patterns
action_item_patterns = [
    [{"LOWER": "send"}, {"POS": {"IN": ["DET", "ADJ"]}, "OP": "*"}, {"POS": "NOUN"}],     # send the report
    [{"LOWER": "follow"}, {"LOWER": "up"}],                                               # follow up
    [{"LOWER": "schedule"}, {"POS": {"IN": ["DET", "ADJ"]}, "OP": "*"}, {"POS": "NOUN"}], # schedule the meeting
    [{"LOWER": "email"}, {"POS": "PROPN", "OP": "?"}],                                     # email John
    [{"LOWER": "call"}, {"POS": "PROPN", "OP": "?"}],                                      # call Sarah
    [{"POS": "VERB"}, {"POS": "NOUN"}]                                                     # fallback: e.g., send file
]

matcher.add("ACTION_ITEM", [pattern for pattern in action_item_patterns])

def extract_action_items(text):
    doc = nlp(text)
    results = []

    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        results.append(span.text)

    return results

@app.route('/detect-actions', methods=['POST'])
def detect_actions():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    action_items = extract_action_items(text)
    return jsonify({"action_items": action_items})
# Supported Languages (50+)
LANGUAGES = {
    'af': {'name': 'Afrikaans', 'facts': [
        "Afrikaans evolved from Dutch in the 17th century.",
        "It's the youngest Germanic language.",
        "About 7 million people speak Afrikaans."
    ]}, 'ar': {'name': 'Arabic', 'facts': [
        "Arabic is written right-to-left.",
        "There are over 30 varieties of spoken Arabic.",
        "Arabic has at least 11 words for love."
    ]}, 'az':{'name':'Azerbaijani','facts':["Azerbaijani is a Turkic language that is mutually intelligible with Turkish to a large extent.",

"The language has two primary dialects: North Azerbaijani (spoken in Azerbaijan) and South Azerbaijani (spoken in Iran).",

"Azerbaijani has used multiple writing systems over time, including Arabic, Cyrillic, and now Latin script."]},
              'be': {'name':'Belarusian','facts':[
    "Belarusian is one of the two official languages of Belarus alongside Russian.",
    "It belongs to the East Slavic group and shares similarities with Russian and Ukrainian.",
    "Belarusian has seen periods of decline and revival, with current efforts to promote its usage in education and media."
]},
    'bg': {'name':'Bulgarian','facts':[
    "Bulgarian is the first Slavic language to have a written record, dating back to the 9th century.",
    "It was the first Slavic language to adopt the Cyrillic alphabet.",
    "Bulgarian is unique among Slavic languages for not using noun cases in modern grammar."
]}
, 'bn': {'name':'Bengali','facts': [
    "Bengali is the seventh most spoken language in the world by number of native speakers.",
    "The Bengali script is derived from the ancient Brahmi script and is known for its curved letters.",
    "Rabindranath Tagore, who wrote the national anthems of both India and Bangladesh, composed them in Bengali."
]}
, 'bs': {'name':'Bosnian','facts':[
    "Bosnian is one of the three official languages of Bosnia and Herzegovina, along with Serbian and Croatian.",
    "It uses both the Latin and Cyrillic alphabets, though Latin is more commonly used.",
    "Bosnian includes many loanwords from Turkish, Arabic, and Persian due to Ottoman influence."
]}
, 'ca': {'name':'Catalan','facts':[
    "Catalan is spoken by around 10 million people, primarily in Catalonia, the Balearic Islands, and Valencia in Spain.",
    "It is a co-official language in Spain, Andorra, and parts of France.",
    "Catalan is closely related to Occitan and shares many similarities with Spanish and French."
]}
,
    'ceb':{'name': 'Cebuano','facts':[
    "Cebuano is spoken by over 20 million people, primarily in the Visayas and Mindanao regions of the Philippines.",
    "It is one of the most widely spoken languages in the Philippines, after Tagalog.",
    "Cebuano is a member of the Austronesian language family and is closely related to other Philippine languages like Hiligaynon and Waray."
]}
, 'cs':{'name': 'Czech','facts':[
    "Czech is the official language of the Czech Republic and is spoken by about 10 million people.",
    "It is a member of the West Slavic group of languages and is closely related to Slovak.",
    "Czech uses the Latin alphabet but includes additional characters like š, č, and ž."
]}
, 'cy':{'name': 'Welsh','facts':[
    "Welsh is a Celtic language spoken by around 700,000 people, primarily in Wales.",
    "It is one of the oldest languages in Europe and has been spoken for over 1,500 years.",
    "In 2011, Welsh was made an official language of Wales alongside English."
]}
, 'da': {'name':'Danish','facts':[
    "Danish is a North Germanic language spoken by around 6 million people, mainly in Denmark.",
    "It shares a lot of similarities with Swedish and Norwegian, making it mutually intelligible with both.",
    "Danish is known for its unique pronunciation, with soft 'd' sounds and a stød (glottal stop)."
]}
,
    'de': {'name':'German','facts':[
    "German is the most widely spoken language in Europe, with over 100 million native speakers.",
    "It is the official language of Germany, Austria, and parts of Switzerland, Belgium, and Luxembourg.",
    "German has a rich literary and philosophical tradition, with famous authors like Goethe and philosophers like Kant."
]}
, 'el': {'name':'Greek','facts':[
    "Greek is one of the oldest languages still spoken today, with a history spanning over 3,000 years.",
    "It is the official language of Greece and Cyprus and has influenced many modern languages, especially in science and philosophy.",
    "The Greek alphabet is the ancestor of many modern alphabets, including the Latin and Cyrillic scripts."
]}
, 'en': {'name':'English','facts':[
    "English is the third most spoken native language in the world, after Mandarin and Spanish.",
    "The word 'set' has the highest number of definitions in the English language, with over 430 different meanings.",
    "English is the official language of 67 countries and is widely used as a global lingua franca."
]}
, 
    'es':{'name': 'Spanish','facts':[
    "Spanish is the second most spoken language in the world by native speakers, after Mandarin.",
    "There are more than 20 countries where Spanish is the official language, including Spain, Mexico, and most of Central and South America.",
    "The longest word in the Spanish language is 'electroencefalografista', which has 23 letters."
]}
, 'et':{'name': 'Estonian','facts': [
    "Estonian is one of the few languages in Europe that belongs to the Finno-Ugric language family, unrelated to most other European languages.",
    "Estonian has 14 grammatical cases, more than most languages in Europe.",
    "The Estonian alphabet is based on the Latin script and consists of 27 letters, with no 'q', 'w', 'x', or 'z'."
]}
, 'eu': {'name':'Basque','facts':[
    "Basque is a language isolate, meaning it is not related to any known language family.",
    "It is spoken in the Basque Country, a region shared by Spain and France.",
    "Basque has a unique system of ergative-absolutive alignment, which is rare among European languages."
]}
, 'fa': {'name':'Persian','facts':["Persian (also known as Farsi) is an Indo-Iranian language spoken primarily in Iran, Afghanistan (as Dari), and Tajikistan (as Tajik).",

"It has a rich literary history, with famous poets like Rumi, Hafez, and Ferdowsi writing in Persian over a thousand years ago.",

"Persian uses a modified Arabic script, but its grammar and vocabulary are distinct and more closely related to European languages like English."]},
    'fi':{'name': 'Finnish','facts':["Finnish is a Uralic language, making it linguistically unrelated to most European languages, including its neighbor Swedish.",

"It features extensive use of cases, with nouns having up to 15 grammatical cases to express relationships and meanings.",

"Finnish is known for its long compound words, like lentokonesuihkuturbiinimoottoriapumekaanikkoaliupseerioppilas, one of the longest words in the language."]},
    'fr':{'name': 'French','facts':["French is a Romance language derived from Latin, sharing roots with Spanish, Italian, and Portuguese.",

"It is spoken on five continents, making it one of the most globally widespread languages."

"French was the official language of diplomacy and international relations from the 17th to the mid-20th century."]},
    'ga':{'name': 'Irish','facts':["Irish is a Celtic language and one of the oldest written languages in Europe still in use today.",

"It is an official language of Ireland and also recognized as an official EU language.",

"Despite English being more commonly spoken, Irish is a compulsory subject in Irish schools and a symbol of national identity."]},
    'gl': {'name':'Galician','facts':["Galician is a Romance language spoken primarily in the autonomous community of Galicia in northwestern Spain.",

"It shares a common origin with Portuguese, and the two languages were once a single medieval language known as Galician-Portuguese.",

"Galician has co-official status with Spanish in Galicia, where it is used in education, media, and government."]},
    'gu': {'name':'Gujarati','facts':["Gujarati is an Indo-Aryan language spoken by over 55 million people, primarily in the Indian state of Gujarat.",

"It is the sixth most spoken language in India and is also widely spoken by the Indian diaspora in countries like the UK, USA, and South Africa."

"Gujarati was the first language of Mahatma Gandhi, who used it for many of his writings and publications."]},
    'ha': {'name':'Hausa','facts':["Hausa is a Chadic language spoken widely across West Africa, especially in Nigeria and Niger.",

"It is one of the most spoken languages in Africa, with over 60 million native speakers and many more using it as a second language.",

"Hausa has a long tradition of written literature, including texts in both Latin and Arabic scripts (Ajami)."]},
    'hi': {'name':'Hindi','facts':["Hindi is the most widely spoken language in India, and one of the official languages of the Indian government.",

"It is written in the Devanagari script, which is also used for Sanskrit, Marathi, and Nepali.",

"Modern Standard Hindi is based on the Khari Boli dialect, and is mutually intelligible with Urdu in spoken form."]},
    'hmn': {'name':'Hmong','facts':["Hmong is a tonal language with eight tones, which can change the meaning of a word based on pitch.",

"It uses a Romanized Popular Alphabet (RPA) for writing, developed in the 1950s.",

"Hmong is spoken by over 4 million people, primarily in Southeast Asia and among diaspora communities in the United States."]},
    'hr': {'name':'Croatian','facts':["Croatian is a South Slavic language that uses the Latin alphabet for writing.", "It has three grammatical genders: masculine, feminine, and neuter.",
                                      "Croatian is one of the official languages of Croatia and is also spoken by minorities in neighboring countries like Serbia and Bosnia and Herzegovina."]},
    'ht': {'name':'Haitian Creole','facts':[" Haitian Creole is a French-based creole language spoken primarily in Haiti.", "It has a simplified grammar compared to French, with no verb conjugation for tense or agreement.",
                                            "Haitian Creole is one of Haiti's official languages, alongside French."]},
    'hu': {'name':'Hungarian','facts':["Hungarian is a Uralic language, unrelated to most other European languages.", "It has 18 cases, used to express various grammatical relations.",
                                       "Hungarian is the official language of Hungary and is spoken by minority communities in several neighboring countries."]},
    'hy': {'name':'Armenian','facts':["Armenian is an independent branch of the Indo-European language family.", "It has its own unique alphabet, created by Saint Mesrop Mashtots in the 5th century.",
                                      "Armenian is the official language of Armenia and is spoken by the Armenian diaspora worldwide."]},
    'id': {'name':'Indonesian','facts':["Indonesian is the official language of Indonesia and is a standardized form of Malay.", "It is an Austronesian language with a simplified grammar compared to other languages in the same family.",
                                        "Indonesian uses the Latin alphabet and has borrowed words from Dutch, Arabic, and other languages."]},
    'ig':{'name': 'Igbo','facts':["Igbo is a Niger-Congo language spoken primarily in southeastern Nigeria.", "It has eight tones, which can change the meaning of words depending on pitch.",
                                  "Igbo uses the Latin alphabet and is one of the official languages of Nigeria."]},
    'is': {'name':'Icelandic','facts':["Icelandic is a North Germanic language, closely related to Old Norse.", "It has retained much of its original grammar, making it one of the most conservative living languages in Europe.",
                                       "Icelandic is the official language of Iceland and is spoken by almost the entire population."]},
    'it': {'name':'Italian','facts':["Italian is a Romance language descended from Latin, spoken mainly in Italy and Switzerland.", "It has a rich system of vowel sounds and is known for its melodic intonation.",
                                     "Italian is the official language of Italy and San Marino, and one of the official languages of Switzerland."]},
    'iw': {'name':'Hebrew','facts':["Hebrew is a Semitic language and one of the official languages of Israel.", "It is written from right to left using the Hebrew alphabet.",
                                    "Hebrew was revived as a spoken language in the 19th and 20th centuries after centuries of being used primarily for religious and literary purposes."]},
    'ja': {'name':'Japanese','facts':["Japanese is an East Asian language that uses three scripts: Kanji, Hiragana, and Katakana.", "It is an agglutinative language, meaning it uses suffixes to express grammatical relationships.",
                                      "Japanese has a system of honorifics to show respect based on social hierarchy."]},
    'jw': {'name':'Javanese','facts':["Javanese is an Austronesian language spoken primarily on the island of Java in Indonesia.", "It has a complex system of honorifics and speech levels used to convey politeness and respect.",
                                      "Javanese is written using both the Latin alphabet and a traditional Javanese script."]},
    'ka': {'name':'Georgian','facts':["Georgian is a Kartvelian language spoken primarily in Georgia.", "It has its own unique alphabet, known as Mkhedruli, which is used in all forms of writing.",
                                      "Georgian is an agglutinative language, meaning it adds affixes to the root of words to express grammatical relationships."]},
    'kk': {'name':'Kazakh','facts':["Kazakh is a Turkic language spoken primarily in Kazakhstan and parts of China, Russia, and Mongolia.", "It was traditionally written in the Arabic script, then Cyrillic, and has recently adopted the Latin alphabet.",
                                    "Kazakh is an agglutinative language, with vowel harmony and a complex case system."]},
    'km':{'name': 'Khmer','facts':["Khmer is a Mon-Khmer language spoken primarily in Cambodia.", "It uses its own script, which is an abugida, where each character represents a syllable rather than an individual sound.",
                                   "Khmer has no verb conjugation and relies on word order and context to indicate tenses."]},
    'kn': {'name':'Kannada','facts':["Kannada is a Dravidian language spoken predominantly in the Indian state of Karnataka.", "It has its own script derived from the ancient Brahmi script and is known for its rounded shapes.",
                                     "Kannada has a rich literary tradition dating back over a thousand years."]},
    'ko': {'name':'Korean','facts':["Korean is a language isolate spoken primarily in North and South Korea.", "It uses the Hangul alphabet, a featural writing system scientifically designed in the 15th century.",
                                    "Korean has an agglutinative grammar and incorporates speech levels to show respect and formality."]},
    'la': {'name':'Latin','facts':["Latin is an ancient Italic language that was spoken in the Roman Empire.", "It is the root of the Romance languages like Spanish, French, and Italian.",
                                   "Though no longer spoken conversationally, Latin is still used in law, science, and the Roman Catholic Church."]},
    'lo': {'name':'Lao','facts':["Lao is a tonal Tai-Kadai language spoken mainly in Laos.", "It uses an abugida script derived from the ancient Khmer script, written from left to right.", "Lao has multiple dialects, with the Vientiane dialect serving as the standard form."]},
    'lt': {'name':'Lithuanian','facts':["Lithuanian is a Baltic language known for preserving many archaic Indo-European features.", "It uses the Latin alphabet with diacritical marks and has a highly inflected grammar.",
                                        "Lithuanian is one of the official languages of Lithuania and the European Union."]},
    'lv': {'name':'Latvian','facts':["Latvian is another Baltic language, closely related to Lithuanian but more modernized.", "It uses a modified Latin script and has three dialects: Livonian, Middle, and High Latvian.",
                                     "Latvian is the official language of Latvia and is known for its pitch accent."]},
    'mg': {'name':'Malagasy','facts':["Malagasy is an Austronesian language spoken mainly in Madagascar.", "It is most closely related to languages spoken in Southeast Asia, particularly Ma'anyan from Borneo.", "Malagasy uses the Latin alphabet and has been influenced by Bantu, Arabic, and French languages."]},
    'mi': {'name':'Maori','facts':["Māori is an Eastern Polynesian language spoken by the indigenous Māori people of New Zealand.", "It uses the Latin alphabet and includes macrons to indicate long vowels.", "Māori is one of the official languages of New Zealand and is taught in schools across the country."]},
    'mk': {'name':'Macedonian','facts':["Macedonian is a South Slavic language closely related to Bulgarian.", "It uses the Cyrillic alphabet and has a simplified grammatical structure compared to other Slavic languages.", "Macedonian is the official language of North Macedonia and is spoken by communities in neighboring countries."]},
    'ml': {'name':'Malayalam','facts':["Malayalam is a Dravidian language spoken predominantly in the Indian state of Kerala.", "It has a script of its own derived from the ancient Brahmi script, known for its rounded letters.", "Malayalam has a rich literary heritage and is known for its long compound words."]},
    'mn': {'name':'Mongolian','facts':["Mongolian is an Altaic language spoken primarily in Mongolia and parts of China.", "It can be written in the traditional vertical Mongolian script or the Cyrillic script in Mongolia.", "Mongolian has vowel harmony and is an agglutinative language with complex suffix usage."]},
    'mr': {'name':'Marathi','facts':["Marathi is an Indo-Aryan language spoken predominantly in the Indian state of Maharashtra.", "It uses the Devanagari script and has a rich literary tradition dating back to the 13th century.", "Marathi has formal and informal speech levels and a complex system of honorifics."]},
    'ms': {'name':'Malay','facts':["Malay is an Austronesian language spoken in Malaysia, Indonesia, Brunei, and Singapore.", "It uses the Latin alphabet and has a standardized form known as Bahasa Melayu.", "Malay has simple grammar with no verb conjugations for tense or subject agreement."]},
    'mt': {'name':'Maltese','facts':["Maltese is a Semitic language heavily influenced by Italian and English, spoken primarily in Malta.", "It is the only Semitic language written in the Latin script and an official EU language.", "Maltese has a rich vocabulary with roots in Arabic, Sicilian, and English."]},
    'my': {'name':'Myanmar','facts':["Burmese is a Sino-Tibetan language and the official language of Myanmar.", "It uses a syllabic script derived from the Mon script, written from left to right.", "Burmese is a tonal and analytic language with no verb conjugations."]},
    'ne': {'name':'Nepali','facts':["Nepali is an Indo-Aryan language and the official language of Nepal.", "It is written in the Devanagari script and shares linguistic roots with Hindi and Sanskrit.", "Nepali has a rich tradition of folk songs, poetry, and classical literature."]},
    'nl': {'name':'Dutch','facts':["Dutch is a West Germanic language spoken mainly in the Netherlands and Belgium.", "It uses the Latin alphabet and is closely related to both German and English.", "Dutch has contributed many loanwords to other languages, especially in trade and maritime vocabulary."]},
    'no': {'name':'Norwegian','facts':["Norwegian is a North Germanic language spoken mainly in Norway.", "It has two official written forms: Bokmål and Nynorsk.", "Norwegian shares mutual intelligibility with Danish and Swedish."]},
    'ny': {'name':'Chichewa','facts':["Chichewa, also known as Chewa or Nyanja, is a Bantu language spoken in Malawi, Zambia, and Mozambique.", "It uses the Latin alphabet and has noun classes typical of Bantu languages.", "Chichewa is the national language of Malawi and is used in education and media."]},
    'pa': {'name':'Punjabi','facts':["Punjabi is an Indo-Aryan language spoken widely in the Punjab regions of India and Pakistan.", "It is unique among Indo-Aryan languages for being tonal.", "Punjabi is written in Gurmukhi script in India and Shahmukhi script in Pakistan."]},
    'pl': {'name':'Polish','facts':["Polish is a West Slavic language spoken mainly in Poland.", "It uses the Latin alphabet with additional diacritical marks and has complex grammar with seven cases.", "Polish is known for its consonant clusters and nasal vowel sounds."]},
    'pt': {'name':'Portuguese','facts':["Portuguese is a Romance language spoken in Portugal, Brazil, and several African countries.", "It uses the Latin script and has two major dialect groups: European and Brazilian Portuguese.", "Portuguese is the official language of nine countries and is one of the most spoken languages in the world."]},
    'ro': {'name':'Romanian','facts':["Romanian is a Romance language that evolved from Latin spoken in ancient Dacia.", "It uses the Latin alphabet and retains many features of Latin grammar.", "Romanian is the official language of Romania and Moldova."]},
    'ru': {'name':'Russian','facts':["Russian is an East Slavic language and the most widely spoken Slavic language.", "It uses the Cyrillic script and features complex inflectional grammar.", "Russian is one of the six official languages of the United Nations."]},
    'si':{'name': 'Sinhala','facts':["Sinhala is an Indo-Aryan language spoken primarily in Sri Lanka.", "It uses the Sinhala script, which is a Brahmic abugida with rounded letters.", "Sinhala has a long literary history dating back over a thousand years."]},
    'sk':{'name': 'Slovak','facts':["Slovak is a West Slavic language closely related to Czech and Polish.", "It uses the Latin alphabet with diacritics and has a highly inflected grammar.", "Slovak is the official language of Slovakia and one of the EU’s official languages."]},
    'sl': {'name':'Slovenian','facts':["Slovenian is a South Slavic language spoken mainly in Slovenia.", "It has 6 grammatical cases and dual number forms, which are rare in modern languages.", "Slovenian uses the Latin script and has a rich dialectal diversity."]},
    'so': {'name':'Somali','facts':["Somali is a Cushitic language spoken mainly in Somalia, Djibouti, and Ethiopia.", "It uses the Latin alphabet officially since 1972 and has a subject–object–verb word order.", "Somali includes influences from Arabic, Italian, and English due to historical contact."]},
    'sq': {'name':'Albanian','facts':["Albanian is an independent branch of the Indo-European language family spoken primarily in Albania and Kosovo.", "It has two main dialects: Gheg in the north and Tosk in the south.", "Albanian uses the Latin alphabet and has many loanwords from Latin, Greek, and Turkish."]},
    'sr': {'name':'Serbian','facts':["Serbian is a South Slavic language spoken mainly in Serbia, Bosnia and Herzegovina, and Montenegro.", "It is one of the few European languages officially written in both Cyrillic and Latin scripts.", "Serbian is mutually intelligible with Croatian, Bosnian, and Montenegrin."]},
    'st': {'name':'Sesotho','facts':["Sesotho, also known as Southern Sotho, is a Bantu language spoken in Lesotho and parts of South Africa.", "It uses the Latin alphabet and is one of the 11 official languages of South Africa.", "Sesotho is known for its use of noun classes and agglutinative morphology."]},
    'su': {'name':'Sundanese','facts':["Sundanese is an Austronesian language spoken mainly in the western part of Java, Indonesia.", "It traditionally used the Javanese script but is now mostly written in the Latin alphabet.", "Sundanese has multiple speech levels to indicate formality and respect."]},
    'sv': {'name':'Swedish','facts':["Swedish is a North Germanic language spoken mainly in Sweden and parts of Finland.", "It uses the Latin alphabet and is closely related to Norwegian and Danish.", "Swedish is known for its pitch accent, which distinguishes word meanings."]},
    'sw':{'name': 'Swahili','facts':["Swahili is a Bantu language with significant Arabic influence, spoken across East Africa.", "It uses the Latin alphabet and serves as a lingua franca in many African countries.", "Swahili has simple grammar and is one of the official languages of the African Union."]},
    'ta':{'name': 'Tamil','facts':["Tamil is a Dravidian language spoken primarily in Tamil Nadu, India, and northern Sri Lanka.", "It has its own script and is one of the longest-surviving classical languages in the world.", "Tamil has a vast literary tradition spanning over 2,000 years."]},
    'te': {'name':'Telugu','facts':["Telugu is a Dravidian language spoken predominantly in the Indian states of Andhra Pradesh and Telangana.",
"It uses the Telugu script, which is derived from the Brahmi script and features rounded shapes.",
"Telugu is known as the 'Italian of the East' due to its mellifluous and vowel-rich sound."]},
    'tg': {'name':'Tajik','facts':["Tajik is a variety of Persian spoken mainly in Tajikistan.",
"It is written in the Cyrillic script, unlike other Persian dialects which use the Arabic script.",
"Tajik contains many Russian loanwords due to Soviet influence."]},
    'th': {'name':'Thai','facts':["Thai is a tonal Tai-Kadai language spoken primarily in Thailand.",
"It uses an abugida script derived from Old Khmer, written left to right without spaces between words.",
"Thai grammar relies heavily on word order and particles rather than inflection."]},
    'tl': {'name':'Filipino','facts':["Filipino is the standardized form of Tagalog and the national language of the Philippines.",
"It is written in the Latin alphabet and incorporates vocabulary from Spanish, English, and native languages.",
"Filipino grammar includes affixation to express verb tense, aspect, and focus."]},
    'tr':{'name': 'Turkish','facts':["Turkish is a Turkic language spoken primarily in Turkey and Cyprus.",
"It uses the Latin alphabet and underwent a major script reform in 1928.",
"Turkish is an agglutinative language with vowel harmony and no grammatical gender."]},
    'uk': {'name':'Ukrainian','facts':["Ukrainian is an East Slavic language spoken mainly in Ukraine.",
"It uses a variant of the Cyrillic script and is closely related to Belarusian and Russian.",
"Ukrainian features a rich system of inflection and a melodic intonation pattern."]},
    'ur':{'name': 'Urdu','facts':["Urdu is an Indo-Aryan language spoken in Pakistan and parts of India.",
"It uses a modified Perso-Arabic script written from right to left.",
"Urdu shares grammar with Hindi but is heavily influenced by Persian and Arabic in vocabulary and script."]},
    'uz':{'name': 'Uzbek','facts':["Uzbek is a Turkic language spoken mainly in Uzbekistan and surrounding Central Asian countries.",
"It transitioned from Arabic to Latin to Cyrillic scripts and now officially uses the Latin alphabet.",
"Uzbek is an agglutinative language with vowel harmony and no grammatical gender."]},
    'vi': {'name':'Vietnamese','facts':["Vietnamese is an Austroasiatic language spoken primarily in Vietnam.",
"It uses a Latin-based script called Quốc Ngữ with many diacritics to indicate tone and pronunciation.",
"Vietnamese has six tones and is strongly influenced by Chinese vocabulary and grammar."]},
    'xh': {'name':'Xhosa','facts':["Xhosa is a Bantu language spoken mainly in South Africa and is known for its click consonants.",
"It uses the Latin alphabet and has 15 click sounds borrowed from Khoisan languages.",
"Xhosa is one of South Africa’s 11 official languages and is mutually intelligible with Zulu to some extent."]},
    'yi': {'name':'Yiddish','facts':["Yiddish is a High German-derived language historically spoken by Ashkenazi Jews.",
"It is written in the Hebrew script and incorporates elements from German, Hebrew, Aramaic, and Slavic languages.",
"Yiddish was widely spoken in Eastern Europe before World War II and has a rich literary tradition."]},
    'yo': {'name':'Yoruba','facts':["Yoruba is a Niger-Congo language spoken mainly in southwestern Nigeria and neighboring countries.",
"It is written in the Latin alphabet with tone marks to indicate its three-level tonal system.",
"Yoruba has a strong oral tradition, including rich folklore, proverbs, and poetry."]},
    'zu':{'name': 'Zulu','facts':["Zulu is a Bantu language spoken mainly in South Africa and is known for its rich system of noun classes.",
"It uses the Latin script and includes click sounds influenced by Khoisan languages.",
"Zulu is one of South Africa’s official languages and has a significant presence in media and education."]}
}
FULL_LANGUAGE_FACTS = {
    'af': [
        "Afrikaans is the only Indo-European language to have developed in Africa.",
        "The word 'Afrikaans' means 'African' in Dutch.",
        "It has simplified grammar compared to Dutch (no verb conjugations by person)."
    ],
    'ar': [
        "Arabic has influenced many languages including Spanish and English (words like algebra, coffee, sugar).",
        "The Arabic alphabet has 28 letters and is written cursively.",
        "Arabic is the liturgical language of Islam."
    ],
    'az': [
        "Azerbaijani is spoken by about 30 million people.",
        "It has two main dialects: North Azerbaijani and South Azerbaijani.",
        "The language uses the Latin script in Azerbaijan but Persian script in Iran."
    ],
    'be': [
        "Belarusian is one of the two official languages of Belarus.",
        "It's closely related to Russian and Ukrainian.",
        "The language uses the Cyrillic alphabet."
    ],
    'bg': [
    "Bulgarian is the first Slavic language to have a written record, dating back to the 9th century.",
    "It was the first Slavic language to adopt the Cyrillic alphabet.",
    "Bulgarian is unique among Slavic languages for not using noun cases in modern grammar."
],
    'bn': [
    "Bengali is the seventh most spoken language in the world by number of native speakers.",
    "The Bengali script is derived from the ancient Brahmi script and is known for its curved letters.",
    "Rabindranath Tagore, who wrote the national anthems of both India and Bangladesh, composed them in Bengali."
],
    'bs': [
    "Bosnian is one of the three official languages of Bosnia and Herzegovina, along with Serbian and Croatian.",
    "It uses both the Latin and Cyrillic alphabets, though Latin is more commonly used.",
    "Bosnian includes many loanwords from Turkish, Arabic, and Persian due to Ottoman influence."
],
    'ca': [
    "Catalan is spoken by around 10 million people, primarily in Catalonia, the Balearic Islands, and Valencia in Spain.",
    "It is a co-official language in Spain, Andorra, and parts of France.",
    "Catalan is closely related to Occitan and shares many similarities with Spanish and French."
],
    'ceb': [
    "Cebuano is spoken by over 20 million people, primarily in the Visayas and Mindanao regions of the Philippines.",
    "It is one of the most widely spoken languages in the Philippines, after Tagalog.",
    "Cebuano is a member of the Austronesian language family and is closely related to other Philippine languages like Hiligaynon and Waray."
],
    'cs': [
    "Czech is the official language of the Czech Republic and is spoken by about 10 million people.",
    "It is a member of the West Slavic group of languages and is closely related to Slovak.",
    "Czech uses the Latin alphabet but includes additional characters like š, č, and ž."
],
    'cy': [
    "Welsh is a Celtic language spoken by around 700,000 people, primarily in Wales.",
    "It is one of the oldest languages in Europe and has been spoken for over 1,500 years.",
    "In 2011, Welsh was made an official language of Wales alongside English."
],
  'da': [
    "Danish is a North Germanic language spoken by around 6 million people, mainly in Denmark.",
    "It shares a lot of similarities with Swedish and Norwegian, making it mutually intelligible with both.",
    "Danish is known for its unique pronunciation, with soft 'd' sounds and a stød (glottal stop)."
],
    'de': [
    "German is the most widely spoken language in Europe, with over 100 million native speakers.",
    "It is the official language of Germany, Austria, and parts of Switzerland, Belgium, and Luxembourg.",
    "German has a rich literary and philosophical tradition, with famous authors like Goethe and philosophers like Kant."
],
    'el': [
    "Greek is one of the oldest languages still spoken today, with a history spanning over 3,000 years.",
    "It is the official language of Greece and Cyprus and has influenced many modern languages, especially in science and philosophy.",
    "The Greek alphabet is the ancestor of many modern alphabets, including the Latin and Cyrillic scripts."
],
    'en': [
    "English is the third most spoken native language in the world, after Mandarin and Spanish.",
    "The word 'set' has the highest number of definitions in the English language, with over 430 different meanings.",
    "English is the official language of 67 countries and is widely used as a global lingua franca."
],
    'es': [
    "Spanish is the second most spoken language in the world by native speakers, after Mandarin.",
    "There are more than 20 countries where Spanish is the official language, including Spain, Mexico, and most of Central and South America.",
    "The longest word in the Spanish language is 'electroencefalografista', which has 23 letters."
],
    'et': [
    "Estonian is one of the few languages in Europe that belongs to the Finno-Ugric language family, unrelated to most other European languages.",
    "Estonian has 14 grammatical cases, more than most languages in Europe.",
    "The Estonian alphabet is based on the Latin script and consists of 27 letters, with no 'q', 'w', 'x', or 'z'."
],
    'eu': [
    "Basque is a language isolate, meaning it is not related to any known language family.",
    "It is spoken in the Basque Country, a region shared by Spain and France.",
    "Basque has a unique system of ergative-absolutive alignment, which is rare among European languages."
],
    'fa':["Persian (also known as Farsi) is an Indo-Iranian language spoken primarily in Iran, Afghanistan (as Dari), and Tajikistan (as Tajik).",

"It has a rich literary history, with famous poets like Rumi, Hafez, and Ferdowsi writing in Persian over a thousand years ago.",

"Persian uses a modified Arabic script, but its grammar and vocabulary are distinct and more closely related to European languages like English."],
    'fi':["Finnish is a Uralic language, making it linguistically unrelated to most European languages, including its neighbor Swedish.",

"It features extensive use of cases, with nouns having up to 15 grammatical cases to express relationships and meanings.",

"Finnish is known for its long compound words, like lentokonesuihkuturbiinimoottoriapumekaanikkoaliupseerioppilas, one of the longest words in the language."],
    'fr':["French is a Romance language derived from Latin, sharing roots with Spanish, Italian, and Portuguese.",

"It is spoken on five continents, making it one of the most globally widespread languages.",

"French was the official language of diplomacy and international relations from the 17th to the mid-20th century."],
    'ga':["Irish is a Celtic language and one of the oldest written languages in Europe still in use today.",

"It is an official language of Ireland and also recognized as an official EU language.",

"Despite English being more commonly spoken, Irish is a compulsory subject in Irish schools and a symbol of national identity."],
    'gl': ["Galician is a Romance language spoken primarily in the autonomous community of Galicia in northwestern Spain.",

"It shares a common origin with Portuguese, and the two languages were once a single medieval language known as Galician-Portuguese.",

"Galician has co-official status with Spanish in Galicia, where it is used in education, media, and government."],
    'gu': ["Gujarati is an Indo-Aryan language spoken by over 55 million people, primarily in the Indian state of Gujarat.",

"It is the sixth most spoken language in India and is also widely spoken by the Indian diaspora in countries like the UK, USA, and South Africa."

"Gujarati was the first language of Mahatma Gandhi, who used it for many of his writings and publications."],
    'ha': ["Hausa is a Chadic language spoken widely across West Africa, especially in Nigeria and Niger.",

"It is one of the most spoken languages in Africa, with over 60 million native speakers and many more using it as a second language.",

"Hausa has a long tradition of written literature, including texts in both Latin and Arabic scripts (Ajami)."],
    'hi': ["Hindi is the most widely spoken language in India, and one of the official languages of the Indian government.",

"It is written in the Devanagari script, which is also used for Sanskrit, Marathi, and Nepali.",

"Modern Standard Hindi is based on the Khari Boli dialect, and is mutually intelligible with Urdu in spoken form."],
    'hmn': ["Hmong is a tonal language with eight tones, which can change the meaning of a word based on pitch.",

"It uses a Romanized Popular Alphabet (RPA) for writing, developed in the 1950s.",

"Hmong is spoken by over 4 million people, primarily in Southeast Asia and among diaspora communities in the United States."],
    'hr': ["Croatian is a South Slavic language that uses the Latin alphabet for writing.", "It has three grammatical genders: masculine, feminine, and neuter.",
           "Croatian is one of the official languages of Croatia and is also spoken by minorities in neighboring countries like Serbia and Bosnia and Herzegovina."],
    'ht': [" Haitian Creole is a French-based creole language spoken primarily in Haiti.", "It has a simplified grammar compared to French, with no verb conjugation for tense or agreement.",
           "Haitian Creole is one of Haiti's official languages, alongside French."],
    'hu': ["Hungarian is a Uralic language, unrelated to most other European languages.", "It has 18 cases, used to express various grammatical relations.",
           "Hungarian is the official language of Hungary and is spoken by minority communities in several neighboring countries."],
    'hy': ["Armenian is an independent branch of the Indo-European language family.", "It has its own unique alphabet, created by Saint Mesrop Mashtots in the 5th century.",
           "Armenian is the official language of Armenia and is spoken by the Armenian diaspora worldwide."],
    'id': ["Indonesian is the official language of Indonesia and is a standardized form of Malay.", "It is an Austronesian language with a simplified grammar compared to other languages in the same family.",
           "Indonesian uses the Latin alphabet and has borrowed words from Dutch, Arabic, and other languages."],
    'ig':["Igbo is a Niger-Congo language spoken primarily in southeastern Nigeria.", "It has eight tones, which can change the meaning of words depending on pitch.", "Igbo uses the Latin alphabet and is one of the official languages of Nigeria."],
    'is': ["Icelandic is a North Germanic language, closely related to Old Norse.", "It has retained much of its original grammar, making it one of the most conservative living languages in Europe.",
           "Icelandic is the official language of Iceland and is spoken by almost the entire population."],
    'it': ["Italian is a Romance language descended from Latin, spoken mainly in Italy and Switzerland.", "It has a rich system of vowel sounds and is known for its melodic intonation.",
           "Italian is the official language of Italy and San Marino, and one of the official languages of Switzerland."],
    'iw': ["Hebrew is a Semitic language and one of the official languages of Israel.", "It is written from right to left using the Hebrew alphabet.",
           "Hebrew was revived as a spoken language in the 19th and 20th centuries after centuries of being used primarily for religious and literary purposes."],
    'ja': ["Japanese is an East Asian language that uses three scripts: Kanji, Hiragana, and Katakana.", "It is an agglutinative language, meaning it uses suffixes to express grammatical relationships.",
           "Japanese has a system of honorifics to show respect based on social hierarchy."],
    'jw': ["Javanese is an Austronesian language spoken primarily on the island of Java in Indonesia.", "It has a complex system of honorifics and speech levels used to convey politeness and respect.", "Javanese is written using both the Latin alphabet and a traditional Javanese script."],
    'ka': ["Georgian is a Kartvelian language spoken primarily in Georgia.", "It has its own unique alphabet, known as Mkhedruli, which is used in all forms of writing.", "Georgian is an agglutinative language, meaning it adds affixes to the root of words to express grammatical relationships."],
    'kk': ["Kazakh is a Turkic language spoken primarily in Kazakhstan and parts of China, Russia, and Mongolia.", "It was traditionally written in the Arabic script, then Cyrillic, and has recently adopted the Latin alphabet.",
           "Kazakh is an agglutinative language, with vowel harmony and a complex case system."],
    'km':["Khmer is a Mon-Khmer language spoken primarily in Cambodia.", "It uses its own script, which is an abugida, where each character represents a syllable rather than an individual sound.",
          "Khmer has no verb conjugation and relies on word order and context to indicate tenses."],
    'kn': ["Kannada is a Dravidian language spoken predominantly in the Indian state of Karnataka.", "It has its own script derived from the ancient Brahmi script and is known for its rounded shapes.",
           "Kannada has a rich literary tradition dating back over a thousand years."],
    'ko': ["Korean is a language isolate spoken primarily in North and South Korea.", "It uses the Hangul alphabet, a featural writing system scientifically designed in the 15th century.",
           "Korean has an agglutinative grammar and incorporates speech levels to show respect and formality."],
    'la': ["Latin is an ancient Italic language that was spoken in the Roman Empire.", "It is the root of the Romance languages like Spanish, French, and Italian.",
           "Though no longer spoken conversationally, Latin is still used in law, science, and the Roman Catholic Church."],
    'lo': ["Lao is a tonal Tai-Kadai language spoken mainly in Laos.", "It uses an abugida script derived from the ancient Khmer script, written from left to right.", "Lao has multiple dialects, with the Vientiane dialect serving as the standard form."],
    'lt': ["Lithuanian is a Baltic language known for preserving many archaic Indo-European features.", "It uses the Latin alphabet with diacritical marks and has a highly inflected grammar.",
           "Lithuanian is one of the official languages of Lithuania and the European Union."],
    'lv': ["Latvian is another Baltic language, closely related to Lithuanian but more modernized.", "It uses a modified Latin script and has three dialects: Livonian, Middle, and High Latvian.", "Latvian is the official language of Latvia and is known for its pitch accent."],
    'mg': ["Malagasy is an Austronesian language spoken mainly in Madagascar.", "It is most closely related to languages spoken in Southeast Asia, particularly Ma'anyan from Borneo.", "Malagasy uses the Latin alphabet and has been influenced by Bantu, Arabic, and French languages."],
    'mi': ["Māori is an Eastern Polynesian language spoken by the indigenous Māori people of New Zealand.", "It uses the Latin alphabet and includes macrons to indicate long vowels.", "Māori is one of the official languages of New Zealand and is taught in schools across the country."],
    'mk':["Macedonian is a South Slavic language closely related to Bulgarian.", "It uses the Cyrillic alphabet and has a simplified grammatical structure compared to other Slavic languages.", "Macedonian is the official language of North Macedonia and is spoken by communities in neighboring countries."],
    'ml': ["Malayalam is a Dravidian language spoken predominantly in the Indian state of Kerala.", "It has a script of its own derived from the ancient Brahmi script, known for its rounded letters.", "Malayalam has a rich literary heritage and is known for its long compound words."],
    'mn': ["Mongolian is an Altaic language spoken primarily in Mongolia and parts of China.", "It can be written in the traditional vertical Mongolian script or the Cyrillic script in Mongolia.", "Mongolian has vowel harmony and is an agglutinative language with complex suffix usage."],
    'mr': ["Marathi is an Indo-Aryan language spoken predominantly in the Indian state of Maharashtra.", "It uses the Devanagari script and has a rich literary tradition dating back to the 13th century.", "Marathi has formal and informal speech levels and a complex system of honorifics."],
    'ms': ["Malay is an Austronesian language spoken in Malaysia, Indonesia, Brunei, and Singapore.", "It uses the Latin alphabet and has a standardized form known as Bahasa Melayu.", "Malay has simple grammar with no verb conjugations for tense or subject agreement."],
    'mt': ["Maltese is a Semitic language heavily influenced by Italian and English, spoken primarily in Malta.", "It is the only Semitic language written in the Latin script and an official EU language.", "Maltese has a rich vocabulary with roots in Arabic, Sicilian, and English."],
    'my': ["Burmese is a Sino-Tibetan language and the official language of Myanmar.", "It uses a syllabic script derived from the Mon script, written from left to right.", "Burmese is a tonal and analytic language with no verb conjugations."],
    'ne': ["Nepali is an Indo-Aryan language and the official language of Nepal.", "It is written in the Devanagari script and shares linguistic roots with Hindi and Sanskrit.", "Nepali has a rich tradition of folk songs, poetry, and classical literature."],
    'nl': ["Dutch is a West Germanic language spoken mainly in the Netherlands and Belgium.", "It uses the Latin alphabet and is closely related to both German and English.", "Dutch has contributed many loanwords to other languages, especially in trade and maritime vocabulary."],
    'no': ["Norwegian is a North Germanic language spoken mainly in Norway.", "It has two official written forms: Bokmål and Nynorsk.", "Norwegian shares mutual intelligibility with Danish and Swedish."],
    'ny': ["Chichewa, also known as Chewa or Nyanja, is a Bantu language spoken in Malawi, Zambia, and Mozambique.", "It uses the Latin alphabet and has noun classes typical of Bantu languages.", "Chichewa is the national language of Malawi and is used in education and media."],
    'pa': ["Punjabi is an Indo-Aryan language spoken widely in the Punjab regions of India and Pakistan.", "It is unique among Indo-Aryan languages for being tonal.", "Punjabi is written in Gurmukhi script in India and Shahmukhi script in Pakistan."],
    'pl': ["Polish is a West Slavic language spoken mainly in Poland.", "It uses the Latin alphabet with additional diacritical marks and has complex grammar with seven cases.", "Polish is known for its consonant clusters and nasal vowel sounds."],
    'pt': ["Portuguese is a Romance language spoken in Portugal, Brazil, and several African countries.", "It uses the Latin script and has two major dialect groups: European and Brazilian Portuguese.", "Portuguese is the official language of nine countries and is one of the most spoken languages in the world."],
    'ro': ["Romanian is a Romance language that evolved from Latin spoken in ancient Dacia.", "It uses the Latin alphabet and retains many features of Latin grammar.", "Romanian is the official language of Romania and Moldova."],
    'ru': ["Russian is an East Slavic language and the most widely spoken Slavic language.", "It uses the Cyrillic script and features complex inflectional grammar.", "Russian is one of the six official languages of the United Nations."],
    'si':["Sinhala is an Indo-Aryan language spoken primarily in Sri Lanka.", "It uses the Sinhala script, which is a Brahmic abugida with rounded letters.", "Sinhala has a long literary history dating back over a thousand years."],
    'sk':["Slovak is a West Slavic language closely related to Czech and Polish.", "It uses the Latin alphabet with diacritics and has a highly inflected grammar.", "Slovak is the official language of Slovakia and one of the EU’s official languages."],
    'sl': ["Slovenian is a South Slavic language spoken mainly in Slovenia.", "It has 6 grammatical cases and dual number forms, which are rare in modern languages.", "Slovenian uses the Latin script and has a rich dialectal diversity."],
    'so': ["Somali is a Cushitic language spoken mainly in Somalia, Djibouti, and Ethiopia.", "It uses the Latin alphabet officially since 1972 and has a subject–object–verb word order.", "Somali includes influences from Arabic, Italian, and English due to historical contact."],
    'sq': ["Albanian is an independent branch of the Indo-European language family spoken primarily in Albania and Kosovo.", "It has two main dialects: Gheg in the north and Tosk in the south.", "Albanian uses the Latin alphabet and has many loanwords from Latin, Greek, and Turkish."],
    'sr': ["Serbian is a South Slavic language spoken mainly in Serbia, Bosnia and Herzegovina, and Montenegro.", "It is one of the few European languages officially written in both Cyrillic and Latin scripts.", "Serbian is mutually intelligible with Croatian, Bosnian, and Montenegrin."],
    'st': ["Sesotho, also known as Southern Sotho, is a Bantu language spoken in Lesotho and parts of South Africa.", "It uses the Latin alphabet and is one of the 11 official languages of South Africa.", "Sesotho is known for its use of noun classes and agglutinative morphology."],
    'su':["Sundanese is an Austronesian language spoken mainly in the western part of Java, Indonesia.", "It traditionally used the Javanese script but is now mostly written in the Latin alphabet.", "Sundanese has multiple speech levels to indicate formality and respect."],
    'sv': ["Swedish is a North Germanic language spoken mainly in Sweden and parts of Finland.", "It uses the Latin alphabet and is closely related to Norwegian and Danish.", "Swedish is known for its pitch accent, which distinguishes word meanings."],
    'sw':["Swahili is a Bantu language with significant Arabic influence, spoken across East Africa.", "It uses the Latin alphabet and serves as a lingua franca in many African countries.", "Swahili has simple grammar and is one of the official languages of the African Union."],
    'ta':["Tamil is a Dravidian language spoken primarily in Tamil Nadu, India, and northern Sri Lanka.", "It has its own script and is one of the longest-surviving classical languages in the world.", "Tamil has a vast literary tradition spanning over 2,000 years."],
    'te': ["Telugu is a Dravidian language spoken predominantly in the Indian states of Andhra Pradesh and Telangana.",
"It uses the Telugu script, which is derived from the Brahmi script and features rounded shapes.",
"Telugu is known as the 'Italian of the East' due to its mellifluous and vowel-rich sound."],
    'tg': ["Tajik is a variety of Persian spoken mainly in Tajikistan.",
"It is written in the Cyrillic script, unlike other Persian dialects which use the Arabic script.",
"Tajik contains many Russian loanwords due to Soviet influence."],
    'th': ["Thai is a tonal Tai-Kadai language spoken primarily in Thailand.",
"It uses an abugida script derived from Old Khmer, written left to right without spaces between words.",
"Thai grammar relies heavily on word order and particles rather than inflection."],
    'tl': ["Filipino is the standardized form of Tagalog and the national language of the Philippines.",
"It is written in the Latin alphabet and incorporates vocabulary from Spanish, English, and native languages.",
"Filipino grammar includes affixation to express verb tense, aspect, and focus."],
    'tr':["Turkish is a Turkic language spoken primarily in Turkey and Cyprus.",
"It uses the Latin alphabet and underwent a major script reform in 1928.",
"Turkish is an agglutinative language with vowel harmony and no grammatical gender."],
    'uk': ["Ukrainian is an East Slavic language spoken mainly in Ukraine.",
"It uses a variant of the Cyrillic script and is closely related to Belarusian and Russian.",
"Ukrainian features a rich system of inflection and a melodic intonation pattern."],
    'ur':["Urdu is an Indo-Aryan language spoken in Pakistan and parts of India.",
"It uses a modified Perso-Arabic script written from right to left.",
"Urdu shares grammar with Hindi but is heavily influenced by Persian and Arabic in vocabulary and script."],
    'uz':["Uzbek is a Turkic language spoken mainly in Uzbekistan and surrounding Central Asian countries.",
"It transitioned from Arabic to Latin to Cyrillic scripts and now officially uses the Latin alphabet.",
"Uzbek is an agglutinative language with vowel harmony and no grammatical gender."],
    'vi': ["Vietnamese is an Austroasiatic language spoken primarily in Vietnam.",
"It uses a Latin-based script called Quốc Ngữ with many diacritics to indicate tone and pronunciation.",
"Vietnamese has six tones and is strongly influenced by Chinese vocabulary and grammar."],
    'xh': ["Xhosa is a Bantu language spoken mainly in South Africa and is known for its click consonants.",
"It uses the Latin alphabet and has 15 click sounds borrowed from Khoisan languages.",
"Xhosa is one of South Africa’s 11 official languages and is mutually intelligible with Zulu to some extent."],
    'yi': ["Yiddish is a High German-derived language historically spoken by Ashkenazi Jews.",
"It is written in the Hebrew script and incorporates elements from German, Hebrew, Aramaic, and Slavic languages.",
"Yiddish was widely spoken in Eastern Europe before World War II and has a rich literary tradition."],
    'yo': ["Yoruba is a Niger-Congo language spoken mainly in southwestern Nigeria and neighboring countries.",
"It is written in the Latin alphabet with tone marks to indicate its three-level tonal system.",
"Yoruba has a strong oral tradition, including rich folklore, proverbs, and poetry."],
    'zu':["Zulu is a Bantu language spoken mainly in South Africa and is known for its rich system of noun classes.",
"It uses the Latin script and includes click sounds influenced by Khoisan languages.",
"Zulu is one of South Africa’s official languages and has a significant presence in media and education."]

    

    }


# Make sure UPLOAD_FOLDER is defined
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



def save_to_history(audio_path, original_text, translated_text, language_code):
    conn = sqlite3.connect('translation_history.db')
    c = conn.cursor()
    c.execute('''INSERT INTO translations 
                 (audio_path, original_text, translated_text, language_code, language_name) 
                 VALUES (?, ?, ?, ?, ?)''',
              (audio_path, original_text, translated_text, 
               language_code, LANGUAGES.get(language_code, {}).get('name', 'Unknown')))
    conn.commit()
    conn.close()
def get_history(limit=10):
    conn = sqlite3.connect('translation_history.db')
    c = conn.cursor()
    c.execute('''SELECT id, audio_path, original_text, translated_text, 
                 language_code, language_name, timestamp 
                 FROM translations ORDER BY timestamp DESC LIMIT ?''', (limit,))
    history = [{
        'id': row[0],
        'audio_path': row[1],
        'original_text': row[2],
        'translated_text': row[3],
        'language_code': row[4],
        'language_name': row[5],
        'timestamp': row[6]
    } for row in c.fetchall()]
    conn.close()
    return history

def get_language_fact(lang_code):
    """Return a random fact about the language"""
    facts = FULL_LANGUAGE_FACTS.get(lang_code, [])
    if facts:
        return random.choice(facts)
    return f"No interesting facts available about {LANGUAGES.get(lang_code, {}).get('name', 'this language')}."
def translate_text(text, target_lang):
    """Translate using Google's unofficial API with MyMemory fallback"""
    try:
        # Try Google Translate first
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "auto",
                "tl": target_lang,
                "dt": "t",
                "q": text
            },
            timeout=5
        )
        if response.status_code == 200:
            return response.json()[0][0][0]
    except:
        pass

    # Fallback to MyMemory
    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={
                "q": text,
                "langpair": f"auto|{target_lang}",
                "de": "user@example.com"  # Required field
            },
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get('responseData', {}).get('translatedText', text)
    except:
        pass

    return text  # Return original if all fail
@app.route('/api/history', methods=['GET'])
def history():
    limit = request.args.get('limit', default=10, type=int)
    return jsonify({'history': get_history(limit)})

@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Return supported languages"""
    return jsonify(LANGUAGES)

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    print("\n🔥 Received request!")  # Check terminal
    print("Files:", request.files)  # Should show your audio file
    print("Form data:", request.form)  # Should show language
    
    
    if 'audio' not in request.files and 'audio_data' not in request.form:
        return jsonify({'error': 'No audio data provided'}), 400
    
    target_language = request.form.get('language', 'en')
    if target_language not in LANGUAGES:
        return jsonify({'error': 'Unsupported language'}), 400

    # Process audio file
    if 'audio' in request.files:
        audio = request.files['audio']
        if not audio.filename:
            return jsonify({'error': 'No selected file'}), 400
        
        # Save temporarily
        filename = secure_filename(f"audio_{datetime.now().timestamp()}.wav")
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        audio.save(temp_path)
        
        # Transcribe
        result = model.transcribe(temp_path)
        os.remove(temp_path)
    
    # Process text input or base64 audio
    elif 'audio_data' in request.form:
        audio_data = request.form['audio_data']
        
        # Check if it's base64 audio
        if audio_data.startswith('data:audio'):
            try:
                import base64
                audio_bytes = base64.b64decode(audio_data.split(',')[1])
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    tmp.write(audio_bytes)
                    temp_path = tmp.name
                
                result = model.transcribe(temp_path)
                os.unlink(temp_path)
            except Exception as e:
                print(f"Error processing base64 audio: {e}")
                return jsonify({'error': 'Invalid audio data format'}), 400
        else:
            # Treat as plain text
            original_text = audio_data
            translated_text = translate_text(original_text, target_language)
            language_fact = get_language_fact(target_language)
            
            return jsonify({
                'original_text': original_text,
                'translated_text': translated_text,
                'language': target_language,
                'language_name': LANGUAGES.get(target_language, {}).get('name', 'Unknown'),
                'language_fact': language_fact,
                'audio_path': None
            })
    
    # Translate
    original_text = result['text']
    translated_text = translate_text(original_text, target_language)
    language_fact = get_language_fact(target_language)

    audio_filename = f"audio_{datetime.now().timestamp()}.wav"
    audio_path = os.path.join('uploads', audio_filename)
    os.makedirs('uploads', exist_ok=True)
    
    # For file uploads
    if 'audio' in request.files:
        request.files['audio'].save(audio_path)
    # For microphone recordings
    elif 'audio_data' in request.form and request.form['audio_data'].startswith('data:audio'):
        import base64
        audio_bytes = base64.b64decode(request.form['audio_data'].split(',')[1])
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)
    
    # Save to history
    save_to_history(
        audio_path=audio_path,
        original_text=original_text,
        translated_text=translated_text,
        language_code=target_language
    )


 
    return jsonify({
        'original_text': original_text,
        'translated_text': translated_text,
        'language': target_language,
        'language_name': LANGUAGES.get(target_language, {}).get('name', 'Unknown'),
        'language_fact': language_fact,
        'audio_path': f"/api/audio/{audio_filename}" if os.path.exists(audio_path) else None
    })
@app.route('/api/audio/<filename>', methods=['GET'])
def get_audio(filename):
    from werkzeug.utils import secure_filename
    safe_filename = secure_filename(filename)
    filepath = os.path.join('uploads', safe_filename)

    print(f"Looking for: {filepath}")  # Logs to terminal

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found', 'filename': safe_filename}), 404

    return send_from_directory('uploads', safe_filename)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
'''if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)'''
