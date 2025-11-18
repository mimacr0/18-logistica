
class SafeDict:
    def __init__(self, data):
        self._data = data

    def __getattr__(self, key):
        if isinstance(self._data, dict):
            return SafeDict(self._data.get(key, None))
        return SafeDict(None)

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __call__(self):
        return self._data

    def __repr__(self):
        return f"SafeDict({self._data})"

    def __bool__(self):
        return bool(self._data)
