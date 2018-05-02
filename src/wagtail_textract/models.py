import logging
import textract

from django.db import models
from wagtail.documents.models import Document as WagtailDocument
from wagtail.search import index

from .signals import document_saved

logger = logging.getLogger(__name__)


class Document(WagtailDocument):
    """Extra fields and methods for Document model."""
    transcription = models.TextField(null=True)
    search_fields = WagtailDocument.search_fields + [
        index.SearchField(
            'transcription',
            partial_match=False,
        ),
    ]

    def transcribe(self):
        """Extract text from file."""
        try:
            text = textract.process(self.file.path)
        except Exception as err:
            text = None
            logger.error(
                'Text extraction error with file {file}: {message}'.format(
                    file=self.filename,
                    message=str(err),
                )
            )

        if text:
            self.transcription = text.decode()
            # Call super() to prevent sending document_saved signal
            super(Document, self).save()
            logger.info("Saved transcription: %s" % text)
            print("Saved transcription: %s" % text)

    def save(self, **kwargs):
        """Send the document_saved signal."""
        super(Document, self).save(**kwargs)
        document_saved.send(sender=self.__class__, instance=self)
