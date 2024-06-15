import os
import timeit

import spacy
from spacy.matcher import Matcher

from . import utils

from .extractor import ResumeExtractor
from .reader import TextReader


curr_dir = os.path.dirname(os.path.abspath(__file__))

class ResumeParser(object):
    def __init__(self, skills_file: str=None) -> None:

        print('Spacy model is loading...')
        self.__nlp = spacy.load('en_core_web_sm')
        self.__resume_nlp = spacy.load(os.path.join(curr_dir, 'models', 'res_model'))

        self.__skills_file = skills_file if skills_file is not None else 'skills.csv'

        self.__matcher = Matcher(self.__nlp.vocab)
        self.__reader = TextReader()
        self.__extractor = ResumeExtractor()

    def parse(self, resume: str) -> dict[str]:
        resume_path = None

        if os.path.isfile(resume):
            resume_path = resume
            text_raw = self.__reader.read(resume_path)
        else:
            text_raw = resume

        text_raw = utils.clean_text(text_raw)
        text = ' '.join(text_raw.split())

        doc = self.__nlp(text)
        resume_doc = self.__resume_nlp(text_raw)

        noun_chunks = list(doc.noun_chunks)
        
        entities = self.__extractor.entities(resume_doc)

        name = self.__extractor.name(doc, self.__matcher)
        skills = self.__extractor.skills(doc, noun_chunks, self.__skills_file)

        education_level = self.__extractor.education_level(doc)

        email = self.__extractor.email(text)
        mobile = self.__extractor.mobile_number(text)

        section_entities = self.__extractor.entities_sections(text_raw)

        details = {
            'name': None,
            'email': None,
            'mobile_number': None,
            'skills': None,
            'skills_entities': None,
            'education_level': None,
            'education': None,
            'college_name': None,
            'degree': None,
            'designation': None,
            'experience': None,
            'company_names': None,
            'total_experience': None,
            'no_of_pages': None,
        }

        details['email'] = email

        details['mobile_number'] = mobile

        details['skills'] = skills

        details['eductaion_level'] = education_level

        try:
            details['name'] = entities['Name'][0]
        except (IndexError, KeyError):
            details['name'] = name

        try:
            details['links'] = entities['Links']
        except KeyError:
            pass

        try:
            details['skills_entities'] = entities['Skills']
        except KeyError:
            pass

        try:
            details['college_name'] = entities['College Name']
        except KeyError:
            pass

        try:
            details['degree'] = entities['Degree']
        except KeyError:
            pass

        try:
            details['designation'] = entities['Designation']
        except KeyError:
            pass

        try:
            details['company_names'] = entities['Companies worked at']
        except KeyError:
            pass

        try:
            details['eductaion'] = section_entities['education']
        except KeyError:
            pass

        try:
            details['experience'] = section_entities['experience']
            try:
                exp = round(
                    utils.get_total_experience(section_entities['experience']) / 12,
                    2
                )
            except KeyError:
                exp = 0
        except KeyError:
            exp = 0
        details['total_experience'] = exp

        if resume_path is not None:
            details['no_of_pages'] = self.__reader.pages_count(resume_path)

        return details
