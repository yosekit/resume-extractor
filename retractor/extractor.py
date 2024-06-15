import os
import re
import pandas as pd
from collections import Counter

from spacy.tokens.doc import Doc
from spacy.tokens.span import Span
from spacy.matcher import Matcher

from . import constants as cs


class ResumeExtractor(object):
    def __init__(self) -> None:
        pass

    def entities(self, ner_doc: Doc) -> dict[str]:
        """
        Extract different entities with custom
        trained model using SpaCy's NER

        :return: dictionary of entities
        """
        
        entities = {}

        for ent in ner_doc.ents:
            if ent.label_ not in entities.keys():
                entities[ent.label_] = [ent.text]
            else:
                entities[ent.label_].append(ent.text)

        for key in entities.keys():
            entities[key] = list(set(entities[key]))

        return entities
    
    def entities_sections(self, text: str) -> dict[str]:
        """
        Extract all the raw text from sections of
        resumes specifically for graduates and undergraduates

        :return: dictionary of entities
        """

        text_split = [i.strip() for i in text.split('\n')]
        entities = {}
        curr_section = False
        for phrase in text_split:
            sections = set(phrase.lower().split()) & set(cs.RESUME_SECTIONS_GRAD)

            try:
                section = list(sections)[0]

                entities[section] = []
                curr_section = section
            except IndexError:
                pass
            
            if curr_section and phrase.strip():
                entities[curr_section].append(phrase)

        return entities

    def name(self, doc: Doc, matcher: Matcher) -> str:
        """
        Extract name from spacy nlp text

        :return: string of full name
        """
        
        pattern = [cs.NAME_PATTERN]

        matcher.add('NAME', pattern)

        matches = matcher(doc)

        for _, start, end in matches:
            span = doc[start:end]
            if 'name' not in span.text.lower():
                return span.text
            
    def email(self, text: str) -> str:
        """
        Extract email from text

        :return: email string
        """

        email = re.findall(r"([^@|\s]+@[^@]+\.[^@|\s]+)", text)
        if email:
            try:
                return email[0].split()[0].strip(';')
            except IndexError:
                return None
            
    def mobile_number(self, text: str) -> str:
        """
        Extract mobile number from text

        :return: string of extracted mobile numbers
        """

        regex = r'''(\(?\d{3}\)?[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)
                                [-\.\s]*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})'''
        
        phone = re.findall(re.compile(regex), text)
        if phone:
            number = ''.join(phone[0])
            return number
    
    def skills(self, doc: Doc, noun_chunks: list[Span], skills_file: str) -> list[str]:
        """
        Extract skills from spacy nlp text

        :return: list of skills extracted
        """

        data = pd.read_csv(os.path.join(os.path.dirname(__file__), skills_file))
        skills_set = set(data.columns.str.lower())

        skill_counter = Counter()

        # Check for one-grams
        for token in doc:
            if not token.is_stop and token.text.lower() in skills_set:
                skill_counter[token.text.lower()] += 1

        # Check for bi-grams and tri-grams
        for chunk in noun_chunks:
            chunk_text = chunk.text.lower().strip()
            if chunk_text in skills_set:
                skill_counter[chunk_text] += 1

        # Sort skills by frequency
        sorted_skills = [
            skill.capitalize() for skill, count in skill_counter.most_common()]
        

        return sorted_skills
    
    
    def education_level(self, doc: Doc) -> list[str]:
        """
        Extract education level from spacy nlp text

        return: list of extracted education levels
        """

        sents = [sent.text.strip() for sent in doc.sents]

        edu = {}
        # Extract education degree
        try:
            for index, text in enumerate(sents):
                for string in text.split():
                    if string.upper() in cs.EDUCATION and string not in cs.STOPWORDS:
                        edu[string] = text + sents[index + 1]
        except IndexError:
            pass

        return [key for key in edu.keys()]
