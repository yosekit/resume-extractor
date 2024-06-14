import html
import json
import logging
import os
import re

from tqdm import tqdm

import spacy
from spacy.util import filter_spans
from spacy.tokens import DocBin

from sklearn.model_selection import train_test_split


logging.basicConfig(level=logging.INFO)


def trim_entity_spans(data: list) -> list:
    invalid_span_tokens = re.compile(r'\s')

    cleaned_data = []
    for text, annotations in data:
        entities = annotations['entities']
        valid_entities = []
        for start, end, label in entities:
            valid_start = start
            valid_end = end
            while valid_start < valid_end and invalid_span_tokens.match(
                    text[valid_start]):
                valid_start += 1
            while valid_end > valid_start and invalid_span_tokens.match(
                    text[valid_end - 1]):
                valid_end -= 1
            if valid_start == valid_end:
                continue
            valid_entities.append([valid_start, valid_end, label])
        cleaned_data.append([text, {'entities': valid_entities}])
    return cleaned_data


def convert_dataturks_to_spacy(file_json: str) -> list:
    try:
        train_data = []
        with open(file_json, 'r', encoding="utf8") as file:
            lines = file.readlines()

        for line in lines:
            data = json.loads(line)
            text = html.unescape(data['content'])
            entities = []
            if data['annotation'] is not None:
                for annotation in data['annotation']:
                    point = annotation['points'][0]
                    label = annotation['label'][0]

                    # dataturks ставит индексы оба вкл. [start, end]
                    # но в spacy последний искл. [start, end)
                    entities.append((
                        point['start'],
                        point['end'] + 1,
                        label
                    ))

            train_data.append((text, {"entities": entities}))
        return train_data
    except Exception:
        logging.exception("Unable to process " + file_json)
        return None


def save_as_spacy_corpus(data: list, dest: str = '', dev_size: float = 0.20) -> list:
    os.makedirs(dest, exist_ok=True)

    nlp = spacy.load('en_core_web_sm')

    db_train = DocBin()
    db_dev = DocBin()
    docs = []

    for text, entities in tqdm(data, desc='Processing resumes'):
        spans = []
        doc = nlp(text)
        for start, end, label in entities['entities']:
            span = doc.char_span(start, end, label)
            if span is None:
                continue
            spans.append(doc.char_span(start, end, label))

        doc.set_ents(filter_spans(spans))
        docs.append(doc)

    train, dev, _, _ = train_test_split(docs, docs, shuffle=True, test_size=dev_size)

    for doc in train:
        db_train.add(doc)

    for doc in dev:
        db_dev.add(doc)
        
    db_train.to_disk(os.path.join(dest, f'train.spacy'))
    db_dev.to_disk(os.path.join(dest, f'dev.spacy'))


def get_train_data(path: str = "./resumes/traindata.json"):
    return trim_entity_spans(convert_dataturks_to_spacy(path))
    

if __name__ == "__main__":
    logging.info('Loading Dataturks dataset...')

    data = get_train_data(os.path.join(os.path.dirname(__file__), 'resumes/traindata.json'))
    save_as_spacy_corpus(data, dest=os.path.join(os.path.dirname(__file__), 'resumes/data'))
