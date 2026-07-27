from base import Exporter


class CsvExporter(Exporter):
    def render(self, rows):
        return "\n".join(",".join(r) for r in rows)

    def extension(self):
        return "csv"

    def filename(self, stem):
        return f"{stem}.{self.extension()}"
