class Exporter:
    def export(self, rows):
        return self.render(rows)

    def render(self, rows):
        raise NotImplementedError

    def extension(self):
        raise NotImplementedError

    def filename(self, stem):
        return f"{stem}.{self.extension()}"
