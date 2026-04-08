from __future__ import annotations

import importlib
import os
import re
from datetime import datetime
from decimal import Decimal

from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone

from .models import IDScanField, IDScanGroup, IDScanRecord


class ScanProcessingError(Exception):
    pass


class ScanDependencyError(ScanProcessingError):
    pass


def process_record(record: IDScanRecord) -> IDScanRecord:
    cv2, np, pytesseract = _import_dependencies()
    image = _decode_image(record, cv2, np)
    group = record.group
    template = record.template

    if not group or not template:
        raise ScanProcessingError("A scan group and template are required.")

    if group.remove_background_enabled or group.level_perspective_enabled:
        warped = _warp_document(image, cv2, np, template.target_width, template.target_height)
        if warped is not None:
            image = warped
            _save_array_to_image_field(record, "warped_image", image, "warped", cv2)

    processed = _preprocess_image(image, group, cv2, np)
    _save_array_to_image_field(record, "processed_image", processed, "processed", cv2)

    raw_ocr_text = {}
    extracted_data = {}
    required_total = 0
    required_valid = 0

    for field in template.fields.all():
        crop = _crop_field(processed, field, group)
        text = _read_text(crop, field, group, cv2, pytesseract)
        normalized_value, valid, errors = _normalize_and_validate(
            text,
            field,
            template.accepted_date_input_formats,
            group,
        )
        raw_ocr_text[field.key] = text
        extracted_data[field.key] = {
            "label": field.label,
            "value": normalized_value,
            "raw_text": text,
            "valid": valid,
            "errors": errors,
        }
        if field.required:
            required_total += 1
            if valid and normalized_value:
                required_valid += 1

    confidence_score = Decimal("100.00")
    if required_total:
        confidence_score = (Decimal(required_valid) / Decimal(required_total)) * Decimal("100")
        confidence_score = confidence_score.quantize(Decimal("0.01"))

    record.raw_ocr_text = raw_ocr_text
    record.extracted_data = extracted_data
    record.confidence_score = confidence_score
    record.status = IDScanRecord.STATUS_SUCCESS
    record.error_message = ""
    record.processed_at = timezone.now()
    record.save()
    return record


def _import_dependencies():
    missing = []
    loaded = {}
    for module_name in ("cv2", "numpy", "pytesseract"):
        try:
            loaded[module_name] = importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)
    if missing:
        missing_text = ", ".join(missing)
        raise ScanDependencyError(
            f"Missing OCR dependencies: {missing_text}. Install opencv-python, numpy, and pytesseract, and make sure the Tesseract binary is available on the server."
        )
    tesseract_cmd = getattr(settings, "TESSERACT_CMD", "").strip()
    if tesseract_cmd:
        loaded["pytesseract"].pytesseract.tesseract_cmd = tesseract_cmd
    _verify_tesseract_binary(loaded["pytesseract"])
    return loaded["cv2"], loaded["numpy"], loaded["pytesseract"]


def _verify_tesseract_binary(pytesseract):
    tesseract_cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "").strip()
    looks_like_path = os.path.sep in tesseract_cmd or (os.path.altsep and os.path.altsep in tesseract_cmd)
    if looks_like_path and not os.path.exists(tesseract_cmd):
        raise ScanDependencyError(
            f"Tesseract binary not found at '{tesseract_cmd}'. Install Tesseract on the server or set TESSERACT_CMD to the correct executable path."
        )
    try:
        pytesseract.get_tesseract_version()
    except (FileNotFoundError, pytesseract.pytesseract.TesseractNotFoundError):
        location_hint = f" at '{tesseract_cmd}'" if tesseract_cmd else ""
        raise ScanDependencyError(
            "Tesseract OCR is not available"
            f"{location_hint}. Install the Tesseract binary on the server and make sure TESSERACT_CMD points to it."
        ) from None


def _decode_image(record: IDScanRecord, cv2, np):
    record.source_image.open("rb")
    raw_bytes = record.source_image.read()
    image_array = np.frombuffer(raw_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ScanProcessingError("Unable to decode the uploaded image.")
    return image


def _preprocess_image(image, group: IDScanGroup, cv2, np):
    current = image.copy()

    if group.grayscale_enabled and len(current.shape) == 3:
        current = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)

    if group.upscale_enabled:
        current = cv2.resize(
            current,
            None,
            fx=float(group.scale_factor),
            fy=float(group.scale_factor),
            interpolation=cv2.INTER_CUBIC,
        )

    if group.deskew_enabled:
        current = _deskew(current, cv2, np)

    if group.noise_removal_enabled:
        current = cv2.GaussianBlur(current, (5, 5), 0)

    if group.binarize_enabled:
        if len(current.shape) == 3:
            current = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
        if group.threshold_mode == IDScanGroup.THRESHOLD_OTSU:
            _, current = cv2.threshold(current, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            current = cv2.adaptiveThreshold(
                current,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                11,
            )

    return current


def _deskew(image, cv2, np):
    gray = image
    if len(gray.shape) == 3:
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    coordinates = np.column_stack(np.where(thresh > 0))
    if len(coordinates) == 0:
        return image

    angle = cv2.minAreaRect(coordinates)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.1:
        return image

    (height, width) = image.shape[:2]
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def _warp_document(image, cv2, np, target_width: int, target_height: int):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)
    contours = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:8]

    screen_contour = None
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approx) == 4:
            screen_contour = approx.reshape(4, 2)
            break

    if screen_contour is None:
        return None

    rect = _order_points(screen_contour, np)
    destination = np.array(
        [
            [0, 0],
            [target_width - 1, 0],
            [target_width - 1, target_height - 1],
            [0, target_height - 1],
        ],
        dtype="float32",
    )
    matrix = cv2.getPerspectiveTransform(rect, destination)
    return cv2.warpPerspective(image, matrix, (target_width, target_height))


def _order_points(points, np):
    rect = np.zeros((4, 2), dtype="float32")
    sums = points.sum(axis=1)
    rect[0] = points[np.argmin(sums)]
    rect[2] = points[np.argmax(sums)]

    diffs = np.diff(points, axis=1)
    rect[1] = points[np.argmin(diffs)]
    rect[3] = points[np.argmax(diffs)]
    return rect


def _crop_field(image, field: IDScanField, group: IDScanGroup):
    if not group.isolate_roi_enabled:
        return image

    height, width = image.shape[:2]
    left = int(float(field.roi_left) * width)
    top = int(float(field.roi_top) * height)
    crop_width = int(float(field.roi_width) * width)
    crop_height = int(float(field.roi_height) * height)
    right = min(width, left + crop_width)
    bottom = min(height, top + crop_height)

    if right <= left or bottom <= top:
        return image
    return image[top:bottom, left:right]


def _read_text(crop, field: IDScanField, group: IDScanGroup, cv2, pytesseract):
    if crop is None or crop.size == 0:
        return ""

    config = _build_tesseract_config(field, group)

    if len(crop.shape) == 2:
        image_for_ocr = crop
    else:
        image_for_ocr = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    try:
        return pytesseract.image_to_string(image_for_ocr, config=config).strip()
    except pytesseract.pytesseract.TesseractNotFoundError as exc:
        raise ScanDependencyError(
            "Tesseract OCR is not available to the scanner. Install the Tesseract binary on the server and verify TESSERACT_CMD."
        ) from exc
    except pytesseract.pytesseract.TesseractError as exc:
        raise ScanProcessingError(f"Tesseract OCR failed: {exc}") from exc


def _build_tesseract_config(field: IDScanField, group: IDScanGroup) -> str:
    config_parts = []
    if group.optimize_ocr_enabled:
        config_parts.append("--oem 3")
    if group.apply_psm_enabled:
        config_parts.append(f"--psm {field.psm or group.default_psm}")

    whitelist = field.whitelist or group.default_whitelist
    if group.apply_whitelist_enabled and whitelist:
        safe_whitelist = whitelist.replace("\\", "\\\\").replace('"', '\\"')
        config_parts.append(f'-c tessedit_char_whitelist="{safe_whitelist}"')

    return " ".join(config_parts).strip()


def _normalize_and_validate(raw_text: str, field: IDScanField, accepted_date_formats: str, group: IDScanGroup):
    value = (raw_text or "").strip()
    if field.normalize_whitespace:
        value = re.sub(r"\s+", " ", value).strip()

    errors = []

    if group.post_process_enabled and field.validation_regex:
        match = re.search(field.validation_regex, value)
        if match:
            value = match.group(0).strip()

    if group.data_validation_enabled:
        if field.field_type in {IDScanField.FIELD_DOB, IDScanField.FIELD_EXPIRY} and value:
            value, date_error = _normalize_date(value, accepted_date_formats)
            if date_error:
                errors.append(date_error)

        if field.expected_length and value:
            compact_value = re.sub(r"[^A-Za-z0-9]", "", value)
            if len(compact_value) != field.expected_length:
                errors.append(f"Expected {field.expected_length} characters.")

        if field.validation_regex and value and not re.search(field.validation_regex, value):
            errors.append("Value did not match the expected pattern.")

    if field.required and not value:
        errors.append("This field is required.")

    return value, len(errors) == 0, errors


def _normalize_date(value: str, accepted_date_formats: str):
    raw_formats = [item.strip() for item in accepted_date_formats.split(",") if item.strip()]
    cleaned_value = value.replace(".", "/").replace("-", "/")
    for input_format in raw_formats:
        format_to_try = input_format.replace("-", "/").replace(" ", "/")
        try:
            parsed = datetime.strptime(cleaned_value, format_to_try)
            return parsed.strftime("%m/%d/%Y"), ""
        except ValueError:
            continue
    return value, "Date does not match the accepted formats."


def _save_array_to_image_field(record: IDScanRecord, field_name: str, image, suffix: str, cv2):
    ok, buffer = cv2.imencode(".png", image)
    if not ok:
        raise ScanProcessingError(f"Could not encode the {suffix} image.")
    filename = f"scan_{record.pk}_{suffix}.png"
    getattr(record, field_name).save(filename, ContentFile(buffer.tobytes()), save=False)
