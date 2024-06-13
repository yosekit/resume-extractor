import os
import io
from typing import Generator

import textract
import docx2txt

from pdfminer.converter import TextConverter as PDFTextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams as PDFLAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFSyntaxError


class TextReader(object):
    def __init__(self) -> None:
        pass

    def read(self, file_path: str) -> str:
        if not isinstance(file_path, io.BytesIO):
            extension = os.path.splitext(file_path)[1].split('.')[1]
        else:
            extension = file_path.name.split('.')[1]

        match extension:
            case 'txt':
                return self.from_txt(file_path)
            case 'pdf':
                return self.from_pdf(file_path)
            case 'docx':
                return self.from_docx(file_path)
            case 'doc':
                return self.from_doc(file_path)
            case _:
                return ''

    def from_txt(self, txt_path: str) -> str:
        with open(txt_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        return text

    def from_pdf(self, pdf_path: str) -> str:
        return ' '.join(page_text for page_text in self.__from_pdf(pdf_path))

    def __from_pdf(self, pdf_path: str) -> Generator[str, None, None]:
        if not isinstance(pdf_path, io.BytesIO):
            # from local pdf file
            with open(pdf_path, 'rb') as file:
                try:
                    for page in PDFPage.get_pages(
                            file,
                            caching=True,
                            check_extractable=True
                    ):
                        resource_manager = PDFResourceManager()
                        fake_file_handle = io.StringIO()
                        converter = PDFTextConverter(
                            resource_manager,
                            fake_file_handle,
                            codec='utf-8',
                            laparams=PDFLAParams()
                        )
                        page_interpreter = PDFPageInterpreter(
                            resource_manager,
                            converter
                        )
                        page_interpreter.process_page(page)

                        text = fake_file_handle.getvalue()
                        yield text

                        converter.close()
                        fake_file_handle.close()
                except PDFSyntaxError:
                    return
        else:
            # from remote pdf file
            try:
                for page in PDFPage.get_pages(
                        pdf_path,
                        caching=True,
                        check_extractable=True
                ):
                    resource_manager = PDFResourceManager()
                    fake_file_handle = io.StringIO()
                    converter = PDFTextConverter(
                        resource_manager,
                        fake_file_handle,
                        # codec='utf-8',
                        laparams=PDFLAParams()
                    )
                    page_interpreter = PDFPageInterpreter(
                        resource_manager,
                        converter
                    )
                    page_interpreter.process_page(page)

                    text = fake_file_handle.getvalue()
                    yield text

                    converter.close()
                    fake_file_handle.close()
            except PDFSyntaxError:
                return

    def from_docx(self, doc_path: str) -> str:
        try:
            temp = docx2txt.process(doc_path)
            text = [line.replace('\t', ' ') for line in temp.split('\n') if line]
            return ' '.join(text)
        except KeyError:
            return ' '

    def from_doc(self, doc_path: str) -> str:
        try:
            text = textract.process(doc_path).decode('utf-8')
            return text
        except KeyError:
            return ' '
    
    def pages_count(self, file_name: str) -> int:
        try:
            if isinstance(file_name, io.BytesIO):
                # for remote pdf file
                count = 0
                for page in PDFPage.get_pages(
                        file_name,
                        caching=True,
                        check_extractable=True
                ):
                    count += 1
                return count
            else:
                # for local pdf file
                if file_name.endswith('.pdf'):
                    count = 0
                    with open(file_name, 'rb') as file:
                        for page in PDFPage.get_pages(
                                file,
                                caching=True,
                                check_extractable=True
                        ):
                            count += 1
                    return count
                else:
                    return None
        except PDFSyntaxError:
            return None