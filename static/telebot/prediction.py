import warnings
warnings.filterwarnings(action='ignore')

import string
import inflect  # convert number into words
from tqdm import tqdm

import pandas as pd
import numpy as np

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from pydictionary import Dictionary

from sentence_transformers import SentenceTransformer, util

# # ####################################################################################
# LOADING DATA AND MODEL
embedder = SentenceTransformer('all-MiniLM-L6-v2')

df = pd.read_excel("static/datasets/final data.xlsx")
diseases = df.disease.values
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

    allowed_tags = ['NN', 'NNP', 'NNS', 'NNPS', 'ADJ', 'NNP', 'VBN', 'JJ']

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
def predict_disease(query):
    results = {}

    query = preprocess_pipe(query)
    query = get_syns(query)

    query_embedding = embedder.encode(query, convert_to_tensor=True)

    # util.semantic_search to perform cosine similarty + topk
    hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=5)
    hits = hits[0]
    for hit in hits:
        results[diseases[hit['corpus_id']]] = hit['score']

    return results


# # ####################################################################################
# FINAL
def combine_functions(queries, multi=False):
    results = []

    if multi:
        for query in queries:
            results.append(predict_disease(query))
    else:
        results.append(predict_disease(queries))

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
