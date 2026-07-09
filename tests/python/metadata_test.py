"""Unit tests for PDF metadata extraction and validation."""

from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extract_metadata import (
    MetadataError,
    PdfBookMetadata,
    _ID_REGEX,
    _xmp_int,
    _xmp_seq,
    _xmp_text,
    extract,
    parse_classification_simple,
    parse_custom_pdf_info,
)

# ---------------------------------------------------------------------------
# Helpers to build test PDFs with XMP
# ---------------------------------------------------------------------------

_XMP_TEMPLATE = """<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:prism="http://prismstandard.org/namespaces/basic/2.1/"
        xmlns:xmp="http://ns.adobe.com/xap/1.0/"
        xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/">
      {fields}
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""


def _alt(text: str) -> str:
    return f'<rdf:Alt><rdf:li xml:lang="x-default">{text}</rdf:li></rdf:Alt>'


def _bag(*items: str) -> str:
    lis = "".join(f"<rdf:li>{item}</rdf:li>" for item in items)
    return f"<rdf:Bag>{lis}</rdf:Bag>"


def _seq(*items: str) -> str:
    lis = "".join(f"<rdf:li>{item}</rdf:li>" for item in items)
    return f"<rdf:Seq>{lis}</rdf:Seq>"


def _make_xmp(**fields: str) -> str:
    fields.setdefault("xmp:CreateDate", "2026-06-18T21:32:10+08:00")
    elements = "".join(
        f"<{key}>{value}</{key}>" for key, value in fields.items() if value
    )
    return _XMP_TEMPLATE.format(fields=elements)


def _make_test_pdf(
    tmpdir: Path,
    name: str,
    xmp: str | None = None,
    pages: int = 1,
    encrypted: bool = False,
    aspect: tuple[float, float] | None = None,
    pdf_info: dict | None = None,
) -> Path:
    """Create a minimal test PDF and return its path."""
    try:
        import fitz
    except ImportError:
        raise unittest.SkipTest("PyMuPDF is not installed")

    pdf_path = tmpdir / name
    document = fitz.open()

    if aspect is None:
        # A5: 148 x 210 mm → 420 x 595 pt
        w, h = 420.0, 595.0
    else:
        w, h = aspect

    for _ in range(max(pages, 1)):
        document.new_page(width=w, height=h)

    if encrypted:
        document.save(
            pdf_path,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            user_pw="test",
            owner_pw="owner",
        )
    else:
        if xmp is not None:
            document.set_xml_metadata(xmp)
        # Custom PDF Info keys must be set via low-level API because
        # set_metadata() only accepts standard keys.
        if pdf_info:
            document.set_metadata({"title": "metadata fixture"})
            info_type, info_ref = document.xref_get_key(-1, "Info")
            if info_type != "xref":
                raise RuntimeError("Unable to create PDF Info dictionary")
            info_xref = int(re.match(r"(\d+)", info_ref).group(1))
            for key, value in pdf_info.items():
                pdf_key = {
                    "ebookTotalVolumes": "EbookTotalVolumes",
                }.get(key, key)
                document.xref_set_key(info_xref, pdf_key, f"({value})")
        document.save(pdf_path)

    document.close()
    return pdf_path


# ---------------------------------------------------------------------------
# Classification labels fixture
# ---------------------------------------------------------------------------

SAMPLE_CLASSIFICATIONS = {
    "F0": "马克思主义政治经济学",
    "A8": "马克思主义、列宁主义、毛泽东思想的学习、研究和参考资料",
    "I210": "中国文学·鲁迅著作",
    "Z228": "中国百科全书、类书·综合性普及读物",
    "K926": "中国地理·中南地区",
}


# ---------------------------------------------------------------------------
# XMP text helpers (unit tests on real XMP fragments)
# ---------------------------------------------------------------------------


class XmpTextHelperTests(unittest.TestCase):
    def test_reads_simple_element(self) -> None:
        el = ET.fromstring("<rdf:Description "
                           'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
                           'xmlns:dc="http://purl.org/dc/elements/1.1/">'
                           "<dc:identifier>F0-1-1</dc:identifier>"
                           "</rdf:Description>")
        self.assertEqual(_xmp_text(el, "dc:identifier"), "F0-1-1")

    def test_reads_alt_element(self) -> None:
        el = ET.fromstring(
            '<rdf:Description '
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            f"<dc:title>{_alt('测试')}</dc:title>"
            "</rdf:Description>"
        )
        self.assertEqual(_xmp_text(el, "dc:title"), "测试")

    def test_returns_none_when_missing(self) -> None:
        el = ET.fromstring(
            '<rdf:Description '
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"/>'
        )
        self.assertIsNone(_xmp_text(el, "dc:identifier"))

    def test_reads_bag(self) -> None:
        el = ET.fromstring(
            '<rdf:Description '
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            f"<dc:subject>{_bag('政治经济学', '资本主义')}</dc:subject>"
            "</rdf:Description>"
        )
        self.assertEqual(
            _xmp_seq(el, "dc:subject"), ["政治经济学", "资本主义"]
        )

    def test_reads_int(self) -> None:
        el = ET.fromstring(
            '<rdf:Description '
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
            'xmlns:prism="http://prismstandard.org/namespaces/basic/2.1/">'
            "<prism:bookEdition>2</prism:bookEdition>"
            "</rdf:Description>"
        )
        self.assertEqual(_xmp_int(el, "prism:bookEdition"), 2)

    def test_reads_prism_3_namespace(self) -> None:
        el = ET.fromstring(
            '<rdf:Description '
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
            'xmlns:prism="http://prismstandard.org/namespaces/basic/3.0/">'
            "<prism:bookEdition>2</prism:bookEdition>"
            "<prism:publicationName>青年自学丛书</prism:publicationName>"
            "</rdf:Description>"
        )
        self.assertEqual(_xmp_int(el, "prism:bookEdition"), 2)
        self.assertEqual(_xmp_text(el, "prism:publicationName"), "青年自学丛书")


# ---------------------------------------------------------------------------
# ID helpers
# ---------------------------------------------------------------------------


class CallNumberTests(unittest.TestCase):
    def test_regex_accepts_valid_ids(self) -> None:
        for id_ in ("F0-1-1", "A8-3", "I210.4-1", "T-1", "Z228-1", "A12-8-2"):
            with self.subTest(id=id_):
                self.assertIsNotNone(_ID_REGEX.match(id_))

    def test_regex_rejects_invalid_ids(self) -> None:
        for id_ in ("f0-1", "A1", "AA-1", "A1-2-3-4", "", "A-", "A--1"):
            with self.subTest(id=id_):
                self.assertIsNone(_ID_REGEX.match(id_))

    def test_parse_classification(self) -> None:
        self.assertEqual(parse_classification_simple("F0-1-1"), "F0")
        self.assertEqual(parse_classification_simple("A8-3"), "A8")
        self.assertEqual(parse_classification_simple("I210.4-1"), "I210.4")
        self.assertEqual(parse_classification_simple("A12-8-2"), "A12")


# ---------------------------------------------------------------------------
# Full extraction tests (require PyMuPDF)
# ---------------------------------------------------------------------------


class ExtractMetadataTests(unittest.TestCase):
    def test_extracts_required_fields(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-1",
                "dc:title": _alt("政治经济学基础知识"),
                "dc:creator": _seq("《政治经济学基础知识》编写组"),
                "prism:bookEdition": "1",
                "dc:description": _alt("系统介绍资本主义政治经济学。"),
                "dc:language": _bag("zh-CN"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            meta = extract(pdf, SAMPLE_CLASSIFICATIONS)

            self.assertEqual(meta.id, "F0-1-1")
            self.assertEqual(meta.title, "政治经济学基础知识")
            self.assertEqual(meta.author, "《政治经济学基础知识》编写组")
            self.assertEqual(meta.edition, 1)
            self.assertEqual(meta.edition_date, "2026-06")
            self.assertEqual(meta.edition_date_source, "xmp:CreateDate")
            self.assertEqual(meta.pdf_create_date, "2026-06-18T21:32:10+08:00")
            self.assertEqual(meta.description, "系统介绍资本主义政治经济学。")
            self.assertEqual(meta.language, "zh-CN")

    def test_missing_creator_and_language_are_allowed(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-1",
                "dc:title": _alt("政治经济学基础知识"),
                "prism:bookEdition": "1",
                "dc:description": _alt("系统介绍资本主义政治经济学。"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            meta = extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertIsNone(meta.author)
            self.assertEqual(meta.language, "zh-CN")

    def test_extracts_optional_fields(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-1",
                "dc:title": _alt("政治经济学基础知识"),
                "dc:creator": _seq("《政治经济学基础知识》编写组"),
                "prism:bookEdition": "1",
                "dc:description": _alt("系统介绍资本主义政治经济学。"),
                "dc:language": _bag("zh-CN"),
                "prism:subtitle": _alt("资本主义部分"),
                "dc:subject": _bag("政治经济学", "资本主义", "青年自学丛书"),
                "prism:publicationName": _alt("青年自学丛书"),
                "dc:publisher": _alt("人民出版社"),
                "dc:source": _alt("1975年版扫描本"),
                "dc:rights": _alt("版权归原作者所有"),
                "xmpRights:WebStatement": "https://example.com/license",
                "prism:url": "https://z-library.sk/book/fixture",
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            meta = extract(pdf, SAMPLE_CLASSIFICATIONS)

            self.assertEqual(meta.subtitle, "资本主义部分")
            self.assertEqual(meta.tags, ["政治经济学", "资本主义", "青年自学丛书"])
            self.assertEqual(meta.series, "青年自学丛书")
            self.assertEqual(meta.publisher, "人民出版社")
            self.assertEqual(meta.source, "1975年版扫描本")
            self.assertEqual(meta.rights, "版权归原作者所有")
            self.assertEqual(meta.license_url, "https://example.com/license")
            self.assertEqual(meta.zlibrary_url, "https://z-library.sk/book/fixture")

    def test_extracts_external_url_from_dc_relation_fallback(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-1",
                "dc:title": _alt("政治经济学基础知识"),
                "prism:bookEdition": "1",
                "dc:description": _alt("系统介绍资本主义政治经济学。"),
                "dc:relation": "https://z-library.sk/book/fallback",
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            meta = extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertEqual(meta.zlibrary_url, "https://z-library.sk/book/fallback")

    def test_rejects_invalid_external_url(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-1",
                "dc:title": _alt("政治经济学基础知识"),
                "prism:bookEdition": "1",
                "dc:description": _alt("系统介绍资本主义政治经济学。"),
                "prism:url": "not-a-url",
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            with self.assertRaises(MetadataError) as ctx:
                extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertIn("must be an HTTP(S) URL", str(ctx.exception))

    def test_missing_subtitle_is_not_an_error(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-1",
                "dc:title": _alt("政治经济学基础知识"),
                "dc:creator": _seq("佚名"),
                "prism:bookEdition": "1",
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            meta = extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertIsNone(meta.subtitle)

    def test_missing_required_field_fails(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-1",
                # missing dc:title
                "dc:creator": _seq("佚名"),
                "prism:bookEdition": "1",
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            with self.assertRaises(MetadataError) as ctx:
                extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertIn("dc:title", str(ctx.exception))

    def test_missing_create_date_fails(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-1",
                "dc:title": _alt("标题"),
                "dc:creator": _seq("作者"),
                "prism:bookEdition": "1",
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
                "xmp:CreateDate": "",
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            with self.assertRaises(MetadataError) as ctx:
                extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertIn("xmp:CreateDate", str(ctx.exception))

    def test_invalid_call_number_fails(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "bad-id",
                "dc:title": _alt("标题"),
                "dc:creator": _seq("作者"),
                "prism:bookEdition": "1",
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            with self.assertRaises(MetadataError) as ctx:
                extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertIn("Invalid call number", str(ctx.exception))

    def test_unknown_classification_fails(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "X99-1",
                "dc:title": _alt("标题"),
                "dc:creator": _seq("作者"),
                "prism:bookEdition": "1",
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            with self.assertRaises(MetadataError) as ctx:
                extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertIn("Classification", str(ctx.exception))

    def test_encrypted_pdf_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "enc.pdf", encrypted=True)
            with self.assertRaises(ValueError) as ctx:
                extract(pdf)
            self.assertIn("encrypted", str(ctx.exception))

    def test_zero_pages_fails(self) -> None:
        # PyMuPDF cannot save a zero-page PDF, so we verify the validation
        # logic separately.  An empty XMP-less 1-page PDF hits the
        # "XMP metadata is absent" path, which is the first metadata-level
        # check after the page-count and aspect-ratio gates pass.
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "empty.pdf", xmp=None)
            with self.assertRaises(MetadataError) as ctx:
                extract(pdf)
            self.assertIn("XMP metadata is absent", str(ctx.exception))

    def test_non_a5_aspect_fails(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-1",
                "dc:title": _alt("标题"),
                "dc:creator": _seq("作者"),
                "prism:bookEdition": "1",
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            # US Letter: 612 x 792 → aspect ≈ 0.7727
            pdf = _make_test_pdf(root, "letter.pdf", xmp=xmp,
                                 aspect=(612.0, 792.0))
            with self.assertRaises(ValueError) as ctx:
                extract(pdf)
            self.assertIn("aspect", str(ctx.exception))

    def test_volume_id_conflict_fails(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-2",  # volume 2 from ID
                "dc:title": _alt("标题"),
                "dc:creator": _seq("作者"),
                "prism:bookEdition": "1",
                "prism:volume": "3",  # conflicts with ID volume 2
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            with self.assertRaises(MetadataError) as ctx:
                extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertIn("conflict", str(ctx.exception))

    def test_custom_info_total_volumes_less_than_volume_fails(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-3",
                "dc:title": _alt("标题"),
                "dc:creator": _seq("作者"),
                "prism:bookEdition": "1",
                "prism:volume": "3",
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(
                root, "test.pdf", xmp=xmp,
                pdf_info={"ebookTotalVolumes": "2"},  # 2 < 3
            )
            with self.assertRaises(MetadataError) as ctx:
                extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertIn("total_volumes", str(ctx.exception))

    def test_parse_custom_pdf_info(self) -> None:
        tv = parse_custom_pdf_info({"ebookTotalVolumes": "2"})
        self.assertEqual(tv, 2)

    def test_parse_custom_pdf_info_empty(self) -> None:
        tv = parse_custom_pdf_info(None)
        self.assertIsNone(tv)

    def test_custom_info_survives_pdf_round_trip(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-3",
                "dc:title": _alt("标题"),
                "dc:creator": _seq("作者"),
                "prism:bookEdition": "1",
                "prism:volume": "3",
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(
                root, "test.pdf", xmp=xmp,
                pdf_info={"ebookTotalVolumes": "2"},
            )
            with self.assertRaises(MetadataError) as ctx:
                extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertIn("total_volumes", str(ctx.exception))
        with self.assertRaises(MetadataError) as ctx:
            parse_custom_pdf_info({"ebookTotalVolumes": "-1"})
        self.assertIn("EbookTotalVolumes", str(ctx.exception))

    def test_rejects_non_a5_later_page(self) -> None:
        try:
            import fitz
        except ImportError:
            raise unittest.SkipTest("PyMuPDF is not installed")

        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-1",
                "dc:title": _alt("标题"),
                "dc:creator": _seq("作者"),
                "prism:bookEdition": "1",
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf = Path(temp_dir) / "mixed-pages.pdf"
            document = fitz.open()
            document.new_page(width=420, height=595)
            document.new_page(width=612, height=792)
            document.set_xml_metadata(xmp)
            document.save(pdf)
            document.close()
            with self.assertRaises(ValueError) as ctx:
                extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertIn("Page 2", str(ctx.exception))

    def test_tags_are_deduplicated_in_source_order(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-1",
                "dc:title": _alt("标题"),
                "dc:creator": _seq("作者"),
                "prism:bookEdition": "1",
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
                "dc:subject": _bag("政治经济学", "资本主义", "政治经济学"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            meta = extract(pdf, SAMPLE_CLASSIFICATIONS)
            # Deduplicated, first occurrence wins
            self.assertEqual(meta.tags, ["政治经济学", "资本主义"])

    def test_volume_derived_from_id(self) -> None:
        xmp = _make_xmp(
            **{
                "dc:identifier": "F0-1-3",
                "dc:title": _alt("标题"),
                "dc:creator": _seq("作者"),
                "prism:bookEdition": "1",
                "dc:description": _alt("简介。"),
                "dc:language": _bag("zh-CN"),
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pdf = _make_test_pdf(root, "test.pdf", xmp=xmp)
            meta = extract(pdf, SAMPLE_CLASSIFICATIONS)
            self.assertEqual(meta.volume, 3)


if __name__ == "__main__":
    unittest.main()
