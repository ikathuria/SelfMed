import warnings
warnings.filterwarnings(action='ignore')

from googletrans import Translator
translator = Translator()

import re
import string
import inflect  # convert number into words

import pandas as pd

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from pydictionary import Dictionary

from sentence_transformers import SentenceTransformer, util

# # ####################################################################################
# LOADING DATA AND MODEL
global df
global diseases
global remedies

embedder = SentenceTransformer('all-MiniLM-L6-v2')
eng_hi = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

df = pd.read_excel("static/final_data.xlsx")
remedies = df.remedies.to_list()
diseases = df.disease.to_list()
diseases_overview = df.overview.values
diseases_symptoms = df.symptoms.values

corpus = []
for o, s in zip(diseases_overview, diseases_symptoms):
    try:
        temp = o.replace("\n", " ") + s.replace("\n", ", ")
        corpus.append(temp)
    except:
        corpus.append(o.replace("\n", " "))

corpus_embeddings = embedder.encode(corpus, convert_to_tensor=True)

# # ####################################################################################
# NLP PREPROCESSING

def text_lowercase(text):
    """Make the test lowercase.

    Args:
        text (str) : input string.

    Returns:
        lowercased input string.
    """
    return text.lower()


def convert_number(text):
    """Convert digits to words.

    Args:
        text (str) : input string.

    Returns:
        converted input string.
    """
    p = inflect.engine()
    temp_str = text.split()

    new_string = []

    for word in temp_str:
        if word.isdigit():
            temp = p.number_to_words(word)
            new_string.append(temp)

        else:
            new_string.append(word)

    temp_str = ' '.join(new_string)
    return temp_str


def remove_punctuation(text):
    """Remove all punctuation.

    Args:
        text (str) : input string.

    Returns:
        lowercased input string.
    """
    text = text.replace('_', ' ')
    translator = str.maketrans('', '', string.punctuation)
    return text.translate(translator)


def remove_whitespace(text):
    return " ".join(text.split())


def stopwords_pos_lematize(text):
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))
    word_tokens = word_tokenize(text)
    tags = nltk.pos_tag(word_tokens)

    allowed_tags = [
        'NN', 'NNP', 'NNS', 'NNP', 'NNPS',
        'ADJ', 'JJ', 'VBN',
    ]

    nouns = [word for word, pos in tags if pos in allowed_tags]

    filtered_text = [word for word in nouns if word not in stop_words]

    lemmas = [lemmatizer.lemmatize(word) for word in filtered_text]

    return " ".join(lemmas)


def preprocess_pipe(text):
    """
    Combining all preprocessing steps.
    """
    text = text_lowercase(text)
    text = convert_number(text)
    text = remove_punctuation(text)
    text = remove_whitespace(text)
    text = stopwords_pos_lematize(text)

    return text


# # ####################################################################################
# URL
def check_url(text):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

    if re.findall(regex, text) != []:
        return True
    return False


def is_hindi(character):
    maxchar = max(character)
    if u'\u0900' <= maxchar <= u'\u097f':
        return True
    else:
      return False


def eng2hi(sentence):
    return translator.translate(sentence, dest="hi").text


# # ####################################################################################
# GET SYNONYMS
def get_syns(text):
    res = ""
    for word in text.split(" "):
        new_instance = Dictionary(word)
        new_instance = new_instance.synonyms()
        res += (" " + word + " " + " ".join(new_instance))

    return res


# # ####################################################################################
# PREDICTION MODEL
def predict_disease(query, hin=False):
    results = {}

    if not hin:
        query = preprocess_pipe(query)
        query = get_syns(query)

        query_embedding = embedder.encode(query, convert_to_tensor=True)
    else:
        query_embedding = eng_hi.encode(query, convert_to_tensor=True)

    # util.semantic_search to perform cosine similarty + topk
    hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=5)
    hits = hits[0]
    for hit in hits:
        results[diseases[hit['corpus_id']]] = hit['score']

    results['none of the above'] = 0

    return results


# # ####################################################################################
# FINAL
def combine_functions(queries, hin=False, multi=False):
    results = []

    if multi:
        for query in queries:
            results.append(predict_disease(query, hin))
    else:
        results.append(predict_disease(queries, hin))

    return results


# print(combine_functions(
#     [
#         "i have nausea and sore throat",
#         "i have flaky scalp and head is itching",
#         "i have sore throat and cough with fever",
#         "i have hair loss",
#         "i have sting",
#     ],
#     multi=True
# ))
