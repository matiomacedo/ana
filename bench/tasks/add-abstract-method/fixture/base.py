class Exporter:
    def export(self, rows):
        return self.render(rows)

    def render(self, rows):
        raise NotImplementedError
