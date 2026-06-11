import base64
from .pdf_loader import FITZ_AVAILABLE

try:
    import fitz
except ImportError:
    fitz = None

MIN_IMAGE_W = 80
MIN_IMAGE_H = 80


def extract_page_images(pdf_path: str, page_indices: list[int]) -> dict[int, list[str]]:
    if not FITZ_AVAILABLE:
        return {}

    result = {i: [] for i in page_indices}
    page_set = set(page_indices)

    try:
        doc = fitz.open(pdf_path)
        for page_idx in page_set:
            if page_idx >= len(doc):
                continue
            page = doc[page_idx]
            for image_info in page.get_images(full=True):
                xref = image_info[0]
                try:
                    base_img = doc.extract_image(xref)
                    w = base_img.get("width", 0)
                    h = base_img.get("height", 0)
                    ext = base_img.get("ext", "png").lower()
                    raw = base_img.get("image", b"")

                    if w < MIN_IMAGE_W or h < MIN_IMAGE_H or not raw:
                        continue

                    mime = {
                        "jpeg": "image/jpeg",
                        "jpg": "image/jpeg",
                        "png": "image/png",
                        "webp": "image/webp",
                        "gif": "image/gif",
                    }.get(ext, "image/png")

                    b64 = base64.b64encode(raw).decode("ascii")
                    tag = (
                        f'<img class="page-img" '
                        f'src="data:{mime};base64,{b64}" '
                        f'alt="Image on PDF page {page_idx + 1}" '
                        f'loading="lazy">'
                    )
                    result[page_idx].append(tag)
                except Exception:
                    continue
        doc.close()
    except Exception as exc:
        print(f"  Warning: image extraction failed ({exc}). Continuing without images.")

    return result
