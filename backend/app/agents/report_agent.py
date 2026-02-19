"""Report Agent — generates professional branded reports.

Supports PDF (WeasyPrint), PPTX (python-pptx), and Excel (openpyxl).
5 report types: executive, rssi, vendor_scorecard, dora_register, benchmark.
Files are saved to MinIO object storage.
"""

import io
import logging
import time
from typing import Any

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.celery_app import celery_app
from app.config import settings

logger = logging.getLogger("mh_cyberscore.agents.report")

REPORT_TYPES = {
    "executive": {
        "name": "Rapport Exécutif COMEX",
        "default_format": "pptx",
        "template": "executive_report.html",
    },
    "rssi": {
        "name": "Rapport RSSI Détaillé",
        "default_format": "pdf",
        "template": "rssi_report.html",
    },
    "vendor_scorecard": {
        "name": "Scorecard Fournisseur",
        "default_format": "pdf",
        "template": "vendor_scorecard.html",
    },
    "dora_register": {
        "name": "Registre DORA (ACPR)",
        "default_format": "xlsx",
        "template": "dora_register.html",
    },
    "benchmark": {
        "name": "Rapport Benchmark Sectoriel",
        "default_format": "pdf",
        "template": "rssi_report.html",
    },
}


class ReportAgent(BaseAgent):
    """Generates branded reports in PDF, PPTX, and Excel formats."""

    def __init__(self) -> None:
        super().__init__(name="report", timeout=120.0)

    async def execute(self, vendor_id: str, **kwargs: Any) -> AgentResult:
        """Generate a report.

        Args:
            vendor_id: Vendor UUID (nullable for portfolio reports).
            **kwargs: report_type, format, user_id.

        Returns:
            AgentResult with file path and metadata.
        """
        report_type = kwargs.get("report_type", "vendor_scorecard")
        fmt = kwargs.get("format", REPORT_TYPES[report_type]["default_format"])
        user_id = kwargs.get("user_id", "system")
        start = time.monotonic()

        self.logger.info(
            "Generating %s report (%s) for vendor %s",
            report_type,
            fmt,
            vendor_id,
        )

        try:
            if fmt == "pdf":
                file_path = await self._generate_pdf(report_type, vendor_id)
            elif fmt == "pptx":
                file_path = await self._generate_pptx(report_type, vendor_id)
            elif fmt == "xlsx":
                file_path = await self._generate_xlsx(report_type, vendor_id)
            else:
                file_path = await self._generate_pdf(report_type, vendor_id)

            duration = time.monotonic() - start
            return AgentResult(
                agent_name=self.name,
                vendor_id=vendor_id,
                success=True,
                data={
                    "file_path": file_path,
                    "report_type": report_type,
                    "format": fmt,
                    "generated_by": user_id,
                },
                duration_seconds=round(duration, 2),
            )
        except Exception as exc:
            duration = time.monotonic() - start
            return AgentResult(
                agent_name=self.name,
                vendor_id=vendor_id,
                success=False,
                errors=[str(exc)],
                duration_seconds=round(duration, 2),
            )

    async def _generate_pdf(
        self, report_type: str, vendor_id: str
    ) -> str:
        """Generate PDF via WeasyPrint (HTML template -> PDF).

        Renders a Jinja2 HTML template with vendor data and converts
        to PDF via WeasyPrint. Uploads the result to MinIO.
        """
        from jinja2 import Environment, FileSystemLoader, select_autoescape
        from weasyprint import HTML

        template_name = REPORT_TYPES[report_type]["template"]
        env = Environment(
            loader=FileSystemLoader("app/templates/reports"),
            autoescape=select_autoescape(["html"]),
        )
        template = env.get_template(template_name)
        html_content = template.render(
            vendor_id=vendor_id,
            report_type=report_type,
            report_name=REPORT_TYPES[report_type]["name"],
            generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        pdf_bytes = HTML(string=html_content).write_pdf()
        object_key = f"reports/{vendor_id}/{report_type}.pdf"
        await self._upload_to_minio(object_key, pdf_bytes, "application/pdf")
        return object_key

    async def _generate_pptx(
        self, report_type: str, vendor_id: str
    ) -> str:
        """Generate PPTX via python-pptx."""
        from pptx import Presentation
        from pptx.util import Inches, Pt

        prs = Presentation()
        # Title slide
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = REPORT_TYPES[report_type]["name"]
        slide.placeholders[1].text = (
            f"Fournisseur: {vendor_id}\n"
            f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Content slide placeholder
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = "Score Global"
        slide.placeholders[1].text = "Données de scoring à charger depuis la base."

        buffer = io.BytesIO()
        prs.save(buffer)
        pptx_bytes = buffer.getvalue()

        object_key = f"reports/{vendor_id}/{report_type}.pptx"
        await self._upload_to_minio(
            object_key, pptx_bytes,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        return object_key

    async def _generate_xlsx(
        self, report_type: str, vendor_id: str
    ) -> str:
        """Generate Excel via openpyxl."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = REPORT_TYPES[report_type]["name"]

        # Header row
        headers = ["Fournisseur", "Domaine", "Score", "Grade", "Date"]
        ws.append(headers)

        # Placeholder data row
        ws.append([vendor_id, "-", "-", "-", time.strftime("%Y-%m-%d")])

        buffer = io.BytesIO()
        wb.save(buffer)
        xlsx_bytes = buffer.getvalue()

        object_key = f"reports/{vendor_id}/{report_type}.xlsx"
        await self._upload_to_minio(
            object_key, xlsx_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        return object_key

    async def _upload_to_minio(
        self, object_key: str, data: bytes, content_type: str,
    ) -> None:
        """Upload a file to MinIO object storage.

        Args:
            object_key: S3-style object key (path).
            data: File bytes.
            content_type: MIME type.
        """
        try:
            from minio import Minio

            client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=False,
            )
            bucket = settings.minio_bucket
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)

            client.put_object(
                bucket,
                object_key,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            self.logger.info("Uploaded %s to MinIO (%d bytes)", object_key, len(data))
        except Exception as exc:
            self.logger.warning(
                "MinIO upload failed for %s, saving locally: %s", object_key, exc
            )
            # Fallback: save locally
            import os
            local_path = os.path.join("data", object_key)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(data)


@celery_app.task(name="app.agents.report_agent.generate_report")
def generate_report(
    report_type: str,
    vendor_id: str = "",
    user_id: str = "system",
    fmt: str = "",
) -> dict[str, Any]:
    """Celery task: generate a report."""
    import asyncio

    agent = ReportAgent()
    result = asyncio.run(
        agent.execute(
            vendor_id,
            report_type=report_type,
            format=fmt or REPORT_TYPES[report_type]["default_format"],
            user_id=user_id,
        )
    )
    return result.data
