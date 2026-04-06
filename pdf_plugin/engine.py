from __future__ import annotations

import logging
from io import BytesIO
from typing import Dict

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject
except ImportError:
    raise ImportError("pypdf is required. Install it with: pip install pypdf")

logger = logging.getLogger(__name__)


class PDFFormEngine:
    """
    Engine for filling PDF AcroForm fields.
    """

    def __init__(self, pdf_path):
        """
        Initialize with a PDF file path (Path object or string).
        """
        self.pdf_path = pdf_path
        self.reader = PdfReader(str(pdf_path))

    @staticmethod
    def list_fields(pdf_path):
        """
        List all AcroForm field names in the PDF.
        Returns a list of field name strings.
        """
        try:
            reader = PdfReader(str(pdf_path))
            if "/AcroForm" not in reader.trailer["/Root"]:
                return []

            fields = []
            if "/Fields" in reader.trailer["/Root"]["/AcroForm"]:
                for field in reader.trailer["/Root"]["/AcroForm"]["/Fields"]:
                    field_obj = field.get_object()
                    if "/T" in field_obj:
                        fields.append(field_obj["/T"])
                    elif "/Kids" in field_obj:
                        # Handle nested fields
                        for kid in field_obj["/Kids"]:
                            kid_obj = kid.get_object()
                            if "/T" in kid_obj:
                                fields.append(kid_obj["/T"])

            return fields
        except Exception as e:
            logger.exception(f"Error listing PDF fields: {e}")
            return []

    def render(self, field_values: Dict[str, str], *, flatten: bool = False) -> bytes:
        """
        Fill the PDF form with the provided field values.

        Args:
            field_values: Dictionary mapping PDF field names to string values
            flatten: If True, attempt to remove form fields after filling

        Returns:
            bytes: The filled PDF as bytes

        Raises:
            ValueError: If PDF does not contain AcroForm (not a fillable form)
        """
        # Check if PDF has AcroForm
        root = self.reader.trailer.get("/Root", {})
        if "/AcroForm" not in root:
            raise ValueError(
                "This PDF does not contain fillable form fields (AcroForm). "
                "Please upload a PDF with form fields enabled."
            )

        # List actual fields in PDF (for logging/debugging if needed)
        self.list_fields(self.pdf_path)

        writer = PdfWriter()

        # Clone the document to preserve AcroForm structure properly
        writer.clone_document_from_reader(self.reader)

        # CRITICAL: Set need_appearances BEFORE filling fields
        writer.set_need_appearances_writer(True)

        # Fill form fields using update_page_form_field_values (handles appearance streams correctly)
        if field_values:
            # Update fields on all pages (form fields can span multiple pages)
            for page_num in range(len(writer.pages)):
                try:
                    # Try using built-in flatten parameter if available (pypdf 3.x+)
                    writer.update_page_form_field_values(
                        writer.pages[page_num], 
                        field_values,
                        auto_regenerate=False  # Don't auto-regenerate, we'll do it manually
                    )
                except TypeError:
                    # Fallback for older pypdf versions
                    writer.update_page_form_field_values(writer.pages[page_num], field_values)

        # Write to buffer
        out = BytesIO()
        writer.write(out)

        if not flatten:
            return out.getvalue()

        # Flatten: Remove form fields while preserving visual appearance
        # WARNING: pypdf doesn't automatically generate appearance streams
        # Without appearance streams, values may not be visible after removing fields
        # This is a limitation of pypdf - proper flatten requires explicit appearance stream generation
        filled = out.getvalue()
        reader2 = PdfReader(BytesIO(filled))
        writer2 = PdfWriter()
        writer2.clone_document_from_reader(reader2)
        writer2.set_need_appearances_writer(True)

        # Remove widget annotations (form fields) from all pages
        # This removes the interactive fields but may also remove their visual appearance
        # if appearance streams weren't generated
        for page in writer2.pages:
            annots = page.get("/Annots")
            if annots:
                kept = []
                for a in annots:
                    obj = a.get_object()
                    # Remove widget annotations (form fields)
                    if obj.get("/Subtype") != NameObject("/Widget"):
                        kept.append(a)
                if kept:
                    page["/Annots"] = kept
                else:
                    try:
                        del page["/Annots"]
                    except Exception:
                        pass

        # Remove AcroForm structure
        try:
            root = writer2._root_object
            if "/AcroForm" in root:
                del root["/AcroForm"]
        except Exception:
            pass

        out2 = BytesIO()
        writer2.write(out2)
        return out2.getvalue()
