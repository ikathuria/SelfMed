import re
import csv
import pdb
import h5py
import json
import string
import inflect  # convert number into words
import pickle
import tarfile
import itertools
from functools import reduce
from tqdm import tqdm

import pandas as pd
import numpy as np

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

import tensorflow as tf
from keras.models import load_model
import transformers
from sklearn.metrics.pairwise import cosine_similarity


# # ####################################################################################
# CONFIGURATION

max_length = 128  # Maximum length of input sentence to the model.
batch_size = 32
epochs = 3

# Labels in our dataset.
labels = ["contradiction", "entailment", "neutral"]

# # ####################################################################################
bert_model = transformers.TFBertModel.from_pretrained("bert-base-uncased")
model = load_model('nov1_backup.h5')


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

    nouns = [word for word, pos in tags if (
        pos == 'NN' or pos == 'NNP' or pos == 'NNS' or pos == 'NNPS' or pos == 'ADJ'
    )]

    filtered_text = [word for word in nouns if word not in stop_words]

    lemmas = [lemmatizer.lemmatize(word, pos='v') for word in filtered_text]

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
# DATA GENERATOR
class BertSemanticDataGenerator(tf.keras.utils.Sequence):
    """Generates batches of data.

    Args:
        sentence_pairs: Array of premise and hypothesis input sentences.
        labels: Array of labels.
        batch_size: Integer batch size.
        shuffle: boolean, whether to shuffle the data.
        include_targets: boolean, whether to incude the labels.

    Returns:
        Tuples `([input_ids, attention_mask, `token_type_ids], labels)`
        (or just `[input_ids, attention_mask, `token_type_ids]`
         if `include_targets=False`)
    """

    def __init__(
        self,
        sentence_pairs,
        labels,
        batch_size=batch_size,
        shuffle=True,
        include_targets=True,
    ):
        self.sentence_pairs = sentence_pairs
        self.labels = labels
        self.shuffle = shuffle
        self.batch_size = batch_size
        self.include_targets = include_targets

        # Loading BERT Tokenizer to encode the text.
        # The bert-base-uncased pretrained model is used.
        self.tokenizer = transformers.BertTokenizer.from_pretrained(
            "bert-base-uncased", do_lower_case=True
        )
        self.indexes = np.arange(len(self.sentence_pairs))
        self.on_epoch_end()

    def __len__(self):
        """Denotes the number of batches per epoch."""
        return len(self.sentence_pairs) // self.batch_size

    def __getitem__(self, idx):
        """Retrieves the batch of index."""
        indexes = self.indexes[idx *
                               self.batch_size: (idx + 1) * self.batch_size]
        sentence_pairs = self.sentence_pairs[indexes]

        # With BERT tokenizer's batch_encode_plus batch of both the sentences are
        # encoded together and separated by [SEP] token.
        encoded = self.tokenizer.batch_encode_plus(
            sentence_pairs.tolist(),
            add_special_tokens=True,
            max_length=max_length,
            return_attention_mask=True,
            return_token_type_ids=True,
            pad_to_max_length=True,
            return_tensors="tf",
        )

        # Convert batch of encoded features to numpy array.
        input_ids = np.array(encoded["input_ids"], dtype="int32")
        attention_masks = np.array(encoded["attention_mask"], dtype="int32")
        token_type_ids = np.array(encoded["token_type_ids"], dtype="int32")

        # Set to true if data generator is used for training/validation.
        if self.include_targets:
            labels = np.array(self.labels[indexes], dtype="int32")
            return [input_ids, attention_masks, token_type_ids], labels
        else:
            return [input_ids, attention_masks, token_type_ids]

    def on_epoch_end(self):
        """Shuffle indexes after each epoch if shuffle is set to True."""
        if self.shuffle:
            np.random.RandomState(42).shuffle(self.indexes)


def check_similarity(sentence1, sentence2):
    sentence_pairs = np.array([[str(sentence1), str(sentence2)]])
    test_data = BertSemanticDataGenerator(
        sentence_pairs, labels=None, batch_size=1, shuffle=False, include_targets=False,
    )

    proba = model.predict(test_data[0])[0]
    idx = np.argmax(proba)
    proba = f"{proba[idx]: .2f}%"
    pred = labels[idx]
    return pred, proba


def predict_disease(query, dis_dict):
    scores = {}
    for key, val in tqdm(dis_dict.items(), desc="scoring items"):
        scores[key] = check_similarity(val, query)

    entails = {}
    neutrals = {}
    for key, val in scores.items():
        if val[0] == 'entailment':
            entails[key] = val

        if val[0] == 'neutral':
            neutrals[key] = val

    entails = dict(
        sorted(entails.items(), key=lambda item: item[1][1], reverse=True))
    neutrals = dict(
        sorted(neutrals.items(), key=lambda item: item[1][1], reverse=True))

    if len(entails) == 0:
        return list(neutrals.keys())
    return list(entails.keys())

