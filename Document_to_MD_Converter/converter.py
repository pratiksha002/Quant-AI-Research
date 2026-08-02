import mimetypes
from markitdown import MarkItDown

class DocumentConverter:
    def __init__(self):
        self.md = MarkItDown()

    def convert_file(self, file_path):
        try:
            result = self.md.convert(file_path)
            # Return the text content instead of saving locally
            return {"status": "completed", "md_content": result.text_content}
        except Exception as e:
            return {"status": "failed", "error": str(e)}