from io import StringIO


class DataWriter(StringIO):
    def __init__(self, terminal, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.terminal = terminal

    def write(self, __text: str) -> int:
        self.terminal.write(__text)
        return super().write(__text)
