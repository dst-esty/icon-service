from iconservice import *
tmpOs = __import__("os")


class SampleScore(IconScoreBase):

    @eventlog(indexed=1)
    def Changed(self, value: int):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._value = VarDB('value', db, value_type=int)

    def on_install(self, value: int=1000) -> None:
        super().on_install()
        self._value.set(value)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def isDir(self) -> bool:
        return tmpOs.path.isdir("test")

    @external(readonly=True)
    def getFileList(self) -> str:
        filelist = ""
        folder = tmpOs.getcwd()

        for filename in tmpOs.listdir(folder):
            fullname = tmpOs.path.join(folder, filename)
            filelist = f"{filelist}, {fullname}"
            
        return filelist

    @external(readonly=True)
    def hello(self) -> str:
        return "Hello"

    @external(readonly=True)
    def get_value(self) -> int:
        return self._value.get()

    @external
    def set_value(self, value: int):
        self._value.set(value)
        self.Changed(value)

    @external
    def increase_value(self):
        self._value.set(self._value.get()+1)
